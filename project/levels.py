# levels.py
# Alles dat met level-difficulty en score-doelen te maken heeft.

# make_level_params() maakt de difficulty parameters per level

# level_star_thresholds() + level_complete_score() berekenen targets per level

# score_to_stars() zet score om naar sterren

# schedule_next_check() regelt de timing wanneer de baas komt checken

import random
from config import STAR_1, STAR_2, STAR_3, MAX_HOLD_BONUS
from utils import clamp

def make_level_params(i: int):
    lvl = i + 1

    min_wait = max(0.55, 3.0 - 0.18 * lvl)
    max_wait = max(min_wait + 0.35, 8 - 0.22 * lvl)

    walk_in  = max(0.45, 1.05 - 0.03 * lvl)
    walk_out = max(0.45, walk_in * 0.95)

    look  = min(2.6, 1.15 + 0.10 * lvl)
    grace = max(0.10, 0.58 - 0.03 * lvl)

    if lvl >= 10:
        grace = max(0.08, grace - 0.04)
    elif lvl >= 5:
        grace = max(0.09, grace - 0.02)

    mult = 1.0 + 0.10 * lvl
    return dict(min_wait=min_wait, max_wait=max_wait, walk_in=walk_in, walk_out=walk_out, look=look, grace=grace, mult=mult)

def level_threshold_offset(level_num: int) -> int:
    return max(0, (level_num - 1) * 100)

def level_star_thresholds(level_num: int):
    off = level_threshold_offset(level_num)
    return (STAR_1 + off, STAR_2 + off, STAR_3 + off)

def level_complete_score(level_num: int) -> int:
    return level_star_thresholds(level_num)[2]

def score_to_stars(score_int: int, level_num: int) -> int:
    t1, t2, t3 = level_star_thresholds(level_num)
    if score_int >= t3:
        return 3
    if score_int >= t2:
        return 2
    if score_int >= t1:
        return 1
    return 0

def schedule_next_check(play_state, params):
    BOSS_SOUND_START_OFFSET = 0.5
    play_state["next_check_in"] = random.uniform(params["min_wait"], params["max_wait"]) - BOSS_SOUND_START_OFFSET
    play_state["next_check_in"] = max(0.1, play_state["next_check_in"])
    play_state["pre_walk_sound_started"] = False
