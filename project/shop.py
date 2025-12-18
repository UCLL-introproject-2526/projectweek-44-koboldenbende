# shop.py
# Shop-logica die losstaat van rendering.

# build_shop_thumbs() maakt thumbnails uit item-images

# reload_laptop_asset() / reload_phone_asset() laadt de equipped skins

# buy_or_equip() verwerkt kopen/equippen + coins + save + popup + sound
import pygame
from config import SHOP_ITEMS, POPUP_DURATION
from save_system import write_save
from utils import load_image, scale

def build_shop_thumbs(THUMB_W, THUMB_H):
    thumbs = {}
    for item_id, item in SHOP_ITEMS.items():
        try:
            img = load_image(item["file"])
            thumbs[item_id] = pygame.transform.smoothscale(img, (THUMB_W, THUMB_H))
        except Exception:
            surf = pygame.Surface((THUMB_W, THUMB_H), pygame.SRCALPHA)
            surf.fill((200, 200, 200))
            thumbs[item_id] = surf
    return thumbs

def reload_laptop_asset(save, layout, img):
    key = save["equipped"].get("laptop", "laptop_default")
    if key not in SHOP_ITEMS or SHOP_ITEMS[key]["type"] != "laptop":
        key = "laptop_default"
    img_laptop = load_image(SHOP_ITEMS[key]["file"])
    layout["laptop_nohands_s"] = scale(img_laptop, *layout["LAPTOP_SIZE"])
    return img_laptop

def reload_phone_asset(save, layout, img):
    key = save["equipped"].get("phone", "phone_default")
    if key not in SHOP_ITEMS or SHOP_ITEMS[key]["type"] != "phone":
        key = "phone_default"
    try:
        img_phone = load_image(SHOP_ITEMS[key]["file"])
    except Exception:
        img_phone = img["phone_default"]
    layout["phone_skin_s"] = scale(img_phone, *layout["PHONE_SIZE"])
    return img_phone

def buy_or_equip(item_id, save, snd, set_popup, layout, img):
    if item_id not in SHOP_ITEMS:
        return

    item = SHOP_ITEMS[item_id]
    item_type = item["type"]
    slot_key = "laptop" if item_type == "laptop" else "phone"

    owned = bool(save["owned"].get(item_id, False))
    equipped = (save["equipped"].get(slot_key) == item_id)

    if equipped:
        set_popup("Dit is al equipped!", POPUP_DURATION)
        return

    if not owned:
        price = int(item["price"])
        if save["coins"] < price:
            set_popup("Niet genoeg coins!", POPUP_DURATION)
            return

        save["coins"] -= price
        save["owned"][item_id] = True
        snd["buy"].play()
        set_popup(f"Gekocht: {item['name']}!", POPUP_DURATION)
    else:
        snd["buy"].play()
        set_popup(f"Equipped: {item['name']}!", POPUP_DURATION)

    save["equipped"][slot_key] = item_id
    write_save(save)

    if item_type == "laptop":
        reload_laptop_asset(save, layout, img)
    else:
        reload_phone_asset(save, layout, img)
