# save_system.py
# Opslaan en laden van progress.

# DEFAULT_SAVE (unlocked, stars, coins, owned, equipped)

# load_save() maakt save backward-compatible (vult missende keys aan)

# write_save() schrijft naar save.json

import json
import os
from config import SAVE_PATH, TOTAL_LEVELS, SHOP_ITEMS
from utils import clamp

DEFAULT_SAVE = {
    "unlocked": 1,
    "stars": [0]*TOTAL_LEVELS,
    "coins": 0,
    "owned": {
        "laptop_default": True,
        "phone_default": True,
    },
    "equipped": {
        "laptop": "laptop_default",
        "phone": "phone_default",
    }
}

def _deepcopy_json(x):
    return json.loads(json.dumps(x))

def load_save():
    if not os.path.exists(SAVE_PATH):
        return _deepcopy_json(DEFAULT_SAVE)
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        for k, v in DEFAULT_SAVE.items():
            if k not in data:
                data[k] = _deepcopy_json(v)

        if len(data["stars"]) != TOTAL_LEVELS:
            data["stars"] = (data["stars"] + [0]*TOTAL_LEVELS)[:TOTAL_LEVELS]

        data["unlocked"] = int(clamp(int(data["unlocked"]), 1, TOTAL_LEVELS))
        data["coins"] = max(0, int(data.get("coins", 0)))
        data["highscore"] = max(0, int(data.get("highscore", 0)))


        if "owned" not in data or not isinstance(data["owned"], dict):
            data["owned"] = _deepcopy_json(DEFAULT_SAVE["owned"])
        if "equipped" not in data or not isinstance(data["equipped"], dict):
            data["equipped"] = _deepcopy_json(DEFAULT_SAVE["equipped"])

        # defaults altijd owned
        data["owned"]["laptop_default"] = True
        data["owned"]["phone_default"] = True

        # equipped laptop
        if "laptop" not in data["equipped"]:
            data["equipped"]["laptop"] = "laptop_default"
        if data["equipped"]["laptop"] not in SHOP_ITEMS:
            data["equipped"]["laptop"] = "laptop_default"

        # equipped phone
        if "phone" not in data["equipped"]:
            data["equipped"]["phone"] = "phone_default"
        if data["equipped"]["phone"] not in SHOP_ITEMS:
            data["equipped"]["phone"] = "phone_default"

        return data
    except Exception:
        return _deepcopy_json(DEFAULT_SAVE)

def write_save(data):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
