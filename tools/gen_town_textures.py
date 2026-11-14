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

bus = Atlas(512, 256, 4)
CABIN = faces(0, 0, 34, 19, 66)
LOWER = faces(0, 88, 34, 16, 66)
BONNET = faces(204, 0, 34, 16, 22)
SCREEN = faces(204, 40, 32, 24, 2)
BUMPER = faces(204, 92, 36, 7, 3)
WHEEL = faces(204, 104, 4, 12, 12)
SIGN = faces(204, 130, 16, 6, 2)
DOOR = faces(320, 0, 1, 30, 20)

bus.fill((0, 0, 200, 85), WHITE)        # cabin
bus.fill((0, 88, 200, 82), WHITE)       # lower body
bus.fill((204, 0, 112, 38), WHITE)      # bonnet
bus.fill((204, 40, 68, 26), WHITE)      # windscreen pillars
bus.fill((204, 70, 26, 18), WHITE)      # windscreen side panels
bus.fill((236, 70, 16, 14), GLASS)
bus.fill((258, 70, 8, 9), WHITE)
bus.fill((204, 92, 78, 10), PLASTIC)    # bumpers
bus.fill((204, 104, 32, 24), TYRE)      # wheels
bus.fill((240, 104, 10, 8), PLASTIC)    # mirrors
bus.fill((260, 104, 56, 15), SHADE)     # roof hatch
bus.fill((204, 130, 36, 8), BLACK)      # route sign
bus.fill((320, 0, 42, 50), WHITE)       # sliding door


def window(p, x0, y0, x1, y1):
    p.rect(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5, BLACK)
    p.rect(x0, y0, x1, y1, GLASS)
    # A diagonal reflection.
    p.polygon([(x0 + (x1 - x0) * 0.55, y0), (x0 + (x1 - x0) * 0.75, y0), (x0 + (x1 - x0) * 0.45, y1),
               (x0 + (x1 - x0) * 0.25, y1)], GLASS_L)


def cabin_side(doorway):
    """Drawn with the front of the bus on the left; x runs from the windscreen to the rear."""
    def paint(p, w, h):
        p.rect(0, 0, w, 1.2, SHADE)                      # roof gutter
        window(p, 1.5, 3, 13, 13)                        # driver's door
        if doorway:
            p.rect(16, 0, 36, h, INTERIOR)
        else:
            window(p, 16.5, 3, 36, 13)
        window(p, 38.5, 3, 50.5, 13)
        window(p, 52, 3, 64, 13)
        p.line([(14.6, 1.2), (14.6, h)], SEAM, 0.3)
    return paint


def route_card(p, w, h, flipped):
    """A paper route card in the first passenger window; drawn after flipping so it reads correctly."""
    x = w - 44.5 if flipped else 44.5
    p.rect(x - 4.5, 8.2, x + 4.5, 12.6, (250, 250, 246, 255))
    p.text(x, 10.4, ROUTE, 3.6, BLACK)


def lower_side(doorway):
    def paint(p, w, h):
        p.rect(0, 8, w, 10.5, PLASTIC)                   # rub strip
        p.rect(0, 13.5, w, h, PLASTIC)                   # sill
        p.line([(14.6, 0), (14.6, 13.5)], SEAM, 0.3)
        p.rect(10.5, 2.4, 13.5, 3.4, PLASTIC)            # driver's door handle
        if doorway:
            p.rect(16, 0, 36, 13.5, INTERIOR)
            p.rect(16, 11.5, 36, 13.5, PLASTIC_L)        # the step
        p.ellipse(41.5, 7, 58.5, 24, PLASTIC)            # rear wheel arch
        p.ellipse(42.8, 8.3, 57.2, 22.7, BLACK)
        p.ellipse(61, 3, 63.4, 5.4, SEAM)                # fuel cap
    return paint


def bonnet_side(p, w, h):
    p.rect(0, 9, 7, h, PLASTIC)                          # bumper corner
    p.rect(6, 8, w, 10.5, PLASTIC)
    p.rect(6, 13.5, w, h, PLASTIC)
    p.polygon([(0, 2.5), (5, 2), (6.5, 6.5), (0, 7)], LAMP)   # headlight wrapping round the corner
    p.ellipse(5.5, 7, 22.5, 24, PLASTIC)                 # front wheel arch
    p.ellipse(6.8, 8.3, 21.2, 22.7, BLACK)
    p.rect(19.5, 4, 21, 5, AMBER)                        # side repeater


def bonnet_front(p, w, h):
    p.rect(0, 8.5, w, h, PLASTIC)
    for x0 in (1, 25.5):                                 # headlights
        p.rect(x0, 1.5, x0 + 7.5, 6.5, (150, 156, 164, 255))
        p.rect(x0 + 0.5, 2, x0 + 7, 6, LAMP)
        p.ellipse(x0 + 1.2, 2.4, x0 + 4.4, 5.6, (255, 255, 255, 255))
        p.rect(x0 + 5 if x0 < 10 else x0 + 0.5, 2, x0 + 7 if x0 < 10 else x0 + 2.5, 6, AMBER)
    p.rect(10.5, 2.2, 23.5, 5.4, BLACK)                  # grille
    for y in (3, 4, 5):
        p.line([(11, y), (23, y)], PLASTIC_L, 0.25)
    p.ellipse(15.6, 2.4, 18.4, 5.2, RIM)                 # badge
    p.rect(6, 10.5, 28, 14.5, BLACK)                     # lower intake
    for y in (11.5, 12.5, 13.5):
        p.line([(6.5, y), (27.5, y)], PLASTIC_L, 0.25)


def bonnet_top(p, w, h):
    for x in (8, 26):
        p.line([(x, 0), (x, h)], SHADE, 0.5)
    p.rect(0, 0, 1, h, SHADE)
    p.rect(w - 1, 0, w, h, SHADE)


def roof(p, w, h):
    for x in range(5, 34, 4):
        p.line([(x, 1), (x, h - 1)], SHADE, 0.6)
    p.rect(0, 0, 1.2, h, SHADE)
    p.rect(w - 1.2, 0, w, h, SHADE)


def cabin_rear(p, w, h):
    p.rect(0, 0, w, 1.2, SHADE)
    window(p, 2, 3, 16, 13)
    window(p, 18, 3, 32, 13)
    p.line([(17, 1.2), (17, h)], SEAM, 0.3)


def lower_rear(p, w, h):
    p.line([(17, 0), (17, 13.5)], SEAM, 0.3)
    p.rect(0, 13.5, w, h, PLASTIC)
    for x0 in (0.5, 30):
        p.rect(x0, 0.5, x0 + 3.5, 8, RED)
        p.rect(x0, 3, x0 + 3.5, 4.5, AMBER)
        p.rect(x0, 6.5, x0 + 3.5, 8, LAMP)
    p.rect(14.5, 5.5, 16.2, 6.4, PLASTIC)                # door handles
    p.rect(17.8, 5.5, 19.5, 6.4, PLASTIC)


def plate(p, w, h):
    """Bumper with a number plate; used at both ends."""
    p.rect(11, 1.2, 25, 5.2, (245, 245, 245, 255))
    p.rect(11, 1.2, 25, 1.5, BLACK)
    p.rect(11, 4.9, 25, 5.2, BLACK)
    p.text(18, 3.2, 'K 161 OP', 2.9, BLACK)
    for x in (4, 32):
        p.ellipse(x - 1.6, 1.8, x + 1.6, 5, LAMP)


def windscreen(card):
    def paint(p, w, h):
        p.rect(1, 1, w - 1, h - 1, BLACK)
        p.rect(1.6, 1.6, w - 1.6, h - 1.6, CLEAR)
        p.rect(1.6, 1.6, w - 1.6, h - 1.6, GLASS)
        p.rect(1, 1, w - 1, 4, (22, 30, 42, 215))        # tinted sun strip
        p.polygon([(14, 4), (22, 4), (15, h - 1), (7, h - 1)], GLASS_L)
        if card:
            p.line([(5, h - 1.5), (15, h - 6)], BLACK, 0.4)   # wipers
            p.line([(17, h - 1.5), (27, h - 6)], BLACK, 0.4)
            p.rect(2.5, 14, 11, 19.5, (250, 250, 246, 255))
            p.rect(2.5, 14, 11, 15.2, (40, 90, 190, 255))
            p.text(6.75, 17.5, ROUTE, 3.6, BLACK)
    return paint


def hub(p, w, h):
    p.ellipse(0, 0, w, h, TYRE)
    p.ellipse(0.6, 0.6, w - 0.6, h - 0.6, (38, 38, 42, 255))
    p.ellipse(2, 2, w - 2, h - 2, RIM)
    p.ellipse(2.8, 2.8, w - 2.8, h - 2.8, (140, 144, 150, 255))
    for i in range(5):                                   # wheel nuts
        angle = i * 2 * np.pi / 5
        cx, cy = w / 2 + 2 * np.cos(angle), h / 2 + 2 * np.sin(angle)
        p.ellipse(cx - 0.5, cy - 0.5, cx + 0.5, cy + 0.5, (60, 62, 68, 255))
    p.ellipse(w / 2 - 1, h / 2 - 1, w / 2 + 1, h / 2 + 1, PLASTIC)


def tread(p, w, h):
    for y in np.arange(0.5, h, 1.5):
        p.line([(0, y), (w, y + 0.8)], (44, 44, 48, 255), 0.4)


def door_outside(p, w, h):
    window(p, 1.5, 1, 18.5, 9)
    p.rect(0, 23, w, 25.5, PLASTIC)
    p.rect(0, 28.5, w, h, PLASTIC)
    p.rect(1.5, 16, 4.5, 17, PLASTIC)                    # handle, at the front edge
    for x in (0, w - 0.3):
        p.rect(x, 0, x + 0.3, h, SEAM)
    p.rect(0, 0, w, 0.3, SEAM)


def door_inside(p, w, h):
    p.rect(0, 0, w, h, (120, 124, 130, 255))
    p.rect(1.5, 1, 18.5, 9, GLASS)


# West is the bus's right-hand side, where the passenger door is; its front is at the right edge.
bus.panel(CABIN['west'], cabin_side(True), flip=True, post=lambda p, w, h: route_card(p, w, h, True))
bus.panel(CABIN['east'], cabin_side(False), post=lambda p, w, h: route_card(p, w, h, False))
bus.panel(CABIN['top'], roof)
bus.panel(CABIN['south'], cabin_rear)
bus.fill(CABIN['bottom'], INTERIOR)
bus.panel(LOWER['west'], lower_side(True), flip=True)
bus.panel(LOWER['east'], lower_side(False))
bus.panel(LOWER['south'], lower_rear)
bus.fill(LOWER['bottom'], BLACK)
bus.fill(LOWER['top'], INTERIOR)
bus.panel(BONNET['west'], bonnet_side, flip=True)
bus.panel(BONNET['east'], bonnet_side)
bus.panel(BONNET['north'], bonnet_front)
bus.panel(BONNET['top'], bonnet_top)
bus.fill(BONNET['bottom'], BLACK)
bus.panel(SCREEN['north'], windscreen(True))
bus.panel(SCREEN['south'], windscreen(False))
bus.panel(BUMPER['north'], plate)
bus.panel(BUMPER['south'], plate)
for side in ('west', 'east'):
    bus.panel(WHEEL[side], hub)
for side in ('top', 'bottom', 'north', 'south'):
    bus.panel(WHEEL[side], tread)
for side in ('north', 'south'):
    bus.panel(SIGN[side], lambda p, w, h: (p.rect(0.4, 0.4, w - 0.4, h - 0.4, (8, 8, 10, 255)),
                                           p.text(w / 2, h / 2, ROUTE, 4.6, AMBER)))
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
b.polygon([(2, 22), (2, 15), (6, 13.5), (9, 8), (29, 8), (30, 9), (30, 22)], (150, 154, 160, 255))
b.polygon([(2.5, 21.5), (2.5, 15.4), (6.4, 14), (9.3, 8.5), (28.8, 8.5), (29.5, 9.3), (29.5, 21.5)], WHITE)
b.polygon([(7.4, 13.8), (9.8, 9.6), (13.5, 9.6), (13.5, 13.8)], (34, 46, 60, 255))
b.rect(14.5, 9.6, 21, 13.8, (34, 46, 60, 255))
b.rect(22, 9.6, 28.5, 13.8, (34, 46, 60, 255))
b.rect(2.5, 18.5, 29.5, 19.6, PLASTIC)
b.rect(2, 20.5, 6, 22, PLASTIC)
b.rect(2.5, 15.6, 4.2, 17, LAMP)
b.rect(28.6, 15, 29.5, 18, RED)
for cx in (8.5, 24):
    b.ellipse(cx - 3.2, 18.6, cx + 3.2, 25, TYRE)
    b.ellipse(cx - 1.5, 20.3, cx + 1.5, 23.3, RIM)
b.rect(15, 4.2, 23, 7.8, BLACK)
b.text(19, 6, ROUTE, 3.2, AMBER)
big.image.resize((32, 32), Image.LANCZOS).save(os.path.join(OUT, 'item', 'marshrutka.png'))
