import pygame
import random
import math
import sys

pygame.init()

# ======================
# CONFIG
# ======================
WIDTH, HEIGHT = 900, 500
FPS = 60

WHITE = (240, 240, 240)
BLACK = (20, 20, 30)
RED = (220, 60, 60)
GREEN = (60, 220, 120)
YELLOW = (240, 220, 70)
BLUE = (80, 140, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Don't Get Caught")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 26)
big_font = pygame.font.SysFont(None, 42)

# ======================
# PLAYER
# ======================
player_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
phone_up = False

# ======================
# BOSS
# ======================
boss_pos = pygame.Vector2(150, 150)
boss_angle = 0
boss_speed = 70
look_cone_deg = 60
look_distance = 260
turn_timer = 0

# ======================
# GAME STATE
# ======================
score = 0
multiplier = 1
suspicion = 0.0
game_over = False
current_minigame = None

# ======================
# HELPERS
# ======================
def draw_text(text, x, y, color=WHITE, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    rect.center = (x, y) if center else rect.move(x, y).topleft
    screen.blit(surf, rect)

def angle_to_vector(angle):
    rad = math.radians(angle)
    return pygame.Vector2(math.cos(rad), math.sin(rad))

def boss_can_see_player():
    to_player = player_pos - boss_pos
    dist = to_player.length()
    if dist > look_distance:
        return False
    forward = angle_to_vector(boss_angle)
    return abs(forward.angle_to(to_player)) < look_cone_deg / 2

# ======================
# MINIGAMES
# ======================
class ReactionTap:
    def __init__(self):
        self.wait = random.uniform(0.8, 2.0)
        self.timer = 0
        self.active = False
        self.time_limit = 1.0
        self.done = False
        self.success = False

    def handle_event(self, event):
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.success = True
                self.done = True

    def update(self, dt):
        self.timer += dt
        if not self.active and self.timer >= self.wait:
            self.active = True
            self.timer = 0
        elif self.active and self.timer > self.time_limit:
            self.done = True

    def draw(self):
        draw_text("REACTION TAP", WIDTH//2, 170, center=True)
        if self.active:
            draw_text("PRESS ENTER!", WIDTH//2, 240, GREEN, True)
            draw_text(f"{self.time_limit - self.timer:.1f}", WIDTH//2, 270, RED, True)
        else:
            draw_text("WAIT...", WIDTH//2, 240, WHITE, True)

class SwipePattern:
    def __init__(self):
        self.pattern = random.choices(
            [pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN], k=4
        )
        self.index = 0
        self.timer = 5
        self.done = False
        self.success = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == self.pattern[self.index]:
                self.index += 1
                if self.index == len(self.pattern):
                    self.success = True
                    self.done = True
            else:
                self.done = True

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.done = True

    def draw(self):
        arrows = {pygame.K_LEFT:"←", pygame.K_UP:"↑", pygame.K_RIGHT:"→", pygame.K_DOWN:"↓"}
        text = " ".join(arrows[k] for k in self.pattern)
        draw_text("SWIPE PATTERN", WIDTH//2, 170, center=True)
        draw_text(text, WIDTH//2, 220, center=True)
        draw_text(f"Time: {self.timer:.1f}", WIDTH//2, 260, RED, True)

class MathQuick:
    def __init__(self):
        self.a = random.randint(1, 9)
        self.b = random.randint(1, 9)
        self.answer = self.a + self.b
        self.input = ""
        self.timer = 5
        self.done = False
        self.success = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.unicode.isdigit():
                self.input += event.unicode
            elif event.key == pygame.K_RETURN:
                if self.input.isdigit() and int(self.input) == self.answer:
                    self.success = True
                self.done = True

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.done = True

    def draw(self):
        draw_text("MATH QUICK", WIDTH//2, 170, center=True)
        draw_text(f"{self.a} + {self.b} = ?", WIDTH//2, 220, center=True)
        draw_text(self.input, WIDTH//2, 250, GREEN, True)
        draw_text(f"Time: {self.timer:.1f}", WIDTH//2, 280, RED, True)

def random_minigame():
    return random.choice([ReactionTap, SwipePattern, MathQuick])()

# ======================
# GAME LOOP
# ======================
running = True
while running:
    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                phone_up = not phone_up
                if phone_up:
                    current_minigame = random_minigame()
                else:
                    current_minigame = None

        if current_minigame:
            current_minigame.handle_event(event)

    if game_over:
        screen.fill(BLACK)
        draw_text("GAME OVER", WIDTH//2, HEIGHT//2-20, RED, True)
        draw_text(f"Score: {score}", WIDTH//2, HEIGHT//2+20, True)
        pygame.display.flip()
        continue

    # ======================
    # BOSS
    # ======================
    turn_timer -= dt
    if turn_timer <= 0:
        boss_angle = random.randint(0, 360)
        turn_timer = random.uniform(1.5, 3)

    boss_pos += angle_to_vector(boss_angle) * boss_speed * dt
    boss_pos.x = max(50, min(WIDTH-50, boss_pos.x))
    boss_pos.y = max(50, min(HEIGHT-50, boss_pos.y))

    # ======================
    # SUSPICION
    # ======================
    seen = boss_can_see_player()
    if phone_up:
        suspicion += (70 if seen else 20) * dt
    else:
        suspicion -= 40 * dt

    suspicion = max(0, min(100, suspicion))
    if suspicion >= 100:
        game_over = True

    # ======================
    # MINIGAME UPDATE
    # ======================
    if current_minigame:
        current_minigame.update(dt)
        if current_minigame.done:
            if current_minigame.success:
                score += 100 * multiplier
                multiplier += 1
            else:
                suspicion += 20
                multiplier = 1
            phone_up = False
            current_minigame = None

    # ======================
    # DRAW
    # ======================
    screen.fill(BLACK)

    pygame.draw.circle(screen, RED, boss_pos, 25)
    pygame.draw.circle(screen, BLUE, player_pos, 20)

    pygame.draw.rect(screen, WHITE, (20, 20, 200, 20), 2)
    pygame.draw.rect(screen, RED, (20, 20, 2*suspicion, 20))

    draw_text(f"Score: {score}", 20, 50)
    draw_text(f"Multiplier: x{multiplier}", 20, 75)

    if seen and phone_up:
        draw_text("BAAS KIJKT!", WIDTH//2, 30, RED, True)

    if current_minigame:
        pygame.draw.rect(screen, (10,10,10), (280,140,340,200))
        pygame.draw.rect(screen, WHITE, (280,140,340,200), 2)
        current_minigame.draw()

    pygame.display.flip()

pygame.quit()
sys.exit()
