# utils.py
# Kleine herbruikbare helper-functies.

# load_image() laadt assets uit de assets-map

# scale() schaalt surfaces

# draw_text(), clamp(), blit_fit_center() (voor thumbnails in shop)

import os
import pygame
from config import ASSETS_DIR

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
