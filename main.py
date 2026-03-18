import asyncio
import sys
import os

# 确保导入本地模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from config import model_client, RUSTY_STYLE
from personas import get_role_persona
from roles import build_standard_role_pool
import rules
import regis


def build_vote_tool(voter_name: str):
    def cast_vote(target: str):
        """白天投票给一名存活玩家。参数示例：P3。"""
        return regis.cast_vote(voter_name, target)

    cast_vote.__name__ = "cast_vote"
    cast_vote.__doc__ = "白天投票给一名存活玩家。参数示例：P3。"
    return cast_vote


def is_alive(player_name: str) -> bool:
    return rules.is_alive(player_name)


def alive_players():
    return rules.alive_players()


def prompt_user_target(prompt: str, excluded=None, allow_skip: bool = True):
    excluded = set(excluded or [])
    while True:
        options = [name for name in alive_players() if name not in excluded]
        if not options:
            return None
        raw = input(f"{prompt} ({', '.join(options)})：").strip()
        if not raw and allow_skip:
            return None
        if raw in options:
            return raw
        print("⚠️ 请输入存活玩家编号。")


def print_alive_banner():
    print(f"🕯️ 当前存活：{', '.join(alive_players())}")


async def main():
    try:
        # --- 1. 标准 6 人局身份池 ---
        player_count = 6
        selected_chars = build_standard_role_pool()
        
        positions = [f"P{i}" for i in range(1, player_count + 1)]
        my_no = positions[0] # 你固定在 P1
        
        all_players_dict = {}
        agents_by_name = {}
        all_agents = []
        my_info = {}
        role_to_player = {}

        # 预先找出所有狼人的名字，方便注入
        dark_names = [positions[i] for i, c in enumerate(selected_chars) if c['team'] == 'dark']

        # --- 3. 实例化 Agent ---
        for no, char in zip(positions, selected_chars):
            is_me = (no == my_no)
            persona = get_role_persona(char["role_id"])
            prompt_text = (
                f"{RUSTY_STYLE}\n"
                f"你是座位 {no}，化身【{char['role_name']}】。{char['desc']}\n"
                f"你的人设：{persona['persona']}\n"
                f"你的说话风格：{persona['speaking_style']}\n"
                f"你的行为原则：{persona['behavior']}"
            )
            
            # 如果是狼人，注入队友信息
            if char['team'] == "dark":
                teammates = [n for n in dark_names if n != no]
                prompt_text += f"\n你的狼人队友是：{', '.join(teammates)}。夜晚请在密谈中合谋，并由其中一人执行工具。"

            if is_me:
                player = UserProxyAgent(name=no)
                my_info = char
            else:
                tools = list(char["tools"]) + [build_vote_tool(no)]
                player = AssistantAgent(
                    name=no, 
                    model_client=model_client, 
                    system_message=prompt_text,
                    tools=tools
                )
            
            all_players_dict[no] = char
            agents_by_name[no] = player
            role_to_player[char["role_name"]] = no
            all_agents.append(player)
        
        rules.reset_ritual_state(
            alive_players=[p.name for p in all_agents],
            player_teams={name: info["team"] for name, info in all_players_dict.items()},
        )

        god = AssistantAgent(
            name="Mr_Owl",
            model_client=model_client,
            system_message=f"{RUSTY_STYLE}\n你是上帝 Mr. Owl。负责主持夜晚、计票和判定。"
        )

        # --- 4. 游戏流程 ---
        print("\n" + "█" * 45)
        print(f"  🎭 你的编号：{my_no} | 化身：【{my_info['role_name']}】")
        if my_info['team'] == "dark":
            print(f"  🐺 你的队友：{', '.join([n for n in dark_names if n != my_no])}")
        print(f"  📜 你的宿命：{my_info['desc']}")
        print("█" * 45 + "\n")

        round_no = 1
        while True:
            dark_alive, light_alive = rules.victory_state()
            if not dark_alive:
                print("\n🏆 【光明阵营胜利】")
                break
            if len(dark_alive) >= len(light_alive):
                print("\n🏆 【黑暗阵营胜利】")
                break

            rules.start_night()
            print(f"\n🌑 第 {round_no} 夜：往生室再度沉入黑暗。")

            # [狼人行动]
            dark_alive_agents = [agents_by_name[name] for name in dark_alive]
            if dark_alive_agents:
                dark_team = RoundRobinGroupChat(dark_alive_agents + [god], max_turns=5)
                wolf_task = "商议献祭目标，只能针对存活好人。达成一致后由一人执行 extract_memory。"
                if my_info["team"] == "dark" and is_alive(my_no):
                    async for msg in dark_team.run_stream(task=wolf_task):
                        if msg.content:
                            print(f"🔒 [低语] {msg.source}: {msg.content}")
                    wolf_target = prompt_user_target("🌘 输入你最终要献祭的目标，留空沿用狼群决定", excluded=dark_alive)
                    if wolf_target:
                        print(regis.extract_memory(wolf_target))
                else:
                    await dark_team.run(task=wolf_task)
                    print(" (你听到了墙壁里齿轮转动的声音...)")

            # [预言家行动]
            ida_no = role_to_player.get("Ida")
            if ida_no and is_alive(ida_no):
                if ida_no == my_no:
                    target = prompt_user_target("🔮 输入你要查验的目标", excluded={my_no})
                    if target:
                        print(regis.gaze_into_crystal(target))
                else:
                    ida_phase = RoundRobinGroupChat([agents_by_name[ida_no], god], max_turns=2)
                    await ida_phase.run(task="选择一名存活玩家，并使用 gaze_into_crystal 查验其阵营。")

            # [女巫行动]
            laura_no = role_to_player.get("Laura")
            if laura_no and is_alive(laura_no):
                night_target = rules.RITUAL_STATE["night_kill"]
                if laura_no == my_no:
                    print(f"🧪 今夜被献祭的目标：{night_target}")
                    choice = input("输入 heal / poison / skip：").strip().lower()
                    if choice == "heal" and night_target != "无":
                        print(regis.laura_shift(night_target, "heal"))
                    elif choice == "poison":
                        poison_target = prompt_user_target("☠️ 输入你要毒杀的目标", excluded=None)
                        if poison_target:
                            print(regis.laura_shift(poison_target, "poison"))
                else:
                    laura_phase = RoundRobinGroupChat([agents_by_name[laura_no], god], max_turns=3)
                    await laura_phase.run(
                        task=(
                            f"今夜被献祭的目标是 {night_target}。"
                            "若要救人，只能对该目标使用 laura_shift(target, 'heal')。"
                            "若要毒人，使用 laura_shift(target, 'poison')。不行动则保持沉默。"
                        )
                    )

            # [乌鸦行动]
            mary_no = role_to_player.get("Mary")
            if mary_no and is_alive(mary_no):
                if mary_no == my_no:
                    curse_target = prompt_user_target("🪶 输入你要诅咒的目标", excluded={my_no})
                    if curse_target:
                        print(regis.mary_curse(curse_target))
                else:
                    mary_phase = RoundRobinGroupChat([agents_by_name[mary_no], god], max_turns=2)
                    await mary_phase.run(task="选择一名存活玩家，并使用 mary_curse 为其追加一票诅咒。")

            # [黎明结算]
            protected_target = rules.RITUAL_STATE["protected_target"]
            night_deaths = rules.resolve_night()
            if night_deaths:
                print(f"\n☀️ 天亮了。昨晚牺牲的是：{', '.join(night_deaths)}")
            elif rules.RITUAL_STATE["night_kill"] != "无" and protected_target == rules.RITUAL_STATE["night_kill"]:
                print("\n☀️ 天亮了。白光降临，被献祭者被挽回，无人死亡。")
            else:
                print("\n☀️ 天亮了。昨夜无人死亡。")
            print_alive_banner()

            dark_alive, light_alive = rules.victory_state()
            if not dark_alive:
                print("\n🏆 【光明阵营胜利】")
                break
            if len(dark_alive) >= len(light_alive):
                print("\n🏆 【黑暗阵营胜利】")
                break

            # [白天辩论与投票]
            rules.start_day()
            alive_agents = [agents_by_name[name] for name in rules.RITUAL_STATE["alive_players"]]
            public_square = SelectorGroupChat(alive_agents + [god], model_client=model_client)

            cursed_player = rules.RITUAL_STATE["cursed_player"]
            if cursed_player != "无":
                print(f"📍 提示：{cursed_player} 被诅咒，白天将额外承受一票。开始辩论。")
            else:
                print("📍 提示：今日没有诅咒加票。开始辩论。")

            debate_task = (
                "我是 Mr. Owl。请每位存活者依次发言。"
                "在自己发言末尾，使用 cast_vote 给一名存活玩家投票。"
                "只能投给存活者，每人仅有一票。"
            )
            async for msg in public_square.run_stream(task=debate_task, max_turns=max(10, len(alive_agents) * 2)):
                if msg.content:
                    print(f"\n📢 [广场] {msg.source}: {msg.content}")

            if is_alive(my_no):
                vote_target = prompt_user_target("🗳️ 输入你的投票目标，留空弃权", excluded=None)
                if vote_target:
                    print(regis.cast_vote(my_no, vote_target))

            eliminated, tally = rules.resolve_day()
            if tally:
                tally_text = " / ".join(f"{target}:{count}" for target, count in sorted(tally.items()))
                print(f"\n📊 票型：{tally_text}")
            else:
                print("\n📊 今日无人投票。")

            if eliminated:
                print(f"⚖️ 放逐结果：{eliminated}")
            else:
                print("⚖️ 放逐结果：平票或无票，今天无人被放逐。")
            print_alive_banner()

            round_no += 1

    except Exception as e:
        print(f"\n⚠️ 仪式中断：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
