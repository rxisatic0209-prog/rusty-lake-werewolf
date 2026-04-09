from copy import deepcopy
import random

import regis


# `role_id` 是狼人杀规则身份。
# `role_name` 是这张身份牌在锈湖世界里的化身名字。
WOLF_ROLE = {
    "role_id": "wolf",
    "role_name": "腐败灵魂",
    "team": "dark",
    "tools": [regis.extract_memory],
    "desc": "狼人。目标杀光好人。",
}


LIGHT_ROLES = [
    {
        "role_id": "witch",
        "role_name": "Laura",
        "team": "light",
        "tools": [regis.laura_shift],
        "desc": "女巫。",
    },
    {
        "role_id": "seer",
        "role_name": "Ida",
        "team": "light",
        "tools": [regis.gaze_into_crystal],
        "desc": "预言家。",
    },
    {
        "role_id": "crow",
        "role_name": "Mary",
        "team": "light",
        "tools": [regis.mary_curse],
        "desc": "乌鸦。",
    },
    {
        "role_id": "hunter",
        "role_name": "Albert",
        "team": "light",
        "tools": [],
        "desc": "猎人。",
    },
    {
        "role_id": "villager",
        "role_name": "祭司",
        "team": "light",
        "tools": [],
        "desc": "平民。",
    },
]


def build_standard_role_pool():
    """构造标准 6 人局身份池：2 狼 + 4 张随机好人身份牌。"""
    role_pool = [deepcopy(WOLF_ROLE), deepcopy(WOLF_ROLE)]
    role_pool.extend(deepcopy(role) for role in random.sample(LIGHT_ROLES, 4))
    random.shuffle(role_pool)
    return role_pool
