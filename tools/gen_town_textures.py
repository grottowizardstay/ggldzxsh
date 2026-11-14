"""Draws the textures for Romich, the marshrutka and their items.

Run from the repository root:  uv run --with pillow --with numpy python tools/gen_town_textures.py

The UV layouts here mirror RomichModel and MarshrutkaModel: a cuboid at uv(u, v) with size
(w, h, d) has its faces at the rectangles returned by faces().
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'resources', 'assets', 'kalabushkin', 'textures')
rng = np.random.default_rng(161)
CLEAR = (0, 0, 0, 0)


def font(size):
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)
    except OSError:
        return ImageFont.load_default(size)


def faces(u, v, w, h, d):
    """Texture rectangles (x, y, width, height) of a cuboid's faces. West is the model's -X side."""
    return {'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d), 'west': (u, v + d, d, h),
            'north': (u + d, v + d, w, h), 'east': (u + d + w, v + d, d, h), 'south': (u + d + w + d, v + d, w, h)}


class Atlas:
    def __init__(self, width, height, scale):
        self.s = scale
        self.image = Image.new('RGBA', (width * scale, height * scale), CLEAR)

    def fill(self, rect, color):
        x, y, w, h = rect
        s = self.s
        self.image.paste(Image.new('RGBA', (int(w * s), int(h * s)), color), (int(x * s), int(y * s)))

    def panel(self, rect, paint, flip=False, post=None):
        """Paints one face. `flip` mirrors it; `post` then draws what must not be mirrored (text)."""
        x, y, w, h = rect
        s = self.s
        # Start from what fill() put there, so painters only add detail.
        img = self.image.crop((int(x * s), int(y * s), int(x * s) + int(w * s), int(y * s) + int(h * s)))
        paint(Pen(img, self.s), w, h)
        if flip:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if post:
            post(Pen(img, self.s), w, h)
        self.image.paste(img, (int(x * self.s), int(y * self.s)))

    def grain(self, amount):
        """A little sensor-like noise on everything opaque, so flat fills do not look painted."""
        pixels = np.asarray(self.image, dtype=float).copy()
        noise = rng.normal(0, amount, pixels.shape[:2])
        solid = pixels[..., 3] > 0
        for c in range(3):
            pixels[..., c][solid] += noise[solid]
        self.image = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))

    def mottle(self, rect, amount, radius):
        """Soft blotches, for washed cotton."""
        x, y, w, h = (int(v * self.s) for v in rect)
        field = rng.normal(0, 1, (h, w))
        field = np.asarray(Image.fromarray(((field - field.min()) / np.ptp(field) * 255).astype(np.uint8))
                           .filter(ImageFilter.GaussianBlur(radius)), dtype=float)
        field = (field - field.mean()) / (field.std() + 1e-6) * amount
        pixels = np.asarray(self.image, dtype=float).copy()
        area = pixels[y:y + h, x:x + w]
        solid = area[..., 3] > 0
        for c in range(3):
            area[..., c][solid] += field[solid]
        self.image = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))

    def save(self, name):
        path = os.path.join(OUT, name + '.png')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.image.save(path)


class Pen:
    """Draws in model pixels on a scaled image."""

    def __init__(self, image, scale):
        self.image = image
        self.s = scale
        self.draw = ImageDraw.Draw(image)

    def rect(self, x0, y0, x1, y1, color):
        s = self.s
        self.draw.rectangle((round(x0 * s), round(y0 * s), round(x1 * s) - 1, round(y1 * s) - 1), fill=color)

    def ellipse(self, x0, y0, x1, y1, color):
        s = self.s
        self.draw.ellipse((x0 * s, y0 * s, x1 * s - 1, y1 * s - 1), fill=color)

    def line(self, points, color, width):
        self.draw.line([(x * self.s, y * self.s) for x, y in points], fill=color, width=max(1, round(width * self.s)))

    def polygon(self, points, color):
        self.draw.polygon([(x * self.s, y * self.s) for x, y in points], fill=color)

    def text(self, cx, cy, value, height, color):
        f = font(max(6, round(height * self.s)))
        box = self.draw.textbbox((0, 0), value, font=f)
        self.draw.text((cx * self.s - (box[0] + box[2]) / 2, cy * self.s - (box[1] + box[3]) / 2), value, font=f, fill=color)


# ================================================================ marshrutka (512x256 model px)
WHITE = (235, 237, 240, 255)
SHADE = (204, 208, 214, 255)
SEAM = (150, 154, 160, 255)
PLASTIC = (50, 52, 56, 255)
PLASTIC_L = (72, 74, 80, 255)
BLACK = (18, 18, 20, 255)
GLASS = (34, 46, 60, 170)
GLASS_L = (70, 92, 116, 150)
TYRE = (24, 24, 27, 255)
RIM = (176, 180, 186, 255)
RED = (190, 26, 30, 255)
AMBER = (255, 168, 36, 255)
LAMP = (232, 240, 248, 255)
INTERIOR = (40, 42, 48, 255)
ROUTE = '161'

TINT = (14, 16, 20, 238)
TINT_L = (44, 50, 60, 238)
STEEL = (58, 60, 66, 255)
DASH = (30, 31, 35, 255)
HEADLAMP = (198, 210, 224, 255)
PLATE = 'К161ОХ'
REGION = '32'

# A white high-roof Peugeot Boxer minibus. The rectangles match MarshrutkaModel.java.
bus = Atlas(512, 256, 4)
MAIN = faces(0, 0, 34, 39, 70)
NOSE = faces(0, 112, 34, 15, 22)
BUMPER_F = faces(0, 152, 36, 8, 3)
BUMPER_R = faces(0, 168, 36, 5, 2)
SCREEN = faces(212, 0, 32, 18, 2)
BONNET = faces(212, 24, 34, 1, 9)
COWL_1 = faces(212, 36, 34, 2, 18)
COWL_2 = faces(212, 58, 34, 2, 14)
WHEEL = faces(320, 0, 4, 12, 12)
MIRROR = faces(320, 28, 3, 8, 3)
HATCH = faces(320, 44, 16, 2, 14)
DOOR = faces(390, 0, 1, 34, 18)

bus.fill((0, 0, 208, 109), WHITE)       # main body
bus.fill((0, 112, 112, 37), WHITE)      # nose
bus.fill((0, 152, 78, 13), PLASTIC)     # front bumper
bus.fill((0, 168, 76, 7), PLASTIC)      # rear bumper
bus.fill((212, 0, 68, 20), WHITE)       # windscreen pillars
bus.fill((212, 24, 86, 10), WHITE)      # bonnet
bus.fill((212, 36, 104, 20), WHITE)     # cowl steps under the bonnet
bus.fill((212, 58, 96, 16), WHITE)
bus.fill((212, 76, 76, 14), WHITE)      # roof brow over the windscreen
bus.fill((212, 92, 80, 16), (34, 46, 60, 225))  # quarter windows beside the windscreen
bus.fill((320, 0, 32, 24), TYRE)        # wheels
bus.fill((320, 28, 12, 11), PLASTIC)    # mirrors
bus.fill((340, 28, 8, 12), BLACK)       # aerial
bus.fill((320, 44, 60, 16), WHITE)      # roof hatch
bus.fill((390, 0, 38, 52), WHITE)       # sliding door


def tinted(p, x0, y0, x1, y1, shines, splits=()):
    """Dark privacy glass in a black frame, with slanted reflections starting at `shines`."""
    p.rect(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5, BLACK)
    p.rect(x0, y0, x1, y1, TINT)
    for x in shines:
        p.polygon([(x, y0), (x + 2.5, y0), (x - 1.5, y1), (x - 4, y1)], TINT_L)
    for x in splits:
        p.rect(x - 0.3, y0, x + 0.3, y1, BLACK)


def number_plate(p, x0, y0, x1, y1):
    split = x1 - 3.2
    p.rect(x0, y0, x1, y1, BLACK)
    p.rect(x0 + 0.25, y0 + 0.25, split - 0.1, y1 - 0.25, (246, 246, 246, 255))
    p.rect(split + 0.1, y0 + 0.25, x1 - 0.25, y1 - 0.25, (246, 246, 246, 255))
    p.text((x0 + split) / 2, (y0 + y1) / 2, PLATE, (y1 - y0) * 0.66, BLACK)
    p.text((split + x1) / 2, (y0 + y1) / 2 - 0.2, REGION, (y1 - y0) * 0.5, BLACK)


def body_side(doorway):
    """Drawn with the front of the bus on the left; x runs from the cab door to the rear."""
    def paint(p, w, h):
        p.rect(0, 0, w, 1, SHADE)                        # roof gutter
        p.line([(0, 4.5), (w, 4.5)], SHADE, 0.3)         # joint of the high roof
        p.rect(1, 8, 13.5, 21, BLACK)                    # cab door window
        p.rect(1.5, 8.5, 13, 20.5, GLASS)
        p.polygon([(7, 8.5), (9.5, 8.5), (6, 20.5), (3.5, 20.5)], GLASS_L)
        p.line([(15.5, 3), (15.5, 36.5)], SEAM, 0.3)
        p.rect(13.4, 22.5, 14.4, 26.5, BLACK)            # cab door handle
        tinted(p, 17.5, 8, 67, 20.5, (24, 42, 59), splits=(34.5, 51))
        p.rect(0, 29, w, 31, PLASTIC)                    # rub strip
        p.rect(0, 36.5, w, h, PLASTIC)                   # sill
        p.rect(61, 29, w, h, PLASTIC)                    # rear bumper corner
        p.ellipse(40, 28, 58, 46, PLASTIC)               # rear wheel arch
        p.ellipse(42, 30, 56, 44, BLACK)
        p.rect(w - 1.5, 19, w, 31, RED)                  # tail lamp wrapping round the corner
        p.rect(w - 1.5, 23, w, 26, AMBER)
        if doorway:
            p.rect(17, 3, 35, 37, INTERIOR)
            p.rect(17, 35, 35, 37, PLASTIC_L)            # the step
        else:
            p.ellipse(60.2, 23.2, 62.8, 25.8, SEAM)      # fuel cap
    return paint


def nose_side(p, w, h):
    p.rect(0, 8, 8, h, PLASTIC)                          # bumper corner
    p.rect(0, 12.5, w, h, PLASTIC)
    p.rect(18, 5, w, 7, PLASTIC)
    p.ellipse(5.5, 4.5, 22.5, 21.5, PLASTIC)             # front wheel arch
    p.ellipse(7, 6, 21, 20, BLACK)
    p.polygon([(0, 0.3), (8, 0.3), (4.3, 7.8), (0, 8.2)], BLACK)
    p.polygon([(0, 0.6), (7.5, 0.6), (4, 7.5), (0, 8)], HEADLAMP)
    p.polygon([(0, 4.6), (2.4, 4.3), (2, 7.6), (0, 8)], AMBER)
    p.ellipse(19.6, 2.2, 21, 3.6, AMBER)                 # side repeater


def nose_front(p, w, h):
    p.rect(9, 1, 15.5, 1.6, PLASTIC)                     # the two slim vents
    p.rect(18.5, 1, 25, 1.6, PLASTIC)
    p.polygon([(11, 3), (23, 3), (21.5, 8), (12.5, 8)], PLASTIC)
    p.ellipse(15.2, 3.6, 18.8, 7.2, RIM)                 # badge
    p.ellipse(16, 4.4, 18, 6.4, (120, 124, 130, 255))
    for side in (1, -1):
        def m(x):
            return x if side == 1 else w - x
        p.polygon([(m(0.3), 0.5), (m(9.6), 3), (m(8.4), 8.2), (m(0.3), 8.2)], BLACK)
        p.polygon([(m(0.6), 0.9), (m(9.2), 3.3), (m(8.1), 7.9), (m(0.6), 7.9)], HEADLAMP)
        lo, hi = sorted((m(3.8), m(7.8)))
        p.ellipse(lo, 3.6, hi, 7.4, (128, 138, 152, 255))
        p.ellipse(lo + 0.9, 4.5, hi - 0.9, 6.5, LAMP)
        lo, hi = sorted((m(0.9), m(3.2)))
        p.rect(lo, 4.6, hi, 7.6, AMBER)
    p.rect(0, 8, w, h, PLASTIC)


def bumper_front(p, w, h):
    p.rect(6, 0.4, 30, 2.6, BLACK)                       # grille
    for y in (1.0, 1.6, 2.2):
        p.line([(6, y), (30, y)], PLASTIC_L, 0.2)
    p.rect(8, 6.8, 28, 7.6, BLACK)                       # lower intake
    number_plate(p, 11, 3.1, 25, 6.4)
    for x in (4, 32):
        p.ellipse(x - 1.5, 3.4, x + 1.5, 6.4, BLACK)     # fog lamps
        p.ellipse(x - 0.9, 4, x + 0.9, 5.8, LAMP)


def bumper_rear(p, w, h):
    p.rect(2, 1.5, 6, 3, RED)
    p.rect(30, 1.5, 34, 3, RED)


def rear(p, w, h):
    p.rect(0, 0, w, 1, SHADE)
    p.rect(14, 1.8, 20, 2.8, RED)                        # high brake light
    tinted(p, 3, 8, 16, 20.5, (10,))
    tinted(p, 18, 8, 31, 20.5, (25,))
    p.line([(17, 3), (17, 33)], SEAM, 0.3)
    for x in (0, w - 2.5):
        p.rect(x, 19, x + 2.5, 31, RED)
        p.rect(x, 23, x + 2.5, 26, AMBER)
        p.rect(x, 29, x + 2.5, 31, LAMP)
    p.rect(15.5, 22, 18.5, 23, BLACK)                    # door handle
    number_plate(p, 10, 25.5, 24, 29)
    p.rect(0, 33, w, h, PLASTIC)
    p.rect(19.5, 15.5, 26, 19.5, (250, 250, 246, 255))   # route card in the rear window
    p.text(22.75, 17.5, ROUTE, 3, BLACK)


def roof(p, w, h):
    for y in range(8, int(h), 9):
        p.line([(1.5, y), (w - 1.5, y)], SHADE, 0.4)
    p.rect(0, 0, 0.8, h, SHADE)
    p.rect(w - 0.8, 0, w, h, SHADE)


def cab_back(p, w, h):
    """Seen through the windscreen."""
    p.rect(0, 0, w, h, INTERIOR)
    for x in (3, 21):
        p.rect(x, 10, x + 10, 24, (54, 56, 64, 255))     # seat backs
        p.rect(x + 2.5, 7, x + 7.5, 10, (62, 64, 72, 255))


def windscreen(card):
    def paint(p, w, h):
        p.rect(0.5, 0.5, w - 0.5, h - 0.5, BLACK)
        p.rect(1.3, 1.3, w - 1.3, h - 1.3, GLASS)
        p.rect(1.3, 1.3, w - 1.3, 3, (22, 30, 42, 215))  # tinted sun strip
        p.polygon([(15, 3), (22, 3), (16, h - 1.3), (9, h - 1.3)], GLASS_L)
        if card:
            p.line([(4, h - 1.6), (14, h - 5)], BLACK, 0.4)    # wipers
            p.line([(16, h - 1.6), (26, h - 5)], BLACK, 0.4)
            p.rect(2.5, 3.4, 10, 4.8, (196, 220, 244, 255))    # route strip under the sun strip
            p.rect(2.5, 9.5, 10, 14.5, (250, 250, 246, 255))   # route card
            p.rect(2.5, 9.5, 10, 10.6, (40, 90, 190, 255))
            p.text(6.25, 12.6, ROUTE, 3.4, (30, 70, 170, 255))
    return paint


def bonnet_top(p, w, h):
    p.line([(8.5, 0), (10.5, h)], SHADE, 0.3)            # the two creases
    p.line([(25.5, 0), (23.5, h)], SHADE, 0.3)


def hub(p, w, h):
    p.ellipse(0, 0, w, h, TYRE)
    p.ellipse(0.6, 0.6, w - 0.6, h - 0.6, (38, 38, 42, 255))
    p.ellipse(2.2, 2.2, w - 2.2, h - 2.2, STEEL)         # black steel wheel
    for i in range(6):                                   # vent holes
        angle = i * np.pi / 3
        cx, cy = w / 2 + 2.7 * np.cos(angle), h / 2 + 2.7 * np.sin(angle)
        p.ellipse(cx - 0.45, cy - 0.45, cx + 0.45, cy + 0.45, BLACK)
    p.ellipse(w / 2 - 1.7, h / 2 - 1.7, w / 2 + 1.7, h / 2 + 1.7, RIM)
    p.ellipse(w / 2 - 0.9, h / 2 - 0.9, w / 2 + 0.9, h / 2 + 0.9, (130, 134, 140, 255))


def tread(p, w, h):
    for y in np.arange(0.5, h, 1.5):
        p.line([(0, y), (w, y + 0.8)], (44, 44, 48, 255), 0.4)


def door_outside(p, w, h):
    tinted(p, 0.5, 5, w - 0.5, 17.5, (9,))
    p.rect(0, 26, w, 28, PLASTIC)
    p.rect(0, 33.5, w, h, PLASTIC)
    p.rect(1.2, 19.5, 2.2, 23.5, BLACK)                  # handle, at the front edge
    for x in (0, w - 0.3):
        p.rect(x, 0, x + 0.3, h, SEAM)
    p.rect(0, 0, w, 0.3, SEAM)


def door_inside(p, w, h):
    p.rect(0, 0, w, h, (120, 124, 130, 255))
    p.rect(0.5, 5, w - 0.5, 17.5, TINT)


def hatch_top(p, w, h):
    p.rect(0.8, 0.8, w - 0.8, h - 0.8, SHADE)
    p.rect(1.4, 1.4, w - 1.4, h - 1.4, (244, 245, 247, 255))


# West is the bus's right-hand side, where the passenger door is; its front is at the right edge.
bus.panel(MAIN['west'], body_side(True), flip=True)
bus.panel(MAIN['east'], body_side(False))
bus.panel(MAIN['top'], roof)
bus.panel(MAIN['north'], cab_back)
bus.panel(MAIN['south'], rear)
bus.fill(MAIN['bottom'], BLACK)
bus.panel(NOSE['west'], nose_side, flip=True)
bus.panel(NOSE['east'], nose_side)
bus.panel(NOSE['north'], nose_front)
bus.fill(NOSE['bottom'], BLACK)
bus.panel(BUMPER_F['north'], bumper_front)
bus.panel(BUMPER_R['south'], bumper_rear)
bus.panel(SCREEN['north'], windscreen(True))
bus.panel(SCREEN['south'], windscreen(False))
bus.panel(BONNET['top'], bonnet_top)
bus.fill(BONNET['bottom'], BLACK)
bus.fill(COWL_1['top'], DASH)
bus.fill(COWL_2['top'], DASH)
for side in ('west', 'east'):
    bus.panel(WHEEL[side], hub)
for side in ('top', 'bottom', 'north', 'south'):
    bus.panel(WHEEL[side], tread)
bus.panel(MIRROR['south'], lambda p, w, h: p.rect(0.4, 0.6, w - 0.4, h - 0.6, (150, 160, 172, 255)))
bus.panel(HATCH['top'], hatch_top)
bus.panel(DOOR['west'], door_outside, flip=True)
bus.panel(DOOR['east'], door_inside)
bus.grain(2.2)
bus.save('entity/marshrutka')
# ================================================================ Romich (64x64 model px)
SKIN = (224, 172, 138, 255)
SKIN_D = (198, 144, 112, 255)
HAIR = (152, 114, 76, 255)
HAIR_D = (120, 86, 56, 255)
BEARD = (126, 90, 60, 255)
TEE = (124, 142, 166, 255)
TEE_D = (98, 114, 140, 255)
NAVY = (42, 52, 82, 255)
SHORTS = (56, 60, 72, 255)
SHORTS_D = (40, 43, 54, 255)
FRAME = (26, 26, 30, 255)
LENS = (58, 60, 92, 255)

man = Atlas(64, 64, 8)
HEAD = faces(0, 0, 8, 8, 8)
HAT = faces(32, 0, 8, 8, 8)
BODY = faces(16, 16, 8, 12, 4)
ARM = faces(40, 16, 4, 12, 4)
LEG = faces(0, 16, 4, 12, 4)
SPECS = faces(0, 32, 9, 2, 1)
CHIN = faces(24, 32, 8, 3, 4)
SHIRT = faces(32, 40, 8, 12, 4)
SLEEVE = faces(0, 44, 4, 5, 4)
TRUNKS = faces(16, 44, 4, 6, 4)


def strands(p, w, h, top):
    """Hair combed forward and to one side."""
    p.rect(0, 0, w, h, HAIR)
    for i in range(26):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        dx, dy = (rng.uniform(0.4, 1.4), rng.uniform(1.0, 2.4)) if top else (rng.uniform(-0.2, 0.2), rng.uniform(1.0, 2.6))
        shade = HAIR_D if i % 3 else (176, 138, 96, 255)
        p.line([(x, y), (x + dx, y + dy)], shade, 0.18)


def face(p, w, h):
    p.rect(0, 0, w, h, SKIN)
    p.rect(0, 0, w, 1.2, HAIR)                           # hairline under the fringe
    p.rect(0, 3.0, 0.9, h, BEARD)                        # sideburns into the beard
    p.rect(w - 0.9, 3.0, w, h, BEARD)
    p.rect(0, 5.9, w, h, BEARD)
    p.rect(1.5, 2.4, 3.6, 2.8, HAIR_D)                   # brows
    p.rect(4.4, 2.4, 6.5, 2.8, HAIR_D)
    p.rect(1.2, 3.0, 3.7, 4.3, FRAME)                    # the glasses' shadow on the face
    p.rect(4.3, 3.0, 6.8, 4.3, FRAME)
    p.rect(3.6, 3.6, 4.4, 5.0, SKIN_D)                   # nose
    p.rect(2.4, 5.1, 5.6, 5.6, BEARD)                    # moustache
    p.rect(3.0, 6.0, 5.0, 6.5, (176, 110, 96, 255))      # mouth


def head_side(p, w, h):
    """Front of the head on the left."""
    p.rect(0, 0, w, h, SKIN)
    p.rect(0, 0, w, 3.2, HAIR)
    p.rect(3.5, 3.2, w, 5.2, HAIR)                       # hair over the back of the ear
    p.rect(0, 3.0, 1.6, h, BEARD)
    p.polygon([(0, 5.6), (4.5, 6.4), (4.5, h), (0, h)], BEARD)
    p.rect(3.2, 3.6, 4.6, 5.4, SKIN_D)                   # ear


def hair_front(p, w, h):
    p.polygon([(0, 0), (w, 0), (w, 1.5), (5, 2.0), (2, 2.7), (0, 2.9)], HAIR)
    for x in np.arange(0.4, w, 0.7):
        p.line([(x, 0), (x - 0.5, 1.6)], HAIR_D, 0.15)


def hair_side(p, w, h):
    p.polygon([(0, 0), (w, 0), (w, 5.6), (4, 5.2), (2.5, 3.6), (0, 3.2)], HAIR)
    for x in np.arange(0.5, w, 0.8):
        p.line([(x, 0.3), (x + 0.4, 3.0)], HAIR_D, 0.15)


def lenses(p, w, h):
    p.rect(0, 0, w, h, FRAME)
    for x0 in (0.4, 5.0):
        p.rect(x0, 0.3, x0 + 3.6, h - 0.3, LENS)
        p.polygon([(x0 + 0.5, 0.3), (x0 + 1.6, 0.3), (x0 + 0.9, h - 0.3), (x0, h - 0.3)], (104, 108, 150, 255))
    p.rect(4.0, 0, 5.0, 0.5, FRAME)


def chin_front(p, w, h):
    p.rect(0, 0, w, h, BEARD)
    p.rect(2.7, 0, 5.3, 1.1, CLEAR)                      # leaves the mouth showing
    for x in np.arange(0.3, w, 0.45):
        p.line([(x, rng.uniform(0, 1.5)), (x + 0.1, h)], (104, 72, 46, 255), 0.12)


def chin_side(p, w, h):
    """Front on the left: the beard fades out towards the ear."""
    p.polygon([(0, 0), (2.2, 0.4), (3.6, 1.8), (2.6, h), (0, h)], BEARD)


def shirt_front(p, w, h):
    p.rect(0, 0, w, h, TEE)
    p.ellipse(2.2, -1.6, 5.8, 1.3, TEE_D)                # ribbed collar
    p.ellipse(2.7, -1.6, 5.3, 0.7, SKIN)
    p.text(w / 2, 3.6, 'ROCK STAR', 1.25, NAVY)
    p.rect(1.4, 4.6, 6.6, 4.75, NAVY)
    p.text(w / 2, 5.5, 'RECORDS', 0.95, NAVY)
    # A rough emblem under the lettering: a fist with horns.
    p.polygon([(3.0, 9.6), (3.0, 7.6), (3.4, 6.5), (3.8, 7.6), (4.3, 7.6), (4.3, 7.2), (4.8, 7.2), (4.8, 7.6),
               (5.2, 6.5), (5.5, 7.7), (5.3, 9.6), (4.6, 10.4), (3.6, 10.4)], NAVY)
    p.line([(3.3, 8.4), (5.2, 8.4)], TEE, 0.12)
    p.rect(0, h - 0.5, w, h, TEE_D)                      # hem


def shirt_plain(p, w, h):
    p.rect(0, 0, w, h, TEE)
    p.rect(0, h - 0.5, w, h, TEE_D)


def shirt_back(p, w, h):
    shirt_plain(p, w, h)
    p.ellipse(2.4, -1.2, 5.6, 0.8, TEE_D)


def shirt_top(p, w, h):
    p.rect(0, 0, w, h, TEE)
    p.ellipse(1.8, 0.2, 6.2, 3.8, TEE_D)
    p.ellipse(2.3, 0.6, 5.7, 3.4, CLEAR)                 # neck hole


def limb(color_top, rows, foot):
    def paint(p, w, h):
        p.rect(0, 0, w, h, SKIN)
        p.rect(0, 0, 0.5, h, SKIN_D)
        p.rect(w - 0.5, 0, w, h, SKIN_D)
        p.rect(0, 0, w, rows, color_top)
        if foot:
            p.rect(0, h - 1.1, w, h, FRAME)              # the sole of a slide
            p.rect(0, h - 2.6, w, h - 1.9, FRAME)        # and its strap
    return paint


def shorts_side(p, w, h):
    p.rect(0, 0, w, h, SHORTS)
    p.rect(0, h - 0.6, w, h, SHORTS_D)
    p.line([(w / 2, 0), (w / 2, h)], SHORTS_D, 0.12)
    p.rect(0, 0, w, 0.7, SHORTS_D)                       # waistband


man.fill((0, 0, 32, 16), SKIN)
man.panel(HEAD['top'], lambda p, w, h: strands(p, w, h, True))
man.panel(HEAD['south'], lambda p, w, h: strands(p, w, h, False))
man.panel(HEAD['north'], face)
man.panel(HEAD['west'], head_side, flip=True)
man.panel(HEAD['east'], head_side)
man.panel(HAT['top'], lambda p, w, h: strands(p, w, h, True))
man.panel(HAT['south'], lambda p, w, h: (strands(p, w, h, False), p.rect(0, 6.6, w, h, CLEAR)))
man.panel(HAT['north'], hair_front)
man.panel(HAT['west'], hair_side, flip=True)
man.panel(HAT['east'], hair_side)

man.fill((16, 16, 24, 16), TEE)
man.fill((40, 16, 16, 16), SKIN)
for side in ('north', 'south', 'west', 'east'):
    man.panel(ARM[side], limb(TEE, 4.5, False))
    man.panel(LEG[side], limb(SHORTS, 6.0, True))
    man.panel(SLEEVE[side], shirt_plain)
    man.panel(TRUNKS[side], shorts_side)
man.fill(ARM['top'], TEE)
man.fill(ARM['bottom'], SKIN_D)
man.fill(LEG['top'], SHORTS)
man.fill(LEG['bottom'], FRAME)
man.fill(SLEEVE['top'], TEE)
man.fill(TRUNKS['top'], SHORTS)

man.fill((0, 32, 20, 3), FRAME)
man.panel(SPECS['north'], lenses)
man.fill((0, 36, 10, 5), FRAME)
man.panel(CHIN['north'], chin_front)
man.panel(CHIN['west'], chin_side, flip=True)
man.panel(CHIN['east'], chin_side)
man.fill(CHIN['bottom'], BEARD)

man.panel(SHIRT['north'], shirt_front)
man.panel(SHIRT['south'], shirt_back)
man.panel(SHIRT['west'], shirt_plain)
man.panel(SHIRT['east'], shirt_plain)
man.panel(SHIRT['top'], shirt_top)
for area in ((32, 40, 24, 16), (0, 44, 16, 9), (16, 16, 24, 16)):
    man.mottle(area, 7, 5)                               # acid-washed cotton
man.grain(2.5)
man.save('entity/romich')


# ================================================================ items
coin = Atlas(16, 16, 1)
c = Pen(coin.image, 1)
c.ellipse(2, 2, 14, 14, (150, 96, 12, 255))
c.ellipse(3, 3, 13, 13, (250, 205, 60, 255))
c.ellipse(4, 4, 13, 13, (232, 172, 36, 255))
c.ellipse(4, 4, 12, 12, (246, 196, 52, 255))
c.rect(7, 5, 9, 11, (176, 118, 16, 255))
c.rect(6, 6, 8, 7, (176, 118, 16, 255))
c.rect(6, 10, 10, 11, (176, 118, 16, 255))
c.rect(5, 4, 7, 5, (255, 244, 170, 255))
coin.save('item/gold_coin')

# The marshrutka's inventory icon: its side view, drawn large and scaled down.
big = Atlas(32, 32, 8)
b = Pen(big.image, 8)
outline = [(2, 24), (2, 17.5), (3, 15.8), (7.6, 14.6), (10.4, 8.4), (12, 6.4), (29.4, 6.4), (30, 7.4), (30, 24)]
b.polygon(outline, WHITE)
b.polygon([(8.7, 14.2), (11.2, 9), (13.6, 9), (13.6, 14.2)], (34, 46, 60, 255))
b.rect(14.6, 9, 28.8, 14.2, (14, 16, 20, 255))
b.rect(2, 19.6, 30, 20.7, PLASTIC)
b.rect(2, 22.6, 30, 24, PLASTIC)
b.rect(2, 18.6, 5.5, 24, PLASTIC)
b.rect(27.6, 19.6, 30, 24, PLASTIC)
b.polygon([(2.2, 16.2), (5.6, 15.5), (4.6, 18), (2.2, 18.2)], LAMP)
b.rect(29.2, 15, 30, 19.4, RED)
b.line(outline + outline[:1], (150, 154, 160, 255), 0.35)
for cx in (8.5, 24):
    b.ellipse(cx - 4.2, 17.8, cx + 4.2, 26.2, PLASTIC)
    b.ellipse(cx - 3.2, 18.8, cx + 3.2, 25.2, TYRE)
    b.ellipse(cx - 1.6, 20.4, cx + 1.6, 23.6, (58, 60, 66, 255))
    b.ellipse(cx - 0.8, 21.2, cx + 0.8, 22.8, RIM)
big.image.resize((32, 32), Image.LANCZOS).save(os.path.join(OUT, 'item', 'marshrutka.png'))
