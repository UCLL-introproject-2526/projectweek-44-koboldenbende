# audio.py
# Laadt alle geluiden + veilige fallback.

# safe_sound() voorkomt crash als een mp3/wav ontbreekt

# load_sounds() geeft een dict met sounds terug

# stop_all_loop_sounds() stopt loopende sounds bij scene switch
import os
import pygame
from config import ASSETS_DIR

def safe_sound(path, volume=None):
    try:
        s = pygame.mixer.Sound(path)
        if volume is not None:
            s.set_volume(volume)
        return s
    except Exception:
        return pygame.mixer.Sound(b"\x00\x00\x00\x00")

def load_sounds():
    return {
        "boss_walk": safe_sound(os.path.join(ASSETS_DIR, "loud-footsteps-62038-VEED.mp3")),
        "typing": safe_sound(os.path.join(ASSETS_DIR, "typing-keyboard-asmr-356116.mp3")),
        "phone_use": safe_sound(os.path.join(ASSETS_DIR, "Mathias Vandenboer_s Video - Dec 16, 2025-VEED.mp3.mp3")),
        "boss_chatter": safe_sound(os.path.join(ASSETS_DIR, "angry-boss-chatter.mp3"), volume=0.8),
        "boss3_chatter": safe_sound(os.path.join(ASSETS_DIR, "gibberish-1-96231"), volume=0.8),
        "game_over": safe_sound(os.path.join(ASSETS_DIR, "game_over.wav")),
        "complete": safe_sound(os.path.join(ASSETS_DIR, "level_complete.wav")),
        "buy": safe_sound(os.path.join(ASSETS_DIR, "purchase-success-384963.mp3")),
        "menu_click": safe_sound(os.path.join(ASSETS_DIR, "menu_click.wav")),
    }

def stop_all_loop_sounds(snd):
    snd["boss_walk"].stop()
    snd["typing"].stop()
    snd["phone_use"].stop()
    snd["boss_chatter"].stop()
