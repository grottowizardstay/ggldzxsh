"""Model of the "Muraveynik" gym building at 1 block = 1 m.

Axes: +x east (entrance facade), +z south (long facade with the GYM sign).
Row 0 is the first layer above the superflat grass; row -1 replaces the grass.

Running this writes commands.txt (/fill and /summon), model.json, meta.json and preview PNGs.
"""
import json
import sys

L, W = 31, 15           # footprint: x 0..L-1, z 0..W-1
FLOORS = (0, 4, 8)      # floor-slab row of each storey; windows sit on rows f+2..f+3
ROOF, PARAPET, CAP = 12, 13, 14
Y0 = -60                # world y of row 0

BRICK = "bricks"
INFILL = "red_terracotta"
GLASS = "gray_stained_glass_pane"
LINTEL = "smooth_quartz_slab[type=top]"
LEAF = "spruce_leaves[persistent=true]"

B = {}
SUMMONS = []


def put(x, y, z, b):
    if b is None:
        B.pop((x, y, z), None)
    else:
        B[(x, y, z)] = b


def box(x0, x1, y0, y1, z0, z1, b):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                put(x, y, z, b)


# ---------------------------------------------------------------- shell
for (x0, x1, z0, z1) in ((0, L - 1, W - 1, W - 1), (0, L - 1, 0, 0), (L - 1, L - 1, 0, W - 1), (0, 0, 0, W - 1)):
    box(x0, x1, 0, PARAPET, z0, z1, BRICK)
    box(x0, x1, 0, 0, z0, z1, "polished_andesite")
    box(x0, x1, CAP, CAP, z0, z1, "deepslate_tile_slab[type=bottom]")

box(1, 21, 0, 0, 1, W - 2, "gray_concrete")        # rubber gym floor
box(22, L - 2, 0, 0, 1, W - 2, "smooth_stone")     # lobby
box(1, L - 2, 4, 4, 1, W - 2, "spruce_planks")
box(1, L - 2, 8, 8, 1, W - 2, "birch_planks")
box(1, L - 2, ROOF, ROOF, 1, W - 2, "gray_concrete")


def window(cells, f, glazed=True):
    """cells: wall positions (x, z) of one opening on the storey whose floor row is f."""
    for (x, z) in cells:
        box(x, x, f + 2, f + 3, z, z, GLASS if glazed else INFILL)
        put(x, f + 4, z, LINTEL)   # half-height lintel; the floor slab behind closes the gap


# long facades: 8 bays of 2-wide windows between 1-wide piers, then a blank end wall
for i in range(8):
    xs = (1 + 3 * i, 2 + 3 * i)
    for f in FLOORS:
        window([(x, W - 1) for x in xs], f, glazed=not (i == 6 and f == 8))  # one bricked-up opening
        window([(x, 0) for x in xs], f)
for zs in ((3, 4), (10, 11)):
    for f in FLOORS:
        window([(0, z) for z in zs], f)


# ---------------------------------------------------------------- entrance facade (east)
def zu(u):
    """Facade column u counted from the viewer's left (south corner)."""
    return W - 1 - u


E = L - 1
for f, cols in ((0, ((1, 2), (4, 5))), (4, ((1, 2), (4, 5), (8, 9))), (8, ((1, 2), (8, 9)))):
    for us in cols:
        window([(E, zu(u)) for u in us], f)
window([(E, zu(4)), (E, zu(5))], 8, glazed=False)

# doorway: 2 wide, 3 high (double door plus glazed transom) in a stone surround
for u in (7, 10):
    box(E, E, 1, 3, zu(u), zu(u), "smooth_sandstone")
box(E, E, 4, 4, zu(10), zu(7), "smooth_sandstone")
box(E, E, 3, 3, zu(9), zu(8), GLASS)
for u, hinge in ((8, "left"), (9, "right")):
    for row, half in ((1, "lower"), (2, "upper")):
        put(E, row, zu(u), f"dark_oak_door[facing=west,half={half},hinge={hinge},open=false]")
box(L, L, 4, 4, zu(10), zu(7), "dark_oak_slab[type=bottom]")   # canopy
for u in (7, 10):
    put(L, 3, zu(u), "lantern[hanging=true]")


# ---------------------------------------------------------------- signs (text displays)
def text(x, y, z, yaw_axis, txt, color, sx, sy):
    """Text is one-sided, so summon it facing both ways along the axis; only the outward copy shows."""
    esc = "".join(c if ord(c) < 128 else "\\\\u%04x" % ord(c) for c in txt)
    for yaw in ((0, 180) if yaw_axis == "z" else (90, 270)):
        SUMMONS.append(
            f"summon minecraft:text_display {x:.2f} {y:.2f} {z:.2f} "
            f"{{Tags:[\"sign\"],Rotation:[{yaw}f,0f],billboard:\"fixed\",alignment:\"center\",background:0,shadow:0b,view_range:4f,"
            f"brightness:{{sky:15,block:15}},"
            f"text:'{{\"text\":\"{esc}\",\"color\":\"{color}\",\"bold\":true}}',"
            f"transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],"
            f"scale:[{sx}f,{sy}f,1f],right_rotation:[0f,0f,0f,1f]}}}}")


# "МУРАВЕЙНИК" between the ground and first floor windows, lit warm
text(L + 0.05, Y0 + 5.0, 8.0, "x", "МУРАВЕЙНИК", "#FFC15E", 5.4, 4)
for z in (4, 7, 10):
    put(L, 5, z, "light[level=11]")

# vertical GYM: black letters standing off the wall over an orange halo
GX = 28.0
for i, ch in enumerate("GYM"):
    y = Y0 + 9.5 - 2.6 * i
    for dx, dy in ((-.12, 0), (.12, 0), (0, -.12), (0, .12)):
        text(GX + dx, y + dy, W + 0.03, "z", ch, "#FF9A2E", 15, 12)
    text(GX, y, W + 0.12, "z", ch, "black", 15, 12)
    for x in (27, 28):
        put(x, 10 - 3 * i, W, "light[level=12]")


# ---------------------------------------------------------------- interior
# stairwell in the north-east corner: one straight flight per storey behind a brick partition
for f in (0, 4):
    for k in range(4):
        for z in (1, 2):
            put(28 - k, f + 1 + k, z, "stone_brick_stairs[facing=west,half=bottom]")
    box(26, 27, f + 4, f + 4, 1, 2, None)
for f in FLOORS:
    box(25, 28, f + 1, f + 3, 3, 3, BRICK)
box(28, 28, 9, 9, 1, 2, "iron_bars")   # guard rail above the top flight

for f in FLOORS:                       # ceiling lights
    for x in (3, 7, 11, 15, 19):
        for z in (4, 10):
            put(x, f + 3, z, "lantern[hanging=true]")
    put(26, f + 3, 8, "lantern[hanging=true]")

# ground floor: lobby with reception, weights room
box(22, 22, 1, 3, 1, W - 2, BRICK)
box(22, 22, 1, 3, 6, 8, None)
box(24, 24, 1, 1, 10, 12, "dark_oak_planks")
box(25, 26, 1, 1, 10, 10, "dark_oak_planks")
put(24, 2, 12, "potted_fern")
put(29, 1, 8, "potted_fern")
for x in (3, 8):                       # squat racks with a bench
    for z in (3, 5):
        box(x, x, 1, 2, z, z, "iron_bars")
    put(x, 2, 4, "chain[axis=z]")
    box(x, x + 1, 1, 1, 4, 4, "blackstone_slab[type=bottom]")
box(12, 15, 1, 1, 1, 1, "anvil[facing=east]")   # dumbbell rack
for x in (3, 6, 9, 12):                # treadmills facing the windows
    box(x, x, 1, 1, 11, 12, "black_carpet")
    put(x, 1, 13, "iron_bars")
for z in (4, 8):                       # punching bags
    put(18, 3, z, "chain[axis=y]")
    put(18, 2, z, "red_nether_brick_wall")

# first floor: boxing ring and benches
box(5, 9, 5, 5, 5, 9, "red_carpet")
for x in (4, 10):
    for z in (4, 10):
        box(x, x, 5, 6, z, z, "polished_blackstone_wall")
    box(x, x, 6, 6, 5, 9, "chain[axis=z]")
for z in (4, 10):
    box(5, 9, 6, 6, z, z, "chain[axis=x]")
for x in (14, 17, 20):
    box(x, x, 5, 5, 3, 4, "blackstone_slab[type=bottom]")
box(13, 18, 5, 5, 13, 13, "anvil[facing=north]")

# second floor: studio with mats
MATS = ("lime_carpet", "light_blue_carpet", "magenta_carpet", "orange_carpet")
for n, x in enumerate(range(3, 20, 3)):
    for z0 in (4, 9):
        box(x, x, 9, 9, z0, z0 + 1, MATS[(n + z0) % 4])

# ---------------------------------------------------------------- facade and roof fittings
for x, row in ((8, 5), (17, 5), (20, 5), (11, 9)):         # air conditioners under windows
    put(x, row, W, "smooth_quartz_slab[type=top]")
for x in (21, 24):                                         # downpipes
    box(x, x, 1, 3, W, W, "lightning_rod[facing=up]")
box(0, 18, 4, 4, W, W + 1, "light_gray_stained_glass")     # lean-to canopy along the long side
for x in range(0, 19, 3):
    box(x, x, 0, 3, W + 1, W + 1, "iron_bars")
box(28, 28, 13, 16, 12, 12, "iron_bars")                   # roof mast
put(28, 17, 12, "lightning_rod[facing=up]")
for (x, z) in ((6, 4), (15, 9), (22, 5)):                  # vents
    put(x, 13, z, "smooth_stone")
    put(x, 14, z, "stone_brick_wall")
box(26, 27, 13, 13, 1, 2, BRICK)                           # roof hatch
box(26, 27, 14, 14, 1, 2, "stone_brick_slab[type=bottom]")

# ---------------------------------------------------------------- site
X0, X1 = -8, L + 13
box(X0, X1, -1, -1, 20, 21, "stone_bricks")                # sidewalk
box(X0, X1, -1, -1, 22, 28, "gray_concrete")               # road
for x in range(X0, X1 + 1):
    if x % 4 < 2:
        put(x, -1, 25, "white_concrete")
STRIPES = ["smooth_sandstone"] * 2 + ["stone_bricks"] * 3 + ["purple_terracotta"] * 2 + ["stone_bricks"]
for x in range(L, X1 + 1):                                 # striped plaza in front of the entrance
    for z in range(-4, 20):
        put(x, -1, z, STRIPES[(x + z) % 8])

box(L, L + 1, 0, 0, zu(11), zu(6), "smooth_stone")         # porch with steps, doormat and bin
box(L + 2, L + 2, 0, 0, zu(12), zu(5), "smooth_stone_slab[type=bottom]")
for u in (5, 12):
    box(L, L + 1, 0, 0, zu(u), zu(u), "smooth_stone_slab[type=bottom]")
box(L, L, 1, 1, zu(9), zu(8), "gray_carpet")
put(L, 1, zu(6), "cauldron")

box(L, L + 1, -1, -1, zu(4), zu(0), "podzol")              # planted bed left of the entrance
for u in (0, 2, 4):
    box(L + 1, L + 1, 0, 1 + (u == 2), zu(u), zu(u), LEAF)

for n, x in enumerate(range(2, 23, 4)):                    # thujas along the long facade
    put(x, -1, 18, "podzol")
    box(x, x, 0, 3 + n % 2, 18, 18, LEAF)
box(24, 24, 0, 5, 18, 18, "andesite_wall")                 # floodlight pole
put(24, 6, 18, "pearlescent_froglight")


# ---------------------------------------------------------------- output
COLORS = {
    "bricks": (166, 92, 70), "red_terracotta": (143, 61, 46), "polished_andesite": (132, 135, 134),
    "smooth_quartz_slab": (236, 230, 223), "gray_stained_glass_pane": (52, 60, 70), "spruce_leaves": (58, 94, 58),
    "gray_concrete": (55, 58, 62), "smooth_stone": (159, 159, 159), "smooth_stone_slab": (159, 159, 159),
    "deepslate_tile_slab": (54, 54, 55), "white_concrete": (207, 213, 214), "smooth_sandstone": (224, 214, 170),
    "dark_oak_slab": (67, 43, 20), "dark_oak_planks": (67, 43, 20), "dark_oak_door": (76, 51, 26),
    "lantern": (240, 190, 90), "iron_bars": (140, 140, 140), "stone_brick_wall": (122, 122, 122),
    "stone_brick_slab": (122, 122, 122), "stone_bricks": (122, 122, 122), "stone_brick_stairs": (122, 122, 122),
    "purple_terracotta": (118, 70, 86), "podzol": (91, 63, 24), "gray_carpet": (63, 68, 72), "cauldron": (74, 74, 74),
    "spruce_planks": (115, 85, 49), "birch_planks": (192, 175, 121), "light_gray_stained_glass": (185, 190, 195),
    "lightning_rod": (190, 110, 80), "andesite_wall": (132, 135, 134), "pearlescent_froglight": (245, 235, 240),
}


def color(b):
    return COLORS.get(b.split("[")[0], (90, 90, 90))


def render(path, flip, s=14):
    """Isometric preview. flip=False looks from the south-east, True from the north-west."""
    from PIL import Image, ImageDraw
    vox = {((L - 1 - x, y, W - 1 - z) if flip else (x, y, z)): b for (x, y, z), b in B.items() if "light[" not in b}

    def proj(x, y, z):
        return ((x - z) * s, (x + z) * s // 2 - y * s)

    pts = [proj(x + a, y + b, z + c) for (x, y, z) in vox for a in (0, 1) for b in (0, 1) for c in (0, 1)]
    minx, miny = min(p[0] for p in pts), min(p[1] for p in pts)
    img = Image.new("RGB", (max(p[0] for p in pts) - minx + 1, max(p[1] for p in pts) - miny + 1), (150, 190, 230))
    d = ImageDraw.Draw(img)

    def P(x, y, z):
        px, py = proj(x, y, z)
        return (px - minx, py - miny)

    for (x, y, z) in sorted(vox, key=lambda p: (p[0] + p[2], p[1])):
        r, g, b = color(vox[(x, y, z)])
        if (x, y + 1, z) not in vox:
            d.polygon([P(x, y + 1, z), P(x + 1, y + 1, z), P(x + 1, y + 1, z + 1), P(x, y + 1, z + 1)], fill=(r, g, b))
        if (x, y, z + 1) not in vox:
            d.polygon([P(x, y, z + 1), P(x + 1, y, z + 1), P(x + 1, y + 1, z + 1), P(x, y + 1, z + 1)],
                      fill=(int(r * .82), int(g * .82), int(b * .82)), outline=(int(r * .7), int(g * .7), int(b * .7)))
        if (x + 1, y, z) not in vox:
            d.polygon([P(x + 1, y, z), P(x + 1, y, z + 1), P(x + 1, y + 1, z + 1), P(x + 1, y + 1, z)],
                      fill=(int(r * .64), int(g * .64), int(b * .64)), outline=(int(r * .55), int(g * .55), int(b * .55)))
    img.save(path)


def plan(path, lo, hi, s=20):
    """Top-down cut of the building showing rows lo..hi (highest block wins)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (L * s, W * s), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for x in range(L):
        for z in range(W):
            for y in range(hi, lo - 1, -1):
                if (x, y, z) in B:
                    d.rectangle([x * s, z * s, x * s + s - 2, z * s + s - 2], fill=color(B[(x, y, z)]))
                    break
    img.save(path)


def commands():
    """Merge the blocks into /fill boxes: runs along x, then stacked along z, then y."""
    runs = {}
    for (x, y, z) in sorted(B, key=lambda p: (p[1], p[2], p[0])):
        b = B[(x, y, z)]
        prev = runs.get((y, z))
        if prev and prev[-1][1] == x - 1 and prev[-1][2] == b:
            prev[-1][1] = x
        else:
            runs.setdefault((y, z), []).append([x, x, b])
    slabs = {}
    for (y, z), rs in sorted(runs.items()):
        for x0, x1, b in rs:
            lst = slabs.setdefault((y, x0, x1, b), [])
            if lst and lst[-1][1] == z - 1:
                lst[-1][1] = z
            else:
                lst.append([z, z])
    boxes = {}
    for (y, x0, x1, b), zs in sorted(slabs.items(), key=lambda kv: kv[0][0]):
        for z0, z1 in zs:
            lst = boxes.setdefault((x0, x1, z0, z1, b), [])
            if lst and lst[-1][1] == y - 1:
                lst[-1][1] = y
            else:
                lst.append([y, y])
    # Blocks that need support or connect to neighbours go last.
    fragile = ("door", "carpet", "lantern[", "pane", "iron_bars", "wall", "potted", "chain", "anvil", "light[")
    out = []
    for (x0, x1, z0, z1, b), ys in boxes.items():
        for y0, y1 in ys:
            out.append((any(f in b for f in fragile), y0,
                        f"fill {x0} {y0 + Y0} {z0} {x1} {y1 + Y0} {z1} minecraft:{b}"))
    out.sort(key=lambda t: (t[0], t[1]))
    return [c for _, _, c in out] + SUMMONS


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    cmds = commands()
    open(f"{out}/commands.txt", "w").write("\n".join(cmds) + "\n")
    json.dump([[x, y + Y0, z, b] for (x, y, z), b in B.items()], open(f"{out}/model.json", "w"))
    json.dump({"spawn": [L + 9, Y0, 19, 135], "text_displays": len(SUMMONS)}, open(f"{out}/meta.json", "w"))
    print(len(B), "blocks,", len(cmds), "commands,", len(SUMMONS), "text displays")
    render(f"{out}/preview_se.png", False)
    render(f"{out}/preview_nw.png", True)
    for n, f in enumerate(FLOORS):
        plan(f"{out}/plan_{n}.png", f, f + 3)
