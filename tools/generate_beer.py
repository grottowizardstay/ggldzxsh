#!/usr/bin/env python3
"""Generates the texture, item models and effect icon for the Stary Melnik beer bottle.
Run from the repository root: python3 tools/generate_beer.py

The bottle is built from stacked boxes with a stepped, pixel-circle cross-section. Its skin is drawn
twice, once full of beer and once as empty glass, and every box is cut at the liquid level, so the beer
visibly drains. The models are picked by three item predicates: "kalabushkin:level" (how much is
left), "kalabushkin:drink" (progress of the current sip) and "kalabushkin:toast" (progress of a toast)."""
import json
import math
import os
import random

from PIL import Image

from generate_weapons import ASSETS, lerp_keys, r

NAME = "stary_melnik"
TEX_W, TEX_H = 256, 128
PX = 5                      # texture pixels per model unit
SIDE = 6 * PX               # one side of the skin: the full bottle width
HEIGHT = 15                 # bottle height in model units
EMPTY_U = 4 * SIDE          # the empty-glass skin sits to the right of the full one
SWATCH_U = 240              # flat colours and the crown cap

SIPS = 3
# Height of the beer after 0, 1, 2 and 3 sips. A full bottle is filled up to the neck label.
LEVELS = [12.0, 9.4, 6.9, 0.0]
DRINK_FRAMES = 12
TOAST_FRAMES = 8

# (y0, y1, [(width along x, depth along z), ...]) from the base to the neck.
PROFILE = [
    (0.0, 7.5, [(6, 2), (4, 4), (2, 6)]),
    (7.5, 8.75, [(5, 3), (3, 5)]),
    (8.75, 9.75, [(4, 2), (2, 4)]),
    (9.75, 10.5, [(3, 1.6), (1.6, 3)]),
    (10.5, 13.6, [(2.2, 2.2)]),
]
LIP = (13.6, 14.1, 2.8)
CAP = (14.1, 15.0, 3.0)

NECK_LABEL = (10, 20)       # texture rows, top to bottom
BODY_LABEL = (44, 68)

CREAM = (248, 236, 180)
GOLD = (206, 160, 60)
INK = (52, 30, 20)
RED = (196, 44, 34)

FONT = {
    "М": ["X.X", "XXX", "XXX", "X.X", "X.X"],
    "Е": ["XXX", "X..", "XX.", "X..", "XXX"],
    "Л": [".XX", "X.X", "X.X", "X.X", "X.X"],
    "Ь": ["X..", "X..", "XX.", "X.X", "XX."],
    "Н": ["X.X", "X.X", "XXX", "X.X", "X.X"],
    "И": ["X..X", "X..X", "X.XX", "XX.X", "X..X"],
    "К": ["X.X", "X.X", "XX.", "X.X", "X.X"],
}


def mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def half_width(row):
    """Half the bottle's width in pixels at a texture row, for placing the glass highlight."""
    y = HEIGHT - (row + 0.5) / PX
    for y0, y1, boxes in PROFILE:
        if y0 <= y < y1:
            return boxes[0][0] * PX / 2
    return LIP[2] * PX / 2


def glass_pixel(col, row, side, liquid):
    centre, edge = ((246, 178, 46), (194, 110, 14)) if liquid else ((226, 236, 230), (168, 190, 186))
    f = abs(col - (SIDE - 1) / 2) / (SIDE / 2)
    color = mix(centre, edge, f * f)
    if row >= HEIGHT * PX - 2:                       # thick glass at the base
        color = mix(color, (120, 70, 12) if liquid else (130, 150, 148), 0.5)
    # A bright streak down the left of the front and a faint one on the back.
    left = SIDE / 2 - half_width(row)
    if side == 0 and left + 2 <= col < left + 4:
        color = mix(color, (255, 250, 226), 0.6)
    elif side == 2 and left + 3 <= col < left + 4:
        color = mix(color, (255, 250, 226), 0.3)
    return color


def draw_text(put, text, x, y, color):
    for letter in text:
        glyph = FONT[letter]
        for gy, line in enumerate(glyph):
            for gx, cell in enumerate(line):
                if cell == "X":
                    put(x + gx, y + gy, color)
        x += len(glyph[0]) + 1


def text_width(text):
    return sum(len(FONT[letter][0]) + 1 for letter in text) - 1


def skin(liquid):
    """The bottle unwrapped: front, right, back and left side by side, 30 px each."""
    img = Image.new("RGBA", (4 * SIDE, HEIGHT * PX), (0, 0, 0, 0))
    rng = random.Random(41)

    def put(x, y, color):
        if 0 <= x < img.width and 0 <= y < img.height:
            img.putpixel((x, y), tuple(color) + (255,))

    for row in range(img.height):
        for x in range(img.width):
            put(x, row, glass_pixel(x % SIDE, row, x // SIDE, liquid))

    # Neck label: "100% malt" in red over an orange "soft" band.
    for row in range(*NECK_LABEL):
        for x in range(img.width):
            edge = row in (NECK_LABEL[0], NECK_LABEL[1] - 1)
            put(x, row, GOLD if edge else mix(CREAM, (236, 214, 150), abs(x % SIDE - 14.5) / 15))
    for x in range(img.width):
        for row in (16, 17):
            put(x, row, (238, 150, 48) if (x + row) % 4 else (176, 96, 30))
    for row, cols in ((12, (11, 13, 14, 15, 17, 18, 19)), (13, (11, 13, 15, 17, 19)), (14, (11, 13, 14, 15, 17, 18, 19))):
        for col in cols:
            put(col, row, RED)

    # Body label: a landscape running all the way round, the name below it.
    top, bottom = BODY_LABEL
    for row in range(top, bottom):
        for x in range(img.width):
            put(x, row, CREAM)
    for x in range(img.width):
        hill = 3 + round(1.5 * math.sin(x * math.tau / 40) + math.sin(x * math.tau / 24 + 1))
        for row in range(top + 1, top + 12):
            if row >= top + 12 - hill:
                color = (88, 140, 60) if row == top + 12 - hill else (118, 168, 76)
            else:
                color = mix((190, 222, 238), (236, 240, 214), (row - top - 1) / 8)
            put(x, row, color)
        put(x, top, GOLD)
        put(x, bottom - 1, GOLD)
    # Side panels: ears of wheat. Back: small print and a barcode.
    for side in (1, 3):
        for i in range(5):
            cx, cy = side * SIDE + 6 + i * 4, top + 14 + (i % 2) * 2
            for dx, dy in ((0, 0), (1, 1), (-1, 1), (0, 2), (1, 3), (-1, 3), (0, 4), (0, 5), (0, 6)):
                put(cx + dx, cy + dy, GOLD if dy < 5 else (150, 120, 50))
    for row in (top + 13, top + 15, top + 17):
        for col in range(3, 22):
            if rng.random() < 0.7:
                put(2 * SIDE + col, row, (120, 108, 90))
    for col in range(15, 27):
        for row in range(top + 18, top + 23):
            put(2 * SIDE + col, row, (24, 22, 22) if rng.random() < 0.55 else (252, 250, 244))

    # Front: a house, the windmill and a horse cart.
    for col in range(4, 8):
        for row in (top + 9, top + 10):
            put(col, row, (232, 222, 200))
    for col in range(3, 9):
        put(col, top + 8, (190, 62, 42))
    put(5, top + 7, (190, 62, 42))
    put(6, top + 7, (190, 62, 42))
    for row in range(top + 6, top + 12):
        spread = 1 if row < top + 9 else 2
        for col in range(15 - spread, 15 + spread + 1):
            put(col, row, (124, 82, 50) if (row + col) % 3 else (98, 62, 38))
    for col in range(13, 18):
        put(col, top + 5, (70, 44, 30))
    for k in range(1, 5):
        for dx, dy in ((k, k), (-k, k), (k, -k), (-k, -k)):
            put(15 + dx, top + 5 + dy, (176, 126, 74))
            put(15 + dx + (1 if dx * dy > 0 else -1), top + 5 + dy, (226, 196, 140))
    put(15, top + 5, (40, 26, 18))
    for col, row in ((22, top + 10), (23, top + 10), (24, top + 9), (24, top + 10), (26, top + 10), (27, top + 10)):
        put(col, row, (64, 42, 30))

    name = "МЕЛЬНИК"
    draw_text(put, name, (SIDE - text_width(name)) // 2, top + 13, INK)
    for col in range(3, 27):                         # the "from the keg" banner
        for row in range(top + 19, top + 23):
            border = col in (3, 26) or row in (top + 19, top + 22)
            if border:
                put(col, row, RED)
            elif row == top + 20 and col % 5 != 4 and 5 <= col <= 24:
                put(col, row, INK)
    return img


def texture():
    img = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 0))
    img.paste(skin(True), (0, 0))
    img.paste(skin(False), (EMPTY_U, 0))
    rng = random.Random(7)
    # Crown cap from above, then its crimped skirt.
    for y in range(15):
        for x in range(15):
            d = math.hypot(x - 7, y - 7)
            color = mix((244, 214, 120), (176, 132, 44), min(d / 9, 1))
            if d > 6.2:
                color = (150, 108, 36)
            img.putpixel((SWATCH_U + x, y), color + (255,))
    for y in range(16, 21):
        for x in range(15):
            color = (224, 184, 84) if x % 2 == 0 else (136, 96, 32)
            if y == 16:
                color = mix(color, (250, 226, 150), 0.5)
            img.putpixel((SWATCH_U + x, y), color + (255,))
    for i, base in enumerate(((236, 166, 38), (206, 222, 216))):   # beer and glass seen from above
        for y in range(24, 32):
            for x in range(8):
                j = rng.randint(-4, 4)
                img.putpixel((SWATCH_U + 8 * i + x, y), tuple(max(0, min(255, c + j)) for c in base) + (255,))
    return img


def uv(u0, v0, u1, v1):
    return [r(u0 * 16 / TEX_W), r(v0 * 16 / TEX_H), r(u1 * 16 / TEX_W), r(v1 * 16 / TEX_H)]


def skin_faces(x0, y0, z0, x1, y1, z1, offset):
    """Side faces sampling the skin by position, so the label wraps round the stepped surface."""
    v0, v1 = (HEIGHT - y1) * PX, (HEIGHT - y0) * PX

    def face(side, a, b):
        return {"uv": uv(offset + side * SIDE + a * PX, v0, offset + side * SIDE + b * PX, v1), "texture": "#0"}

    return {
        "south": face(0, x0 - 5, x1 - 5),
        "east": face(1, 11 - z1, 11 - z0),
        "north": face(2, 11 - x1, 11 - x0),
        "west": face(3, z0 - 5, z1 - 5),
    }


def flat(index):
    return {"uv": uv(SWATCH_U + 8 * index + 1, 25, SWATCH_U + 8 * index + 7, 31), "texture": "#0"}


def bottle_elements(level):
    elements = []

    def add(y0, y1, width, depth, liquid):
        x0, x1, z0, z1 = 8 - width / 2, 8 + width / 2, 8 - depth / 2, 8 + depth / 2
        faces = skin_faces(x0, y0, z0, x1, y1, z1, 0 if liquid else EMPTY_U)
        faces["up"] = faces["down"] = flat(0 if liquid else 1)
        elements.append({"from": [r(x0), r(y0), r(z0)], "to": [r(x1), r(y1), r(z1)], "faces": faces})

    for y0, y1, boxes in PROFILE:
        cut = min(max(level, y0), y1)
        for width, depth in boxes:
            if cut > y0:
                add(y0, cut, width, depth, True)
            if cut < y1:
                add(cut, y1, width, depth, False)
    add(LIP[0], LIP[1], LIP[2], LIP[2], False)

    y0, y1, size = CAP
    side = {"uv": uv(SWATCH_U, 16, SWATCH_U + 15, 21), "texture": "#0"}
    top = {"uv": uv(SWATCH_U, 0, SWATCH_U + 15, 15), "texture": "#0"}
    elements.append({"from": [r(8 - size / 2), y0, r(8 - size / 2)], "to": [r(8 + size / 2), y1, r(8 + size / 2)],
                     "faces": {"north": side, "south": side, "east": side, "west": side, "up": top, "down": top}})
    return elements


def display(drink=0.0, toast=0.0):
    """Hand transforms. drink tips the bottle up to the mouth; toast lifts it and knocks it forwards."""
    tip = lerp_keys([(0, 0), (0.25, 1), (0.85, 1), (1, 0)], drink)
    lift = lerp_keys([(0, 0), (0.25, 1), (0.8, 1), (1, 0)], toast)
    # The clink: a quick jab forwards and back while the bottle is up.
    clink = math.sin(max(0.0, min(1.0, (toast - 0.3) / 0.3)) * math.pi)
    return {
        "thirdperson_righthand": {"rotation": [r(-80 + 200 * tip + 95 * lift - 25 * clink), 0, 0],
                                  "translation": [0, r(1.5 + 1.5 * lift), r(-1.0)], "scale": [0.8] * 3},
        "firstperson_righthand": {"rotation": [r(-25 * clink), 0, r(78 * tip + 12 * lift)],
                                  "translation": [r(1.13 - 3.0 * lift), r(3.6 + 3.0 * lift), r(1.13 - 2.5 * clink)],
                                  "scale": [0.5] * 3},
        "gui": {"rotation": [12, 28, 0], "translation": [0, 0.5, 0], "scale": [1.02] * 3},
        "ground": {"translation": [0, 2, 0], "scale": [0.5] * 3},
        "fixed": {"translation": [0, 0.5, 0], "scale": [1.0] * 3},
        "head": {"translation": [0, 14, 0], "scale": [1.0] * 3},
    }


def write_models():
    def model(level, **pose):
        return {"textures": {"0": f"kalabushkin:item/{NAME}", "particle": f"kalabushkin:item/{NAME}"},
                "elements": bottle_elements(level), "display": display(**pose)}

    def save(name, data):
        with open(f"{ASSETS}/models/item/{name}.json", "w") as f:
            json.dump(data, f, separators=(",", ":"))

    overrides = []
    # Emptiest first: the last matching override wins, so a fuller bottle overrides an emptier one.
    for sips in reversed(range(SIPS)):
        level, after = LEVELS[sips], LEVELS[sips + 1]
        remaining = (SIPS - sips) / SIPS - 0.05
        if sips > 0:
            save(f"{NAME}_{sips}", model(level))
            overrides.append({"predicate": {"kalabushkin:level": r(remaining)}, "model": f"kalabushkin:item/{NAME}_{sips}"})
        elif overrides:
            overrides.append({"predicate": {"kalabushkin:level": r(remaining)}, "model": f"kalabushkin:item/{NAME}"})
        for i in range(DRINK_FRAMES):
            t = (i + 0.5) / DRINK_FRAMES
            drained = lerp_keys([(0, level), (0.3, level), (0.9, after), (1, after)], t)
            frame = f"{NAME}_{sips}_drink_{i}"
            save(frame, model(drained, drink=t))
            overrides.append({"predicate": {"kalabushkin:level": r(remaining),
                                            "kalabushkin:drink": max(r(i / DRINK_FRAMES), 0.001)},
                              "model": f"kalabushkin:item/{frame}"})
        for i in range(TOAST_FRAMES):
            frame = f"{NAME}_{sips}_toast_{i}"
            save(frame, model(level, toast=(i + 0.5) / TOAST_FRAMES))
            overrides.append({"predicate": {"kalabushkin:level": r(remaining),
                                            "kalabushkin:toast": max(r(i / TOAST_FRAMES), 0.001)},
                              "model": f"kalabushkin:item/{frame}"})
    base = model(LEVELS[0])
    base["overrides"] = overrides
    save(NAME, base)


def effect_icon():
    """18x18 status effect icon: a foaming mug."""
    img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    outline, beer, shine, foam = (74, 44, 16, 255), (238, 168, 40, 255), (252, 214, 110, 255), (252, 250, 240, 255)
    for y in range(5, 16):
        for x in range(3, 12):
            edge = x in (3, 11) or y == 15
            img.putpixel((x, y), outline if edge else (shine if x == 5 else beer))
    for y in range(7, 13):                           # handle
        for x in range(12, 15):
            if x == 14 or y in (7, 12):
                img.putpixel((x, y), outline)
    for x, y in ((3, 4), (4, 3), (5, 3), (6, 2), (7, 2), (8, 3), (9, 3), (10, 2), (11, 3), (12, 4), (2, 5), (12, 5)):
        img.putpixel((x, y), outline)
    for y in range(3, 7):
        for x in range(3, 12):
            if img.getpixel((x, y))[3] == 0 or (y >= 5 and 3 < x < 11 and (y == 5 or x % 3 == 1)):
                if y >= 4 or 4 <= x <= 10:
                    img.putpixel((x, y), foam)
    img.putpixel((2, 7), foam)                       # a drip of foam down the side
    img.putpixel((2, 6), foam)
    return img


def main():
    os.makedirs(f"{ASSETS}/textures/item", exist_ok=True)
    os.makedirs(f"{ASSETS}/textures/mob_effect", exist_ok=True)
    os.makedirs(f"{ASSETS}/models/item", exist_ok=True)
    texture().save(f"{ASSETS}/textures/item/{NAME}.png")
    effect_icon().save(f"{ASSETS}/textures/mob_effect/intoxication.png")
    write_models()


if __name__ == "__main__":
    main()
