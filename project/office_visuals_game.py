import os
import random
import pygame
from minigames import create_random_game


# -----------------------------
# Config
# -----------------------------
WIDTH, HEIGHT = 960, 420
FPS = 60

PHONE_POINTS_PER_SEC = 18

# Level difficulty
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

def schedule_next_check(lvl):
    return random.uniform(lvl["min_wait"], lvl["max_wait"])

def level_for_score(score: float) -> int:
    return min(len(LEVELS) - 1, int(score // LEVEL_UP_SCORE_STEP))

def scale(img, w, h):
    # pixel-sharp (geen smoothscale)
    return pygame.transform.scale(img, (w, h))

# -----------------------------
# Init
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Office Reaction Game (First Person)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 26)
big_font = pygame.font.SysFont(None, 70)

# Load your assets
img_desk = load_image("Desk.png")
img_door = load_image("pixel_door.png")
img_boss = load_image("boss.png")
img_plant = load_image("Big-Plant.png")
img_cabinet = load_image("Big-Filing-Cabinet.png")
img_printer_big = load_image("Big-Office-Printer.png")

# -----------------------------
# First-person scene layout
# -----------------------------
# Background "horizon" where wall meets desk
HORIZON_Y = 170

# Door is far away (small)
DOOR_POS = (45, 40)
DOOR_SIZE = (90, 170)

# Props in background (medium-small)
PLANT_POS = (210, 95)
PLANT_SIZE = (70, 105)

CABINET_POS = (120, 60)
CABINET_SIZE = (90, 135)

PRINTER_POS = (740, 70)
PRINTER_SIZE = (140, 150)

# Desk is close to camera (big), at bottom
DESK_POS = (0, 230)
DESK_SIZE = (WIDTH, 210)

# Laptop overlay (we draw it ourselves so you don't need a laptop.png)
LAPTOP_RECT = pygame.Rect(WIDTH//2 - 150, 235, 300, 140)   # screen
KEYBOARD_RECT = pygame.Rect(WIDTH//2 - 190, 380, 380, 35)  # keyboard

# Boss movement: from door (far) to near center
BOSS_START = (DOOR_POS[0] + DOOR_SIZE[0]//2, DOOR_POS[1] + DOOR_SIZE[1] - 10)
BOSS_END = (WIDTH//2, 250)  # comes forward behind laptop

# Boss size grows with distance (first-person effect)
BOSS_FAR = (28, 42)
BOSS_NEAR = (120, 180)

# Pre-scale static items
door_s = scale(img_door, *DOOR_SIZE)
plant_s = scale(img_plant, *PLANT_SIZE)
cabinet_s = scale(img_cabinet, *CABINET_SIZE)
printer_s = scale(img_printer_big, *PRINTER_SIZE)
desk_s = scale(img_desk, *DESK_SIZE)

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

        # 📱 phone minigame
        "phone_game": create_random_game(),
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
        if state["phone"]:
            result = state["phone_game"].update(dt, pygame.key.get_pressed())

            if result == "WIN":
                state["score"] += 30 * lvl["mult"]
                state["phone_game"] = create_random_game()

            elif result == "LOSE":
                state["caught"] = True
                state["gameover"] = True


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
                state["phone_game"] = create_random_game()
                state["reaction_timer"] = 0.0
                state["caught"] = False

        elif state["boss_state"] == WALKING_IN:
            state["reaction_timer"] += dt
            if state["phone"] and state["reaction_timer"] > lvl["grace"]:
                state["caught"] = True
                state["gameover"] = True

            if state["boss_timer"] >= lvl["walk_in"]:
                state["boss_timer"] = 0.0
                state["boss_state"] = LOOKING

        elif state["boss_state"] == LOOKING:
            # While boss is close/looking: if you go phone -> instant caught
            if state["phone"]:
                state["caught"] = True
                state["gameover"] = True

            if state["boss_timer"] >= lvl["look"]:
                state["boss_state"] = WAIT
                state["boss_timer"] = 0.0
                state["next_check_in"] = schedule_next_check(lvl)

    # -----------------------------
    # Draw (first-person)
    # -----------------------------
    # wall
    screen.fill((216, 216, 222))
    # subtle wall lines
    for x in range(0, WIDTH, 90):
        pygame.draw.line(screen, (206, 206, 212), (x, 0), (x, HEIGHT), 1)

    # horizon shadow
    pygame.draw.rect(screen, (200, 200, 206), (0, HORIZON_Y, WIDTH, 8))

    # Background objects (far)
    screen.blit(door_s, DOOR_POS)
    screen.blit(cabinet_s, CABINET_POS)
    screen.blit(plant_s, PLANT_POS)
    screen.blit(printer_s, PRINTER_POS)

    # Boss (behind laptop, walks in)
    if state["boss_state"] in (WALKING_IN, LOOKING):
        # progress based on boss_state timer
        if state["boss_state"] == WALKING_IN:
            t = max(0.0, min(1.0, state["boss_timer"] / lvl["walk_in"]))
        else:
            t = 1.0

        bx = int(BOSS_START[0] + (BOSS_END[0] - BOSS_START[0]) * t)
        by = int(BOSS_START[1] + (BOSS_END[1] - BOSS_START[1]) * t)

        bw = int(BOSS_FAR[0] + (BOSS_NEAR[0] - BOSS_FAR[0]) * t)
        bh = int(BOSS_FAR[1] + (BOSS_NEAR[1] - BOSS_FAR[1]) * t)

        boss_scaled = scale(img_boss, bw, bh)
        boss_rect = boss_scaled.get_rect(center=(bx, by))
        screen.blit(boss_scaled, boss_rect)

    # Desk foreground (near)
    screen.blit(desk_s, DESK_POS)

    # Laptop foreground (drawn)
    pygame.draw.rect(screen, (35, 35, 40), LAPTOP_RECT, border_radius=10)
    pygame.draw.rect(screen, (220, 220, 230), LAPTOP_RECT.inflate(-12, -12), border_radius=8)

    pygame.draw.rect(screen, (25, 25, 30), KEYBOARD_RECT, border_radius=10)

# Phone minigame on laptop screen
if state["phone"] and not state["gameover"]:
    inner = LAPTOP_RECT.inflate(-30, -30)
    pygame.draw.rect(screen, (20, 20, 25), inner, border_radius=10)

    state["phone_game"].draw(screen, inner)

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
