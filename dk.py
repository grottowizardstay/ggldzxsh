"""House of Culture (the yellow DK building) at 1 block = 1 m, added to the gym world.

Local axes: +x east (main facade with the entrance), +z south. The building sits
OX/OZ away from the gym; importing build places the gym into the shared model.

Running this writes commands.txt, model.json, meta.json and preview PNGs for both buildings.
"""
import json
import sys

import build as g

OX, OZ = 70, -10
Y0 = g.Y0

YEL = "yellow_concrete"
SAND = "smooth_sandstone"
WHITE = "white_concrete"
RED = "red_concrete"
PANE = "light_gray_stained_glass_pane"
EAVE = "deepslate_tile_slab[type=bottom]"
ROOFING = "gray_concrete"
PAVE = "light_gray_concrete"
ASPHALT = "gray_concrete"
FLOORS = (0, 4, 8)


def put(x, y, z, b):
    g.put(x + OX, y, z + OZ, b)


def box(x0, x1, y0, y1, z0, z1, b):
    g.box(x0 + OX, x1 + OX, y0, y1, z0 + OZ, z1 + OZ, b)


def free(x, y, z):
    return (x + OX, y, z + OZ) not in g.B


def ring(x0, x1, z0, z1):
    return ((x0, x1, z0, z0), (x0, x1, z1, z1), (x0, x0, z0, z1), (x1, x1, z0, z1))


def label(x, y, z, axis, txt, color, sx, sy, italic=False, bg=0):
    """Floating text; one-sided, so summon it facing both ways along the axis."""
    esc = "".join(c if ord(c) < 128 else "\\\\u%04x" % ord(c) for c in txt)
    for yaw in ((0, 180) if axis == "z" else (90, 270)):
        g.SUMMONS.append(
            f"summon minecraft:text_display {x + OX:.2f} {y + Y0:.2f} {z + OZ:.2f} "
            f"{{Tags:[\"sign\"],Rotation:[{yaw}f,0f],billboard:\"fixed\",alignment:\"center\",background:{bg},"
            f"shadow:0b,view_range:4f,brightness:{{sky:15,block:15}},"
            f"text:'{{\"text\":\"{esc}\",\"color\":\"{color}\",\"bold\":true,\"italic\":{str(italic).lower()}}}',"
            f"transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],"
            f"scale:[{sx}f,{sy}f,1f],right_rotation:[0f,0f,0f,1f]}}}}")


# ================================================================ auditorium block (tall, blank)
for (a, b, c, d) in ring(8, 39, 10, 37):
    box(a, b, 0, 14, c, d, SAND)
    box(a, b, 0, 0, c, d, RED)
    box(a, b, 15, 15, c, d, EAVE)
box(9, 38, 13, 13, 11, 36, ROOFING)
box(9, 38, 0, 0, 11, 36, "spruce_planks")
for z0 in (18, 25):                                   # recessed panels high on the west wall
    box(8, 8, 10, 12, z0, z0 + 4, "cut_sandstone")

# ================================================================ one-storey annexes (west, north-west, south)
def annex_wall(x0, x1, z0, z1):
    box(x0, x1, 0, 0, z0, z1, RED)
    box(x0, x1, 1, 1, z0, z1, SAND)                   # faded band above the plinth
    box(x0, x1, 2, 4, z0, z1, YEL)


annex_wall(2, 2, 6, 43)
annex_wall(2, 19, 6, 6)
annex_wall(2, 39, 43, 43)
box(3, 7, 0, 0, 7, 42, "smooth_stone")
box(8, 19, 0, 0, 7, 9, "smooth_stone")
box(8, 39, 0, 0, 38, 42, "smooth_stone")
box(1, 7, 5, 5, 5, 44, EAVE)
box(8, 19, 5, 5, 5, 9, EAVE)
box(8, 39, 5, 5, 38, 44, EAVE)
for k in range(8):                                    # the row of eight windows facing the street
    box(2, 2, 2, 3, 11 + 4 * k, 12 + 4 * k, PANE)
for x in range(5, 37, 5):
    box(x, x + 1, 2, 3, 43, 43, PANE)
for x in (5, 11, 16):
    box(x, x + 1, 2, 3, 6, 6, PANE)
for z in (14, 22, 30, 38):                            # roof vents
    put(5, 6, z, "stone_brick_wall")
box(7, 7, 6, 7, 11, 12, "iron_bars")                  # caged AC unit
box(3, 3, 1, 4, 44, 44, "lightning_rod[facing=up]")   # downpipe

# service door with a porch and canopy
for row, half in ((1, "lower"), (2, "upper")):
    put(2, row, 42, f"spruce_door[facing=east,half={half},hinge=left,open=false]")
put(1, 0, 42, "smooth_stone_slab[type=bottom]")
box(0, 1, 3, 3, 41, 43, "deepslate_tile_slab[type=top]")
for z in (41, 43):
    box(0, 0, 0, 2, z, z, "warped_fence")
    put(1, 0, z, "warped_fence")

# ================================================================ north hall with tall windows
box(20, 39, 0, 9, 2, 2, SAND)
box(20, 20, 0, 9, 2, 9, SAND)
box(39, 39, 0, 9, 2, 9, SAND)
box(20, 39, 0, 0, 2, 2, RED)
box(20, 20, 0, 0, 2, 5, RED)
box(21, 38, 0, 0, 3, 9, "birch_planks")
box(20, 39, 10, 10, 1, 9, EAVE)
for x0 in (22, 27, 32):
    box(x0, x0 + 3, 4, 7, 2, 2, "white_stained_glass_pane")
for x in (23, 29, 34):
    for row, half in ((1, "lower"), (2, "upper")):
        put(x, row, 2, f"spruce_door[facing=south,half={half},hinge=left,open=false]")
    put(x, 0, 1, "smooth_stone_slab[type=bottom]")
for x in (24, 30, 36):
    put(x, 9, 6, "pearlescent_froglight")
for x in (24, 27):                                    # gym mats
    box(x, x + 1, 1, 1, 7, 8, "blue_carpet")
box(38, 38, 1, 3, 3, 4, "ladder[facing=west]")        # wall bars

# ================================================================ front block (three storeys, facing east)
for (a, b, c, d) in ring(40, 51, 0, 52):
    box(a, b, 0, 12, c, d, YEL)
    box(a, b, 13, 13, c, d, WHITE)
    box(a, b, 0, 0, c, d, "white_terracotta")
    box(a, b, 14, 14, c, d, "smooth_quartz_slab[type=bottom]")

# entrance risalit at the north end: one block forward and one block taller
box(51, 51, 0, 14, 1, 15, None)
for (a, b, c, d) in ((40, 52, 0, 0), (52, 52, 0, 16), (40, 40, 0, 16)):
    box(a, b, 0, 13, c, d, YEL)
    box(a, b, 0, 0, c, d, "white_terracotta")
for (a, b, c, d) in ((40, 52, 0, 0), (52, 52, 0, 16), (40, 40, 0, 16), (40, 52, 16, 16)):
    box(a, b, 13, 13, c, d, YEL)
    box(a, b, 14, 14, c, d, WHITE)
    box(a, b, 15, 15, c, d, "smooth_quartz_slab[type=bottom]")

for f in FLOORS:
    mat = "polished_andesite" if f == 0 else "spruce_planks"
    box(41, 50, f, f, 1, 51, mat)
    box(51, 51, f, f, 1, 15, mat)
box(41, 50, 12, 12, 16, 51, ROOFING)
box(41, 51, 13, 13, 1, 15, ROOFING)

for z in (17, 24, 31, 38, 45, 52):                    # white pilasters
    box(51, 51, 0, 13, z, z, WHITE)
for z in (0, 8, 16):
    box(52, 52, 0, 14, z, z, WHITE)
box(52, 52, 4, 4, 0, 16, WHITE)
box(40, 40, 0, 13, 52, 52, WHITE)

for f in FLOORS:                                      # wide windows, five bays
    for s in (18, 25, 32, 39, 46):
        box(51, 51, f + 2, f + 3, s + 1, s + 4, PANE)
    for x0 in (42, 47):
        box(x0, x0 + 3, f + 2, f + 3, 52, 52, PANE)
    box(40, 40, f + 2, f + 3, 45, 48, PANE)
for f in (4, 8):
    for z0 in (2, 10):
        box(52, 52, f + 2, f + 3, z0, z0 + 4, PANE)

# glazed ground floor of the risalit with two doorways, each 2 wide and 3 high
for z0 in (1, 9):
    box(52, 52, 1, 3, z0, z0 + 6, "gray_stained_glass_pane")
    for z, hinge in ((z0 + 4, "left"), (z0 + 3, "right")):
        for row, half in ((1, "lower"), (2, "upper")):
            put(52, row, z, f"dark_oak_door[facing=west,half={half},hinge={hinge},open=false]")

# portrait banner on the north face
box(43, 49, 5, 10, 0, 0, "white_wool")
box(43, 49, 5, 5, 0, 0, "light_blue_wool")
for i in range(4):
    box(43, 46 - i, 10 - i, 10 - i, 0, 0, "red_wool")

# roof sign on a frame, banner over the entrance, house number
box(52, 52, 15, 17, 2, 14, "iron_bars")
label(52.62, 15.3, 8.5, "x", "Культура", "#D8322B", 9, 9, italic=True)
label(53.05, 4.15, 12.5, "x", "С ПРАЗДНИКОМ!", "white", 3.4, 2.8, bg=-3790808)
label(53.05, 6.2, 8.5, "x", "17", "white", 2, 2, bg=-14787896)
box(47, 47, 14, 19, 4, 4, "iron_bars")                # antenna mast behind the sign
put(47, 20, 4, "lightning_rod[facing=up]")

# cell mast on the auditorium roof
box(10, 10, 14, 22, 12, 12, "iron_bars")
for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
    put(10 + dx, 20, 12 + dz, "end_rod[facing=up]")
put(10, 23, 12, "lightning_rod[facing=up]")

# ================================================================ front block interior
for f in (0, 4):                                      # staircase at the south end
    for k in range(4):
        box(41, 42, f + 1 + k, f + 1 + k, 50 - k, 50 - k, "stone_brick_stairs[facing=north,half=bottom]")
    box(41, 42, f + 4, f + 4, 48, 49, None)
for f in FLOORS:
    for z in range(4, 50, 6):
        put(46, 12 if (f == 8 and z <= 15) else f + 3, z, "lantern[hanging=true]")
for f in (4, 8):                                      # partitions upstairs
    box(41, 50, f + 1, f + 3, 28, 28, WHITE)
    box(45, 46, f + 1, f + 2, 28, 28, None)

for z0 in (4, 12):                                    # foyer: runners, ticket desk, cloakroom, plants
    box(44, 51, 1, 1, z0, z0 + 1, "red_carpet")
box(42, 43, 1, 1, 8, 9, "dark_oak_planks")
box(43, 43, 1, 1, 26, 38, "dark_oak_planks")
box(41, 41, 1, 2, 26, 38, "oak_fence")
for z in (18, 30, 44):
    put(50, 1, z, "potted_fern")
for z in (21, 35):
    box(49, 49, 1, 1, z, z + 1, "spruce_stairs[facing=east,half=bottom]")

box(41, 50, 5, 5, 23, 24, "red_carpet")               # first floor: way into the hall, library
box(41, 41, 5, 6, 30, 40, "bookshelf")
for z in (33, 39):
    put(46, 5, z, "spruce_slab[type=top]")
    put(47, 5, z, "spruce_stairs[facing=east,half=bottom]")
    put(45, 5, z, "spruce_stairs[facing=west,half=bottom]")

box(41, 41, 9, 11, 30, 44, "glass")                   # second floor: rehearsal room with mirrors and a piano
box(44, 45, 9, 9, 50, 50, "note_block")
put(44, 9, 49, "dark_oak_stairs[facing=north,half=bottom]")
for z in (5, 10):
    box(44, 48, 9, 9, z, z, "spruce_slab[type=top]")

# ================================================================ auditorium interior
def rake(x):
    return 0 if x <= 23 else 1 if x <= 27 else 2 if x <= 31 else 3 if x <= 34 else 4


AISLES = (11, 12, 23, 24, 35, 36)
for x in range(24, 39):
    box(x, x, 1, rake(x), 11, 36, "spruce_planks")
for x in (24, 28, 32, 35):
    for z in AISLES:
        put(x, rake(x), z, "spruce_stairs[facing=east,half=bottom]")
for x in (21, 23, 25, 27, 29, 31, 33, 36):            # 160 seats facing the stage
    for z in list(range(13, 23)) + list(range(25, 35)):
        put(x, rake(x) + 1, z, "mangrove_stairs[facing=east,half=bottom]")

box(9, 18, 1, 1, 11, 36, "dark_oak_planks")           # stage, proscenium and curtains
for z in (11, 12, 35, 36):
    put(19, 1, z, "dark_oak_stairs[facing=west,half=bottom]")
box(16, 16, 2, 12, 11, 36, SAND)
box(16, 16, 2, 9, 14, 33, None)
box(15, 15, 2, 9, 14, 16, "red_wool")
box(15, 15, 2, 9, 31, 33, "red_wool")
box(15, 15, 9, 9, 17, 30, "red_wool")
box(10, 10, 2, 10, 12, 35, "black_wool")
for x in (12, 20, 26, 32, 37):
    for z in (15, 23, 32):
        put(x, 12, z, "pearlescent_froglight")

# doors: hall from the first-floor foyer, side exit, links to the annex and the north hall
box(39, 39, 5, 6, 23, 24, None)
for z, hinge in ((24, "left"), (23, "right")):
    for row, half in ((5, "lower"), (6, "upper")):
        put(40, row, z, f"dark_oak_door[facing=west,half={half},hinge={hinge},open=false]")
box(20, 21, 1, 2, 37, 37, None)
box(40, 40, 1, 2, 40, 41, None)
box(39, 40, 1, 2, 5, 6, None)
for x in range(6, 38, 6):
    put(x, 4, 40, "lantern[hanging=true]")
for z in range(10, 38, 6):
    put(5, 4, z, "lantern[hanging=true]")


# ================================================================ site
def tree(x, z, h, kind="birch"):
    """Round-crowned tree with a few hanging strands."""
    put(x, -1, z, "podzol")
    box(x, x, 0, h - 1, z, z, kind + "_log")
    leaf = kind + "_leaves[persistent=true]"
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            for dy in range(-2, 3):
                if dx * dx + dz * dz + 1.6 * dy * dy <= 7.5 and free(x + dx, h + dy, z + dz):
                    put(x + dx, h + dy, z + dz, leaf)
    for dx, dz in ((2, 1), (-2, -1), (1, -2), (-1, 2)):
        for y in (h - 3, h - 2):
            if free(x + dx, y, z + dz):
                put(x + dx, y, z + dz, leaf)


def spruce(x, z, h):
    put(x, -1, z, "podzol")
    box(x, x, 0, h - 2, z, z, "spruce_log")
    radii = [0, 1, 1, 2, 1, 2, 2, 3, 2, 3]
    for y in range(2, h):
        r = radii[min(h - 1 - y, len(radii) - 1)]
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r + 1 and free(x + dx, y, z + dz):
                    put(x + dx, y, z + dz, "spruce_leaves[persistent=true]")


def lamp(x, z):
    box(x, x, 0, 3, z, z, "polished_blackstone_wall")
    put(x, 4, z, "ochre_froglight")


def bed(x0, x1, z0, z1):
    """Flower bed: leave the grass, add a white curb and scattered flowers."""
    box(x0, x1, -1, -1, z0, z1, None)
    for (a, b, c, d) in ring(x0, x1, z0, z1):
        box(a, b, 0, 0, c, d, "smooth_quartz_slab[type=bottom]")
    flowers = ("poppy", "oxeye_daisy", "azure_bluet", "dandelion", "grass")
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if (x * 7 + z * 13) % 3 == 0:
                put(x, 0, z, flowers[(x * 3 + z * 5) % 5])


def bust(x, z, rot):
    box(x - 1, x + 1, 0, 0, z - 1, z + 1, "polished_andesite")
    box(x, x, 1, 3, z, z, "polished_deepslate")
    put(x, 4, z, "polished_blackstone_wall")
    put(x, 5, z, f"wither_skeleton_skull[rotation={rot}]")


def bench(x, z, facing):
    along_z = facing in ("east", "west")
    for i in (0, 1):
        put(x + (0 if along_z else i), 0, z + (i if along_z else 0), f"warped_stairs[facing={facing},half=bottom]")


# streets on both sides, joined to the gym's road
for x0, mid in ((-14, -11), (84, 87)):
    box(x0, x0 + 6, -1, -1, -20, 66, ASPHALT)
    for z in range(-20, 67):
        if z % 4 < 2:
            put(mid, -1, z, "white_concrete")
box(-7, -6, -1, -1, -20, 66, "stone_bricks")
box(82, 83, -1, -1, -20, 66, "stone_bricks")
g.box(45, 55, -1, -1, 20, 21, "stone_bricks")
g.box(45, 55, -1, -1, 22, 28, ASPHALT)
for x in range(45, 56):
    if x % 4 < 2:
        g.put(x, -1, 25, "white_concrete")

box(53, 81, -1, -1, -14, 60, PAVE)                    # square in front of the entrance
box(2, 52, -1, -1, -6, -1, PAVE)                      # walk along the north side
box(-5, 1, -1, -1, 14, 30, PAVE)                      # driveway from the west street
box(-5, 1, -1, -1, 41, 43, PAVE)
box(53, 55, 0, 0, 0, 16, "smooth_stone")              # entrance porch and step
box(56, 56, 0, 0, -1, 17, "smooth_stone_slab[type=bottom]")
for z in (-1, 17):
    box(53, 55, 0, 0, z, z, "smooth_stone_slab[type=bottom]")
for z0 in (4, 12):
    box(53, 54, 1, 1, z0, z0 + 1, "gray_carpet")

bed(57, 61, 20, 50)                                   # planted strip along the facade
for z, h in ((23, 10), (31, 12), (39, 11), (47, 10)):
    spruce(59, z, h)
bed(66, 78, 4, 16)
bed(66, 78, 24, 42)
bust(72, 33, 4)
bed(63, 71, -11, -3)
bust(67, -7, 6)
spruce(61, -9, 11)
spruce(75, -8, 12)
for x, z in ((63, 1), (63, 20), (63, 46), (80, -12), (80, 20), (80, 46)):
    lamp(x, z)
bench(64, 9, "west")
bench(79, 30, "east")
bench(79, 8, "east")

# park to the south with the Wall of Memory along a paved path
box(-5, 81, -1, -1, 58, 59, "polished_granite")
box(52, 53, -1, -1, 53, 57, "polished_granite")
for x in range(6, 35, 7):
    box(x, x, 0, 3, 56, 56, "iron_bars")
for x0 in (7, 14, 21, 28):
    box(x0, x0 + 5, 1, 3, 56, 56, "light_blue_stained_glass_pane")
    label(x0 + 3, 3.25, 56.6, "z", "СТЕНА ПАМЯТИ", "#1F3A6E", 1.7, 1.7)
for x, z, h in ((0, 51, 7), (12, 63, 8), (26, 64, 7), (41, 63, 8), (47, 55, 7), (62, 64, 8)):
    tree(x, z, h)
bench(18, 60, "north")
bench(36, 60, "north")
lamp(3, 57)
lamp(44, 57)

# lawn on the west side, big trees to the north
for x, z, h in ((-3, 8, 8), (-3, 36, 8), (-3, 52, 7)):
    tree(x, z, h)
for x, z, h in ((30, -12, 9), (45, -13, 8)):
    tree(x, z, h, "oak")
tree(77, -17, 9)

# playground by the north-west corner
box(-4, 12, -1, -1, -18, -8, "sand")
for x in (2, 3):
    for z in (-14, -13):
        box(x, x, 0, 1, z, z, "oak_fence")
        put(x, 2, z, "oak_slab[type=bottom]")
put(4, 1, -14, "mangrove_stairs[facing=west,half=bottom]")
put(5, 0, -14, "mangrove_stairs[facing=west,half=bottom]")
put(1, 1, -13, "oak_stairs[facing=east,half=bottom]")
put(0, 0, -13, "oak_stairs[facing=east,half=bottom]")
for z in (-17, -11):
    box(8, 8, 0, 2, z, z, "oak_fence")
box(8, 8, 3, 3, -17, -11, "oak_fence")
for z in (-15, -13):
    box(8, 8, 1, 2, z, z, "chain[axis=y]")
bench(11, -10, "north")
bench(-2, -10, "north")
lamp(13, -7)

g.COLORS.update({
    "yellow_concrete": (241, 185, 40), "white_stained_glass_pane": (205, 215, 225),
    "light_gray_stained_glass_pane": (95, 105, 115), "red_concrete": (142, 33, 33),
    "white_terracotta": (210, 178, 161), "light_gray_concrete": (150, 150, 144), "spruce_log": (58, 37, 16),
    "birch_log": (216, 215, 210), "birch_leaves": (104, 150, 72), "oak_log": (102, 81, 50),
    "oak_leaves": (72, 130, 52), "sand": (219, 207, 163), "mangrove_stairs": (117, 54, 48),
    "red_wool": (160, 39, 34), "black_wool": (20, 21, 25), "white_wool": (233, 236, 236),
    "light_blue_wool": (58, 175, 217), "polished_granite": (154, 106, 89), "cut_sandstone": (200, 188, 140),
    "light_blue_stained_glass_pane": (150, 190, 225), "ochre_froglight": (250, 240, 180),
    "dark_oak_stairs": (67, 43, 20), "warped_stairs": (43, 104, 99), "warped_fence": (43, 104, 99),
    "poppy": (200, 40, 40), "oxeye_daisy": (230, 230, 230), "azure_bluet": (200, 220, 230),
    "dandelion": (250, 220, 50), "grass": (100, 150, 60), "polished_deepslate": (72, 72, 73),
    "oak_fence": (162, 130, 78), "oak_slab": (162, 130, 78), "oak_stairs": (162, 130, 78),
    "spruce_stairs": (115, 85, 49), "polished_blackstone_wall": (53, 49, 57), "bookshelf": (120, 90, 55),
})


def elevation(path, face, s=12):
    """Flat view of the building's east or west side; the block nearest the viewer wins."""
    from PIL import Image, ImageDraw
    best = {}
    for (x, y, z), b in g.B.items():
        x, z = x - OX, z - OZ
        if y < 0 or "light[" in b or not (0 <= x <= 54 and -2 <= z <= 54):
            continue
        depth = x if face == "east" else -x
        key = (z if face == "east" else 54 - z, y)
        if key not in best or depth > best[key][0]:
            best[key] = (depth, b)
    h = max(k[1] for k in best) + 1
    img = Image.new("RGB", (58 * s, h * s), (150, 190, 230))
    d = ImageDraw.Draw(img)
    for (u, y), (_, b) in best.items():
        u = 56 - (u + 2) if face == "east" else u + 2   # east face is seen with north on the right
        d.rectangle([u * s, (h - 1 - y) * s, (u + 1) * s - 2, (h - y) * s - 2], fill=g.color(b))
    img.save(path)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    cmds = g.commands()
    open(f"{out}/commands.txt", "w").write("\n".join(cmds) + "\n")
    json.dump([[x, y + Y0, z, b] for (x, y, z), b in g.B.items()], open(f"{out}/model.json", "w"))
    json.dump({"spawn": [OX + 80, Y0, OZ - 8, 45], "text_displays": len(g.SUMMONS)}, open(f"{out}/meta.json", "w"))
    print(len(g.B), "blocks,", len(cmds), "commands,", len(g.SUMMONS), "text displays")
    here = lambda x, y, z: x >= OX - 6
    g.render(f"{out}/dk_se.png", False, 9, here)
    g.render(f"{out}/dk_nw.png", True, 9, here)
    # auditorium with the roof and the south and east walls cut away
    g.render(f"{out}/dk_hall.png", False, 20,
             lambda x, y, z: 8 <= x - OX <= 38 and 10 <= z - OZ <= 36 and 0 <= y <= 11)
    elevation(f"{out}/dk_east.png", "east")
    elevation(f"{out}/dk_west.png", "west")
