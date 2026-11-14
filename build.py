"""Voxel model of the "Muraveynik" gym building.

Scale is roughly 1 block = 0.33 m. Axes: +x east (entrance facade), +z south
(long facade with the GYM sign). Row 0 is the first layer above the superflat
grass; row -1 replaces the grass itself.

Running this writes commands.txt (/fill commands), model.json and preview PNGs.
"""
import json
import sys

L, W = 92, 48          # footprint: x 0..L-1, z 0..W-1
TOP = 39               # last wall row below the parapet band
Y0 = -60               # world y of row 0
WIN_ROWS = (4, 19, 31)  # bottom row of the windows on each storey

BRICK = "bricks"
INFILL = "red_terracotta"
PLINTH = "polished_andesite"
TRIM = "smooth_quartz"
TRIM_TOP = "smooth_quartz_slab[type=top]"
TRIM_BOT = "smooth_quartz_slab[type=bottom]"
GLASS = "gray_stained_glass_pane"
LEAF = "spruce_leaves[persistent=true]"

B = {}


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
box(0, L - 1, 0, 42, W - 1, W - 1, BRICK)   # south, outer plane
box(0, L - 1, 0, TOP, W - 2, W - 2, BRICK)  # south, panel plane
box(0, L - 1, 0, 42, 0, 0, BRICK)           # north
box(0, L - 1, 0, TOP, 1, 1, BRICK)
box(L - 1, L - 1, 0, 42, 0, W - 1, BRICK)   # east (front), 2 thick
box(L - 2, L - 2, 0, TOP, 0, W - 1, BRICK)
box(0, 0, 0, 42, 0, W - 1, BRICK)           # west
for (x0, x1, z0, z1) in ((0, L - 1, W - 1, W - 1), (0, L - 1, 0, 0),
                         (L - 1, L - 1, 0, W - 1), (0, 0, 0, W - 1)):
    box(x0, x1, 0, 1, z0, z1, PLINTH)
    box(x0, x1, 43, 43, z0, z1, "deepslate_tile_slab[type=bottom]")

# floors, ceilings with flush lights, roof deck
box(1, L - 3, 0, 0, 2, W - 3, "gray_concrete")
for row in (15, 27, 39):
    box(1, L - 3, row, row, 2, W - 3, "smooth_stone")
    for x in range(5, L - 3, 7):
        for z in range(5, W - 3, 7):
            put(x, row, z, "sea_lantern")
box(1, L - 2, 40, 40, 1, W - 2, "gray_concrete")


# ---------------------------------------------------------------- long facades
def long_bay(x0, z_out, z_in):
    """Recessed 6-wide panel between pilasters with a window on each storey."""
    box(x0, x0 + 5, 2, TOP, z_out, z_out, None)
    for wb in WIN_ROWS:
        box(x0 + 1, x0 + 4, wb, wb + 5, z_in, z_in, GLASS)
        box(x0, x0 + 5, wb + 6, wb + 7, z_in, z_in, INFILL)  # bricked-up top of the old opening
        box(x0, x0 + 5, wb + 8, wb + 8, z_out, z_out, TRIM_BOT)
        box(x0 + 1, x0 + 4, wb - 1, wb - 1, z_out, z_out, TRIM_TOP)


for i in range(9):   # south: 9 bays, then the blank wall carrying the GYM sign
    long_bay(2 + 8 * i, W - 1, W - 2)
for i in range(11):  # north: bays along the whole length
    long_bay(2 + 8 * i, 0, 1)

# air conditioners on the south facade
for bay, row in ((2, 16), (5, 16), (7, 16), (3, 28)):
    x0 = 2 + 8 * bay
    box(x0 + 4, x0 + 5, row, row + 1, W - 1, W - 1, "white_concrete")

# ---------------------------------------------------------------- west facade
for z0 in (8, 22, 36):
    for wb in WIN_ROWS:
        box(0, 0, wb, wb + 5, z0, z0 + 3, GLASS)
        box(0, 0, wb + 6, wb + 6, z0 - 1, z0 + 4, TRIM)


# ---------------------------------------------------------------- front (east) facade
def zu(u):
    """Facade column u counted from the viewer's left (south corner)."""
    return W - 1 - u


def front_window(u0, wb):
    for u in range(u0, u0 + 4):
        for r in range(wb, wb + 6):
            put(L - 1, r, zu(u), None)
            put(L - 2, r, zu(u), GLASS)
        put(L, wb - 1, zu(u), TRIM_TOP)
    for u in range(u0 - 1, u0 + 5):
        put(L - 1, wb + 6, zu(u), TRIM)


for u0 in (6, 15):
    front_window(u0, WIN_ROWS[0])
for u0 in (6, 15, 27):
    front_window(u0, WIN_ROWS[1])
    front_window(u0, WIN_ROWS[2])

# entrance portal: stone surround, canopy, double door with glazing
for u in (26, 31):
    box(L - 1, L, 1, 9, zu(u), zu(u), "smooth_sandstone")
box(L - 1, L - 1, 9, 9, zu(31), zu(26), "smooth_sandstone")
box(L, L + 1, 10, 10, zu(32), zu(25), "dark_oak_slab[type=bottom]")
box(L, L, 9, 9, zu(30), zu(27), "dark_oak_planks")
box(L - 1, L - 1, 1, 8, zu(30), zu(27), None)
box(L - 2, L - 2, 1, 8, zu(30), zu(27), GLASS)
for u in (27, 30):
    box(L - 2, L - 2, 1, 6, zu(u), zu(u), "dark_oak_planks")
box(L - 2, L - 2, 6, 6, zu(30), zu(27), "dark_oak_planks")
box(L - 2, L - 2, 3, 3, zu(29), zu(28), "dark_oak_planks")
for u, hinge in ((28, "left"), (29, "right")):
    for row, half in ((1, "lower"), (2, "upper")):
        put(L - 2, row, zu(u), f"dark_oak_door[facing=west,half={half},hinge={hinge},open=false]")
for u in (25, 32):
    put(L + 1, 9, zu(u), "lantern[hanging=true]")

# "МУРАВЕЙНИК" in glowing letters across the facade
FONT = {
    "М": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "У": ["#.#", "#.#", "###", "..#", "##."],
    "Р": ["##.", "#.#", "##.", "#..", "#.."],
    "А": [".#.", "#.#", "###", "#.#", "#.#"],
    "В": ["##.", "#.#", "##.", "#.#", "##."],
    "Е": ["###", "#..", "##.", "#..", "###"],
    "И": ["#..#", "#.##", "##.#", "#..#", "#..#"],
    "Н": ["#.#", "#.#", "###", "#.#", "#.#"],
    "К": ["#.#", "#.#", "##.", "#.#", "#.#"],
}
u = 3
for ch in "МУРАВЕЙНИК":
    glyph = FONT["И" if ch == "Й" else ch]
    for r, line in enumerate(glyph):
        for c, px in enumerate(line):
            if px == "#":
                put(L, 16 - r, zu(u + c), "ochre_froglight")
    if ch == "Й":
        put(L, 17, zu(u + 1), "ochre_froglight")
        put(L, 17, zu(u + 2), "ochre_froglight")
    u += len(glyph[0]) + 1

# ---------------------------------------------------------------- GYM sign
GYM = [
    ["..#####..", ".#######.", "###...###", "###......", "###.#####", "###...###", ".#######.", "..#####.."],
    ["###...###", "###...###", ".###.###.", "..#####..", "...###...", "...###...", "...###...", "...###..."],
    ["###...###", "####.####", "#########", "###.#.###", "###...###", "###...###", "###...###", "###...###"],
]
letters = set()
for li, glyph in enumerate(GYM):
    for r, line in enumerate(glyph):
        for c, px in enumerate(line):
            if px == "#":
                letters.add((L - 14 + c, TOP - (li * 9 + r)))
# Black letters stand off the wall over a wider glowing backing, like the real halo-lit sign.
for (x, y) in letters:
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        put(x + dx, y + dy, W, "shroomlight")
for (x, y) in letters:
    put(x, y, W + 1, "black_concrete")

# ---------------------------------------------------------------- roof clutter
box(L - 4, L - 4, 41, 50, W - 4, W - 4, "iron_bars")
for (x, z) in ((20, 14), (48, 30), (70, 12)):
    box(x, x + 2, 41, 41, z, z + 2, "smooth_stone")
    put(x + 1, 42, z + 1, "stone_brick_wall")
box(34, 37, 41, 42, 20, 23, "bricks")
box(34, 37, 43, 43, 20, 23, "stone_brick_slab[type=bottom]")


# ---------------------------------------------------------------- site
def thuja(x, z, base, h):
    for i in range(h):
        put(x, base + i, z, LEAF)
        if 1 <= i <= h - 3:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(x + dx, base + i, z + dz, LEAF)


X0, X1 = -24, L + 44
box(X0, X1, -1, -1, W + 13, W + 23, "gray_concrete")          # road
box(X0, X1, -1, -1, W + 12, W + 12, "smooth_stone")           # curb
box(X0, X1, -1, -1, W + 9, W + 11, "stone_bricks")            # sidewalk
STRIPES = ["smooth_sandstone"] * 2 + ["stone_bricks"] * 3 + ["purple_terracotta"] * 2 + ["stone_bricks"]
for x in range(L, X1 + 1):                                    # striped plaza in front of the entrance
    for z in range(-10, W + 9):
        put(x, -1, z, STRIPES[(x + z) % 8])
for i in range(9):                                            # trees along the long facade
    thuja(8 + 8 * i, W + 5, 0, 9 if i % 2 else 7)
    put(8 + 8 * i, -1, W + 5, "podzol")

# porch with a step, doormat and bin
box(L, L + 4, 0, 0, zu(34), zu(23), "smooth_stone")
box(L + 5, L + 5, 0, 0, zu(35), zu(23), "smooth_stone_slab[type=bottom]")
box(L, L + 4, 0, 0, zu(35), zu(35), "smooth_stone_slab[type=bottom]")
box(L + 1, L + 2, 1, 1, zu(30), zu(27), "gray_carpet")
put(L, 1, zu(24), "cauldron")

# planted bed with three thujas left of the entrance
box(L, L + 3, 0, 0, zu(22), zu(3), "smooth_stone")
box(L, L + 2, 0, 0, zu(21), zu(4), "grass_block")
for u in (4, 12, 21):
    thuja(L + 1, zu(u), 1, 6)

# ---------------------------------------------------------------- output
def color(b):
    name = b.split("[")[0]
    table = {
        "bricks": (166, 92, 70), "red_terracotta": (143, 61, 46), "polished_andesite": (132, 135, 134),
        "smooth_quartz": (236, 230, 223), "smooth_quartz_slab": (236, 230, 223),
        "gray_stained_glass_pane": (52, 60, 70), "spruce_leaves": (58, 94, 58), "gray_concrete": (55, 58, 62),
        "smooth_stone": (159, 159, 159), "smooth_stone_slab": (159, 159, 159), "sea_lantern": (172, 200, 190),
        "deepslate_tile_slab": (54, 54, 55), "white_concrete": (207, 213, 214), "smooth_sandstone": (224, 214, 170),
        "dark_oak_slab": (67, 43, 20), "dark_oak_planks": (67, 43, 20), "dark_oak_door": (76, 51, 26),
        "lantern": (240, 190, 90), "ochre_froglight": (250, 240, 180), "shroomlight": (241, 147, 71),
        "black_concrete": (8, 10, 15), "iron_bars": (140, 140, 140), "stone_brick_wall": (122, 122, 122),
        "stone_brick_slab": (122, 122, 122), "stone_bricks": (122, 122, 122), "purple_terracotta": (118, 70, 86),
        "podzol": (91, 63, 24), "gray_carpet": (63, 68, 72), "cauldron": (74, 74, 74), "grass_block": (112, 160, 70),
    }
    return table[name]


def render(path, flip, crop=None, scale=6):
    """Isometric preview. flip=False looks from the south-east, True from the north-west."""
    from PIL import Image, ImageDraw
    vox = {((L - 1 - x, y, W - 1 - z) if flip else (x, y, z)): b for (x, y, z), b in B.items()}
    if crop:
        vox = {p: b for p, b in vox.items() if crop(*p)}
    s = scale

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
                      fill=(int(r * .82), int(g * .82), int(b * .82)))
        if (x + 1, y, z) not in vox:
            d.polygon([P(x + 1, y, z), P(x + 1, y, z + 1), P(x + 1, y + 1, z + 1), P(x + 1, y + 1, z)],
                      fill=(int(r * .64), int(g * .64), int(b * .64)))
    img.save(path)


def commands():
    """Merge the voxels into /fill boxes: runs along x, then stacked along z, then y."""
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
            key = (y, x0, x1, b)
            lst = slabs.setdefault(key, [])
            if lst and lst[-1][1] == z - 1:
                lst[-1][1] = z
            else:
                lst.append([z, z])
    boxes = {}
    for (y, x0, x1, b), zs in sorted(slabs.items(), key=lambda kv: kv[0][0]):
        for z0, z1 in zs:
            key = (x0, x1, z0, z1, b)
            lst = boxes.setdefault(key, [])
            if lst and lst[-1][1] == y - 1:
                lst[-1][1] = y
            else:
                lst.append([y, y])
    # Blocks that need support or neighbours (doors, carpet, lanterns, panes) go last.
    fragile = ("door", "carpet", "lantern[", "pane", "iron_bars", "wall")
    out = []
    for (x0, x1, z0, z1, b), ys in boxes.items():
        for y0, y1 in ys:
            late = any(f in b for f in fragile)
            out.append((late, y0, f"fill {x0} {y0 + Y0} {z0} {x1} {y1 + Y0} {z1} minecraft:{b}"))
    out.sort(key=lambda t: (t[0], t[1]))
    return [c for _, _, c in out]


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    cmds = commands()
    open(f"{out}/commands.txt", "w").write("\n".join(cmds) + "\n")
    json.dump([[x, y + Y0, z, b] for (x, y, z), b in B.items()], open(f"{out}/model.json", "w"))
    print(len(B), "blocks,", len(cmds), "commands")
    near = lambda x, y, z: -6 <= x <= L + 14 and -4 <= z <= W + 12
    render(f"{out}/preview_se.png", False, near)
    render(f"{out}/preview_nw.png", True, lambda x, y, z: -4 <= x <= L + 4 and -4 <= z <= W + 4)


def elevation(path, face, s=8):
    """Flat view of one facade: 'south' or 'east', nearest block wins."""
    from PIL import Image, ImageDraw
    best = {}
    for (x, y, z), b in B.items():
        if y < 0:
            continue
        key, depth = ((x, y), z) if face == "south" else ((W - 1 - z, y), x)
        if key not in best or depth > best[key][0]:
            best[key] = (depth, b)
    us = [k[0] for k in best]
    u0, w, h = min(us), max(us) - min(us) + 1, max(k[1] for k in best) + 1
    img = Image.new("RGB", (w * s, h * s), (150, 190, 230))
    d = ImageDraw.Draw(img)
    for (u, y), (_, b) in best.items():
        d.rectangle([(u - u0) * s, (h - 1 - y) * s, (u - u0 + 1) * s - 2, (h - y) * s - 2], fill=color(b))
    img.save(path)


if __name__ == "__main__":
    elevation(f"{out}/elev_south.png", "south")
    elevation(f"{out}/elev_east.png", "east")
