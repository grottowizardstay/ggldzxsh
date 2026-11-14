#!/usr/bin/env python3
"""Generates the texture and item model of the EGE Literature textbook Seryoga drops.
Run from the repository root: python3 tools/generate_textbook.py

The cover in tools/textbook is shrunk to a 22x30 book with a reduced palette; a strip of page
edges down the right and along the bottom gives it thickness."""
import json

from PIL import Image

from generate_weapons import ASSETS

NAME = "ege_literature_textbook"
COVER = "tools/textbook/cover.png"
WIDTH, HEIGHT = 22, 30
COLORS = 24
PAGES = (236, 232, 220, 255)
PAGES_SHADE = (196, 190, 176, 255)


def main():
    cover = Image.open(COVER).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    cover = cover.quantize(COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    left, top = 4, 0
    out.paste(cover, (left, top))
    for y in range(top + 1, top + HEIGHT + 1):
        out.putpixel((left + WIDTH, y), PAGES if y % 2 else PAGES_SHADE)
    for x in range(left + 1, left + WIDTH + 1):
        out.putpixel((x, top + HEIGHT), PAGES_SHADE)
    out.save(f"{ASSETS}/textures/item/{NAME}.png")
    with open(f"{ASSETS}/models/item/{NAME}.json", "w") as f:
        json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": f"kalabushkin:item/{NAME}"}}, f,
                  separators=(",", ":"))


if __name__ == "__main__":
    main()
