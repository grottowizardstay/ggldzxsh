"""Draws the gym textures.

Run from the repository root:  uv run --with pillow --with numpy python tools/gen_textures.py
The T-shirt print is taken from tools/tee_print.png.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, '..', 'src', 'main', 'resources', 'assets', 'kalabushkin', 'textures')
rng = np.random.default_rng(7)


def save(array, name):
    path = os.path.join(OUT, name + '.png')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.clip(array, 0, 255).astype(np.uint8)).save(path)


def rgb(value, tint=(1.0, 1.0, 1.0)):
    """Greyscale field -> opaque RGBA with a colour tint."""
    out = np.empty(value.shape + (4,))
    for i in range(3):
        out[..., i] = value * tint[i]
    out[..., 3] = 255
    return out


def smooth(shape, radius, amplitude):
    """Soft low-frequency noise."""
    field = rng.normal(0, 1, shape)
    image = Image.fromarray(((field - field.min()) / np.ptp(field) * 255).astype(np.uint8))
    blurred = np.asarray(image.filter(ImageFilter.GaussianBlur(radius)), dtype=float)
    blurred = (blurred - blurred.mean()) / (blurred.std() + 1e-6)
    return blurred * amplitude


# ---------------------------------------------------------------- materials (32x32)
N = 32
yy, xx = np.mgrid[0:N, 0:N]

# Brushed chrome: long horizontal streaks under a soft highlight band.
streaks = np.repeat(rng.normal(0, 9, (N, 1)), N, axis=1) + rng.normal(0, 3, (N, N))
steel = 186 + streaks + 22 * np.cos((yy - 9) / N * 2 * np.pi)
save(rgb(steel, (0.97, 0.99, 1.0)), 'block/gym_steel')

# Powder-coated frame: dark graphite with a fine orange-peel grain and a few scuffs.
frame = 46 + rng.normal(0, 2.5, (N, N)) + smooth((N, N), 3, 2.5)
for _ in range(5):
    x, y, length = rng.integers(0, N), rng.integers(0, N), rng.integers(3, 8)
    for i in range(length):
        frame[(y + i // 3) % N, (x + i) % N] += 14
save(rgb(frame, (0.94, 0.97, 1.06)), 'block/gym_frame')

# Rubber: matte black with lighter crumb flecks.
rubber = 27 + rng.normal(0, 2, (N, N)) + smooth((N, N), 2, 2)
flecks = rng.random((N, N)) > 0.955
rubber[flecks] += rng.uniform(10, 22, flecks.sum())
save(rgb(rubber, (1.0, 1.0, 1.03)), 'block/gym_rubber')

# Knurling: a diamond cross-hatch cut into steel.
ridge = np.minimum((xx + yy) % 4, (xx - yy) % 4)
knurl = 120 + 34 * ridge + rng.normal(0, 4, (N, N))
save(rgb(knurl, (0.97, 0.99, 1.0)), 'block/gym_knurl')

# Vinyl pad: leather grain, a soft sheen and a stitched seam near the edge.
vinyl = 24 + rng.normal(0, 1.6, (N, N)) + smooth((N, N), 1.2, 3)
vinyl += 10 * np.exp(-(((xx - 11) / 9.0) ** 2 + ((yy - 9) / 12.0) ** 2))
edge = np.minimum.reduce([xx, yy, N - 1 - xx, N - 1 - yy])
vinyl[edge == 3] -= 7          # the seam's groove
stitch = (edge == 4) & (((xx + yy) % 4) < 2)
vinyl[stitch] = 120
vinyl[edge == 0] -= 6
save(rgb(vinyl, (1.0, 1.0, 1.05)), 'block/gym_vinyl')


# ---------------------------------------------------------------- wrist wraps
def elastic(height, width, scale):
    """Black elastic webbing: vertical ribs crossed by a fine weave, with two red bands around it."""
    y, x = np.mgrid[0:height, 0:width]
    rib = 5 * np.cos(x / scale * np.pi) + 2.5 * np.cos(y / scale * 2 * np.pi)
    value = 30 + rib + rng.normal(0, 1.5, (height, width))
    out = rgb(value, (1.0, 1.0, 1.04))
    band = height / 6.0
    for start in (height * 0.30, height * 0.56):
        rows = (y >= start) & (y < start + band)
        out[rows, 0] = 196 + rib[rows] * 4
        out[rows, 1] = 30 + rib[rows]
        out[rows, 2] = 36 + rib[rows]
    # The sewn edges.
    out[0:max(1, height // 16), :, :3] *= 0.7
    out[height - max(1, height // 16):, :, :3] *= 0.7
    return out


save(elastic(N, N, 2.0), 'item/wrist_wraps_side')

# The top of a rolled wrap: the layers show as a square spiral.
ring = np.maximum(np.abs(xx - 15.5), np.abs(yy - 15.5))
top = 30 + 9 * np.cos(ring * np.pi / 2.0) + rng.normal(0, 1.5, (N, N))
top[ring < 2] = 14
save(rgb(top, (1.0, 1.0, 1.04)), 'item/wrist_wraps_top')

# Worn on the arm: 32x8 model units at 8 px each. Each wrist is a 4x3x4 box at u=0 and u=16.
S = 8
worn = np.zeros((8 * S, 32 * S, 4))
for u in (0, 16):
    band = elastic(3 * S, 16 * S, 2.0)
    worn[4 * S:7 * S, u * S:(u + 16) * S] = band
    # The overlapping end of the wrap with its hook-and-loop patch, on the outside of the wrist.
    worn[4 * S + 2:7 * S - 2, u * S + 3 * S - 1:u * S + 3 * S + 1, :3] *= 0.45
    patch = worn[4 * S + 5:7 * S - 5, u * S + S:u * S + 3 * S - 3]
    patch[..., :3] = 44 + rng.normal(0, 4, patch.shape[:2])[..., None]
save(worn, 'entity/wrist_wraps')

# Empty hands slot: a flat silhouette of one wrap, like the vanilla empty armor slots.
icon = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(icon)
grey = (85, 85, 85, 255)
draw.rectangle((4, 6, 11, 13), outline=grey)
draw.line((4, 8, 11, 8), fill=grey)
draw.line((4, 11, 11, 11), fill=grey)
draw.arc((6, 1, 10, 9), 180, 360, fill=grey)
draw.line((6, 5, 6, 6), fill=grey)
draw.line((10, 5, 10, 6), fill=grey)
icon.save(os.path.join(OUT, 'item', 'empty_slot_hands.png'))


# ---------------------------------------------------------------- T-shirt
def cotton(height, width):
    """Black jersey: a fine knit with soft vertical folds."""
    y, x = np.mgrid[0:height, 0:width]
    knit = 1.6 * np.cos(x * np.pi) * np.cos(y * np.pi / 2.0)
    return 27 + knit + rng.normal(0, 1.2, (height, width)) + smooth((height, width), 6, 1.5)


def print_layer(width, height):
    """The print, keyed out of the photographed shirt so only the picture is left."""
    source = Image.open(os.path.join(HERE, 'tee_print.png')).convert('RGB')
    picture = np.asarray(source.resize((width, height), Image.LANCZOS), dtype=float)
    brightness = picture.max(axis=2)
    alpha = np.clip((brightness - 34) / 30.0, 0, 1)
    # Fade the border so no edge of the photo shows.
    fy = np.minimum(np.arange(height), np.arange(height)[::-1])[:, None]
    fx = np.minimum(np.arange(width), np.arange(width)[::-1])[None, :]
    alpha *= np.clip(np.minimum(fx, fy) / 3.0, 0, 1)
    return picture, alpha


def tee_texture(scale):
    """64x32 model units. Torso (8x13x4) unwrapped at u=0, sleeves (4x5x4) at u=24 and u=40."""
    s = scale
    tex = np.zeros((32 * s, 64 * s, 4))

    def fill(u, v, w, h, shade=0.0):
        tex[v * s:(v + h) * s, u * s:(u + w) * s] = rgb(cotton(h * s, w * s) + shade, (1.0, 1.0, 1.06))

    fill(4, 0, 8, 4)             # shoulders
    fill(0, 4, 24, 13)           # right side, front, left side, back
    for u in (24, 40):
        fill(u + 4, 0, 4, 4)     # top of the sleeve
        fill(u, 4, 16, 5)        # around the sleeve

    y, x = np.mgrid[0:32 * s, 0:64 * s]

    def region(u, v, w, h):
        return (x >= u * s) & (x < (u + w) * s) & (y >= v * s) & (y < (v + h) * s)

    def shade(mask, amount):
        tex[mask, :3] = np.clip(tex[mask, :3] + amount[mask][..., None], 0, 255)

    front = region(4, 4, 8, 13)
    back = region(16, 4, 8, 13)
    fx = (x - 8 * s) / (4.0 * s)           # -1..1 across the front
    fy = (y - 4 * s) / (13.0 * s)          # 0..1 down the torso
    # Chest catches the light; the fabric darkens towards the sides and hangs in folds below.
    shade(front, 7 * np.exp(-(fx ** 2) * 2.2 - ((fy - 0.28) ** 2) * 9) - 4 * fx ** 2)
    shade(front, 3.5 * np.sin(fx * 9 + fy * 3) * np.clip(fy - 0.45, 0, 1) * 2)
    bx = (x - 20 * s) / (4.0 * s)
    shade(back, 5 * np.exp(-(bx ** 2) * 2 - ((fy - 0.2) ** 2) * 8) - 4 * bx ** 2
          + 3 * np.sin(bx * 8 - fy * 2) * np.clip(fy - 0.4, 0, 1) * 2)
    shade(region(0, 4, 4, 13) | region(12, 4, 4, 13), np.full(x.shape, -6.0))

    def hem(u, v, w):
        """A turned-up hem: a fold line with two rows of stitching above the edge."""
        row = (v * s) - 1
        tex[row - int(0.75 * s), u * s:(u + w) * s, :3] *= 0.6
        for offset in (int(0.45 * s), int(0.6 * s)):
            cols = np.arange(u * s, (u + w) * s)
            dashes = cols[(cols % 4) < 3]
            tex[row - offset, dashes, :3] = 62
        tex[row, u * s:(u + w) * s, :3] *= 0.55

    hem(0, 17, 24)
    hem(24, 9, 16)
    hem(40, 9, 16)

    def neckline(cx, cy, rx, ry, band):
        """Cuts the neck opening and draws the ribbed collar around it."""
        d = ((x - cx * s) / (rx * s)) ** 2 + ((y - cy * s) / (ry * s)) ** 2
        outer = ((x - cx * s) / ((rx + band) * s)) ** 2 + ((y - cy * s) / ((ry + band) * s)) ** 2
        return d < 1, (outer < 1) & (d >= 1)

    for face, (cx, cy, rx, ry) in ((front, (8, 4, 2.3, 1.5)), (back, (20, 4, 2.1, 0.6)),
                                    (region(4, 0, 8, 4), (8, 2, 2.3, 2.0))):
        hole, collar = neckline(cx, cy, rx, ry, 0.55)
        ribs = 36 + 5 * np.cos(np.arctan2(y - cy * s, x - cx * s) * 40)
        tex[collar & face, :3] = ribs[collar & face][..., None]
        tex[hole & face] = 0

    # The print sits high on the chest, 5.2 of the 8 units wide.
    width, height = int(5.2 * s), int(4.5 * s)
    picture, alpha = print_layer(width, height)
    left, top = int((8 - 2.6) * s), int((4 + 2.6) * s)
    area = tex[top:top + height, left:left + width]
    lit = area[..., :3].mean(axis=2, keepdims=True) / 27.0     # the folds shade the print too
    area[..., :3] = area[..., :3] * (1 - alpha[..., None]) + picture * 0.92 * np.clip(lit, 0.8, 1.25) * alpha[..., None]
    return tex


save(tee_texture(16), 'entity/masculine_tee')

# Inventory icon: the shirt laid flat, drawn large and scaled down so the edges stay smooth.
big = 8
shirt = Image.new('RGBA', (32 * big, 32 * big), (0, 0, 0, 0))
draw = ImageDraw.Draw(shirt)
outline = [(9, 3), (13, 2), (16, 4), (19, 2), (23, 3), (31, 9), (27, 14), (24, 12), (24, 30), (8, 30), (8, 12),
           (5, 14), (1, 9)]
draw.polygon([(px * big, py * big) for px, py in outline], fill=(29, 29, 33, 255), outline=(12, 12, 14, 255))
draw.line([(8 * big, 12 * big), (9 * big, 29 * big)], fill=(16, 16, 19, 255), width=big // 2)
draw.line([(24 * big, 12 * big), (23 * big, 29 * big)], fill=(16, 16, 19, 255), width=big // 2)
draw.arc((12 * big, -2 * big, 20 * big, 6 * big), 20, 160, fill=(58, 58, 64, 255), width=big)
draw.line([(8 * big, 28 * big), (24 * big, 28 * big)], fill=(52, 52, 58, 255), width=big // 3)
picture, alpha = print_layer(11 * big, int(9.5 * big))
overlay = np.dstack([picture, alpha * 255]).astype(np.uint8)
shirt.alpha_composite(Image.fromarray(overlay), (int(10.5 * big), 9 * big))
shirt.resize((32, 32), Image.LANCZOS).save(os.path.join(OUT, 'item', 'masculine_tee.png'))
