# assets.py
# Laadt alle afbeeldingen (en flags voor optionele backgrounds).

# load_images() geeft een dict terug met alle images

# boss_asset_for_level() kiest boss sprite op basis van level
import pygame
from utils import load_image, scale

def load_images():
    img = {}

    img["background"] = load_image("Background.png")
    img["desk"] = load_image("desk.png")

    img["boss_1"] = load_image("boss_lvl1.png")
    img["boss_2"] = load_image("boss_lvl2.png")
    img["boss_3"] = load_image("boss_lvl3.png")

    img["hands_0"] = load_image("hands1.png")
    img["hands_1"] = load_image("hands2.png")
    img["smoking_hand"] = load_image("Smoking.png")

    img["phone_default"] = load_image("phone.png")

    # Optional backgrounds
    try:
        img["main_menu_bg"] = load_image("main_menu_bg.png")
        img["HAS_MENU_BG"] = True
    except Exception:
        img["main_menu_bg"] = None
        img["HAS_MENU_BG"] = False

    try:
        img["caught_bg"] = load_image("caught_bg.png")
        img["HAS_CAUGHT_BG"] = True
    except Exception:
        img["caught_bg"] = None
        img["HAS_CAUGHT_BG"] = False

    try:
        img["level_select_bg"] = load_image("office_building.png")
        img["HAS_LEVEL_SELECT_BG"] = True
    except Exception:
        img["level_select_bg"] = None
        img["HAS_LEVEL_SELECT_BG"] = False

    return img

def boss_asset_for_level(img, level_num: int) -> pygame.Surface:
    if level_num >= 10:
        return img["boss_3"]
    if level_num >= 5:
        return img["boss_2"]
    return img["boss_1"]
