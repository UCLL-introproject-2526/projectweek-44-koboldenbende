# scenes.py
# Alle scene-logica (tekenen + interactie) en play-update.

# start_level() reset state en start typing + schedule boss

# update_play() bevat alle gameplay mechanics (boss detectie, score, win/lose)

# draw_scene() bevat de volledige draw + click-handling per scene
# Dit is het “grootste” bestand omdat hier je UI flow samenkomt.

import random
import pygame
from ui import draw_panel, draw_text_shadow, draw_big_star

from config import (
    GRID_COLS, GRID_ROWS, TOTAL_LEVELS,
    MAIN_MENU_BG_COLOR,
    COL_PANEL_BG, COL_CARD_BG, COL_BORDER, COL_MUTED, COL_TEXT,
    COINS_BASE_WIN, COINS_PER_STAR, COINS_FIRST_CLEAR_BONUS,
    POPUP_DURATION,
    MAX_HOLD_BONUS, PHONE_POINTS_PER_SEC,
    SHOP_ITEMS,
)
from constants import (
    SCENE_MAIN_MENU, SCENE_LEVEL_SELECT, SCENE_PLAY, SCENE_COMPLETE, SCENE_GAMEOVER, SCENE_SHOP,
    WAIT, WALKING_IN, LOOKING, WALKING_OUT
)
from utils import draw_text, clamp, blit_fit_center, scale
from levels import (
    make_level_params,
    schedule_next_check,
    score_to_stars,
    level_star_thresholds,
    level_complete_score,
)
from save_system import write_save
from assets import boss_asset_for_level
from shop import buy_or_equip


# -----------------------------
# Boss path helper
# -----------------------------
def set_boss_path(game, direction="in"):
    if direction == "in":
        from_left = random.choice([True, False])
        start_x = -80 if from_left else game.WIDTH + 80
        end_x = game.layout["LAPTOP_POS"][0] + game.layout["LAPTOP_SIZE"][0] // 2
        game.play["boss_start"] = (start_x, game.layout["BOSS_START_Y"])
        game.play["boss_end"] = (end_x, game.layout["BOSS_END_Y"])
        game.play["boss_from_left"] = from_left
    else:
        from_left = game.play.get("boss_from_left", True)
        start_x = game.layout["LAPTOP_POS"][0] + game.layout["LAPTOP_SIZE"][0] // 2
        end_x = -80 if from_left else game.WIDTH + 80
        game.play["boss_start"] = (start_x, game.layout["BOSS_START_Y"])
        game.play["boss_end"] = (end_x, game.layout["BOSS_END_Y"])


# -----------------------------
# Start level (called from main menu, level select, retry, next)
# -----------------------------
def start_level(game, level_num: int):
    game.selected_level = level_num
    params = make_level_params(level_num - 1)

    game.play["score"] = 0.0
    game.play["phone"] = False
    game.play["phone_hold_time"] = 0.0
    game.play["gameover"] = False
    game.play["caught"] = False
    game.play["boss_state"] = WAIT
    game.play["boss_timer"] = 0.0
    game.play["reaction_timer"] = 0.0
    game.play["boss_start"] = (0, 0)
    game.play["boss_end"] = (0, 0)
    game.play["boss_from_left"] = True
    game.play["hands_anim_t"] = 0.0
    game.play["hands_anim_frame"] = 0
    game.play["pre_walk_sound_started"] = False

    game.play["smoking"] = False
    game.play["smoking_timer"] = 0.0
    game.play["high_timer"] = 0.0
    game.play["shake_x"] = 0
    game.play["shake_y"] = 0
    game.play["hallucination_color"] = (0, 255, 0)
    game.play["hallucination_timer"] = 0.0

    game.stop_all_loop_sounds()
    schedule_next_check(game.play, params)

    game.scene = SCENE_PLAY
    game.snd["typing"].play(-1)


# -----------------------------
# Update logic for play scene
# -----------------------------
def update_play(game, dt):
    params = make_level_params(game.selected_level - 1)

    # hands animation
    if not game.play["phone"] and not game.play["smoking"]:
        game.play["hands_anim_t"] += dt
        if game.play["hands_anim_t"] >= 0.15:
            game.play["hands_anim_t"] -= 0.15
            game.play["hands_anim_frame"] = 1 - game.play["hands_anim_frame"]
    else:
        game.play["hands_anim_t"] = 0.0
        game.play["hands_anim_frame"] = 0

    # phone scoring
    if game.play["phone"]:
        game.play["phone_hold_time"] += dt
        combo_curve_exponent = 0.5
        raw_bonus = 1.0 + (game.play["phone_hold_time"] ** combo_curve_exponent)
        hold_bonus = min(raw_bonus, MAX_HOLD_BONUS)
        high_bonus = 1.2 if game.play["high_timer"] > 0 else 1.0
        game.play["score"] += PHONE_POINTS_PER_SEC * hold_bonus * params["mult"] * high_bonus * dt
    else:
        game.play["phone_hold_time"] = 0.0

    # smoking -> high
    if game.play["smoking"]:
        game.play["smoking_timer"] += dt
        if game.play["smoking_timer"] >= 5.0:
            game.play["smoking"] = False
            game.play["high_timer"] = 15.0
            game.set_popup("Joint smoked! You're high!", POPUP_DURATION)
    else:
        game.play["smoking_timer"] = 0.0

    # high effects
    if game.play["high_timer"] > 0:
        game.play["high_timer"] -= dt
        game.play["shake_x"] = random.randint(-15, 15)
        game.play["shake_y"] = random.randint(-15, 15)

        game.play["hallucination_timer"] += dt
        if game.play["hallucination_timer"] >= 1.0:
            game.play["hallucination_timer"] -= 1.0
            game.play["hallucination_color"] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
    else:
        game.play["shake_x"] = 0
        game.play["shake_y"] = 0
        game.play["hallucination_color"] = (0, 255, 0)
        game.play["hallucination_timer"] = 0.0

    # boss timing/state machine
    game.play["boss_timer"] += dt

    if game.play["boss_state"] == WAIT:
        if game.play["boss_timer"] >= game.play["next_check_in"] and not game.play["pre_walk_sound_started"]:
            game.snd["boss_walk"].play(-1)
            game.play["pre_walk_sound_started"] = True

        if game.play["boss_timer"] >= game.play["next_check_in"] + 0.5:
            game.play["boss_timer"] = 0.0
            game.play["boss_state"] = WALKING_IN
            game.play["reaction_timer"] = 0.0
            game.play["caught"] = False
            set_boss_path(game, direction="in")

    elif game.play["boss_state"] == WALKING_IN:
        game.play["reaction_timer"] += dt
        if (game.play["phone"] or game.play["smoking"]) and game.play["reaction_timer"] > params["grace"]:
            game.play["caught"] = True
            game.play["gameover"] = True

        if game.play["boss_timer"] >= params["walk_in"]:
            game.play["boss_timer"] = 0.0
            game.play["boss_state"] = LOOKING
            game.snd["boss_walk"].stop()
            game.snd["boss_chatter"].play(-1)

    elif game.play["boss_state"] == LOOKING:
        if game.play["phone"] or game.play["smoking"]:
            game.play["caught"] = True
            game.play["gameover"] = True

        if game.play["boss_timer"] >= params["look"]:
            game.play["boss_state"] = WALKING_OUT
            game.play["boss_timer"] = 0.0
            game.snd["boss_chatter"].stop()
            set_boss_path(game, direction="out")
            game.snd["boss_walk"].play(-1)

    elif game.play["boss_state"] == WALKING_OUT:
        if game.play["boss_timer"] >= params["walk_out"]:
            game.play["boss_state"] = WAIT
            game.play["boss_timer"] = 0.0
            game.snd["boss_walk"].stop()
            schedule_next_check(game.play, params)
            if not game.play["phone"] and not game.play["smoking"] and not game.play["gameover"]:
                game.snd["typing"].play(-1)

    # WIN condition (dynamic per level)
    complete_score = level_complete_score(game.selected_level)
    if game.play["score"] >= complete_score:
        game.last_run_score = int(game.play["score"])
        game.last_run_level = game.selected_level
        game.last_run_stars = score_to_stars(game.last_run_score, game.last_run_level)

        prev_stars = game.save["stars"][game.last_run_level - 1]
        first_clear = (prev_stars == 0)

        game.save["stars"][game.last_run_level - 1] = max(prev_stars, game.last_run_stars)
        if game.last_run_level < TOTAL_LEVELS:
            game.save["unlocked"] = max(game.save["unlocked"], game.last_run_level + 1)

        game.save["coins"] += (COINS_BASE_WIN + game.last_run_stars * COINS_PER_STAR)
        if first_clear:
            game.save["coins"] += COINS_FIRST_CLEAR_BONUS

        write_save(game.save)
        game.scene = SCENE_COMPLETE
        return

    # GAME OVER
    if game.play["gameover"]:
        game.last_run_score = int(game.play["score"])
        game.last_run_level = game.selected_level
        game.last_run_stars = score_to_stars(game.last_run_score, game.last_run_level)

        prev_stars = game.save["stars"][game.last_run_level - 1]
        game.save["stars"][game.last_run_level - 1] = max(prev_stars, game.last_run_stars)

        coins_earned = game.last_run_stars * COINS_PER_STAR
        game.save["coins"] += coins_earned

        write_save(game.save)
        game.scene = SCENE_GAMEOVER


# -----------------------------
# Draw current scene + handle click interactions
# -----------------------------
def draw_scene(game, click: bool):
    scene = game.scene
    screen = game.screen
    mx, my = pygame.mouse.get_pos()

    # -----------------------------
    # MAIN MENU
    # -----------------------------
    if game.scene == SCENE_MAIN_MENU:
        if game.img["HAS_MENU_BG"] and game.layout["main_menu_bg"] is not None:
            screen.blit(game.layout["main_menu_bg"], (0, 0))
            overlay = pygame.Surface((game.WIDTH, game.HEIGHT))
            overlay.set_alpha(64)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(MAIN_MENU_BG_COLOR)
            for i in range(0, game.WIDTH, 40):
                for j in range(0, game.HEIGHT, 40):
                    pygame.draw.rect(screen, (35, 45, 60), (i, j, 40, 40), 1)

        button_width = int(game.WIDTH * 0.32)
        button_height = int(game.HEIGHT * 0.11)
        button_x = game.WIDTH // 2 - button_width // 2

        start_rect = pygame.Rect(button_x, int(game.HEIGHT * 0.33), button_width, button_height)
        if game.menu_button(start_rect, "START GAME") and click:
            start_level(game, game.save["unlocked"])

        levels_rect = pygame.Rect(button_x, int(game.HEIGHT * 0.48), button_width, button_height)
        if game.menu_button(levels_rect, "LEVEL SELECT") and click:
            game.scene = SCENE_LEVEL_SELECT

        shop_rect = pygame.Rect(button_x, int(game.HEIGHT * 0.63), button_width, button_height)
        if game.menu_button(shop_rect, "SHOP") and click:
            game.scene = SCENE_SHOP
            if game.shop_tab == "phone":
                game.shop_selected_id = game.save["equipped"].get("phone", "phone_default")
            else:
                game.shop_selected_id = game.save["equipped"].get("laptop", "laptop_default")

        quit_rect = pygame.Rect(button_x, int(game.HEIGHT * 0.78), button_width, button_height)
        if game.menu_button(quit_rect, "QUIT GAME") and click:
            game.running = False

        footer_text = game.small.render("SPATIE = telefoon | ESC = menu", True, (0, 0, 0))
        screen.blit(
            footer_text,
            (game.WIDTH // 2 - footer_text.get_width() // 2, game.HEIGHT - int(game.HEIGHT * 0.06)),
        )

    # -----------------------------
    # LEVEL SELECT
    # -----------------------------
    elif game.scene == SCENE_LEVEL_SELECT:
        if game.img["HAS_LEVEL_SELECT_BG"] and game.layout["level_select_bg"] is not None:
            screen.blit(game.layout["level_select_bg"], (0, 0))

            overlay = pygame.Surface((game.WIDTH, game.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 64))
            screen.blit(overlay, (0, 0))

            header_overlay = pygame.Surface((game.WIDTH, int(game.HEIGHT * 0.22)), pygame.SRCALPHA)
            header_overlay.fill((0, 0, 0, 128))
            screen.blit(header_overlay, (0, 0))
        else:
            pygame.draw.rect(screen, (170, 210, 240), (0, 0, game.WIDTH, int(game.HEIGHT * 0.30)))
            pygame.draw.rect(
                screen,
                (120, 180, 230),
                (0, int(game.HEIGHT * 0.30), game.WIDTH, game.HEIGHT - int(game.HEIGHT * 0.30)),
            )

        back_rect = pygame.Rect(int(game.WIDTH * 0.02), int(game.HEIGHT * 0.03), int(game.WIDTH * 0.12), int(game.HEIGHT * 0.07))
        if game.button(back_rect, "< Terug") and click:
            game.scene = SCENE_MAIN_MENU

        draw_text(screen, game.font, f"Unlocked: {game.save['unlocked']} / {TOTAL_LEVELS}",
                  int(game.WIDTH * 0.04), int(game.HEIGHT * 0.18), (255, 255, 255))
        draw_text(screen, game.font, f"Coins: {game.save['coins']}",
                  int(game.WIDTH * 0.82), int(game.HEIGHT * 0.18), (255, 255, 255))

        shop_btn = pygame.Rect(int(game.WIDTH * 0.79), int(game.HEIGHT * 0.04), int(game.WIDTH * 0.17), int(game.HEIGHT * 0.09))
        if game.button(shop_btn, "SHOP") and click:
            game.scene = SCENE_SHOP
            if game.shop_tab == "phone":
                game.shop_selected_id = game.save["equipped"].get("phone", "phone_default")
            else:
                game.shop_selected_id = game.save["equipped"].get("laptop", "laptop_default")

        TILE_W = game.layout["TILE_W"]
        TILE_H = game.layout["TILE_H"]
        GRID_TOP = game.layout["GRID_TOP"]
        GRID_LEFT = game.layout["GRID_LEFT"]

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                idx = r * GRID_COLS + c
                lvl_num = idx + 1
                x = GRID_LEFT + c * TILE_W
                y = GRID_TOP + r * TILE_H
                rect = pygame.Rect(x + int(TILE_W * 0.07), y + int(TILE_H * 0.10), int(TILE_W * 0.86), int(TILE_H * 0.78))

                unlocked = lvl_num <= game.save["unlocked"]
                hover = rect.collidepoint(mx, my)

                if unlocked:
                    fill = (245, 230, 160) if hover else (240, 220, 140)
                    pygame.draw.rect(screen, fill, rect, border_radius=16)
                    pygame.draw.rect(screen, (150, 120, 70), rect, 3, border_radius=16)

                    t = game.font.render(str(lvl_num), True, (55, 45, 35))
                    screen.blit(t, (rect.x + 12, rect.y + 10))

                    star_size = max(12, int((game.HEIGHT / 540) * 18))
                    game.draw_star_row(rect.x + 18, rect.y + int(rect.h * 0.55), game.save["stars"][idx],
                                       size=star_size, gap=max(4, int(star_size * 0.35)))

                    if click and hover:
                        start_level(game, lvl_num)
                else:
                    fill = (200, 200, 205) if hover else (190, 190, 195)
                    pygame.draw.rect(screen, fill, rect, border_radius=16)
                    pygame.draw.rect(screen, (130, 130, 140), rect, 3, border_radius=16)
                    draw_text(screen, game.font, "LOCK", rect.centerx - 22, rect.centery - 12, (90, 90, 100))

        draw_text(screen, game.small, "Klik op een level. (ESC = hoofdmenu)",
                  int(game.WIDTH * 0.04), game.HEIGHT - int(game.HEIGHT * 0.06), (255, 255, 255))

    # -----------------------------
    # SHOP
    # -----------------------------
    elif game.scene == SCENE_SHOP:
        screen.fill(COL_PANEL_BG)

        margin = int(game.WIDTH * 0.04)
        top_y = int(game.HEIGHT * 0.04)

        grid_x, grid_y = margin, int(game.HEIGHT * 0.22)
        grid_w, grid_h = int(game.WIDTH * 0.64), int(game.HEIGHT * 0.70)
        side_x = grid_x + grid_w + int(game.WIDTH * 0.02)
        side_y = grid_y
        side_w = game.WIDTH - side_x - margin

        grid_rect = pygame.Rect(grid_x, grid_y, grid_w, grid_h)
        side_rect = pygame.Rect(side_x, side_y, side_w, grid_h)

        tab_h = int(game.HEIGHT * 0.08)
        tab_w = int(game.WIDTH * 0.18)
        tab_gap = int(game.WIDTH * 0.015)

        tabs_y = grid_y - tab_h - int(game.HEIGHT * 0.02)

        phone_tab_rect = pygame.Rect(grid_x, tabs_y, tab_w, tab_h)
        laptop_tab_rect = pygame.Rect(grid_x + tab_w + tab_gap, tabs_y, tab_w, tab_h)

        if game.tab_button(phone_tab_rect, "TELEFOONS", game.shop_tab == "phone") and click:
            game.shop_tab = "phone"
            game.shop_selected_id = game.save["equipped"].get("phone", "phone_default")

        if game.tab_button(laptop_tab_rect, "LAPTOPS", game.shop_tab == "laptop") and click:
            game.shop_tab = "laptop"
            game.shop_selected_id = game.save["equipped"].get("laptop", "laptop_default")

        title_surf = game.title_font.render("SHOP", True, COL_TEXT)
        title_x = game.WIDTH // 2 - title_surf.get_width() // 2
        title_y = top_y
        screen.blit(title_surf, (title_x, title_y))

        coins_surf = game.font.render(f"Coins: {game.save['coins']}", True, COL_TEXT)
        screen.blit(coins_surf, (game.WIDTH - margin - coins_surf.get_width(), top_y + int(game.HEIGHT * 0.02)))

        pygame.draw.rect(screen, COL_CARD_BG, grid_rect, border_radius=18)
        pygame.draw.rect(screen, COL_BORDER, grid_rect, 3, border_radius=18)
        pygame.draw.rect(screen, COL_CARD_BG, side_rect, border_radius=18)
        pygame.draw.rect(screen, COL_BORDER, side_rect, 3, border_radius=18)

        items = [(iid, it) for (iid, it) in SHOP_ITEMS.items() if it["type"] == game.shop_tab]
        items.sort(key=lambda kv: int(kv[1]["price"]))

        if (game.shop_selected_id is None) or (game.shop_selected_id not in SHOP_ITEMS) or (SHOP_ITEMS[game.shop_selected_id]["type"] != game.shop_tab):
            game.shop_selected_id = game.save["equipped"].get(
                "phone" if game.shop_tab == "phone" else "laptop",
                "phone_default" if game.shop_tab == "phone" else "laptop_default"
            )

        cols = 3
        pad = int(game.WIDTH * 0.012)
        card_w = (grid_w - pad * (cols + 1)) // cols
        card_h = int(game.HEIGHT * 0.20)

        # Cards
        for idx, (item_id, item) in enumerate(items):
            rr = idx // cols
            cc = idx % cols
            x = grid_x + pad + cc * (card_w + pad)
            y = grid_y + pad + rr * (card_h + pad)
            card = pygame.Rect(x, y, card_w, card_h)

            owned = bool(game.save["owned"].get(item_id, False))
            slot_key = "laptop" if item["type"] == "laptop" else "phone"
            equipped = (game.save["equipped"].get(slot_key) == item_id)
            selected = (game.shop_selected_id == item_id)

            bg = (255, 255, 255) if not selected else (255, 245, 210)
            pygame.draw.rect(screen, bg, card, border_radius=16)
            pygame.draw.rect(screen, COL_BORDER if selected else COL_MUTED, card, 3, border_radius=16)

            text_area_h = int(card_h * 0.36)
            thumb_area = pygame.Rect(card.x, card.y, card.w, card.h - text_area_h)
            text_area = pygame.Rect(card.x, card.y + thumb_area.h, card.w, text_area_h)

            thumb = game.shop_thumbs.get(item_id)
            if thumb:
                blit_fit_center(screen, thumb, thumb_area, padding=10)

            pygame.draw.rect(screen, (255, 255, 255), text_area, border_radius=14)
            pygame.draw.rect(screen, COL_MUTED, text_area, 2, border_radius=14)

            name_s = game.small.render(item["name"], True, COL_TEXT)
            screen.blit(name_s, (text_area.x + 10, text_area.y + 6))

            if equipped:
                tag = "EQUIPPED"
            elif owned:
                tag = "OWNED"
            else:
                tag = f"{item['price']} coins"

            tag_s = game.small.render(tag, True, COL_TEXT)
            screen.blit(tag_s, (text_area.x + 10, text_area.y + 6 + name_s.get_height() + 2))

            if click and card.collidepoint(mx, my):
                game.shop_selected_id = item_id

        # Side panel
        if game.shop_selected_id in SHOP_ITEMS and SHOP_ITEMS[game.shop_selected_id]["type"] == game.shop_tab:
            item = SHOP_ITEMS[game.shop_selected_id]
            owned = bool(game.save["owned"].get(game.shop_selected_id, False))
            slot_key = "laptop" if item["type"] == "laptop" else "phone"
            equipped = (game.save["equipped"].get(slot_key) == game.shop_selected_id)

            draw_text(screen, game.font, "Selected:", side_x + 18, side_y + 18, COL_TEXT)
            draw_text(screen, game.font, item["name"], side_x + 18, side_y + 46, COL_TEXT)

            preview = game.shop_thumbs.get(game.shop_selected_id)
            if preview:
                prev_w = side_w - 36
                prev_h = int(grid_h * 0.22)
                prev_rect = pygame.Rect(side_x + 18, side_y + 80, prev_w, prev_h)
                blit_fit_center(screen, preview, prev_rect, padding=8)

            draw_text(screen, game.font, f"Price: {item['price']} coins", side_x + 18, side_y + int(grid_h * 0.36), COL_TEXT)
            status = "Equipped" if equipped else ("Owned" if owned else "Not owned")
            draw_text(screen, game.font, f"Status: {status}", side_x + 18, side_y + int(grid_h * 0.41), COL_TEXT)

            btn = pygame.Rect(side_x + 18, side_y + int(grid_h * 0.52), side_w - 36, int(grid_h * 0.10))

            if equipped:
                game.ui_button(btn, "EQUIPPED", enabled=False)
            else:
                if owned:
                    if game.ui_button(btn, "EQUIP") and click:
                        buy_or_equip(
                            game.shop_selected_id,
                            game.save,
                            game.snd,
                            game.set_popup,
                            game.layout,
                            game.img,
                        )
                else:
                    can_buy = game.save["coins"] >= int(item["price"])
                    if game.ui_button(btn, "KOOP" if can_buy else "TE WEINIG COINS", enabled=can_buy) and click and can_buy:
                        buy_or_equip(
                            game.shop_selected_id,
                            game.save,
                            game.snd,
                            game.set_popup,
                            game.layout,
                            game.img,
                        )
                    elif click and btn.collidepoint(mx, my) and not can_buy:
                        game.set_popup("Niet genoeg coins!", POPUP_DURATION)

        # Popup
        if game.popup_timer > 0 and game.popup_text:
            w, h = int(game.WIDTH * 0.54), int(game.HEIGHT * 0.12)
            px = (game.WIDTH - w) // 2
            py = int(game.HEIGHT * 0.03)
            rect = pygame.Rect(px, py, w, h)
            pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=16)
            pygame.draw.rect(screen, COL_BORDER, rect, 3, border_radius=16)
            t = game.font.render(game.popup_text, True, COL_TEXT)
            screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    # -----------------------------
    # PLAY
    # -----------------------------
    elif game.scene == SCENE_PLAY:
        params = make_level_params(game.selected_level - 1)

        t1, t2, t3 = level_star_thresholds(game.selected_level)
        complete_score = t3

        # background with shake
        screen.blit(game.layout["background_s"], (game.play["shake_x"], game.play["shake_y"]))

        # boss draw
        if game.play["boss_state"] in (WALKING_IN, LOOKING, WALKING_OUT):
            if game.play["boss_state"] == WALKING_IN:
                t = clamp(game.play["boss_timer"] / params["walk_in"], 0.0, 1.0)
            elif game.play["boss_state"] == WALKING_OUT:
                t = clamp(game.play["boss_timer"] / params["walk_out"], 0.0, 1.0)
            else:
                t = 1.0

            sx0, sy0 = game.play["boss_start"]
            ex0, ey0 = game.play["boss_end"]
            bx = int(sx0 + (ex0 - sx0) * t)
            by = int(sy0 + (ey0 - sy0) * t)

            bw = int(game.layout["BOSS_FAR"][0] + (game.layout["BOSS_NEAR"][0] - game.layout["BOSS_FAR"][0]) * t)
            bh = int(game.layout["BOSS_FAR"][1] + (game.layout["BOSS_NEAR"][1] - game.layout["BOSS_FAR"][1]) * t)

            boss_img = boss_asset_for_level(game.img, game.selected_level)
            boss_scaled = scale(boss_img, bw, bh)
            boss_rect = boss_scaled.get_rect(center=(bx, by))
            screen.blit(boss_scaled, (boss_rect.x + game.play["shake_x"], boss_rect.y + game.play["shake_y"]))

        # desk + laptop
        DESK_POS = game.layout["DESK_POS"]
        screen.blit(game.layout["desk_s"], (DESK_POS[0] + game.play["shake_x"], DESK_POS[1] + game.play["shake_y"]))
        screen.blit(game.layout["laptop_nohands_s"], (game.layout["LAPTOP_POS"][0] + game.play["shake_x"], game.layout["LAPTOP_POS"][1] + game.play["shake_y"]))

        from config import HANDS_Y_OFFSET
        hands_pos = (
            game.layout["LAPTOP_POS"][0] + game.play["shake_x"],
            game.layout["LAPTOP_POS"][1] + int(HANDS_Y_OFFSET * (game.HEIGHT/540)) + game.play["shake_y"],
        )


        if game.play["phone"]:
            if game.layout["phone_skin_s"] is not None:
                screen.blit(game.layout["phone_skin_s"], (game.layout["PHONE_POS"][0] + game.play["shake_x"], game.layout["PHONE_POS"][1] + game.play["shake_y"]))
            else:
                phone_fallback = scale(game.img["phone_default"], *game.layout["PHONE_SIZE"])
                screen.blit(phone_fallback, (game.layout["PHONE_POS"][0] + game.play["shake_x"], game.layout["PHONE_POS"][1] + game.play["shake_y"]))
        elif game.play["smoking"]:
            if game.layout["smoking_hand_s"] is not None:
                screen.blit(game.layout["smoking_hand_s"], hands_pos)
        else:
            screen.blit(game.layout["hands_0_s"] if game.play["hands_anim_frame"] == 0 else game.layout["hands_1_s"], hands_pos)

        # top HUD
        draw_text(screen, game.font,
                  f"Level {game.selected_level}  |  Punten: {int(game.play['score'])}  |  x{params['mult']:.2f}",
                  int(game.WIDTH * 0.02), int(game.HEIGHT * 0.02), (0, 0, 0))
        draw_text(screen, game.small,
                  "Houd SPATIE = telefoon | Houd C = joint | ESC = hoofdmenu",
                  int(game.WIDTH * 0.02), int(game.HEIGHT * 0.07), (0, 0, 0))
        draw_text(screen, game.small,
                  f"Doel: {complete_score}",
                  int(game.WIDTH * 0.02), int(game.HEIGHT * 0.11), (0, 0, 0))

        # warnings
        if game.play["boss_state"] == WALKING_IN:
            left = max(0.0, params["grace"] - game.play["reaction_timer"])
            draw_text(screen, game.font, f"BAAS KOMT! Loslaten binnen {left:.2f}s!", int(game.WIDTH * 0.02), int(game.HEIGHT * 0.15), (204, 0, 0))
        elif game.play["boss_state"] == LOOKING:
            draw_text(screen, game.font, "BAAS KIJKT!", int(game.WIDTH * 0.02), int(game.HEIGHT * 0.15), (204, 0, 0))
        elif game.play["smoking"]:
            progress = min(game.play["smoking_timer"] / 5.0, 1.0)
            draw_text(screen, game.font, f"Roken: {progress:.1%}", int(game.WIDTH * 0.02), int(game.HEIGHT * 0.15), (0, 150, 0))

        # progress bar (goal-based)
        pct = clamp(game.play["score"] / complete_score, 0.0, 1.0)
        bar = pygame.Rect(int(game.WIDTH * 0.02) + game.play["shake_x"], int(game.HEIGHT * 0.20) + game.play["shake_y"],
                          int(game.WIDTH * 0.27), int(game.HEIGHT * 0.03))
        pygame.draw.rect(screen, (20, 20, 25), bar, border_radius=8)
        pygame.draw.rect(screen, (90, 220, 120), (bar.x, bar.y, int(bar.w * pct), bar.h), border_radius=8)

        # hold bonus bar
        if game.play["phone"]:
            combo_curve_exponent = 0.5
            raw_bonus = 1.0 + (game.play["phone_hold_time"] ** combo_curve_exponent)
            hold_bonus = min(raw_bonus, MAX_HOLD_BONUS)

            bar_w = int(game.WIDTH * 0.02)
            bar_h = int(game.HEIGHT * 0.22)
            bar_x = game.WIDTH - bar_w - int(game.WIDTH * 0.02) + game.play["shake_x"]
            bar_y = game.HEIGHT - bar_h - int(game.HEIGHT * 0.04) + game.play["shake_y"]

            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            fill_h = int(bar_h * (hold_bonus / MAX_HOLD_BONUS))
            pygame.draw.rect(screen, (255, 200, 50), (bar_x, bar_y + bar_h - fill_h, bar_w, fill_h), border_radius=6)
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)
            draw_text(screen, game.small, f"x{hold_bonus:.2f}", bar_x - int(game.WIDTH * 0.03), bar_y - int(game.HEIGHT * 0.04), (204, 0, 0))

        # hallucination overlay
        if game.play["high_timer"] > 0:
            overlay = pygame.Surface((game.WIDTH, game.HEIGHT))
            overlay.fill(game.play["hallucination_color"])
            overlay.set_alpha(50)
            screen.blit(overlay, (0, 0))

    # -----------------------------
    # COMPLETE
    # -----------------------------
    elif scene == SCENE_COMPLETE:
        # Achtergrond + donkere overlay (met fallback als bg None is)
        bg = game.layout.get("complete_bg")
        if bg is not None:
            screen.blit(bg, (0, 0))
        else:
            screen.fill((10, 10, 12))

        overlay = pygame.Surface((game.WIDTH, game.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        # Centrale kaart
        card_w = int(game.WIDTH * 0.55)
        card_h = int(game.HEIGHT * 0.65)
        card_x = game.WIDTH // 2 - card_w // 2
        card_y = game.HEIGHT // 2 - card_h // 2

        draw_panel(
            screen,
            (card_x, card_y, card_w, card_h),
            fill=(20, 20, 25, 220),
            border=(253, 221, 131),
            radius=28
        )

        # Titel
        title_y = card_y + int(card_h * 0.07)
        title = "LEVEL COMPLETE!"
        draw_text_shadow(
            screen,
            game.big,
            title,
            game.WIDTH // 2 - game.big.size(title)[0] // 2,
            title_y,
            color=(253, 221, 131)
        )

        # Sub info
        info_text = f"Level {game.last_run_level}   |   Score: {game.last_run_score}"
        draw_text_shadow(
            screen,
            game.font,
            info_text,
            game.WIDTH // 2 - game.font.size(info_text)[0] // 2,
            title_y + int(card_h * 0.12),
            color=(230, 230, 230)
        )

        # Sterren
        star_y = card_y + int(card_h * 0.42)
        center_x = game.WIDTH // 2
        gap = int(card_w * 0.18)
        s1 = int(40 * (game.HEIGHT / 540))
        s2 = int(55 * (game.HEIGHT / 540))

        draw_big_star(screen, center_x - gap, star_y + 10, s1, filled=game.last_run_stars >= 1)
        draw_big_star(screen, center_x,       star_y,      s2, filled=game.last_run_stars >= 2)
        draw_big_star(screen, center_x + gap, star_y + 10, s1, filled=game.last_run_stars >= 3)

        # Coins reward (zelfde berekening als in je win logic)
        coins_earned = COINS_BASE_WIN + game.last_run_stars * COINS_PER_STAR
        coins_text = f"+{coins_earned} coins"
        draw_text_shadow(
            screen,
            game.font,
            coins_text,
            game.WIDTH // 2 - game.font.size(coins_text)[0] // 2,
            card_y + int(card_h * 0.58),
            color=(255, 215, 100)
        )

        # Knoppen
        btn_w = int(card_w * 0.55)
        btn_h = int(card_h * 0.12)
        btn_x = game.WIDTH // 2 - btn_w // 2

        btn_menu = pygame.Rect(btn_x, card_y + int(card_h * 0.70), btn_w, btn_h)
        btn_next = pygame.Rect(btn_x, card_y + int(card_h * 0.84), btn_w, btn_h)

        if game.menu_button(btn_menu, "HOOFDMENU") and click:
            game.scene = SCENE_MAIN_MENU

        if game.last_run_level < TOTAL_LEVELS:
            can_next = (game.last_run_level + 1) <= game.save["unlocked"]
            if game.menu_button(btn_next, "VOLGENDE LEVEL", enabled=can_next) and click and can_next:
                start_level(game, game.last_run_level + 1)
        else:
            game.menu_button(btn_next, "LAATSTE LEVEL!", enabled=False)


    # -----------------------------
    # GAME OVER
    # -----------------------------
    elif game.scene == SCENE_GAMEOVER:
        if game.img["HAS_CAUGHT_BG"] and game.layout["caught_bg"] is not None:
            screen.blit(game.layout["caught_bg"], (0, 0))
            overlay = pygame.Surface((game.WIDTH, game.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 70))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill((25, 25, 25))

        bw, bh = int(game.WIDTH * 0.33), int(game.HEIGHT * 0.12)
        bx = game.WIDTH // 2 - bw // 2

        retry_rect = pygame.Rect(bx, int(game.HEIGHT * 0.66), bw, bh)
        if game.menu_button(retry_rect, "RETRY") and click:
            start_level(game, game.last_run_level)

        back_rect = pygame.Rect(bx, int(game.HEIGHT * 0.80), bw, bh)
        if game.menu_button(back_rect, "TERUG NAAR LEVELS") and click:
            game.scene = SCENE_LEVEL_SELECT

        hint = game.small.render("ESC = hoofdmenu", True, (255, 255, 255))
        screen.blit(hint, (game.WIDTH // 2 - hint.get_width() // 2, game.HEIGHT - int(game.HEIGHT * 0.06)))
