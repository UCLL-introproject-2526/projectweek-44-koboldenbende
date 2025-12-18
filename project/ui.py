# ui.py`
# UI-tekenfuncties (knoppen en sterren).

# menu_button() (main menu stijl)

# button() en ui_button() (level select / shop stijl)

# tab_button() (shop tabs)

# draw_star_row() tekent de 3 sterren
import pygame
from config import BUTTON_BG_COLOR, BUTTON_TEXT_COLOR, COL_BTN_BG, COL_BORDER, COL_TEXT

def draw_star_row(screen, x, y, n, size=18, gap=8):
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

def button(screen, font, rect, text, enabled=True):
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

def ui_button(screen, font, rect, text, enabled=True):
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

def menu_button(screen, font, rect, text, enabled=True):
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

def tab_button(screen, font, rect, text, active, COL_BORDER, COL_TEXT):
    bg = (255, 245, 210) if active else (255, 255, 255)
    pygame.draw.rect(screen, bg, rect, border_radius=14)
    pygame.draw.rect(screen, COL_BORDER, rect, 3, border_radius=14)
    t = font.render(text, True, COL_TEXT)
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    return rect.collidepoint(pygame.mouse.get_pos())
