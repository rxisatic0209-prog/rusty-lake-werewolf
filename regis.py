import rules


def extract_memory(target: str):
    """【腐败灵魂】夜晚选择一名存活的好人作为献祭目标。"""
    ok, msg = rules.set_night_kill(target)
    if not ok:
        return msg
    return f"【系统】：{target} 已被列为今夜的献祭目标。"


def laura_shift(target: str, form: str):
    """【Laura】form 支持 heal/poison，可救回狼人目标或毒杀一名存活者。"""
    form = (form or "").strip().lower()
    if form in {"laura", "heal"}:
        ok, msg = rules.set_protected_target(target)
        if not ok:
            return msg
        return f"【白光】：你守护了 {target}。"

    if form not in {"poison", "soul"}:
        return "未知的药剂形态。请使用 heal 或 poison。"
    ok, msg = rules.set_poison_target(target)
    if not ok:
        return msg
    return f"【腐败】：你毒杀了 {target}。"


def gaze_into_crystal(target: str):
    """【Ida】查验一名存活玩家的阵营，结果只返回 light 或 dark。"""
    ok, msg = rules.inspect_team(target)
    if not ok:
        return msg
    return f"【水晶球】：{target} 属于 {msg}。"


def mary_curse(target: str):
    """【Mary】白天为一名存活玩家追加一票诅咒。"""
    ok, msg = rules.set_cursed_player(target)
    if not ok:
        return msg
    return f"【黑羽】：诅咒已落在 {target} 身上。"


def cast_vote(voter: str, target: str):
    """白天投票。"""
    ok, msg = rules.record_vote(voter, target)
    if not ok:
        return msg
    return f"【投票】：{voter} 把票投给了 {target}。"


def resolve_night():
    """结算夜晚死亡。"""
    deaths = []

    night_kill = RITUAL_STATE["night_kill"]
    protected = RITUAL_STATE["protected_target"]
    poison_target = RITUAL_STATE["poison_target"]

    if night_kill != "无" and night_kill != protected:
        deaths.append(night_kill)
        _record_death(night_kill, "wolf")

    if poison_target != "无":
        if poison_target not in deaths:
            deaths.append(poison_target)
        _record_death(poison_target, "poison")

    for target in deaths:
        if target in RITUAL_STATE["alive_players"]:
            RITUAL_STATE["alive_players"].remove(target)

    return deaths


def resolve_day():
    """结算白天放逐。乌鸦诅咒为目标追加一票。"""
    tally = {}
    for target in RITUAL_STATE["votes"].values():
        tally[target] = tally.get(target, 0) + 1

    cursed = RITUAL_STATE["cursed_player"]
    if cursed != "无" and cursed in RITUAL_STATE["alive_players"]:
        tally[cursed] = tally.get(cursed, 0) + 1

    if not tally:
        RITUAL_STATE["cursed_player"] = "无"
        return None, tally

    top_votes = max(tally.values())
    top_targets = [target for target, count in tally.items() if count == top_votes]
    if len(top_targets) != 1:
        RITUAL_STATE["cursed_player"] = "无"
        return None, tally

    eliminated = top_targets[0]
    if eliminated in RITUAL_STATE["alive_players"]:
        RITUAL_STATE["alive_players"].remove(eliminated)
        _record_death(eliminated, "vote")

    RITUAL_STATE["cursed_player"] = "无"
    return eliminated, tally
