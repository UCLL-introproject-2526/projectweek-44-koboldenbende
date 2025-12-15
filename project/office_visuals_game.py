import os
import random
import pygame

# -----------------------------
# Config
# -----------------------------
WIDTH, HEIGHT = 960, 420
FPS = 60

PHONE_POINTS_PER_SEC = 18
FLOOR_Y = 330

# Levels (wordt steeds moeilijker)
LEVEL_UP_SCORE_STEP = 220
LEVELS = [
    dict(name="Level 1", min_wait=3.0, max_wait=6.0, walk_in=1.00, look=1.25, grace=0.55, mult=1.00),
    dict(name="Level 2", min_wait=2.6, max_wait=5.4, walk_in=0.95, look=1.35, grace=0.48, mult=1.05),
    dict(name="Level 3", min_wait=2.2, max_wait=4.9, walk_in=0.90, look=1.45, grace=0.42, mult=1.10),
    dict(name="Level 4", min_wait=1.9, max_wait=4.5, walk_in=0.85, look=1.55, grace=0.36, mult=1.15),
    dict(name="Level 5", min_wait=1.6, max_wait=4.1, walk_in=0.80, look=1.70, grace=0.30, mult=1.20),
]

WAIT, WALKING_IN, LOOKING = "wait", "walking_in", "looking"

# -----------------------------
# Assets
# -----------------------------
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def load_image(filename: str) -> pygame.Surface:
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Asset ontbreekt: {path}")
    return pygame.image.load(path).convert_alpha()

# -----------------------------
# Helpers
# -----------------------------
def schedule_next_check(lvl):
    return random.uniform(lvl["min_wait"], lvl["max_wait"])

def level_for_score(score: float) -> int:
    return min(len(LEVELS) - 1, int(score // LEVEL_UP_SCORE_STEP))

def blit_bottom(screen, img, x, bottom_y):
    r = img.get_rect()
    r.x = x
    r.bottom = bottom_y
    screen.blit(img, r)
    return r

def blit_bottom_center(screen, img, center_x, bottom_y):
    r = img.get_rect()
    r.centerx = center_x
    r.bottom = bottom_y
    screen.blit(img, r)
    return r

# -----------------------------
# Init
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Office Reaction Game (Your Visuals - Fixed)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 26)
big_font = pygame.font.SysFont(None, 70)

# Load PNGs (exact filenames from your screenshot)
img_desk = load_image("Desk.png")
img_door = load_image("pixel_door.png")
img_boss = load_image("boss.png")
img_boss_chair = load_image("Boss-Chair.png")
img_plant = load_image("Big-Plant.png")
img_cabinet = load_image("Big-Filing-Cabinet.png")
img_printer_big = load_image("Big-Office-Printer.png")
img_printer_small = load_image("Printer.png")

# IMPORTANT: per-asset scaling (sharp) - NO smoothscale
door_s = pygame.transform.scale(img_door, (96, 192))
boss_s = pygame.transform.scale(img_boss, (64, 96))

desk_s = pygame.transform.scale(img_desk, (220, 90))
boss_chair_s = pygame.transform.scale(img_boss_chair, (64, 64))
plant_s = pygame.transform.scale(img_plant, (64, 96))
cabinet_s = pygame.transform.scale(img_cabinet, (80, 120))
printer_big_s = pygame.transform.scale(img_printer_big, (96, 96))
printer_small_s = pygame.transform.scale(img_printer_small, (64, 64))

# -----------------------------
# Layout (logische posities)
# -----------------------------
DOOR_X = 40
CABINET_X = 150

DESK_X = 300
PLANT_X = 260
BOSS_CHAIR_X = 540

PRINTER_SMALL_X = 680
PRINTER_BIG_X = 760

# Player placeholder (blauwe cirkel) bij bureau
PLAYER_X = DESK_X + 150
PLAYER_Y = FLOOR_Y - 130

# Boss movement
BOSS_OFFSCREEN_X = -80
BOSS_DOOR_STAND_X = DOOR_X + door_s.get_width() + 10
BOSS_BOTTOM_Y = FLOOR_Y

# -----------------------------
# State
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

        "boss_x": BOSS_OFFSCREEN_X,
    }

state = reset()

# -----------------------------
# Main loop
# -----------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    lvl = LEVELS[state["lvl_idx"]]

    # Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not state["gameover"]:
                state["phone"] = True
            if event.key == pygame.K_r:
                state = reset()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                state["phone"] = False

    # Update
    if not state["gameover"]:
        # Score
        if state["phone"]:
            state["score"] += PHONE_POINTS_PER_SEC * lvl["mult"] * dt

        # Level up
        new_idx = level_for_score(state["score"])
        if new_idx > state["lvl_idx"]:
            state["lvl_idx"] = new_idx
            lvl = LEVELS[state["lvl_idx"]]
            state["boss_state"] = WAIT
            state["boss_timer"] = 0.0
            state["next_check_in"] = schedule_next_check(lvl)
            state["boss_x"] = BOSS_OFFSCREEN_X

        # Boss logic
        state["boss_timer"] += dt

        if state["boss_state"] == WAIT:
            state["boss_x"] = BOSS_OFFSCREEN_X
            if state["boss_timer"] >= state["next_check_in"]:
                state["boss_timer"] = 0.0
                state["boss_state"] = WALKING_IN
                state["reaction_timer"] = 0.0
                state["caught"] = False

        elif state["boss_state"] == WALKING_IN:
            t = max(0.0, min(1.0, state["boss_timer"] / lvl["walk_in"]))
            state["boss_x"] = BOSS_OFFSCREEN_X + t * (BOSS_DOOR_STAND_X - BOSS_OFFSCREEN_X)

            state["reaction_timer"] += dt
            if state["phone"] and state["reaction_timer"] > lvl["grace"]:
                state["caught"] = True
                state["gameover"] = True

            if state["boss_timer"] >= lvl["walk_in"]:
                state["boss_timer"] = 0.0
                state["boss_state"] = LOOKING

        elif state["boss_state"] == LOOKING:
            state["boss_x"] = BOSS_DOOR_STAND_X

            # als je tijdens kijken phone aanzet -> direct gepakt
            if state["phone"]:
                state["caught"] = True
                state["gameover"] = True

            if state["boss_timer"] >= lvl["look"]:
                state["boss_state"] = WAIT
                state["boss_timer"] = 0.0
                state["next_check_in"] = schedule_next_check(lvl)

    # Draw background (simple)
    screen.fill((214, 214, 220))
    pygame.draw.rect(screen, (180, 180, 186), (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y))  # floor
    pygame.draw.rect(screen, (160, 160, 166), (0, FLOOR_Y - 6, WIDTH, 6))            # baseboard

    # Draw office items (bottom aligned)
    blit_bottom(screen, door_s, DOOR_X, FLOOR_Y)
    blit_bottom(screen, cabinet_s, CABINET_X, FLOOR_Y)

    blit_bottom(screen, desk_s, DESK_X, FLOOR_Y)
    blit_bottom(screen, plant_s, PLANT_X, FLOOR_Y)
    blit_bottom(screen, boss_chair_s, BOSS_CHAIR_X, FLOOR_Y)

    blit_bottom(screen, printer_small_s, PRINTER_SMALL_X, FLOOR_Y)
    blit_bottom(screen, printer_big_s, PRINTER_BIG_X, FLOOR_Y)

    # Player (placeholder)
    pygame.draw.circle(screen, (60, 120, 220), (PLAYER_X, PLAYER_Y), 12)
    pygame.draw.circle(screen, (255, 255, 255), (PLAYER_X, PLAYER_Y), 12, 2)
    if state["phone"]:
        pygame.draw.rect(screen, (25, 25, 30), (PLAYER_X + 16, PLAYER_Y + 8, 14, 18), border_radius=3)
        pygame.draw.rect(screen, (220, 220, 230), (PLAYER_X + 19, PLAYER_Y + 11, 8, 12), border_radius=2)

    # Boss
    if state["boss_state"] in (WALKING_IN, LOOKING):
        blit_bottom_center(screen, boss_s, int(state["boss_x"]), BOSS_BOTTOM_Y)

    # UI
    score_i = int(state["score"])
    lvl = LEVELS[state["lvl_idx"]]
    screen.blit(font.render(f'{lvl["name"]} | Punten: {score_i} | x{lvl["mult"]:.2f}', True, (20, 20, 25)), (16, 12))
    screen.blit(font.render("Houd SPATIE = telefoon | R = restart", True, (70, 70, 80)), (16, 36))

    if state["boss_state"] == WALKING_IN and not state["gameover"]:
        left = max(0.0, lvl["grace"] - state["reaction_timer"])
        screen.blit(font.render(f"BAAS KOMT! Reageer binnen {left:.2f}s!", True, (200, 40, 40)), (16, 62))

    if state["gameover"]:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        screen.blit(overlay, (0, 0))
        go = big_font.render("GAME OVER", True, (255, 255, 255))
        screen.blit(go, (WIDTH // 2 - go.get_width() // 2, HEIGHT // 2 - 90))
        reason = "Je werd betrapt!" if state["caught"] else "Game over!"
        info = font.render(f"{reason} Score: {score_i} | Druk op R", True, (255, 255, 255))
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 - 20))

    pygame.display.flip()

pygame.quit()
