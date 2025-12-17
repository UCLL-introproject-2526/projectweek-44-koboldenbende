import os
import json
import random
import pygame

# -----------------------------
# Config
# -----------------------------
WIDTH, HEIGHT = 960, 540
FPS = 60

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SAVE_PATH = os.path.join(os.path.dirname(__file__), "save.json")

PHONE_POINTS_PER_SEC = 10
MAX_HOLD_BONUS = 3.0  # Maximum multiplier

# Level select layout
GRID_COLS = 5
GRID_ROWS = 3
TOTAL_LEVELS = GRID_COLS * GRID_ROWS  # 15
TILE_W, TILE_H = 140, 110
GRID_TOP = 140
GRID_LEFT = (WIDTH - GRID_COLS * TILE_W) // 2

# Stars thresholds
STAR_1 = 180
STAR_2 = 320
STAR_3 = 500

# Desk overlay tuning
DESK_Y_OFFSET = 0

# Hands overlay tuning
HANDS_Y_OFFSET = 6

# Coins rewards
COINS_BASE_WIN = 10
COINS_PER_STAR = 10
COINS_FIRST_CLEAR_BONUS = 50

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
# Shop catalog (ALLEEN laptops)
# -----------------------------
SHOP_ITEMS = {
    "laptop_default": {"type": "laptop", "price": 0,   "file": "laptopnohands.png", "name": "Laptop Default"},
    "laptop_gaming":  {"type": "laptop", "price": 150, "file": "gaminglaptop.png",  "name": "Gaming Laptop"},
    "roze_laptop":    {"type": "laptop", "price": 250, "file": "rozelaptop.png",    "name": "Roze Laptop"},
    "future_gaming":  {"type": "laptop", "price": 300, "file": "futurlaptop.png",   "name": "Future Laptop"},
}

# -----------------------------
# Difficulty generator
# -----------------------------
def make_level_params(i: int):
    t = i / (TOTAL_LEVELS - 1)
    min_wait = 3.2 - 1.6 * t
    max_wait = 6.2 - 2.2 * t
    walk_in = 1.05 - 0.35 * t
    walk_out = walk_in  # ✅ nieuw: terug lopen duurt zelfde als binnenlopen
    look = 1.20 + 0.70 * t
    grace = 0.60 - 0.35 * t
    mult = 1.00 + 0.30 * t
    min_wait = max(1.0, min_wait)
    max_wait = max(min_wait + 0.5, max_wait)
    walk_in = max(0.55, walk_in)
    walk_out = max(0.55, walk_out)
    grace = max(0.18, grace)
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
    return pygame.transform.scale(img, (w, h))

def draw_text(surf, font_obj, text, x, y, color=(20, 20, 25)):
    surf.blit(font_obj.render(text, True, color), (x, y))

def clamp(v, a, b):
    return max(a, min(b, v))

# -----------------------------
# Save (coins + laptop shop)
# -----------------------------
DEFAULT_SAVE = {
    "unlocked": 1,
    "stars": [0]*TOTAL_LEVELS,
    "coins": 0,
    "owned": {
        "laptop_default": True,
    },
    "equipped": {
        "laptop": "laptop_default",
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

        data["owned"]["laptop_default"] = True

        if "laptop" not in data["equipped"]:
            data["equipped"]["laptop"] = "laptop_default"
        if data["equipped"]["laptop"] not in SHOP_ITEMS:
            data["equipped"]["laptop"] = "laptop_default"

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

# -----------------------------
# Game helpers
# -----------------------------
def schedule_next_check(play_state, params):
    BOSS_SOUND_START_OFFSET = 0.5
    play_state["next_check_in"] = random.uniform(params["min_wait"], params["max_wait"]) - BOSS_SOUND_START_OFFSET
    play_state["next_check_in"] = max(0.1, play_state["next_check_in"])
    play_state["pre_walk_sound_started"] = False

def score_to_stars(score_int: int) -> int:
    if score_int >= STAR_3:
        return 3
    if score_int >= STAR_2:
        return 2
    if score_int >= STAR_1:
        return 1
    return 0

def set_boss_path(play_state, direction="in"):
    # binnenkomen: random side
    if direction == "in":
        from_left = random.choice([True, False])
        start_x = -80 if from_left else WIDTH + 80
        end_x = LAPTOP_POS[0] + LAPTOP_SIZE[0] // 2
        play_state["boss_start"] = (start_x, BOSS_START_Y)
        play_state["boss_end"] = (end_x, BOSS_END_Y)
        play_state["boss_from_left"] = from_left
    else:
        # wegwandelen: terug naar dezelfde kant
        from_left = play_state.get("boss_from_left", True)
        start_x = LAPTOP_POS[0] + LAPTOP_SIZE[0] // 2
        end_x = -80 if from_left else WIDTH + 80
        play_state["boss_start"] = (start_x, BOSS_START_Y)
        play_state["boss_end"] = (end_x, BOSS_END_Y)

# -----------------------------
# Init pygame
# -----------------------------
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Office Game - Main Menu + Shop")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 28)
small = pygame.font.SysFont(None, 22)
big = pygame.font.SysFont(None, 72)
title_font = pygame.font.SysFont(None, 86)

# -----------------------------
# Load visuals
# -----------------------------
img_background = load_image("Background.png")
background_s = scale(img_background, WIDTH, HEIGHT)

img_desk = load_image("desk.png")
img_boss = load_image("boss.png")

img_hands_0 = load_image("hands1.png")
img_hands_1 = load_image("hands2.png")
img_phone = load_image("phone.png")

# Main menu background (optional)
try:
    img_main_menu_bg = load_image("main_menu_bg.png")
    main_menu_bg = scale(img_main_menu_bg, WIDTH, HEIGHT)
    HAS_MENU_BG = True
except Exception:
    HAS_MENU_BG = False

# Game over background: caught_bg.png
try:
    img_caught_bg = load_image("caught_bg.png")
    caught_bg = scale(img_caught_bg, WIDTH, HEIGHT)
    HAS_CAUGHT_BG = True
except Exception:
    HAS_CAUGHT_BG = False

# Desk scaling
desk_scale = WIDTH / img_desk.get_width()
desk_h = int(img_desk.get_height() * desk_scale - 120)
desk_s = pygame.transform.smoothscale(img_desk, (WIDTH, desk_h))
DESK_POS = (0, HEIGHT - desk_h + DESK_Y_OFFSET)

# Laptop placement
LAPTOP_SIZE = (520, 260)
LAPTOP_POS = (WIDTH//2 - LAPTOP_SIZE[0]//2, HEIGHT - LAPTOP_SIZE[1] - 22)

# Phone placement
PHONE_SIZE = (300, 300)
PHONE_POS = (
    WIDTH//2 - PHONE_SIZE[0]//2,
    LAPTOP_POS[1] + (LAPTOP_SIZE[1]//2 - PHONE_SIZE[1]//2) + 6
)

hands_0_s = scale(img_hands_0, *LAPTOP_SIZE)
hands_1_s = scale(img_hands_1, *LAPTOP_SIZE)
phone_s = scale(img_phone, *PHONE_SIZE)

# Boss sizing
BOSS_FAR  = (190, 285)
BOSS_NEAR = (190, 285)
BOSS_END_Y = LAPTOP_POS[1] + 12
BOSS_START_Y = BOSS_END_Y

# -----------------------------
# Load audio
# -----------------------------
try:
    snd_boss_walk = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "loud-footsteps-62038-VEED.mp3"))
    snd_typing = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "typing-keyboard-asmr-356116.mp3"))
    snd_phone_use = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "Mathias Vandenboer_s Video - Dec 16, 2025-VEED.mp3.mp3"))
    snd_boss_chatter = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "angry-boss-chatter.mp3"))
    snd_boss_chatter.set_volume(0.5)

    try:
        snd_game_over = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "game_over.wav"))
    except Exception:
        snd_game_over = pygame.mixer.Sound(b"\x00\x00\x00\x00")

    try:
        snd_complete = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "level_complete.wav"))
    except Exception:
        snd_complete = pygame.mixer.Sound(b"\x00\x00\x00\x00")
except pygame.error as e:
    print(f"Fout bij het laden van audio: {e}")
    snd_boss_walk = pygame.mixer.Sound(b"\x00\x00\x00\x00")
    snd_typing = pygame.mixer.Sound(b"\x00\x00\x00\x00")
    snd_phone_use = pygame.mixer.Sound(b"\x00\x00\x00\x00")
    snd_game_over = pygame.mixer.Sound(b"\x00\x00\x00\x00")
    snd_complete = pygame.mixer.Sound(b"\x00\x00\x00\x00")
    snd_boss_chatter = pygame.mixer.Sound(b"\x00\x00\x00\x00")

try:
    snd_buy = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "purchase-success-384963.mp3"))
except Exception:
    snd_buy = pygame.mixer.Sound(b"\x00\x00\x00\x00")

try:
    snd_menu_click = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "menu_click.wav"))
except Exception:
    snd_menu_click = pygame.mixer.Sound(b"\x00\x00\x00\x00")

# -----------------------------
# Save + laptop asset loader
# -----------------------------
save = load_save()

img_laptop_nohands = None
laptop_nohands_s = None

def reload_laptop_asset():
    global img_laptop_nohands, laptop_nohands_s
    key = save["equipped"].get("laptop", "laptop_default")
    if key not in SHOP_ITEMS:
        key = "laptop_default"
    img_laptop_nohands = load_image(SHOP_ITEMS[key]["file"])
    laptop_nohands_s = scale(img_laptop_nohands, *LAPTOP_SIZE)

reload_laptop_asset()

# -----------------------------
# Shop thumbnails
# -----------------------------
THUMB_W, THUMB_H = 180, 95
shop_thumbs = {}

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

build_shop_thumbs()

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

    stop_all_loop_sounds()
    schedule_next_check(play, params)

    scene = SCENE_PLAY
    snd_typing.play(-1)

def buy_or_equip(item_id: str):
    global popup_text, popup_timer

    if item_id not in SHOP_ITEMS:
        return

    item = SHOP_ITEMS[item_id]
    owned = bool(save["owned"].get(item_id, False))
    equipped = (save["equipped"].get("laptop") == item_id)

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

    save["equipped"]["laptop"] = item_id
    write_save(save)
    reload_laptop_asset()

# -----------------------------
# Main loop
# -----------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    if popup_timer > 0:
        popup_timer = max(0.0, popup_timer - dt)

    # scene change sound logic
    if scene != current_scene:
        stop_all_loop_sounds()

        if scene == SCENE_COMPLETE:
            snd_complete.play()
        elif scene == SCENE_GAMEOVER:
            snd_game_over.play()

        if scene == SCENE_PLAY and not play["phone"] and not play["gameover"]:
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

            if event.key == pygame.K_r and scene in (SCENE_GAMEOVER, SCENE_COMPLETE):
                scene = SCENE_MAIN_MENU

        if event.type == pygame.KEYUP:
            if scene == SCENE_PLAY and event.key == pygame.K_SPACE:
                play["phone"] = False
                snd_phone_use.stop()
                if not play["gameover"]:
                    snd_typing.play(-1)

    # Update play
    if scene == SCENE_PLAY and not play["gameover"]:
        params = make_level_params(selected_level - 1)

        # hands anim
        if not play["phone"]:
            play["hands_anim_t"] += dt
            if play["hands_anim_t"] >= 0.15:
                play["hands_anim_t"] -= 0.15
                play["hands_anim_frame"] = 1 - play["hands_anim_frame"]
        else:
            play["hands_anim_t"] = 0.0
            play["hands_anim_frame"] = 0

        # scoring + combo
        if play["phone"]:
            play["phone_hold_time"] += dt
            combo_curve_exponent = 0.5
            raw_bonus = 1.0 + (play["phone_hold_time"] ** combo_curve_exponent)
            hold_bonus = min(raw_bonus, MAX_HOLD_BONUS)
            play["score"] += PHONE_POINTS_PER_SEC * hold_bonus * params["mult"] * dt
        else:
            play["phone_hold_time"] = 0.0

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
            if play["phone"] and play["reaction_timer"] > params["grace"]:
                play["caught"] = True
                play["gameover"] = True

            if play["boss_timer"] >= params["walk_in"]:
                play["boss_timer"] = 0.0
                play["boss_state"] = LOOKING
                snd_boss_walk.stop()
                snd_boss_chatter.play(-1)

        elif play["boss_state"] == LOOKING:
            if play["phone"]:
                play["caught"] = True
                play["gameover"] = True

            if play["boss_timer"] >= params["look"]:
                # ✅ eerst wegwandelen ipv despawnen
                play["boss_state"] = WALKING_OUT
                play["boss_timer"] = 0.0
                snd_boss_chatter.stop()
                set_boss_path(play, direction="out")
                snd_boss_walk.play(-1)

        elif play["boss_state"] == WALKING_OUT:
            # baas kijkt niet meer, dus geen catch
            if play["boss_timer"] >= params["walk_out"]:
                play["boss_state"] = WAIT
                play["boss_timer"] = 0.0
                snd_boss_walk.stop()
                schedule_next_check(play, params)
                if not play["phone"] and not play["gameover"]:
                    snd_typing.play(-1)

        # Win condition
        if play["score"] >= STAR_3:
            last_run_score = int(play["score"])
            last_run_level = selected_level
            last_run_stars = score_to_stars(last_run_score)

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
            last_run_stars = score_to_stars(last_run_score)
            scene = SCENE_GAMEOVER

    # -----------------------------
    # DRAW
    # -----------------------------
    if scene == SCENE_MAIN_MENU:
        if HAS_MENU_BG:
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

        button_width = 300
        button_height = 60
        button_x = WIDTH//2 - button_width//2

        start_rect = pygame.Rect(button_x, 180, button_width, button_height)
        if menu_button(start_rect, "START GAME") and click:
            start_level(save["unlocked"])

        levels_rect = pygame.Rect(button_x, 260, button_width, button_height)
        if menu_button(levels_rect, "LEVEL SELECT") and click:
            scene = SCENE_LEVEL_SELECT

        shop_rect = pygame.Rect(button_x, 340, button_width, button_height)
        if menu_button(shop_rect, "SHOP") and click:
            scene = SCENE_SHOP
            if shop_selected_id is None:
                shop_selected_id = "laptop_default"

        quit_rect = pygame.Rect(button_x, 420, button_width, button_height)
        if menu_button(quit_rect, "QUIT GAME") and click:
            running = False

        footer_text = small.render("SPATIE = telefoon | ESC = menu", True, (0, 0, 0))
        screen.blit(footer_text, (WIDTH//2 - footer_text.get_width()//2, HEIGHT - 40))

    elif scene == SCENE_LEVEL_SELECT:
        pygame.draw.rect(screen, (170, 210, 240), (0, 0, WIDTH, 160))
        pygame.draw.rect(screen, (120, 180, 230), (0, 160, WIDTH, HEIGHT-160))

        back_rect = pygame.Rect(20, 20, 120, 40)
        if button(back_rect, "< Terug") and click:
            scene = SCENE_MAIN_MENU

        draw_text(screen, big, "LEVELS", 40, 30, (255, 255, 255))
        draw_text(screen, font, f"Unlocked: {save['unlocked']} / {TOTAL_LEVELS}", 42, 95, (255, 255, 255))
        draw_text(screen, font, f"Coins: {save['coins']}", WIDTH - 170, 95, (255, 255, 255))

        shop_btn = pygame.Rect(WIDTH - 200, 30, 160, 52)
        if button(shop_btn, "SHOP") and click:
            scene = SCENE_SHOP
            if shop_selected_id is None:
                shop_selected_id = "laptop_default"

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                idx = r*GRID_COLS + c
                lvl_num = idx + 1
                x = GRID_LEFT + c*TILE_W
                y = GRID_TOP + r*TILE_H
                rect = pygame.Rect(x+10, y+10, TILE_W-20, TILE_H-20)

                unlocked = lvl_num <= save["unlocked"]
                mx, my = pygame.mouse.get_pos()
                hover = rect.collidepoint(mx, my)

                if unlocked:
                    fill = (245, 230, 160) if hover else (240, 220, 140)
                    pygame.draw.rect(screen, fill, rect, border_radius=16)
                    pygame.draw.rect(screen, (150, 120, 70), rect, 3, border_radius=16)

                    t = font.render(str(lvl_num), True, (55, 45, 35))
                    screen.blit(t, (rect.x + 12, rect.y + 10))

                    draw_star_row(rect.x + 18, rect.y + 52, save["stars"][idx], size=18, gap=6)

                    if click and hover:
                        start_level(lvl_num)
                else:
                    fill = (200, 200, 205) if hover else (190, 190, 195)
                    pygame.draw.rect(screen, fill, rect, border_radius=16)
                    pygame.draw.rect(screen, (130, 130, 140), rect, 3, border_radius=16)
                    draw_text(screen, font, "LOCK", rect.centerx-22, rect.centery-12, (90, 90, 100))

        draw_text(screen, small, "Klik op een level. (ESC = hoofdmenu)", 40, HEIGHT-40, (255, 255, 255))

    elif scene == SCENE_SHOP:
        screen.fill(COL_PANEL_BG)

        draw_text(screen, big, "SHOP", 40, 18, COL_TEXT)
        draw_text(screen, font, f"Coins: {save['coins']}", WIDTH - 200, 40, COL_TEXT)
        draw_text(screen, small, "Klik laptop. Rechts: prijs + KOOP/EQUIP. ESC = hoofdmenu.", 40, 88, COL_TEXT)

        grid_x, grid_y = 40, 120
        grid_w, grid_h = 620, HEIGHT - 160
        side_x = grid_x + grid_w + 20
        side_y = grid_y
        side_w = WIDTH - side_x - 40

        grid_rect = pygame.Rect(grid_x, grid_y, grid_w, grid_h)
        side_rect = pygame.Rect(side_x, side_y, side_w, grid_h)

        pygame.draw.rect(screen, COL_CARD_BG, grid_rect, border_radius=18)
        pygame.draw.rect(screen, COL_BORDER, grid_rect, 3, border_radius=18)
        pygame.draw.rect(screen, COL_CARD_BG, side_rect, border_radius=18)
        pygame.draw.rect(screen, COL_BORDER, side_rect, 3, border_radius=18)

        items = list(SHOP_ITEMS.items())
        if shop_selected_id is None and items:
            shop_selected_id = items[0][0]

        cols = 3
        pad = 16
        card_w = (grid_w - pad*(cols+1)) // cols
        card_h = 150

        mx, my = pygame.mouse.get_pos()

        for idx, (item_id, item) in enumerate(items):
            rr = idx // cols
            cc = idx % cols
            x = grid_x + pad + cc*(card_w + pad)
            y = grid_y + pad + rr*(card_h + pad)
            card = pygame.Rect(x, y, card_w, card_h)

            owned = bool(save["owned"].get(item_id, False))
            equipped = (save["equipped"].get("laptop") == item_id)
            selected = (shop_selected_id == item_id)

            bg = (255, 255, 255) if not selected else (255, 245, 210)
            pygame.draw.rect(screen, bg, card, border_radius=16)
            pygame.draw.rect(screen, COL_BORDER if selected else COL_MUTED, card, 3, border_radius=16)

            thumb = shop_thumbs.get(item_id)
            if thumb:
                thumb_rect = thumb.get_rect(center=(card.centerx, card.y + 60))
                screen.blit(thumb, thumb_rect)

            name_s = small.render(item["name"], True, COL_TEXT)
            screen.blit(name_s, (card.x + 10, card.y + 102))

            if equipped:
                tag = "EQUIPPED"
            elif owned:
                tag = "OWNED"
            else:
                tag = f"{item['price']} coins"

            tag_s = small.render(tag, True, COL_TEXT)
            screen.blit(tag_s, (card.x + 10, card.y + 124))

            if click and card.collidepoint(mx, my):
                shop_selected_id = item_id

        if shop_selected_id in SHOP_ITEMS:
            item = SHOP_ITEMS[shop_selected_id]
            owned = bool(save["owned"].get(shop_selected_id, False))
            equipped = (save["equipped"].get("laptop") == shop_selected_id)

            draw_text(screen, font, "Selected:", side_x + 18, side_y + 18, COL_TEXT)
            draw_text(screen, font, item["name"], side_x + 18, side_y + 46, COL_TEXT)

            preview = shop_thumbs.get(shop_selected_id)
            if preview:
                big_prev = pygame.transform.smoothscale(preview, (side_w - 36, 120))
                screen.blit(big_prev, (side_x + 18, side_y + 80))

            draw_text(screen, font, f"Price: {item['price']} coins", side_x + 18, side_y + 215, COL_TEXT)
            status = "Equipped" if equipped else ("Owned" if owned else "Not owned")
            draw_text(screen, font, f"Status: {status}", side_x + 18, side_y + 245, COL_TEXT)

            btn = pygame.Rect(side_x + 18, side_y + 300, side_w - 36, 56)

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
            w, h = 520, 70
            px = (WIDTH - w) // 2
            py = 20
            rect = pygame.Rect(px, py, w, h)
            pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=16)
            pygame.draw.rect(screen, COL_BORDER, rect, 3, border_radius=16)
            t = font.render(popup_text, True, COL_TEXT)
            screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

    elif scene == SCENE_PLAY:
        params = make_level_params(selected_level - 1)

        screen.blit(background_s, (0, 0))

        # boss: ook tekenen tijdens WALKING_OUT
        if play["boss_state"] in (WALKING_IN, LOOKING, WALKING_OUT):
            if play["boss_state"] == WALKING_IN:
                t = clamp(play["boss_timer"] / params["walk_in"], 0.0, 1.0)
            elif play["boss_state"] == WALKING_OUT:
                t = clamp(play["boss_timer"] / params["walk_out"], 0.0, 1.0)
            else:
                t = 1.0

            sx, sy = play["boss_start"]
            ex, ey = play["boss_end"]

            bx = int(sx + (ex - sx) * t)
            by = int(sy + (ey - sy) * t)

            bw = int(BOSS_FAR[0] + (BOSS_NEAR[0] - BOSS_FAR[0]) * t)
            bh = int(BOSS_FAR[1] + (BOSS_NEAR[1] - BOSS_FAR[1]) * t)

            boss_scaled = scale(img_boss, bw, bh)
            boss_rect = boss_scaled.get_rect(center=(bx, by))
            screen.blit(boss_scaled, boss_rect)

        screen.blit(desk_s, DESK_POS)
        screen.blit(laptop_nohands_s, LAPTOP_POS)

        hands_pos = (LAPTOP_POS[0], LAPTOP_POS[1] + HANDS_Y_OFFSET)
        if play["phone"]:
            screen.blit(phone_s, PHONE_POS)
        else:
            screen.blit(hands_0_s if play["hands_anim_frame"] == 0 else hands_1_s, hands_pos)

        # UI
        draw_text(screen, font,
                  f"Level {selected_level}  |  Punten: {int(play['score'])}  |  x{params['mult']:.2f}",
                  16, 14, (0, 0, 0))
        draw_text(screen, small, "Houd SPATIE = telefoon | ESC = hoofdmenu",
                  16, 44, (0, 0, 0))

        if play["boss_state"] == WALKING_IN:
            left = max(0.0, params["grace"] - play["reaction_timer"])
            draw_text(screen, font, f"BAAS KOMT! Loslaten binnen {left:.2f}s!", 16, 72, (204, 0, 0))
        elif play["boss_state"] == LOOKING:
            draw_text(screen, font, "BAAS KIJKT!", 16, 72, (204, 0, 0))

        pct = clamp(play["score"] / STAR_3, 0.0, 1.0)
        bar = pygame.Rect(16, 110, 260, 18)
        pygame.draw.rect(screen, (20, 20, 25), bar, border_radius=8)
        pygame.draw.rect(screen, (90, 220, 120), (bar.x, bar.y, int(bar.w*pct), bar.h), border_radius=8)
        draw_text(screen, small, f"Doel: {STAR_3} punten (finish)", 16, 132, (0, 0, 0))

        # Vertical multiplier bar (bottom-right)
        if play["phone"]:
            combo_curve_exponent = 0.5
            raw_bonus = 1.0 + (play["phone_hold_time"] ** combo_curve_exponent)
            hold_bonus = min(raw_bonus, MAX_HOLD_BONUS)

            bar_w = 20
            bar_h = 120
            bar_x = WIDTH - bar_w - 20
            bar_y = HEIGHT - bar_h - 20

            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            fill_h = int(bar_h * (hold_bonus / MAX_HOLD_BONUS))
            pygame.draw.rect(screen, (255, 200, 50), (bar_x, bar_y + bar_h - fill_h, bar_w, fill_h), border_radius=6)
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)
            draw_text(screen, small, f"x{hold_bonus:.2f}", bar_x - 10, bar_y - 24, (204, 0, 0))

    elif scene == SCENE_COMPLETE:
        screen.fill((170, 230, 190))
        draw_text(screen, big, "LEVEL COMPLETE!", 60, 70, (25, 60, 35))
        draw_text(screen, font, f"Level {last_run_level}  Score: {last_run_score}", 65, 165, (25, 60, 35))
        draw_star_row(70, 210, last_run_stars, size=34, gap=16)

        b1 = pygame.Rect(60, 300, 300, 60)
        b2 = pygame.Rect(60, 370, 300, 60)

        if button(b1, "Hoofdmenu") and click:
            scene = SCENE_MAIN_MENU

        if last_run_level < TOTAL_LEVELS:
            can_next = (last_run_level + 1) <= save["unlocked"]
            if button(b2, "Volgende Level", enabled=can_next) and click and can_next:
                start_level(last_run_level + 1)
        else:
            button(b2, "Laatste level!", enabled=False)

    elif scene == SCENE_GAMEOVER:
        if HAS_CAUGHT_BG:
            screen.blit(caught_bg, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 70))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill((25, 25, 25))

        bw, bh = 320, 62
        bx = WIDTH // 2 - bw // 2

        retry_rect = pygame.Rect(bx, 360, bw, bh)
        if menu_button(retry_rect, "RETRY") and click:
            start_level(last_run_level)

        back_rect = pygame.Rect(bx, 435, bw, bh)
        if menu_button(back_rect, "TERUG NAAR LEVELS") and click:
            scene = SCENE_LEVEL_SELECT

        hint = small.render("ESC = hoofdmenu", True, (255, 255, 255))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 30))

    pygame.display.flip()

pygame.quit()
