# config.py
# Alle instellingen op één plek.

# FPS, paths (assets/, save.json)

# Balancing (punten per sec, thresholds, coins rewards)

# Kleuren voor menu/shop

# SHOP_ITEMS catalogus (laptops + phones)



import os

FPS = 60

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SAVE_PATH  = os.path.join(os.path.dirname(__file__), "save.json")

PHONE_POINTS_PER_SEC = 10
MAX_HOLD_BONUS = 3.0

GRID_COLS = 5
GRID_ROWS = 3
TOTAL_LEVELS = GRID_COLS * GRID_ROWS  # 15

STAR_1 = 180
STAR_2 = 320
STAR_3 = 500

DESK_Y_OFFSET = 0
HANDS_Y_OFFSET = 6

COINS_BASE_WIN = 50
COINS_PER_STAR = 10
COINS_FIRST_CLEAR_BONUS = 100

POPUP_DURATION = 1.4

# Main menu settings
MAIN_MENU_BG_COLOR = (45, 55, 70)
BUTTON_BG_COLOR = (109, 52, 18)
BUTTON_TEXT_COLOR = (253, 221, 131)
TITLE_COLOR = (255, 230, 180)

# Shop colors
COL_TEXT = (109, 52, 18)
COL_BTN_BG = (253, 221, 131)
COL_PANEL_BG = (248, 236, 200)
COL_CARD_BG  = (255, 248, 225)
COL_BORDER   = (109, 52, 18)
COL_MUTED    = (170, 150, 120)

SHOP_ITEMS = {
    # --- Laptops ---
    "laptop_default": {"type": "laptop", "price": 0,   "file": "laptopnohands.png",   "name": "Laptop Default"},
    "laptop_gaming":  {"type": "laptop", "price": 400, "file": "gaminglaptop.png",    "name": "Gaming Laptop"},
    "kity_laptop":    {"type": "laptop", "price": 550, "file": "hellokitylaptop.png", "name": "Hello kity Laptop"},
    "roze_laptop":    {"type": "laptop", "price": 700, "file": "rozelaptop.png",      "name": "Roze Laptop"},
    "future_gaming":  {"type": "laptop", "price": 900, "file": "futurlaptop.png",     "name": "Future Laptop"},

    # --- Telefoons ---
    "phone_default":  {"type": "phone",  "price": 0,   "file": "phone.png",           "name": "Phone Default"},
    "kity_phone":     {"type": "phone",  "price": 250, "file": "kity_phone.png",      "name": "Kity Phone"},
}
