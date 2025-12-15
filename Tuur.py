import pygame
import math
import random

WIDTH, HEIGHT = 960, 540
BG_COLOR = (32, 36, 48)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 20)

# --- Scene base ---
class Scene:
    def handle_event(self, e): pass
    def update(self, dt): pass
    def draw(self, s): pass

class SceneManager:
    def __init__(self, start_scene):
        self.scene = start_scene
    def switch(self, scene):
        self.scene = scene

# --- Entities ---
class Player:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.phone_up = False
    def toggle_phone(self):
        self.phone_up = not self.phone_up
    def draw(self, s):
        pygame.draw.rect(s, (70, 70, 90), (self.pos.x-120, self.pos.y, 240, 30))
        color = (80, 180, 120) if not self.phone_up else (220, 160, 60)
        pygame.draw.circle(s, color, (int(self.pos.x), int(self.pos.y-20)), 20)
        if self.phone_up:
            pygame.draw.rect(s, (20, 20, 20), (self.pos.x+25, self.pos.y-40, 16, 28))

class Boss:
    def __init__(self, path_points):
        self.path = [pygame.Vector2(p) for p in path_points]
        self.idx = 0
        self.pos = self.path[0].copy()
        self.speed = 90
        self.facing = pygame.Vector2(1, 0)
        self.wait_timer = 0.0
        self.look_cone_deg = 45
        self.look_range = 280

    def update(self, dt):
        if self.wait_timer > 0:
            self.wait_timer -= dt
            angle = math.sin(pygame.time.get_ticks()*0.002)*0.6
            self.facing = pygame.Vector2(1, 0).rotate_rad(angle)
            return
        target = self.path[self.idx]
        to = target - self.pos
        d = to.length()
        if d < 4:
            self.idx = (self.idx + 1) % len(self.path)
            self.wait_timer = random.uniform(0.6, 1.6)
        else:
            self.facing = to.normalize()
            self.pos += self.facing * self.speed * dt

    def sees(self, player):
        to_player = player.pos - self.pos
        dist = to_player.length()
        if dist > self.look_range: return False
        if dist == 0: return True
        dir_dot = self.facing.normalize().dot(to_player.normalize())
        angle = math.degrees(math.acos(max(-1, min(1, dir_dot))))
        return angle <= self.look_cone_deg

    def draw(self, s):
        pygame.draw.circle(s, (200, 80, 80), (int(self.pos.x), int(self.pos.y)), 18)
        base = self.facing.angle_to(pygame.Vector2(1,0))
        for a in (-self.look_cone_deg, self.look_cone_deg):
            ray = pygame.Vector2(1,0).rotate(base + a) * self.look_range
            pygame.draw.line(s, (160, 60, 60), self.pos, self.pos + ray, 1)

# --- Minigames ---
class ReactionTap:
    def __init__(self):
        self.active = False
        self.timer = 0.0
        self.prompt_time = 0
        self.prompt_on = False
        self.done = False
        self.success = False

    def start(self):
        self.active = True
        self.timer = 0.0
        self.prompt_time = random.uniform(0.6, 2.0)
        self.prompt_on = False
        self.done = False
        self.success = False

    def handle_event(self, e):
        if not self.active or self.done: return
        if self.prompt_on and e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self.done = True
            self.success = True
        elif e.type == pygame.KEYDOWN:
            self.done = True
            self.success = False

    def update(self, dt):
        if not self.active or self.done: return
        self.timer += dt
        if not self.prompt_on and self.timer >= self.prompt_time:
            self.prompt_on = True

    def draw(self, s):
        if not self.active: return
        msg = "Wacht..." if not self.prompt_on else "DRUK ENTER NU!"
        text = font.render(msg, True, (240, 240, 240))
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))

class MathQuick:
    def __init__(self):
        self.active = False
        self.done = False
        self.success = False
        self.question = ""
        self.answer = 0
        self.input_text = ""

    def start(self):
        a, b = random.randint(1,9), random.randint(1,9)
        self.question = f"{a} + {b} = ?"
        self.answer = a+b
        self.input_text = ""
        self.active = True
        self.done = False
        self.success = False

    def handle_event(self, e):
        if not self.active or self.done: return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN:
                try:
                    if int(self.input_text) == self.answer:
                        self.success = True
                    else:
                        self.success = False
                except:
                    self.success = False
                self.done = True
            elif e.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if e.unicode.isdigit():
                    self.input_text += e.unicode

    def update(self, dt): pass

    def draw(self, s):
        if not self.active: return
        q = font.render(self.question, True, (240,240,240))
        s.blit(q, (WIDTH//2 - q.get_width()//2, HEIGHT//2 - 20))
        inp = font.render(self.input_text, True, (200,200,200))
        s.blit(inp, (WIDTH//2 - inp.get_width()//2, HEIGHT//2 + 20))

# --- Game Scene ---
class GameScene(Scene):
    def __init__(self, manager):
        self.mgr = manager
        self.player = Player(WIDTH//2, HEIGHT//2 + 60)
        self.boss = Boss([(180, 140), (780, 140), (780, 420), (180, 420)])
        self.suspicion = 0.0
        self.score = 0
        self.combo = 1.0
        self.current_minigame = None
        self.warning_flash = 0.0

    def start_random_minigame(self):
        choice = random.choice([ReactionTap(), MathQuick()])
        choice.start()
        self.current_minigame = choice

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_SPACE, pygame.K_t):
                self.player.toggle_phone()
                if self.player.phone_up:
                    self.start_random_minigame()
                else:
                    self.current_minigame = None
        if self.current_minigame:
            self.current_minigame.handle_event(e)

    def update(self, dt):
        self.boss.update(dt)
        seen = self.boss.sees(self.player)
        if self.player.phone_up and seen:
            self.suspicion += 40 * dt
            self.warning_flash = 0.3
        elif self.player.phone_up:
            self.suspicion += 10 * dt
        else:
            self.suspicion -= 20 * dt
        self.suspicion = max(0.0, min(100.0, self.suspicion))

        if self.current_minigame and self.player.phone_up:
            self.current_minigame.update(dt)
            if self.current_minigame.done:
                if self.current_minigame.success:
                    gained = int(50 * self.combo)
                    self.score += gained
                    self.combo = min(5.0, self.combo + 0.25)
                else:
                    self.combo = 1.0
                self.current_minigame = None

        self.warning_flash = max(0.0, self.warning_flash - dt)
        if self.suspicion >= 100.0:
            self.mgr.switch(GameOverScene(self.mgr, self.score))

    def draw(self, s):
        s.fill(BG_COLOR)
        pygame.draw.rect(s, (50, 50, 70), (80, 100, WIDTH-160, HEIGHT))
                # continue draw in GameScene
        pygame.draw.rect(s, (50, 50, 70), (80, 100, WIDTH-160, HEIGHT-160), 4)

        self.player.draw(s)
        self.boss.draw(s)
        if self.current_minigame:
            self.current_minigame.draw(s)

        # UI
        self._draw_ui(s)

    def _draw_ui(self, s):
        bar_w, bar_h = 240, 16
        x, y = 20, 20
        pygame.draw.rect(s, (80, 80, 80), (x, y, bar_w, bar_h))
        fill = int(bar_w * (self.suspicion / 100.0))
        color = (80+int(175*(self.suspicion/100.0)), 140-int(80*(self.suspicion/100.0)), 60)
        pygame.draw.rect(s, color, (x, y, fill, bar_h))

        s.blit(font.render(f"Score: {self.score}", True, (230,230,230)), (x, y+24))
        s.blit(font.render(f"Combo: x{self.combo:.2f}", True, (230,230,230)), (x, y+44))

        phone_text = "Telefoon: OMHOOG (gevaar!)" if self.player.phone_up else "Telefoon: OMLAAG (veilig)"
        s.blit(font.render(phone_text, True, (230,230,230)), (x, y+68))

        if self.warning_flash > 0:
            alpha = int(120 * self.warning_flash)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 80, 80, alpha))
            s.blit(overlay, (0,0))

# --- Menu Scene ---
class MenuScene(Scene):
    def __init__(self, manager):
        self.mgr = manager
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self.mgr.switch(GameScene(self.mgr))
    def update(self, dt): pass
    def draw(self, s):
        s.fill((20, 24, 32))
        title = pygame.font.SysFont("arial", 36).render("Stiekem Op Je Telefoon", True, (240,240,240))
        s.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 60))
        msg = font.render("Druk ENTER om te starten", True, (200,200,200))
        s.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))

# --- Game Over Scene ---
class GameOverScene(Scene):
    def __init__(self, manager, score):
        self.mgr = manager
        self.score = score
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self.mgr.switch(MenuScene(self.mgr))
    def update(self, dt): pass
    def draw(self, s):
        s.fill((18, 18, 26))
        t = pygame.font.SysFont("arial", 32).render("Betrapped! Game Over", True, (240,240,240))
        s.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 60))
        sc = font.render(f"Score: {self.score}", True, (220,220,220))
        s.blit(sc, (WIDTH//2 - sc.get_width()//2, HEIGHT//2))
        msg = font.render("ENTER: Terug naar menu", True, (200,200,200))
        s.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 + 30))

# --- Main loop ---
def main():
    mgr = SceneManager(MenuScene(None))
    mgr.scene.mgr = mgr
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            else:
                mgr.scene.handle_event(e)
        mgr.scene.update(dt)
        mgr.scene.draw(screen)
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()