# state.py
# De “default play state” als dictionary.

# make_initial_play_state() geeft dezelfde keys als je originele play = {...}
# Handig zodat je state consistent blijft en je niet overal defaults dubbel zet.

import random
from constants import WAIT
from config import POPUP_DURATION

def make_initial_play_state():
    return {
        "score": 0.0,
        "phone": False,
        "phone_hold_time": 0.0,
        "gameover": False,
        "caught": False,
        "boss_state": WAIT,
        "boss_timer": 0.0,
        "next_check_in": 3.0,
        "reaction_timer": 0.0,
        "boss_start": (0, 0),
        "boss_end": (0, 0),
        "boss_from_left": True,
        "hands_anim_t": 0.0,
        "hands_anim_frame": 0,
        "pre_walk_sound_started": False,

        "smoking": False,
        "smoking_timer": 0.0,
        "high_timer": 0.0,
        "shake_x": 0,
        "shake_y": 0,
        "hallucination_color": (0, 255, 0),
        "hallucination_timer": 0.0,
    }
