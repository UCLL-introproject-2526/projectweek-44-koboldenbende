# Reactiegame in Python met startscherm en highscore
# Je scoort alleen punten als je op je gsm zit (SPACE ingedrukt)
# Als de baas komt, moet je sneller reageren

import pygame
import random
import sys
import os

pygame.init()

# Scherm
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kantoor GSM Game")

# Kleuren
WHITE = (255, 255, 255)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
BLACK = (0, 0, 0)
BLUE = (50, 50, 200)

# Font
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 56)

clock = pygame.time.Clock()

# Highscore bestand
HIGHSCORE_FILE = "highscore.txt"
if os.path.exists(HIGHSCORE_FILE):
    with open(HIGHSCORE_FILE, "r") as f:
        highscore = int(f.read())
else:
    highscore = 0

# Game-variabelen
using_phone = False
boss_here = False
boss_timer = random.randint(120, 300)
reaction_time = 20  # sneller reageren
reaction_counter = 0
score = 0

def start_screen():
    while True:
        screen.fill(WHITE)
        title = big_font.render("KANTOOR GSM GAME", True, BLACK)
        start_text = font.render("Druk ENTER om te starten", True, BLUE)
        hs_text = font.render(f"Highscore: {highscore}", True, BLACK)

        screen.blit(title, (120, 100))
        screen.blit(start_text, (160, 200))
        screen.blit(hs_text, (220, 250))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return

# Startscherm tonen
start_screen()

running = True
while running:
    clock.tick(60)
    screen.fill(WHITE)

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                using_phone = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                using_phone = False

    # Boss logic
    boss_timer -= 1
    if boss_timer <= 0 and not boss_here:
        boss_here = True
        reaction_counter = reaction_time

    if boss_here:
        screen.fill(RED)
        reaction_counter -= 1

        if using_phone and reaction_counter <= 0:
            # Game over
            if score > highscore:
                with open(HIGHSCORE_FILE, "w") as f:
                    f.write(str(score))
            text = big_font.render("BETRAPT!", True, BLACK)
            screen.blit(text, (200, 170))
            pygame.display.flip()
            pygame.time.wait(2000)
            running = False

        if not using_phone:
            boss_here = False
            boss_timer = random.randint(120, 300)

    else:
        screen.fill(GREEN)
        # Score alleen verhogen als je op gsm zit
        if using_phone:
            score += 1

    # Tekst
    status = "Op je gsm (SPACE)" if using_phone else "Werken..."
    status_text = font.render(status, True, BLACK)
    score_text = font.render(f"Score: {score}", True, BLACK)

    screen.blit(status_text, (20, 20))
    screen.blit(score_text, (20, 60))

    pygame.display.flip()

pygame.quit()
sys.exit()

