import os
import json
import random
import pygame

# -----------------------------
# Config
# -----------------------------
FPS = 60

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SAVE_PATH = os.path.join(os.path.dirname(__file__), "save.json")

PHONE_POINTS_PER_SEC = 10
MAX_HOLD_BONUS = 3.0  # Maximum multiplier

# Level select layout (basis; wordt dynamisch geschaald)
GRID_COLS = 5
GRID_ROWS = 3
TOTAL_LEVELS = GRID_COLS * GRID_ROWS  # 15

# Stars thresholds (BASE voor level 1)
STAR_1 = 180
STAR_2 = 320
STAR_3 = 500

# Desk overlay tuning
DESK_Y_OFFSET = 0

# Hands overlay tuning
HANDS_Y_OFFSET = 6

# -----------------------------
# Coins rewards
# -----------------------------
COINS_BASE_WIN = 50
COINS_PER_STAR = 10
COINS_FIRST_CLEAR_BONUS = 100

# Popup
POPUP_DURATION = 1.4  # sec

# -----------------------------
# Main menu settings
# -----------------------------
MAIN_MENU_BG_COLOR = (45, 55, 70)      # fallback
BUTTON_BG_COLOR = (109, 52, 18)        # donker bruin
BUTTON_TEXT_COLOR = (253, 221, 131)    # licht goud
TITLE_COLOR = (255, 230, 180)

# -----------------------------
# Shop colors
# -----------------------------
COL_TEXT = (109, 52, 18)           # text
COL_BTN_BG = (253, 221, 131)       # knop background
COL_PANEL_BG = (248, 236, 200)
COL_CARD_BG  = (255, 248, 225)
COL_BORDER   = (109, 52, 18)
COL_MUTED    = (170, 150, 120)

# -----------------------------
# Shop catalog (TELEFOONS + LAPTOPS)
# -----------------------------
SHOP_ITEMS = {
    # --- Laptops ---
    "laptop_default": {"type": "laptop", "price": 0,   "file": "laptopnohands.png",   "name": "Laptop Default"},
    "laptop_gaming":  {"type": "laptop", "price": 400, "file": "gaminglaptop.png",    "name": "Gaming Laptop"},
    "kity_laptop":    {"type": "laptop", "price": 550, "file": "hellokitylaptop.png", "name": "Hello kity Laptop"},
    "roze_laptop":    {"type": "laptop", "price": 700, "file": "rozelaptop.png",      "name": "Roze Laptop"},
    "future_gaming":  {"type": "laptop", "price": 900, "file": "futurlaptop.png",     "name": "Future Laptop"},

    # --- Telefoons ---
    "phone_default":  {"type": "phone",  "price": 0,   "file": "phone.png",           "name": "Phone Default"},
    "kity_phone":     {"type": "phone",  "price": 250, "file": "kity_phone.png",      "name": "Kity Phone"},
}

# -----------------------------
# Difficulty generator
# -----------------------------
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

# Boss states
WAIT, WALKING_IN, LOOKING, WALKING_OUT = "wait", "walking_in", "looking", "walking_out"

# Scenes
SCENE_MAIN_MENU    = "main_menu"
SCENE_LEVEL_SELECT = "level_select"
SCENE_PLAY         = "play"
SCENE_COMPLETE     = "complete"
SCENE_GAMEOVER     = "gameover"
SCENE_SHOP         = "shop"

# -----------------------------
# Utils
# -----------------------------
def load_image(filename: str) -> pygame.Surface:
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Asset ontbreekt: {path}")
    return pygame.image.load(path).convert_alpha()

def scale(img, w, h):
    return pygame.transform.smoothscale(img, (int(w), int(h)))

def draw_text(surf, font_obj, text, x, y, color=(20, 20, 25)):
    surf.blit(font_obj.render(text, True, color), (x, y))

def clamp(v, a, b):
    return max(a, min(b, v))

def blit_fit_center(surf, img, rect, padding=8):
    """Schaal img proportioneel zodat hij in rect past (met padding) en center hem."""
    max_w = max(1, rect.w - 2*padding)
    max_h = max(1, rect.h - 2*padding)
    iw, ih = img.get_width(), img.get_height()
    if iw <= 0 or ih <= 0:
        return
    s = min(max_w / iw, max_h / ih)
    w, h = max(1, int(iw * s)), max(1, int(ih * s))
    scaled = pygame.transform.smoothscale(img, (w, h))
    dst = scaled.get_rect(center=rect.center)
    surf.blit(scaled, dst)

# -----------------------------
# Save (coins + shop)
# -----------------------------
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

# -----------------------------
# Init pygame + dynamic fullscreen resolution
# -----------------------------
pygame.init()
pygame.mixer.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Office Game - Main Menu + Shop")
clock = pygame.time.Clock()

# Fonts (dynamisch)
def setup_fonts():
    global font, small, big, title_font
    sy = HEIGHT / 540
    font = pygame.font.SysFont(None, max(18, int(28 * sy)))
    small = pygame.font.SysFont(None, max(14, int(22 * sy)))
    big = pygame.font.SysFont(None, max(34, int(72 * sy)))
    title_font = pygame.font.SysFont(None, max(40, int(86 * sy)))

setup_fonts()

# -----------------------------
# Load visuals (raw)
# -----------------------------
img_background = load_image("Background.png")
img_desk = load_image("desk.png")

# 3 bosses
img_boss_1 = load_image("boss_lvl1.png")
img_boss_2 = load_image("boss_lvl2.png")
img_boss_3 = load_image("boss_lvl3.png")

img_hands_0 = load_image("hands1.png")
img_hands_1 = load_image("hands2.png")

# smoking hand
img_smoking_hand = load_image("Smoking.png")

# Default phone img (fallback)
img_phone_default = load_image("phone.png")

try:
    img_main_menu_bg = load_image("main_menu_bg.png")
    HAS_MENU_BG = True
except Exception:
    HAS_MENU_BG = False
    img_main_menu_bg = None

try:
    img_caught_bg = load_image("caught_bg.png")
    HAS_CAUGHT_BG = True
except Exception:
    HAS_CAUGHT_BG = False
    img_caught_bg = None

# level select background
try:
    img_level_select_bg = load_image("office_building.png")
    HAS_LEVEL_SELECT_BG = True
except Exception:
    HAS_LEVEL_SELECT_BG = False
    img_level_select_bg = None

# -----------------------------
# Globals die door layout bepaald worden
# -----------------------------
background_s = None
main_menu_bg = None
caught_bg = None
level_select_bg = None

desk_s = None
desk_h = 0
desk_scale = 1.0
DESK_POS = (0, 0)

TILE_W = 140
TILE_H = 110
GRID_TOP = 140
GRID_LEFT = 0

LAPTOP_SIZE = (520, 260)
LAPTOP_POS = (0, 0)

PHONE_SIZE = (300, 300)
PHONE_POS = (0, 0)

hands_0_s = None
hands_1_s = None

smoking_hand_s = None

# phone skin (equipped)
img_phone_skin = None
phone_skin_s = None

# Boss sizing
BOSS_FAR = (190, 285)
BOSS_NEAR = (190, 285)
BOSS_END_Y = 0
BOSS_START_Y = 0

# Shop thumbs
THUMB_W, THUMB_H = 180, 95
shop_thumbs = {}

def recalc_layout():
    global background_s, main_menu_bg, caught_bg, level_select_bg
    global GRID_LEFT, GRID_TOP, TILE_W, TILE_H
    global DESK_POS, desk_scale, desk_h, desk_s
    global LAPTOP_SIZE, LAPTOP_POS
    global PHONE_SIZE, PHONE_POS, phone_skin_s
    global hands_0_s, hands_1_s
    global smoking_hand_s
    global BOSS_END_Y, BOSS_START_Y
    global BOSS_FAR, BOSS_NEAR
    global THUMB_W, THUMB_H

    sx = WIDTH / 960
    sy = HEIGHT / 540

    background_s = scale(img_background, WIDTH, HEIGHT)

    if HAS_MENU_BG and img_main_menu_bg is not None:
        main_menu_bg = scale(img_main_menu_bg, WIDTH, HEIGHT)
    if HAS_CAUGHT_BG and img_caught_bg is not None:
        caught_bg = scale(img_caught_bg, WIDTH, HEIGHT)

    if HAS_LEVEL_SELECT_BG and img_level_select_bg is not None:
        level_select_bg = scale(img_level_select_bg, WIDTH, HEIGHT)

    TILE_W = int(140 * sx)
    TILE_H = int(110 * sy)
    GRID_TOP = int(140 * sy)
    GRID_LEFT = (WIDTH - GRID_COLS * TILE_W) // 2

    desk_scale = WIDTH / img_desk.get_width()
    desk_h = int(img_desk.get_height() * desk_scale - 120 * sy)
    desk_s = pygame.transform.smoothscale(img_desk, (WIDTH, desk_h))
    DESK_POS = (0, HEIGHT - desk_h + int(DESK_Y_OFFSET * sy))

    laptop_w = int(WIDTH * 0.54)
    laptop_h = int(laptop_w * (260 / 520))
    LAPTOP_SIZE = (laptop_w, laptop_h)
    LAPTOP_POS = (WIDTH // 2 - laptop_w // 2, HEIGHT - laptop_h - int(22 * sy))

    phone_w = int(laptop_w * (300 / 520))
    phone_h = phone_w
    PHONE_SIZE = (phone_w, phone_h)
    PHONE_POS = (
        WIDTH // 2 - phone_w // 2,
        LAPTOP_POS[1] + (laptop_h // 2 - phone_h // 2) + int(6 * sy)
    )

    hands_0_s = scale(img_hands_0, *LAPTOP_SIZE)
    hands_1_s = scale(img_hands_1, *LAPTOP_SIZE)

    smoking_hand_s = scale(img_smoking_hand, *LAPTOP_SIZE)

    BOSS_FAR = (int(190 * sx), int(285 * sy))
    BOSS_NEAR = (int(190 * sx), int(285 * sy))
    BOSS_END_Y = LAPTOP_POS[1] + int(12 * sy)
    BOSS_START_Y = BOSS_END_Y

    THUMB_W = int(180 * sx)
    THUMB_H = int(95 * sy)

    if img_phone_skin is not None:
        phone_skin_s = scale(img_phone_skin, *PHONE_SIZE)

def build_shop_thumbs():
    global shop_thumbs
    shop_thumbs = {}
    for item_id, item in SHOP_ITEMS.items():
        try:
            img = load_image(item["file"])
            shop_thumbs[item_id] = pygame.transform.smoothscale(img, (THUMB_W, THUMB_H))
        except Exception:
            surf = pygame.Surface((THUMB_W, THUMB_H), pygame.SRCALPHA)
            surf.fill((200, 200, 200))
            shop_thumbs[item_id] = surf

recalc_layout()
build_shop_thumbs()

# -----------------------------
# Load audio
# -----------------------------
def safe_sound(path, volume=None):
    try:
        s = pygame.mixer.Sound(path)
        if volume is not None:
            s.set_volume(volume)
        return s
    except Exception:
        return pygame.mixer.Sound(b"\x00\x00\x00\x00")

snd_boss_walk = safe_sound(os.path.join(ASSETS_DIR, "loud-footsteps-62038-VEED.mp3"))
snd_typing = safe_sound(os.path.join(ASSETS_DIR, "typing-keyboard-asmr-356116.mp3"))
snd_phone_use = safe_sound(os.path.join(ASSETS_DIR, "Mathias Vandenboer_s Video - Dec 16, 2025-VEED.mp3.mp3"))
snd_boss_chatter = safe_sound(os.path.join(ASSETS_DIR, "angry-boss-chatter.mp3"), volume=0.5)
snd_game_over = safe_sound(os.path.join(ASSETS_DIR, "game_over.wav"))
snd_complete = safe_sound(os.path.join(ASSETS_DIR, "level_complete.wav"))
snd_buy = safe_sound(os.path.join(ASSETS_DIR, "purchase-success-384963.mp3"))
snd_menu_click = safe_sound(os.path.join(ASSETS_DIR, "menu_click.wav"))

# -----------------------------
# Save + asset loaders
# -----------------------------
save = load_save()

img_laptop_nohands = None
laptop_nohands_s = None

def reload_laptop_asset():
    global img_laptop_nohands, laptop_nohands_s
    key = save["equipped"].get("laptop", "laptop_default")
    if key not in SHOP_ITEMS:
        key = "laptop_default"
    if SHOP_ITEMS[key]["type"] != "laptop":
        key = "laptop_default"
    img_laptop_nohands = load_image(SHOP_ITEMS[key]["file"])
    laptop_nohands_s = scale(img_laptop_nohands, *LAPTOP_SIZE)

def reload_phone_asset():
    global img_phone_skin, phone_skin_s
    key = save["equipped"].get("phone", "phone_default")
    if key not in SHOP_ITEMS:
        key = "phone_default"
    if SHOP_ITEMS[key]["type"] != "phone":
        key = "phone_default"
    try:
        img_phone_skin = load_image(SHOP_ITEMS[key]["file"])
    except Exception:
        img_phone_skin = img_phone_default
    phone_skin_s = scale(img_phone_skin, *PHONE_SIZE)

reload_laptop_asset()
reload_phone_asset()

# -----------------------------
# UI helpers
# -----------------------------
def draw_star_row(x, y, n, size=18, gap=8):
    for i in range(3):
        cx = x + i*(size+gap) + size//2
        cy = y + size//2
        color = (240, 200, 60) if i < n else (170, 170, 180)
        pts = [
            (cx, cy - size//2),
            (cx + size*0.18, cy - size*0.15),
            (cx + size//2, cy - size*0.15),
            (cx + size*0.26, cy + size*0.05),
            (cx + size*0.35, cy + size//2),
            (cx, cy + size*0.22),
            (cx - size*0.35, cy + size//2),
            (cx - size*0.26, cy + size*0.05),
            (cx - size//2, cy - size*0.15),
            (cx - size*0.18, cy - size*0.15),
        ]
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, (110, 110, 120), pts, 2)

def button(rect, text, enabled=True):
    mx, my = pygame.mouse.get_pos()
    hover = rect.collidepoint(mx, my)
    base = (245, 210, 120) if enabled else (190, 190, 195)
    border = (150, 120, 70) if enabled else (130, 130, 135)
    fill = tuple(min(255, c+12) for c in base) if hover and enabled else base
    pygame.draw.rect(screen, fill, rect, border_radius=14)
    pygame.draw.rect(screen, border, rect, 3, border_radius=14)
    t = font.render(text, True, (40, 35, 30) if enabled else (90, 90, 95))
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    return hover and enabled

def ui_button(rect, text, enabled=True):
    mx, my = pygame.mouse.get_pos()
    hover = rect.collidepoint(mx, my)
    bg = COL_BTN_BG if enabled else (220, 220, 220)
    if hover and enabled:
        bg = (min(255, bg[0]+8), min(255, bg[1]+8), min(255, bg[2]+8))
    pygame.draw.rect(screen, bg, rect, border_radius=14)
    pygame.draw.rect(screen, COL_BORDER, rect, 3, border_radius=14)
    t = font.render(text, True, COL_TEXT if enabled else (130, 130, 130))
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    return hover and enabled

def menu_button(rect, text, enabled=True):
    mx, my = pygame.mouse.get_pos()
    hover = rect.collidepoint(mx, my)

    base_color = BUTTON_BG_COLOR
    hover_color = tuple(min(255, c + 30) for c in base_color)
    fill_color = hover_color if hover and enabled else base_color

    text_color = BUTTON_TEXT_COLOR if enabled else (150, 150, 150)

    pygame.draw.rect(screen, fill_color, rect, border_radius=12)
    pygame.draw.rect(screen, (70, 35, 10), rect, 3, border_radius=12)

    if hover and enabled:
        pygame.draw.rect(screen, (150, 100, 50), rect, 2, border_radius=12)

    t = font.render(text, True, text_color)
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    return hover and enabled

def tab_button(rect, text, active):
    bg = (255, 245, 210) if active else (255, 255, 255)
    pygame.draw.rect(screen, bg, rect, border_radius=14)
    pygame.draw.rect(screen, COL_BORDER, rect, 3, border_radius=14)
    t = font.render(text, True, COL_TEXT)
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    return rect.collidepoint(pygame.mouse.get_pos())

# -----------------------------
# Dynamic thresholds per level
# -----------------------------
def level_threshold_offset(level_num: int) -> int:
    # level 1 => +0, level 2 => +100, level 3 => +200, ...
    return max(0, (level_num - 1) * 100)

def level_star_thresholds(level_num: int):
    off = level_threshold_offset(level_num)
    return (STAR_1 + off, STAR_2 + off, STAR_3 + off)

def level_complete_score(level_num: int) -> int:
    # Completen = 3-star threshold van dat level
    return level_star_thresholds(level_num)[2]

# -----------------------------
# Game helpers
# -----------------------------
def schedule_next_check(play_state, params):
    BOSS_SOUND_START_OFFSET = 0.5
    play_state["next_check_in"] = random.uniform(params["min_wait"], params["max_wait"]) - BOSS_SOUND_START_OFFSET
    play_state["next_check_in"] = max(0.1, play_state["next_check_in"])
    play_state["pre_walk_sound_started"] = False

def score_to_stars(score_int: int, level_num: int) -> int:
    t1, t2, t3 = level_star_thresholds(level_num)
    if score_int >= t3:
        return 3
    if score_int >= t2:
        return 2
    if score_int >= t1:
        return 1
    return 0

def boss_asset_for_level(level_num: int) -> pygame.Surface:
    if level_num >= 10:
        return img_boss_3
    if level_num >= 5:
        return img_boss_2
    return img_boss_1

def set_boss_path(play_state, direction="in"):
    if direction == "in":
        from_left = random.choice([True, False])
        start_x = -80 if from_left else WIDTH + 80
        end_x = LAPTOP_POS[0] + LAPTOP_SIZE[0] // 2
        play_state["boss_start"] = (start_x, BOSS_START_Y)
        play_state["boss_end"] = (end_x, BOSS_END_Y)
        play_state["boss_from_left"] = from_left
    else:
        from_left = play_state.get("boss_from_left", True)
        start_x = LAPTOP_POS[0] + LAPTOP_SIZE[0] // 2
        end_x = -80 if from_left else WIDTH + 80
        play_state["boss_start"] = (start_x, BOSS_START_Y)
        play_state["boss_end"] = (end_x, BOSS_END_Y)

def buy_or_equip(item_id: str):
    global popup_text, popup_timer

    if item_id not in SHOP_ITEMS:
        return

    item = SHOP_ITEMS[item_id]
    item_type = item["type"]  # "laptop" of "phone"
    slot_key = "laptop" if item_type == "laptop" else "phone"

    owned = bool(save["owned"].get(item_id, False))
    equipped = (save["equipped"].get(slot_key) == item_id)

    if equipped:
        popup_text = "Dit is al equipped!"
        popup_timer = POPUP_DURATION
        return

    if not owned:
        price = int(item["price"])
        if save["coins"] < price:
            popup_text = "Niet genoeg coins!"
            popup_timer = POPUP_DURATION
            return

        save["coins"] -= price
        save["owned"][item_id] = True
        snd_buy.play()
        popup_text = f"Gekocht: {item['name']}!"
        popup_timer = POPUP_DURATION
    else:
        snd_buy.play()
        popup_text = f"Equipped: {item['name']}!"
        popup_timer = POPUP_DURATION

    save["equipped"][slot_key] = item_id
    write_save(save)

    if item_type == "laptop":
        reload_laptop_asset()
    else:
        reload_phone_asset()

# -----------------------------
# Game state
# -----------------------------
scene = SCENE_MAIN_MENU
selected_level = 1
last_run_score = 0
last_run_level = 1
last_run_stars = 0
current_scene = None

shop_selected_id = None
shop_tab = "phone"   # "phone" of "laptop"
popup_text = ""
popup_timer = 0.0

play = {
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

def stop_all_loop_sounds():
    snd_boss_walk.stop()
    snd_typing.stop()
    snd_phone_use.stop()
    snd_boss_chatter.stop()

def start_level(level_num: int):
    global scene, selected_level
    selected_level = level_num
    params = make_level_params(level_num - 1)

    play["score"] = 0.0
    play["phone"] = False
    play["phone_hold_time"] = 0.0
    play["gameover"] = False
    play["caught"] = False
    play["boss_state"] = WAIT
    play["boss_timer"] = 0.0
    play["reaction_timer"] = 0.0
    play["boss_start"] = (0, 0)
    play["boss_end"] = (0, 0)
    play["boss_from_left"] = True
    play["hands_anim_t"] = 0.0
    play["hands_anim_frame"] = 0
    play["pre_walk_sound_started"] = False

    play["smoking"] = False
    play["smoking_timer"] = 0.0
    play["high_timer"] = 0.0
    play["shake_x"] = 0
    play["shake_y"] = 0
    play["hallucination_color"] = (0, 255, 0)
    play["hallucination_timer"] = 0.0

    stop_all_loop_sounds()
    schedule_next_check(play, params)

    scene = SCENE_PLAY
    snd_typing.play(-1)

# -----------------------------
# Main loop
# -----------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    if popup_timer > 0:
        popup_timer = max(0.0, popup_timer - dt)

    if scene != current_scene:
        stop_all_loop_sounds()
        if scene == SCENE_COMPLETE:
            snd_complete.play()
        elif scene == SCENE_GAMEOVER:
            snd_game_over.play()
        if scene == SCENE_PLAY and not play["phone"] and not play["smoking"] and not play["gameover"]:
            snd_typing.play(-1)
        current_scene = scene

    click = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = True
            if scene == SCENE_MAIN_MENU:
                snd_menu_click.play()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if scene == SCENE_PLAY:
                    scene = SCENE_MAIN_MENU
                elif scene in (SCENE_LEVEL_SELECT, SCENE_SHOP, SCENE_COMPLETE, SCENE_GAMEOVER):
                    scene = SCENE_MAIN_MENU

            if scene == SCENE_PLAY:
                if event.key == pygame.K_SPACE and not play["gameover"]:
                    play["phone"] = True
                    snd_typing.stop()
                    snd_phone_use.play(-1)

                if event.key == pygame.K_c and not play["gameover"] and not play["phone"]:
                    play["smoking"] = True
                    snd_typing.stop()

            if event.key == pygame.K_r and scene in (SCENE_GAMEOVER, SCENE_COMPLETE):
                scene = SCENE_MAIN_MENU

        if event.type == pygame.KEYUP:
            if scene == SCENE_PLAY and event.key == pygame.K_SPACE:
                play["phone"] = False
                snd_phone_use.stop()
                if not play["gameover"] and not play["smoking"]:
                    snd_typing.play(-1)

            if scene == SCENE_PLAY and event.key == pygame.K_c:
                play["smoking"] = False
                if not play["gameover"]:
                    snd_typing.play(-1)

    # Update play
    if scene == SCENE_PLAY and not play["gameover"]:
        params = make_level_params(selected_level - 1)

        if not play["phone"] and not play["smoking"]:
            play["hands_anim_t"] += dt
            if play["hands_anim_t"] >= 0.15:
                play["hands_anim_t"] -= 0.15
                play["hands_anim_frame"] = 1 - play["hands_anim_frame"]
        else:
            play["hands_anim_t"] = 0.0
            play["hands_anim_frame"] = 0

        if play["phone"]:
            play["phone_hold_time"] += dt
            combo_curve_exponent = 0.5
            raw_bonus = 1.0 + (play["phone_hold_time"] ** combo_curve_exponent)
            hold_bonus = min(raw_bonus, MAX_HOLD_BONUS)
            high_bonus = 1.2 if play["high_timer"] > 0 else 1.0
            play["score"] += PHONE_POINTS_PER_SEC * hold_bonus * params["mult"] * high_bonus * dt
        else:
            play["phone_hold_time"] = 0.0

        if play["smoking"]:
            play["smoking_timer"] += dt
            if play["smoking_timer"] >= 5.0:
                play["smoking"] = False
                play["high_timer"] = 15.0
                popup_text = "Joint smoked! You're high!"
                popup_timer = POPUP_DURATION
        else:
            play["smoking_timer"] = 0.0

        if play["high_timer"] > 0:
            play["high_timer"] -= dt
            play["shake_x"] = random.randint(-15, 15)
            play["shake_y"] = random.randint(-15, 15)

            play["hallucination_timer"] += dt
            if play["hallucination_timer"] >= 1.0:
                play["hallucination_timer"] -= 1.0
                play["hallucination_color"] = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
        else:
            play["shake_x"] = 0
            play["shake_y"] = 0
            play["hallucination_color"] = (0, 255, 0)
            play["hallucination_timer"] = 0.0

        play["boss_timer"] += dt

        if play["boss_state"] == WAIT:
            if play["boss_timer"] >= play["next_check_in"] and not play["pre_walk_sound_started"]:
                snd_boss_walk.play(-1)
                play["pre_walk_sound_started"] = True

            if play["boss_timer"] >= play["next_check_in"] + 0.5:
                play["boss_timer"] = 0.0
                play["boss_state"] = WALKING_IN
                play["reaction_timer"] = 0.0
                play["caught"] = False
                set_boss_path(play, direction="in")

        elif play["boss_state"] == WALKING_IN:
            play["reaction_timer"] += dt
            if (play["phone"] or play["smoking"]) and play["reaction_timer"] > params["grace"]:
                play["caught"] = True
                play["gameover"] = True

            if play["boss_timer"] >= params["walk_in"]:
                play["boss_timer"] = 0.0
                play["boss_state"] = LOOKING
                snd_boss_walk.stop()
                snd_boss_chatter.play(-1)

        elif play["boss_state"] == LOOKING:
            if play["phone"] or play["smoking"]:
                play["caught"] = True
                play["gameover"] = True

            if play["boss_timer"] >= params["look"]:
                play["boss_state"] = WALKING_OUT
                play["boss_timer"] = 0.0
                snd_boss_chatter.stop()
                set_boss_path(play, direction="out")
                snd_boss_walk.play(-1)

        elif play["boss_state"] == WALKING_OUT:
            if play["boss_timer"] >= params["walk_out"]:
                play["boss_state"] = WAIT
                play["boss_timer"] = 0.0
                snd_boss_walk.stop()
                schedule_next_check(play, params)
                if not play["phone"] and not play["smoking"] and not play["gameover"]:
                    snd_typing.play(-1)

        # ✅ WIN condition: dynamisch per level
        complete_score = level_complete_score(selected_level)
        if play["score"] >= complete_score:
            last_run_score = int(play["score"])
            last_run_level = selected_level
            last_run_stars = score_to_stars(last_run_score, last_run_level)

            prev_stars = save["stars"][last_run_level - 1]
            first_clear = (prev_stars == 0)

            save["stars"][last_run_level - 1] = max(prev_stars, last_run_stars)
            if last_run_level < TOTAL_LEVELS:
                save["unlocked"] = max(save["unlocked"], last_run_level + 1)

            save["coins"] += (COINS_BASE_WIN + last_run_stars * COINS_PER_STAR)
            if first_clear:
                save["coins"] += COINS_FIRST_CLEAR_BONUS

            write_save(save)
            scene = SCENE_COMPLETE

        if play["gameover"]:
            last_run_score = int(play["score"])
            last_run_level = selected_level
            last_run_stars = score_to_stars(last_run_score, last_run_level)

            prev_stars = save["stars"][last_run_level - 1]
            save["stars"][last_run_level - 1] = max(prev_stars, last_run_stars)

            coins_earned = last_run_stars * COINS_PER_STAR
            save["coins"] += coins_earned

            write_save(save)
            scene = SCENE_GAMEOVER

    # -----------------------------
    # DRAW
    # -----------------------------
    if scene == SCENE_MAIN_MENU:
        if HAS_MENU_BG and main_menu_bg is not None:
            screen.blit(main_menu_bg, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(64)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(MAIN_MENU_BG_COLOR)
            for i in range(0, WIDTH, 40):
                for j in range(0, HEIGHT, 40):
                    pygame.draw.rect(screen, (35, 45, 60), (i, j, 40, 40), 1)

        button_width = int(WIDTH * 0.32)
        button_height = int(HEIGHT * 0.11)
        button_x = WIDTH//2 - button_width//2

        start_rect = pygame.Rect(button_x, int(HEIGHT * 0.33), button_width, button_height)
        if menu_button(start_rect, "START GAME") and click:
            start_level(save["unlocked"])

        levels_rect = pygame.Rect(button_x, int(HEIGHT * 0.48), button_width, button_height)
        if menu_button(levels_rect, "LEVEL SELECT") and click:
            scene = SCENE_LEVEL_SELECT

        shop_rect = pygame.Rect(button_x, int(HEIGHT * 0.63), button_width, button_height)
        if menu_button(shop_rect, "SHOP") and click:
            scene = SCENE_SHOP
            if shop_tab == "phone":
                shop_selected_id = save["equipped"].get("phone", "phone_default")
            else:
                shop_selected_id = save["equipped"].get("laptop", "laptop_default")

        quit_rect = pygame.Rect(button_x, int(HEIGHT * 0.78), button_width, button_height)
        if menu_button(quit_rect, "QUIT GAME") and click:
            running = False

        footer_text = small.render("SPATIE = telefoon | ESC = menu", True, (0, 0, 0))
        screen.blit(footer_text, (WIDTH//2 - footer_text.get_width()//2, HEIGHT - int(HEIGHT * 0.06)))

    elif scene == SCENE_LEVEL_SELECT:
        if HAS_LEVEL_SELECT_BG and level_select_bg is not None:
            screen.blit(level_select_bg, (0, 0))

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 64))
            screen.blit(overlay, (0, 0))

            header_overlay = pygame.Surface((WIDTH, int(HEIGHT * 0.22)), pygame.SRCALPHA)
            header_overlay.fill((0, 0, 0, 128))
            screen.blit(header_overlay, (0, 0))
        else:
            pygame.draw.rect(screen, (170, 210, 240), (0, 0, WIDTH, int(HEIGHT * 0.30)))
            pygame.draw.rect(screen, (120, 180, 230), (0, int(HEIGHT * 0.30), WIDTH, HEIGHT - int(HEIGHT * 0.30)))

        back_rect = pygame.Rect(int(WIDTH * 0.02), int(HEIGHT * 0.03), int(WIDTH * 0.12), int(HEIGHT * 0.07))
        if button(back_rect, "< Terug") and click:
            scene = SCENE_MAIN_MENU

        draw_text(screen, font, f"Unlocked: {save['unlocked']} / {TOTAL_LEVELS}", int(WIDTH * 0.04), int(HEIGHT * 0.18), (255, 255, 255))
        draw_text(screen, font, f"Coins: {save['coins']}", int(WIDTH * 0.82), int(HEIGHT * 0.18), (255, 255, 255))

        shop_btn = pygame.Rect(int(WIDTH * 0.79), int(HEIGHT * 0.04), int(WIDTH * 0.17), int(HEIGHT * 0.09))
        if button(shop_btn, "SHOP") and click:
            scene = SCENE_SHOP
            if shop_tab == "phone":
                shop_selected_id = save["equipped"].get("phone", "phone_default")
            else:
                shop_selected_id = save["equipped"].get("laptop", "laptop_default")

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                idx = r*GRID_COLS + c
                lvl_num = idx + 1
                x = GRID_LEFT + c*TILE_W
                y = GRID_TOP + r*TILE_H
                rect = pygame.Rect(x + int(TILE_W*0.07), y + int(TILE_H*0.10), int(TILE_W*0.86), int(TILE_H*0.78))

                unlocked = lvl_num <= save["unlocked"]
                mx, my = pygame.mouse.get_pos()
                hover = rect.collidepoint(mx, my)

                if unlocked:
                    fill = (245, 230, 160) if hover else (240, 220, 140)
                    pygame.draw.rect(screen, fill, rect, border_radius=16)
                    pygame.draw.rect(screen, (150, 120, 70), rect, 3, border_radius=16)

                    t = font.render(str(lvl_num), True, (55, 45, 35))
                    screen.blit(t, (rect.x + 12, rect.y + 10))

                    star_size = max(12, int((HEIGHT/540) * 18))
                    draw_star_row(rect.x + 18, rect.y + int(rect.h * 0.55), save["stars"][idx], size=star_size, gap=max(4, int(star_size*0.35)))

                    if click and hover:
                        start_level(lvl_num)
                else:
                    fill = (200, 200, 205) if hover else (190, 190, 195)
                    pygame.draw.rect(screen, fill, rect, border_radius=16)
                    pygame.draw.rect(screen, (130, 130, 140), rect, 3, border_radius=16)
                    draw_text(screen, font, "LOCK", rect.centerx-22, rect.centery-12, (90, 90, 100))

        draw_text(screen, small, "Klik op een level. (ESC = hoofdmenu)", int(WIDTH * 0.04), HEIGHT - int(HEIGHT * 0.06), (255, 255, 255))

    elif scene == SCENE_SHOP:
        screen.fill(COL_PANEL_BG)

        margin = int(WIDTH * 0.04)
        top_y = int(HEIGHT * 0.04)

        grid_x, grid_y = margin, int(HEIGHT * 0.22)
        grid_w, grid_h = int(WIDTH * 0.64), int(HEIGHT * 0.70)
        side_x = grid_x + grid_w + int(WIDTH * 0.02)
        side_y = grid_y
        side_w = WIDTH - side_x - margin

        grid_rect = pygame.Rect(grid_x, grid_y, grid_w, grid_h)
        side_rect = pygame.Rect(side_x, side_y, side_w, grid_h)

        tab_h = int(HEIGHT * 0.08)
        tab_w = int(WIDTH * 0.18)
        tab_gap = int(WIDTH * 0.015)

        tabs_y = grid_y - tab_h - int(HEIGHT * 0.02)

        phone_tab_rect  = pygame.Rect(grid_x, tabs_y, tab_w, tab_h)
        laptop_tab_rect = pygame.Rect(grid_x + tab_w + tab_gap, tabs_y, tab_w, tab_h)

        if tab_button(phone_tab_rect, "TELEFOONS", shop_tab == "phone") and click:
            shop_tab = "phone"
            shop_selected_id = save["equipped"].get("phone", "phone_default")

        if tab_button(laptop_tab_rect, "LAPTOPS", shop_tab == "laptop") and click:
            shop_tab = "laptop"
            shop_selected_id = save["equipped"].get("laptop", "laptop_default")

        title_surf = title_font.render("SHOP", True, COL_TEXT)
        title_x = WIDTH // 2 - title_surf.get_width() // 2
        title_y = top_y
        screen.blit(title_surf, (title_x, title_y))

        coins_surf = font.render(f"Coins: {save['coins']}", True, COL_TEXT)
        screen.blit(coins_surf, (WIDTH - margin - coins_surf.get_width(), top_y + int(HEIGHT * 0.02)))

        pygame.draw.rect(screen, COL_CARD_BG, grid_rect, border_radius=18)
        pygame.draw.rect(screen, COL_BORDER, grid_rect, 3, border_radius=18)
        pygame.draw.rect(screen, COL_CARD_BG, side_rect, border_radius=18)
        pygame.draw.rect(screen, COL_BORDER, side_rect, 3, border_radius=18)

        items = [(iid, it) for (iid, it) in SHOP_ITEMS.items() if it["type"] == shop_tab]
        items.sort(key=lambda kv: int(kv[1]["price"]))

        if (shop_selected_id is None) or (shop_selected_id not in SHOP_ITEMS) or (SHOP_ITEMS[shop_selected_id]["type"] != shop_tab):
            shop_selected_id = save["equipped"].get(
                "phone" if shop_tab == "phone" else "laptop",
                "phone_default" if shop_tab == "phone" else "laptop_default"
            )

        cols = 3
        pad = int(WIDTH * 0.012)
        card_w = (grid_w - pad*(cols+1)) // cols
        card_h = int(HEIGHT * 0.20)

        mx, my = pygame.mouse.get_pos()

        for idx, (item_id, item) in enumerate(items):
            rr = idx // cols
            cc = idx % cols
            x = grid_x + pad + cc*(card_w + pad)
            y = grid_y + pad + rr*(card_h + pad)
            card = pygame.Rect(x, y, card_w, card_h)

            owned = bool(save["owned"].get(item_id, False))
            slot_key = "laptop" if item["type"] == "laptop" else "phone"
            equipped = (save["equipped"].get(slot_key) == item_id)
            selected = (shop_selected_id == item_id)

            bg = (255, 255, 255) if not selected else (255, 245, 210)
            pygame.draw.rect(screen, bg, card, border_radius=16)
            pygame.draw.rect(screen, COL_BORDER if selected else COL_MUTED, card, 3, border_radius=16)

            text_area_h = int(card_h * 0.36)
            thumb_area = pygame.Rect(card.x, card.y, card.w, card.h - text_area_h)
            text_area  = pygame.Rect(card.x, card.y + thumb_area.h, card.w, text_area_h)

            thumb = shop_thumbs.get(item_id)
            if thumb:
                blit_fit_center(screen, thumb, thumb_area, padding=10)

            pygame.draw.rect(screen, (255, 255, 255), text_area, border_radius=14)
            pygame.draw.rect(screen, COL_MUTED, text_area, 2, border_radius=14)

            name_s = small.render(item["name"], True, COL_TEXT)
            screen.blit(name_s, (text_area.x + 10, text_area.y + 6))

            if equipped:
                tag = "EQUIPPED"
            elif owned:
                tag = "OWNED"
            else:
                tag = f"{item['price']} coins"

            tag_s = small.render(tag, True, COL_TEXT)
            screen.blit(tag_s, (text_area.x + 10, text_area.y + 6 + name_s.get_height() + 2))

            if click and card.collidepoint(mx, my):
                shop_selected_id = item_id

        if shop_selected_id in SHOP_ITEMS and SHOP_ITEMS[shop_selected_id]["type"] == shop_tab:
            item = SHOP_ITEMS[shop_selected_id]
            owned = bool(save["owned"].get(shop_selected_id, False))
            slot_key = "laptop" if item["type"] == "laptop" else "phone"
            equipped = (save["equipped"].get(slot_key) == shop_selected_id)

            draw_text(screen, font, "Selected:", side_x + 18, side_y + 18, COL_TEXT)
            draw_text(screen, font, item["name"], side_x + 18, side_y + 46, COL_TEXT)

            preview = shop_thumbs.get(shop_selected_id)
            if preview:
                prev_w = side_w - 36
                prev_h = int(grid_h * 0.22)
                prev_rect = pygame.Rect(side_x + 18, side_y + 80, prev_w, prev_h)
                blit_fit_center(screen, preview, prev_rect, padding=8)

            draw_text(screen, font, f"Price: {item['price']} coins", side_x + 18, side_y + int(grid_h * 0.36), COL_TEXT)
            status = "Equipped" if equipped else ("Owned" if owned else "Not owned")
            draw_text(screen, font, f"Status: {status}", side_x + 18, side_y + int(grid_h * 0.41), COL_TEXT)

            btn = pygame.Rect(side_x + 18, side_y + int(grid_h * 0.52), side_w - 36, int(grid_h * 0.10))

            if equipped:
                ui_button(btn, "EQUIPPED", enabled=False)
            else:
                if owned:
                    if ui_button(btn, "EQUIP") and click:
                        buy_or_equip(shop_selected_id)
                else:
                    can_buy = save["coins"] >= int(item["price"])
                    if ui_button(btn, "KOOP" if can_buy else "TE WEINIG COINS", enabled=can_buy) and click and can_buy:
                        buy_or_equip(shop_selected_id)
                    elif click and btn.collidepoint(mx, my) and not can_buy:
                        popup_text = "Niet genoeg coins!"
                        popup_timer = POPUP_DURATION

        if popup_timer > 0 and popup_text:
            w, h = int(WIDTH * 0.54), int(HEIGHT * 0.12)
            px = (WIDTH - w) // 2
            py = int(HEIGHT * 0.03)
            rect = pygame.Rect(px, py, w, h)
            pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=16)
            pygame.draw.rect(screen, COL_BORDER, rect, 3, border_radius=16)
            t = font.render(popup_text, True, COL_TEXT)
            screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

    elif scene == SCENE_PLAY:
        params = make_level_params(selected_level - 1)

        # ✅ thresholds voor dit level
        t1, t2, t3 = level_star_thresholds(selected_level)
        complete_score = t3

        screen.blit(background_s, (play["shake_x"], play["shake_y"]))

        if play["boss_state"] in (WALKING_IN, LOOKING, WALKING_OUT):
            if play["boss_state"] == WALKING_IN:
                t = clamp(play["boss_timer"] / params["walk_in"], 0.0, 1.0)
            elif play["boss_state"] == WALKING_OUT:
                t = clamp(play["boss_timer"] / params["walk_out"], 0.0, 1.0)
            else:
                t = 1.0

            sx0, sy0 = play["boss_start"]
            ex0, ey0 = play["boss_end"]
            bx = int(sx0 + (ex0 - sx0) * t)
            by = int(sy0 + (ey0 - sy0) * t)

            bw = int(BOSS_FAR[0] + (BOSS_NEAR[0] - BOSS_FAR[0]) * t)
            bh = int(BOSS_FAR[1] + (BOSS_NEAR[1] - BOSS_FAR[1]) * t)

            boss_img = boss_asset_for_level(selected_level)
            boss_scaled = scale(boss_img, bw, bh)
            boss_rect = boss_scaled.get_rect(center=(bx, by))
            screen.blit(boss_scaled, (boss_rect.x + play["shake_x"], boss_rect.y + play["shake_y"]))

        screen.blit(desk_s, (DESK_POS[0] + play["shake_x"], DESK_POS[1] + play["shake_y"]))
        screen.blit(laptop_nohands_s, (LAPTOP_POS[0] + play["shake_x"], LAPTOP_POS[1] + play["shake_y"]))

        hands_pos = (
            LAPTOP_POS[0] + play["shake_x"],
            LAPTOP_POS[1] + int(HANDS_Y_OFFSET * (HEIGHT/540)) + play["shake_y"]
        )

        if play["phone"]:
            if phone_skin_s is not None:
                screen.blit(phone_skin_s, (PHONE_POS[0] + play["shake_x"], PHONE_POS[1] + play["shake_y"]))
            else:
                phone_fallback = scale(img_phone_default, *PHONE_SIZE)
                screen.blit(phone_fallback, (PHONE_POS[0] + play["shake_x"], PHONE_POS[1] + play["shake_y"]))
        elif play["smoking"]:
            if smoking_hand_s is not None:
                screen.blit(smoking_hand_s, hands_pos)
        else:
            screen.blit(hands_0_s if play["hands_anim_frame"] == 0 else hands_1_s, hands_pos)

        draw_text(screen, font,
                  f"Level {selected_level}  |  Punten: {int(play['score'])}  |  x{params['mult']:.2f}",
                  int(WIDTH*0.02), int(HEIGHT*0.02), (0, 0, 0))
        draw_text(screen, small, "Houd SPATIE = telefoon | Houd C = joint | ESC = hoofdmenu",
                  int(WIDTH*0.02), int(HEIGHT*0.07), (0, 0, 0))

        # ✅ Links boven: juiste doelen + sterren thresholds
        draw_text(screen, small, f"Doel: {complete_score}  |  1★ {t1}  2★ {t2}  3★ {t3}",
                  int(WIDTH*0.02), int(HEIGHT*0.11), (0, 0, 0))

        if play["boss_state"] == WALKING_IN:
            left = max(0.0, params["grace"] - play["reaction_timer"])
            draw_text(screen, font, f"BAAS KOMT! Loslaten binnen {left:.2f}s!", int(WIDTH*0.02), int(HEIGHT*0.15), (204, 0, 0))
        elif play["boss_state"] == LOOKING:
            draw_text(screen, font, "BAAS KIJKT!", int(WIDTH*0.02), int(HEIGHT*0.15), (204, 0, 0))
        elif play["smoking"]:
            progress = min(play["smoking_timer"] / 5.0, 1.0)
            draw_text(screen, font, f"Roken: {progress:.1%}", int(WIDTH*0.02), int(HEIGHT*0.15), (0, 150, 0))

        # ✅ progress bar schaalt nu mee met het level-doel
        pct = clamp(play["score"] / complete_score, 0.0, 1.0)
        bar = pygame.Rect(int(WIDTH*0.02) + play["shake_x"], int(HEIGHT*0.20) + play["shake_y"], int(WIDTH*0.27), int(HEIGHT*0.03))
        pygame.draw.rect(screen, (20, 20, 25), bar, border_radius=8)
        pygame.draw.rect(screen, (90, 220, 120), (bar.x, bar.y, int(bar.w*pct), bar.h), border_radius=8)

        if play["phone"]:
            combo_curve_exponent = 0.5
            raw_bonus = 1.0 + (play["phone_hold_time"] ** combo_curve_exponent)
            hold_bonus = min(raw_bonus, MAX_HOLD_BONUS)

            bar_w = int(WIDTH*0.02)
            bar_h = int(HEIGHT*0.22)
            bar_x = WIDTH - bar_w - int(WIDTH*0.02) + play["shake_x"]
            bar_y = HEIGHT - bar_h - int(HEIGHT*0.04) + play["shake_y"]

            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            fill_h = int(bar_h * (hold_bonus / MAX_HOLD_BONUS))
            pygame.draw.rect(screen, (255, 200, 50), (bar_x, bar_y + bar_h - fill_h, bar_w, fill_h), border_radius=6)
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)
            draw_text(screen, small, f"x{hold_bonus:.2f}", bar_x - int(WIDTH*0.03), bar_y - int(HEIGHT*0.04), (204, 0, 0))

        if play["high_timer"] > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.fill(play["hallucination_color"])
            overlay.set_alpha(50)
            screen.blit(overlay, (0, 0))

    elif scene == SCENE_COMPLETE:
        screen.fill((170, 230, 190))
        draw_text(screen, big, "LEVEL COMPLETE!", int(WIDTH*0.06), int(HEIGHT*0.12), (25, 60, 35))
        draw_text(screen, font, f"Level {last_run_level}  Score: {last_run_score}", int(WIDTH*0.07), int(HEIGHT*0.30), (25, 60, 35))

        star_size = max(18, int((HEIGHT/540) * 34))
        draw_star_row(int(WIDTH*0.07), int(HEIGHT*0.39), last_run_stars, size=star_size, gap=int(star_size*0.5))

        b1 = pygame.Rect(int(WIDTH*0.06), int(HEIGHT*0.56), int(WIDTH*0.30), int(HEIGHT*0.11))
        b2 = pygame.Rect(int(WIDTH*0.06), int(HEIGHT*0.69), int(WIDTH*0.30), int(HEIGHT*0.11))

        if button(b1, "Hoofdmenu") and click:
            scene = SCENE_MAIN_MENU

        if last_run_level < TOTAL_LEVELS:
            can_next = (last_run_level + 1) <= save["unlocked"]
            if button(b2, "Volgende Level", enabled=can_next) and click and can_next:
                start_level(last_run_level + 1)
        else:
            button(b2, "Laatste level!", enabled=False)

    elif scene == SCENE_GAMEOVER:
        if HAS_CAUGHT_BG and caught_bg is not None:
            screen.blit(caught_bg, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 70))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill((25, 25, 25))

        bw, bh = int(WIDTH*0.33), int(HEIGHT*0.12)
        bx = WIDTH // 2 - bw // 2

        retry_rect = pygame.Rect(bx, int(HEIGHT*0.66), bw, bh)
        if menu_button(retry_rect, "RETRY") and click:
            start_level(last_run_level)

        back_rect = pygame.Rect(bx, int(HEIGHT*0.80), bw, bh)
        if menu_button(back_rect, "TERUG NAAR LEVELS") and click:
            scene = SCENE_LEVEL_SELECT

        hint = small.render("ESC = hoofdmenu", True, (255, 255, 255))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - int(HEIGHT*0.06)))

    pygame.display.flip()

pygame.quit()
