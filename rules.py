from copy import deepcopy


DEFAULT_RITUAL_STATE = {
    "night_kill": "无",
    "protected_target": "无",
    "poison_target": "无",
    "cursed_player": "无",
    "laura_used_heal": False,
    "laura_used_poison": False,
    "how_died": {},
    "alive_players": [],
    "player_teams": {},
    "votes": {},
}


RITUAL_STATE = deepcopy(DEFAULT_RITUAL_STATE)


def reset_ritual_state(alive_players=None, player_teams=None):
    """重置整局状态。"""
    RITUAL_STATE.clear()
    RITUAL_STATE.update(deepcopy(DEFAULT_RITUAL_STATE))
    RITUAL_STATE["alive_players"] = list(alive_players or [])
    RITUAL_STATE["player_teams"] = dict(player_teams or {})


def start_night():
    """清空本夜行动。"""
    RITUAL_STATE["night_kill"] = "无"
    RITUAL_STATE["protected_target"] = "无"
    RITUAL_STATE["poison_target"] = "无"


def start_day():
    """清空本昼投票。"""
    RITUAL_STATE["votes"] = {}


def alive_players():
    return list(RITUAL_STATE["alive_players"])


def is_alive(target: str) -> bool:
    return target in RITUAL_STATE["alive_players"]


def validate_target(target: str, allow_dead: bool = False):
    if not target:
        return False, "目标不能为空。"
    if target not in RITUAL_STATE["player_teams"]:
        return False, f"{target} 不在这场仪式中。"
    if not allow_dead and not is_alive(target):
        return False, f"{target} 已不在存活名单中。"
    return True, ""


def _record_death(target: str, cause: str):
    previous = RITUAL_STATE["how_died"].get(target)
    if not previous:
        RITUAL_STATE["how_died"][target] = cause
    elif cause not in previous.split("+"):
        RITUAL_STATE["how_died"][target] = f"{previous}+{cause}"


def set_night_kill(target: str):
    ok, msg = validate_target(target)
    if not ok:
        return False, msg
    if RITUAL_STATE["player_teams"].get(target) == "dark":
        return False, "黑暗不会吞噬自己的倒影。请选择好人。"
    RITUAL_STATE["night_kill"] = target
    return True, target


def set_protected_target(target: str):
    if RITUAL_STATE["laura_used_heal"]:
        return False, "药水已枯竭。"
    if target != RITUAL_STATE["night_kill"]:
        return False, "白光只能照向今夜被献祭的人。"
    RITUAL_STATE["protected_target"] = target
    RITUAL_STATE["laura_used_heal"] = True
    return True, target


def set_poison_target(target: str):
    if RITUAL_STATE["laura_used_poison"]:
        return False, "药水已枯竭。"
    ok, msg = validate_target(target)
    if not ok:
        return False, msg
    RITUAL_STATE["poison_target"] = target
    RITUAL_STATE["laura_used_poison"] = True
    return True, target


def inspect_team(target: str):
    ok, msg = validate_target(target)
    if not ok:
        return False, msg
    return True, RITUAL_STATE["player_teams"].get(target, "unknown")


def set_cursed_player(target: str):
    ok, msg = validate_target(target)
    if not ok:
        return False, msg
    RITUAL_STATE["cursed_player"] = target
    return True, target


def record_vote(voter: str, target: str):
    ok, msg = validate_target(voter)
    if not ok:
        return False, f"投票无效：{msg}"
    ok, msg = validate_target(target)
    if not ok:
        return False, f"投票无效：{msg}"
    RITUAL_STATE["votes"][voter] = target
    return True, target


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


def victory_state():
    dark_alive = [n for n in RITUAL_STATE["alive_players"] if RITUAL_STATE["player_teams"].get(n) == "dark"]
    light_alive = [n for n in RITUAL_STATE["alive_players"] if RITUAL_STATE["player_teams"].get(n) == "light"]
    return dark_alive, light_alive
