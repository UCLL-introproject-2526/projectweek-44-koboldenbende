import os
import json
import random
import pygame
from minigames import create_random_game


# -----------------------------
# Config
# -----------------------------
WIDTH, HEIGHT = 960, 540
FPS = 60

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SAVE_PATH = os.path.join(os.path.dirname(__file__), "save.json")

PHONE_POINTS_PER_SEC = 18

# Level select layout
GRID_COLS = 5
GRID_ROWS = 3
TOTAL_LEVELS = GRID_COLS * GRID_ROWS  # 15
TILE_W, TILE_H = 140, 110
GRID_TOP = 140
GRID_LEFT = (WIDTH - GRID_COLS * TILE_W) // 2

# Stars thresholds (punten nodig in 1 run)
STAR_1 = 180
STAR_2 = 320
STAR_3 = 500

# Difficulty generator per level index (0..14)
def make_level_params(i: int):
    t = i / (TOTAL_LEVELS - 1)
    min_wait = 3.2 - 1.6 * t
    max_wait = 6.2 - 2.2 * t
    walk_in = 1.05 - 0.35 * t
    look = 1.20 + 0.70 * t
    grace = 0.60 - 0.35 * t
    mult = 1.00 + 0.30 * t
    min_wait = max(1.0, min_wait)
    max_wait = max(min_wait + 0.5, max_wait)
    walk_in = max(0.55, walk_in)
    grace = max(0.18, grace)
    return dict(min_wait=min_wait, max_wait=max_wait, walk_in=walk_in, look=look, grace=grace, mult=mult)

WAIT, WALKING_IN, LOOKING = "wait", "walking_in", "looking"

# Scenes
SCENE_LEVEL_SELECT = "level_select"
SCENE_PLAY = "play"
SCENE_COMPLETE = "complete"
SCENE_GAMEOVER = "gameover"

# -----------------------------
# Utils
# -----------------------------
def load_image(filename: str) -> pygame.Surface:
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Asset ontbreekt: {path}")
    return pygame.image.load(path).convert_alpha()

def scale(img, w, h):
    # pixel-sharp
    return pygame.transform.scale(img, (w, h))

def draw_text(surf, font_obj, text, x, y, color=(20, 20, 25)):
    surf.blit(font_obj.render(text, True, color), (x, y))

def clamp(v, a, b):
    return max(a, min(b, v))

def load_save():
    if not os.path.exists(SAVE_PATH):
        return {"unlocked": 1, "stars": [0]*TOTAL_LEVELS}
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "unlocked" not in data or "stars" not in data:
            raise ValueError("bad save")
        if len(data["stars"]) != TOTAL_LEVELS:
            data["stars"] = (data["stars"] + [0]*TOTAL_LEVELS)[:TOTAL_LEVELS]
        data["unlocked"] = int(clamp(int(data["unlocked"]), 1, TOTAL_LEVELS))
        return data
    except Exception:
        return {"unlocked": 1, "stars": [0]*TOTAL_LEVELS}

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

# -----------------------------
# Game helpers
# -----------------------------
def schedule_next_check(play_state, params):
    play_state["next_check_in"] = random.uniform(params["min_wait"], params["max_wait"])

def score_to_stars(score_int: int) -> int:
    if score_int >= STAR_3:
        return 3
    if score_int >= STAR_2:
        return 2
    if score_int >= STAR_1:
        return 1
    return 0

# -----------------------------
# Init pygame
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Office Game - Laptop Hands Switch")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 28)
small = pygame.font.SysFont(None, 22)
big = pygame.font.SysFont(None, 72)

# -----------------------------
# Load visuals (OFFICE)
# -----------------------------
img_desk = load_image("Desk.png")
img_door = load_image("pixel_door.png")
img_boss = load_image("boss.png")
img_chair = load_image("Boss-Chair.png")
img_plant = load_image("Big-Plant.png")
img_cabinet = load_image("Big-Filing-Cabinet.png")
img_printer_big = load_image("Big-Office-Printer.png")
img_printer_small = load_image("Printer.png")

# NEW: laptop+hands, laptop zonder handen, telefoon overlay
img_laptop_hands = load_image("laptophands.png")
img_laptop_nohands = load_image("laptopnohands.png")
img_phone = load_image("phone.png")

# -----------------------------
# First-person scene layout
# -----------------------------
HORIZON_Y = 190

DOOR_POS = (55, 50)
DOOR_SIZE = (100, 190)

CABINET_POS = (150, 85)
CABINET_SIZE = (95, 145)

PLANT_POS = (220, 120)
PLANT_SIZE = (75, 115)

PRINTER_BIG_POS = (740, 90)
PRINTER_BIG_SIZE = (150, 160)

PRINTER_SMALL_POS = (660, 160)
PRINTER_SMALL_SIZE = (90, 90)

CHAIR_POS = (540, 205)
CHAIR_SIZE = (80, 80)

DESK_POS = (0, 330)
DESK_SIZE = (WIDTH, 230)

# Laptop placement
LAPTOP_POS = (WIDTH//2 - 260, 285)
LAPTOP_SIZE = (520, 260)

# Phone placement (centered on laptop area)
PHONE_SIZE = (300, 300)
PHONE_POS = (WIDTH//2 - PHONE_SIZE[0]//2, 285 + 10)

# Boss comes in
BOSS_START = (DOOR_POS[0] + DOOR_SIZE[0]//2, DOOR_POS[1] + DOOR_SIZE[1] - 10)
BOSS_END = (WIDTH//2, 330)  # behind laptop
BOSS_FAR = (28, 42)
BOSS_NEAR = (120, 180)

# Pre-scale static items
desk_s = scale(img_desk, *DESK_SIZE)
door_s = scale(img_door, *DOOR_SIZE)
plant_s = scale(img_plant, *PLANT_SIZE)
cabinet_s = scale(img_cabinet, *CABINET_SIZE)
printer_big_s = scale(img_printer_big, *PRINTER_BIG_SIZE)
printer_small_s = scale(img_printer_small, *PRINTER_SMALL_SIZE)
chair_s = scale(img_chair, *CHAIR_SIZE)

# Pre-scale laptop variants + phone
laptop_hands_s = scale(img_laptop_hands, *LAPTOP_SIZE)
laptop_nohands_s = scale(img_laptop_nohands, *LAPTOP_SIZE)
phone_s = scale(img_phone, *PHONE_SIZE)

# -----------------------------
# Game state
# -----------------------------
def reset():
    lvl_idx = 0
    return {
        "score": 0.0,
        "phone": False,
        "gameover": False,
        "caught": False,

        "lvl_idx": lvl_idx,

        "boss_state": WAIT,
        "boss_timer": 0.0,
        "next_check_in": schedule_next_check(LEVELS[lvl_idx]),
        "reaction_timer": 0.0,
    }

def start_level(level_num: int):
    global scene, selected_level
    selected_level = level_num
    params = make_level_params(level_num - 1)

    play["score"] = 0.0
    play["phone"] = False
    play["gameover"] = False
    play["caught"] = False
    play["boss_state"] = WAIT
    play["boss_timer"] = 0.0
    play["reaction_timer"] = 0.0
    schedule_next_check(play, params)

    scene = SCENE_PLAY

# -----------------------------
# Main loop
# -----------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    click = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and scene == SCENE_PLAY:
                scene = SCENE_LEVEL_SELECT

            if scene == SCENE_PLAY:
                if event.key == pygame.K_SPACE and not play["gameover"]:
                    play["phone"] = True

            if event.key == pygame.K_r and scene in (SCENE_GAMEOVER, SCENE_COMPLETE):
                scene = SCENE_LEVEL_SELECT

        if event.type == pygame.KEYUP:
            if scene == SCENE_PLAY and event.key == pygame.K_SPACE:
                play["phone"] = False

    # Update
    if not state["gameover"]:
        if state["phone"]:
            state["score"] += PHONE_POINTS_PER_SEC * lvl["mult"] * dt

        # level up
        new_idx = level_for_score(state["score"])
        if new_idx > state["lvl_idx"]:
            state["lvl_idx"] = new_idx
            lvl = LEVELS[state["lvl_idx"]]
            state["boss_state"] = WAIT
            state["boss_timer"] = 0.0
            state["next_check_in"] = schedule_next_check(lvl)

        state["boss_timer"] += dt

        if state["boss_state"] == WAIT:
            if state["boss_timer"] >= state["next_check_in"]:
                state["boss_timer"] = 0.0
                state["boss_state"] = WALKING_IN
                state["reaction_timer"] = 0.0
                state["caught"] = False

        elif play["boss_state"] == WALKING_IN:
            play["reaction_timer"] += dt
            if play["phone"] and play["reaction_timer"] > params["grace"]:
                play["caught"] = True
                play["gameover"] = True

            if play["boss_timer"] >= params["walk_in"]:
                play["boss_timer"] = 0.0
                play["boss_state"] = LOOKING

        elif play["boss_state"] == LOOKING:
            if play["phone"]:
                play["caught"] = True
                play["gameover"] = True

            if play["boss_timer"] >= params["look"]:
                play["boss_state"] = WAIT
                play["boss_timer"] = 0.0
                schedule_next_check(play, params)

        # Win condition
        if play["score"] >= STAR_3:
            last_run_score = int(play["score"])
            last_run_level = selected_level
            last_run_stars = score_to_stars(last_run_score)

            save["stars"][last_run_level - 1] = max(save["stars"][last_run_level - 1], last_run_stars)
            if last_run_level < TOTAL_LEVELS:
                save["unlocked"] = max(save["unlocked"], last_run_level + 1)
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
    screen.fill((210, 225, 245))

    if scene == SCENE_LEVEL_SELECT:
        pygame.draw.rect(screen, (170, 210, 240), (0, 0, WIDTH, 160))
        pygame.draw.rect(screen, (120, 180, 230), (0, 160, WIDTH, HEIGHT-160))

        draw_text(screen, big, "LEVELS", 40, 30, (255, 255, 255))
        draw_text(screen, font, f"Unlocked: {save['unlocked']} / {TOTAL_LEVELS}", 42, 95, (255, 255, 255))

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

        draw_text(screen, small, "Klik op een level. (ESC in-game = terug)", 40, HEIGHT-40, (255, 255, 255))

    elif scene == SCENE_PLAY:
        params = make_level_params(selected_level - 1)

        # wall
        screen.fill((216, 216, 222))
        for x in range(0, WIDTH, 90):
            pygame.draw.line(screen, (206, 206, 212), (x, 0), (x, HEIGHT), 1)
        pygame.draw.rect(screen, (200, 200, 206), (0, HORIZON_Y, WIDTH, 8))

        # background props
        screen.blit(door_s, DOOR_POS)
        screen.blit(cabinet_s, CABINET_POS)
        screen.blit(plant_s, PLANT_POS)
        screen.blit(printer_big_s, PRINTER_BIG_POS)
        screen.blit(printer_small_s, PRINTER_SMALL_POS)
        screen.blit(chair_s, CHAIR_POS)

        # boss (walks in and grows)
        if play["boss_state"] in (WALKING_IN, LOOKING):
            if play["boss_state"] == WALKING_IN:
                t = clamp(play["boss_timer"] / params["walk_in"], 0.0, 1.0)
            else:
                t = 1.0
            bx = int(BOSS_START[0] + (BOSS_END[0] - BOSS_START[0]) * t)
            by = int(BOSS_START[1] + (BOSS_END[1] - BOSS_START[1]) * t)
            bw = int(BOSS_FAR[0] + (BOSS_NEAR[0] - BOSS_FAR[0]) * t)
            bh = int(BOSS_FAR[1] + (BOSS_NEAR[1] - BOSS_FAR[1]) * t)
            boss_scaled = scale(img_boss, bw, bh)
            boss_rect = boss_scaled.get_rect(center=(bx, by))
            screen.blit(boss_scaled, boss_rect)

        # desk
        screen.blit(desk_s, DESK_POS)

    # Laptop foreground (drawn)
    pygame.draw.rect(screen, (35, 35, 40), LAPTOP_RECT, border_radius=10)
    pygame.draw.rect(screen, (220, 220, 230), LAPTOP_RECT.inflate(-12, -12), border_radius=8)

    pygame.draw.rect(screen, (25, 25, 30), KEYBOARD_RECT, border_radius=10)

    # Phone overlay on laptop screen
    if state["phone"] and not state["gameover"]:
        # A "phone game" UI on screen
        inner = LAPTOP_RECT.inflate(-40, -40)
        pygame.draw.rect(screen, (20, 20, 25), inner, border_radius=10)
        pygame.draw.rect(screen, (70, 220, 120), (inner.x + 20, inner.y + 20, inner.w - 40, 18), border_radius=6)
        pygame.draw.rect(screen, (220, 60, 60), (inner.x + 20, inner.y + 50, inner.w - 40, 18), border_radius=6)
        pygame.draw.rect(screen, (80, 140, 240), (inner.x + 20, inner.y + 80, inner.w - 40, 18), border_radius=6)

    # UI
    score_i = int(state["score"])
    lvl = LEVELS[state["lvl_idx"]]
    screen.blit(font.render(f'{lvl["name"]} | Punten: {score_i} | x{lvl["mult"]:.2f}', True, (20, 20, 25)), (16, 12))
    screen.blit(font.render("Houd SPATIE = telefoon | R = restart", True, (70, 70, 80)), (16, 36))

    if state["boss_state"] == WALKING_IN and not state["gameover"]:
        left = max(0.0, lvl["grace"] - state["reaction_timer"])
        screen.blit(font.render(f"BAAS KOMT BINNEN! Loslaten binnen {left:.2f}s!", True, (200, 40, 40)), (16, 62))

    if state["gameover"]:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        go = big_font.render("GAME OVER", True, (255, 255, 255))
        screen.blit(go, (WIDTH // 2 - go.get_width() // 2, HEIGHT // 2 - 90))
        reason = "Je werd betrapt!" if state["caught"] else "Game over!"
        info = font.render(f"{reason} Score: {score_i} | Druk op R", True, (255, 255, 255))
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 - 20))

    pygame.display.flip()

pygame.quit()
