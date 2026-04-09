import rules


def extract_memory(target: str):
    """【腐败灵魂】夜晚引诱一名存活的好人一起沉入锈湖。"""
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
        return f"【繁花】：你守护了 {target}。"

    if form not in {"poison", "soul"}:
        return "未知的药剂形态。请使用 heal 或 poison。"
    ok, msg = rules.set_poison_target(target)
    if not ok:
        return msg
    return f"【腐败】：你杀掉了 {target}。"


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
    return f"【天堂岛的诅咒】：诅咒已落在 {target} 身上。"


def cast_vote(voter: str, target: str):
    """白天投票。"""
    ok, msg = rules.record_vote(voter, target)
    if not ok:
        return msg
    return f"【投票】：{voter} 把票投给了 {target}。"
