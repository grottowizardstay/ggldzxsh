#!/usr/bin/env python3
"""Generates the textures and item models of the gifts the diamond phone fires.
Run from the repository root: python3 tools/generate_gifts.py

The pixel art is cut out of the reference pictures in tools/gifts: the dark backdrop is flood-filled
away from the corners, the picture is shrunk to SIZE pixels and its palette is reduced."""
import json

from PIL import Image, ImageDraw

from generate_weapons import ASSETS

SIZE = 32
COLORS = 20
BACKDROP_TOLERANCE = 28
GIFTS = {"gift_rose": "tools/gifts/rose.png", "gift_diamond": "tools/gifts/diamond.png"}


def cut_out(path):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        ImageDraw.floodfill(img, corner, (0, 0, 0, 0), thresh=BACKDROP_TOLERANCE)
    img = img.crop(img.getchannel("A").getbbox())
    side = max(img.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return square


def pixelate(img):
    small = img.resize((SIZE - 2, SIZE - 2), Image.LANCZOS)
    alpha = small.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    flat = small.convert("RGB").quantize(COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")
    flat.putalpha(alpha)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(flat, (1, 1))
    return out


def main():
    for name, source in GIFTS.items():
        pixelate(cut_out(source)).save(f"{ASSETS}/textures/item/{name}.png")
        with open(f"{ASSETS}/models/item/{name}.json", "w") as f:
            json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": f"kalabushkin:item/{name}"}}, f,
                      separators=(",", ":"))


if __name__ == "__main__":
    main()
