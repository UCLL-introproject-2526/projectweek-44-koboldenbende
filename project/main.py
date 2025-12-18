# main.py

#De “launcher” van de game.
#Start pygame + fullscreen window
#Maakt de Game class (bevat alle globale game-data)
#Doet de main loop: events lezen → update_play() → draw_scene() → flip()
#Regelt ook scene-change sounds (typing/complete/gameover)


import pygame
import random

from config import (
    FPS, GRID_COLS, GRID_ROWS, TOTAL_LEVELS,
    DESK_Y_OFFSET, HANDS_Y_OFFSET,
    COL_BORDER, COL_TEXT, COL_PANEL_BG, COL_CARD_BG, COL_MUTED,
)
from constants import (
    SCENE_MAIN_MENU, SCENE_LEVEL_SELECT, SCENE_PLAY, SCENE_COMPLETE, SCENE_GAMEOVER, SCENE_SHOP
)
from utils import scale
from save_system import load_save
from assets import load_images
from audio import load_sounds, stop_all_loop_sounds
from ui import draw_star_row, button, ui_button, menu_button, tab_button
from shop import build_shop_thumbs, reload_laptop_asset, reload_phone_asset
from state import make_initial_play_state
from scenes import update_play, draw_scene  # + start_level zit in scenes.py

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        info = pygame.display.Info()
        self.WIDTH, self.HEIGHT = info.current_w, info.current_h

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption("Office Game - Main Menu + Shop")
        self.clock = pygame.time.Clock()

        self.img = load_images()
        self.snd = load_sounds()

        self.save = load_save()

        self.scene = SCENE_MAIN_MENU
        self.current_scene = None
        self.running = True

        self.selected_level = 1
        self.last_run_score = 0
        self.last_run_level = 1
        self.last_run_stars = 0

        self.shop_selected_id = None
        self.shop_tab = "phone"
        self.popup_text = ""
        self.popup_timer = 0.0

        self.play = make_initial_play_state()

        self._setup_fonts()

        self.mode = "level"   # of MODE_LEVEL


        # Layout container
        self.layout = {
            "background_s": None,
            "main_menu_bg": None,
            "caught_bg": None,
            "level_select_bg": None,

            "desk_s": None,
            "desk_h": 0,
            "desk_scale": 1.0,
            "DESK_POS": (0, 0),

            "TILE_W": 140,
            "TILE_H": 110,
            "GRID_TOP": 140,
            "GRID_LEFT": 0,

            "LAPTOP_SIZE": (520, 260),
            "LAPTOP_POS": (0, 0),

            "PHONE_SIZE": (300, 300),
            "PHONE_POS": (0, 0),

            "hands_0_s": None,
            "hands_1_s": None,
            "smoking_hand_s": None,

            "img_phone_skin": None,
            "phone_skin_s": None,

            "BOSS_FAR": (190, 285),
            "BOSS_NEAR": (190, 285),
            "BOSS_END_Y": 0,
            "BOSS_START_Y": 0,

            "THUMB_W": 180,
            "THUMB_H": 95,

            "laptop_nohands_s": None,
        }

        self.recalc_layout()

        # Thumbs
        self.shop_thumbs = build_shop_thumbs(self.layout["THUMB_W"], self.layout["THUMB_H"])

        # Equipped assets
        reload_laptop_asset(self.save, self.layout, self.img)
        reload_phone_asset(self.save, self.layout, self.img)

        # UI function shortcuts
        self.draw_star_row = lambda x,y,n,size=18,gap=8: draw_star_row(self.screen, x, y, n, size, gap)
        self.button = lambda rect, text, enabled=True: button(self.screen, self.font, rect, text, enabled)
        self.ui_button = lambda rect, text, enabled=True: ui_button(self.screen, self.font, rect, text, enabled)
        self.menu_button = lambda rect, text, enabled=True: menu_button(self.screen, self.font, rect, text, enabled)
        self.tab_button = lambda rect, text, active: tab_button(self.screen, self.font, rect, text, active, COL_BORDER, COL_TEXT)

    def _setup_fonts(self):
        sy = self.HEIGHT / 540
        self.font = pygame.font.SysFont(None, max(18, int(28 * sy)))
        self.small = pygame.font.SysFont(None, max(14, int(22 * sy)))
        self.big = pygame.font.SysFont(None, max(34, int(72 * sy)))
        self.title_font = pygame.font.SysFont(None, max(40, int(86 * sy)))

    def set_popup(self, text, duration):
        self.popup_text = text
        self.popup_timer = duration

    def stop_all_loop_sounds(self):
        stop_all_loop_sounds(self.snd)

    def recalc_layout(self):
        sx = self.WIDTH / 960
        sy = self.HEIGHT / 540

        self.layout["background_s"] = scale(self.img["background"], self.WIDTH, self.HEIGHT)

        if self.img["HAS_MENU_BG"] and self.img["main_menu_bg"] is not None:
            self.layout["main_menu_bg"] = scale(self.img["main_menu_bg"], self.WIDTH, self.HEIGHT)
        if self.img["HAS_CAUGHT_BG"] and self.img["caught_bg"] is not None:
            self.layout["caught_bg"] = scale(self.img["caught_bg"], self.WIDTH, self.HEIGHT)
        if self.img["HAS_LEVEL_SELECT_BG"] and self.img["level_select_bg"] is not None:
            self.layout["level_select_bg"] = scale(self.img["level_select_bg"], self.WIDTH, self.HEIGHT)

        self.layout["TILE_W"] = int(140 * sx)
        self.layout["TILE_H"] = int(110 * sy)
        self.layout["GRID_TOP"] = int(140 * sy)
        self.layout["GRID_LEFT"] = (self.WIDTH - GRID_COLS * self.layout["TILE_W"]) // 2

        desk_scale = self.WIDTH / self.img["desk"].get_width()
        desk_h = int(self.img["desk"].get_height() * desk_scale - 120 * sy)
        self.layout["desk_scale"] = desk_scale
        self.layout["desk_h"] = desk_h
        self.layout["desk_s"] = pygame.transform.smoothscale(self.img["desk"], (self.WIDTH, desk_h))
        self.layout["DESK_POS"] = (0, self.HEIGHT - desk_h + int(DESK_Y_OFFSET * sy))

        laptop_w = int(self.WIDTH * 0.54)
        laptop_h = int(laptop_w * (260 / 520))
        self.layout["LAPTOP_SIZE"] = (laptop_w, laptop_h)
        self.layout["LAPTOP_POS"] = (self.WIDTH // 2 - laptop_w // 2, self.HEIGHT - laptop_h - int(22 * sy))

        phone_w = int(laptop_w * (300 / 520))
        phone_h = phone_w
        self.layout["PHONE_SIZE"] = (phone_w, phone_h)
        self.layout["PHONE_POS"] = (
            self.WIDTH // 2 - phone_w // 2,
            self.layout["LAPTOP_POS"][1] + (laptop_h // 2 - phone_h // 2) + int(6 * sy)
        )

        self.layout["hands_0_s"] = scale(self.img["hands_0"], *self.layout["LAPTOP_SIZE"])
        self.layout["hands_1_s"] = scale(self.img["hands_1"], *self.layout["LAPTOP_SIZE"])
        self.layout["smoking_hand_s"] = scale(self.img["smoking_hand"], *self.layout["LAPTOP_SIZE"])

        self.layout["BOSS_FAR"] = (int(190 * sx), int(285 * sy))
        self.layout["BOSS_NEAR"] = (int(190 * sx), int(285 * sy))
        self.layout["BOSS_END_Y"] = self.layout["LAPTOP_POS"][1] + int(12 * sy)
        self.layout["BOSS_START_Y"] = self.layout["BOSS_END_Y"]

        self.layout["THUMB_W"] = int(180 * sx)
        self.layout["THUMB_H"] = int(95 * sy)
        if self.img.get("HAS_COMPLETE_BG") and self.img.get("complete_bg") is not None:
            self.layout["complete_bg"] = scale(self.img["complete_bg"], self.WIDTH, self.HEIGHT)
        else:
            self.layout["complete_bg"] = None

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            if self.popup_timer > 0:
                self.popup_timer = max(0.0, self.popup_timer - dt)

            # scene change sounds
            if self.scene != self.current_scene:
                self.stop_all_loop_sounds()
                if self.scene == SCENE_COMPLETE:
                    self.snd["complete"].play()
                elif self.scene == SCENE_GAMEOVER:
                    self.snd["game_over"].play()
                if self.scene == SCENE_PLAY and not self.play["phone"] and not self.play["smoking"] and not self.play["gameover"]:
                    self.snd["typing"].play(-1)
                self.current_scene = self.scene

            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    click = True
                    if self.scene == SCENE_MAIN_MENU:
                        self.snd["menu_click"].play()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.scene == SCENE_PLAY:
                            self.scene = SCENE_MAIN_MENU
                        elif self.scene in (SCENE_LEVEL_SELECT, SCENE_SHOP, SCENE_COMPLETE, SCENE_GAMEOVER):
                            self.scene = SCENE_MAIN_MENU

                    if self.scene == SCENE_PLAY:
                        if event.key == pygame.K_SPACE and not self.play["gameover"]:
                            self.play["phone"] = True
                            self.snd["typing"].stop()
                            self.snd["phone_use"].play(-1)

                        if event.key == pygame.K_c and not self.play["gameover"] and not self.play["phone"]:
                            self.play["smoking"] = True
                            self.snd["typing"].stop()

                    if event.key == pygame.K_r and self.scene in (SCENE_GAMEOVER, SCENE_COMPLETE):
                        self.scene = SCENE_MAIN_MENU

                if event.type == pygame.KEYUP:
                    if self.scene == SCENE_PLAY and event.key == pygame.K_SPACE:
                        self.play["phone"] = False
                        self.snd["phone_use"].stop()
                        if not self.play["gameover"] and not self.play["smoking"]:
                            self.snd["typing"].play(-1)

                    if self.scene == SCENE_PLAY and event.key == pygame.K_c:
                        self.play["smoking"] = False
                        if not self.play["gameover"]:
                            self.snd["typing"].play(-1)

            if self.scene == SCENE_PLAY and not self.play["gameover"]:
                update_play(self, dt)

            draw_scene(self, click)

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    Game().run()
