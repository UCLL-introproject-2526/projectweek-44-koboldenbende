import random
import pygame

# ======================================================
# Base helper
# ======================================================

def clamp(v, a, b):
    return max(a, min(b, v))


# ======================================================
# MINIGAME 1 — REACTION TAP
# ======================================================

class ReactionTap:
    def __init__(self):
        self.wait_time = random.uniform(0.6, 2.2)
        self.timer = 0.0
        self.state = "WAIT"  # WAIT -> GO
        self.done = False

    def update(self, dt, keys):
        if self.done:
            return "PLAYING"

        self.timer += dt

        if self.state == "WAIT":
            if keys[pygame.K_SPACE]:
                return "LOSE"  # too early
            if self.timer >= self.wait_time:
                self.state = "GO"
                self.timer = 0

        elif self.state == "GO":
            if keys[pygame.K_SPACE]:
                self.done = True
                return "WIN"
            if self.timer > 0.35:
                return "LOSE"

        return "PLAYING"

    def draw(self, surf, rect):
        if self.state == "WAIT":
            pygame.draw.rect(surf, (200, 60, 60), rect, border_radius=8)
        else:
            pygame.draw.rect(surf, (60, 200, 100), rect, border_radius=8)


# ======================================================
# MINIGAME 2 — MATCH THE BAR
# ======================================================

class MatchBar:
    def __init__(self):
        self.x = 0.0
        self.dir = 1
        self.speed = 1.3
        self.done = False

    def update(self, dt, keys):
        if self.done:
            return "PLAYING"

        self.x += self.dir * self.speed * dt
        if self.x <= 0 or self.x >= 1:
            self.dir *= -1

        if keys[pygame.K_SPACE]:
            self.done = True
            if 0.42 <= self.x <= 0.58:
                return "WIN"
            return "LOSE"

        return "PLAYING"

    def draw(self, surf, rect):
        # target zone
        tz = pygame.Rect(
            rect.x + rect.w * 0.42,
            rect.y + rect.h * 0.15,
            rect.w * 0.16,
            rect.h * 0.7,
        )
        pygame.draw.rect(surf, (80, 160, 220), tz)

        # moving bar
        bx = rect.x + rect.w * self.x
        bar = pygame.Rect(bx - 6, rect.y + 8, 12, rect.h - 16)
        pygame.draw.rect(surf, (230, 230, 230), bar)


# ======================================================
# MINIGAME 3 — SPAM CLICK
# ======================================================

class SpamClick:
    def __init__(self):
        self.power = 0.0
        self.timer = 0.0

    def update(self, dt, keys):
        self.timer += dt

        if keys[pygame.K_SPACE]:
            self.power += 120 * dt
        else:
            self.power -= 60 * dt

        self.power = clamp(self.power, 0, 100)

        if self.power >= 100:
            return "WIN"
        if self.timer >= 2.2:
            return "LOSE"

        return "PLAYING"

    def draw(self, surf, rect):
        bg = pygame.Rect(rect.x + 20, rect.centery - 8, rect.w - 40, 16)
        fill = pygame.Rect(bg.x, bg.y, bg.w * (self.power / 100), bg.h)

        pygame.draw.rect(surf, (40, 40, 40), bg)
        pygame.draw.rect(surf, (80, 220, 120), fill)


# ======================================================
# FACTORY
# ======================================================

def create_random_game():
    return random.choice([
        ReactionTap(),
        MatchBar(),
        SpamClick()
    ])
