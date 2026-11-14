"""Writes the gym models, blockstate, loot table and item tag.

Run from the repository root:  python3 tools/gen_models.py
"""
import json
import math
import os

RES = os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'resources')
NS = 'kalabushkin'
TEXTURES = {
    'steel': f'{NS}:block/gym_steel',
    'frame': f'{NS}:block/gym_frame',
    'rubber': f'{NS}:block/gym_rubber',
    'knurl': f'{NS}:block/gym_knurl',
    'vinyl': f'{NS}:block/gym_vinyl',
    'wrap': f'{NS}:item/wrist_wraps_side',
    'wrap_top': f'{NS}:item/wrist_wraps_top',
}


def write(path, data):
    full = os.path.join(RES, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent='\t') + '\n')


def r(value):
    return round(value, 4)


def box(frm, to, tex, angle=0.0, full=(), faces=None):
    """A cuboid. Faces get a UV area matching their size, so every material keeps one texel density.

    `full` lists faces that show the whole texture instead; `angle` turns the box around the X axis.
    """
    (x1, y1, z1), (x2, y2, z2) = frm, to
    sizes = {'north': (x2 - x1, y2 - y1), 'south': (x2 - x1, y2 - y1), 'east': (z2 - z1, y2 - y1),
             'west': (z2 - z1, y2 - y1), 'up': (x2 - x1, z2 - z1), 'down': (x2 - x1, z2 - z1)}
    out = {}
    for side, (w, h) in sizes.items():
        texture = (faces or {}).get(side, tex)
        uv = [0, 0, 16, 16] if side in full else [0, 0, r(min(16, w)), r(min(16, h))]
        out[side] = {'uv': uv, 'texture': '#' + texture}
    element = {'from': [r(v) for v in frm], 'to': [r(v) for v in to], 'faces': out}
    if angle:
        element['rotation'] = {'origin': [8, 8, 8], 'axis': 'x', 'angle': angle}
    return element


def disc(x1, x2, apothem, tex, sides=16):
    """A regular polygon prism around the X axis through the model centre, built from flat boxes."""
    half = apothem * math.tan(math.pi / sides)
    angles = [0.0, 22.5, 45.0, -22.5, -45.0] if sides == 16 else [0.0, 45.0, -45.0]
    crossed = [0.0, 22.5, -22.5] if sides == 16 else [0.0]
    boxes = [(apothem, half, a) for a in angles] + [(half, apothem, a) for a in crossed]
    elements = []
    for i, (hy, hz, angle) in enumerate(boxes):
        inset = 0.012 * i  # keeps the flat ends of the boxes from z-fighting
        elements.append(box([x1 + inset, 8 - hy, 8 - hz], [x2 - inset, 8 + hy, 8 + hz], tex, angle))
    return elements


def mirrored(elements):
    """The same elements on the other side of the model centre (x -> 16 - x)."""
    out = []
    for e in elements:
        m = json.loads(json.dumps(e))
        m['from'][0], m['to'][0] = r(16 - e['to'][0]), r(16 - e['from'][0])
        out.append(m)
    return out


def model(elements, display, particle):
    used = {face['texture'][1:] for e in elements for face in e['faces'].values()}
    textures = {name: TEXTURES[name] for name in sorted(used)}
    textures['particle'] = TEXTURES[particle]
    return {'textures': textures, 'elements': elements, 'display': display}


def view(rotation, translation, scale):
    return {'rotation': rotation, 'translation': translation, 'scale': [scale] * 3}


# --- Barbell: a 36 px bar along X with two rubber plates and a clamp on each sleeve. ---
side = (disc(-10, -2.5, 1.0, 'steel', 8) + disc(-2.5, -1.7, 1.8, 'steel', 8)
        + disc(-5.0, -2.6, 6.3, 'rubber') + disc(-7.2, -5.1, 5.0, 'rubber')
        + disc(-8.3, -7.3, 3.2, 'frame') + disc(-9.4, -8.4, 1.7, 'steel', 8))
barbell = ([box([-2.5, 7.45, 7.45], [18.5, 8.55, 8.55], 'steel'),
            box([0.5, 7.4, 7.4], [5.5, 8.6, 8.6], 'knurl'),
            box([10.5, 7.4, 7.4], [15.5, 8.6, 8.6], 'knurl')]
           + side + mirrored(side))
write(f'assets/{NS}/models/item/barbell.json', model(barbell, {
    'gui': view([25, -40, 0], [0, 0, 0], 0.42),
    'ground': view([0, 0, 0], [0, 2, 0], 0.5),
    'fixed': view([0, 0, 0], [0, 0, 0], 0.44),
    'head': view([0, 0, 0], [0, 0, 0], 0.6),
    'thirdperson_righthand': view([0, 90, 0], [0, 1, 1], 0.6),
    'thirdperson_lefthand': view([0, 90, 0], [0, 1, 1], 0.6),
    'firstperson_righthand': view([0, 60, 0], [2, 3, -3], 0.4),
    'firstperson_lefthand': view([0, 60, 0], [2, 3, -3], 0.4),
}, 'steel'))

# --- Dumbbell: knurled handle along X between two octagonal rubber heads. ---
head = disc(2.5, 5.5, 2.6, 'rubber', 8) + disc(5.5, 5.9, 1.3, 'steel', 8) + disc(2.3, 2.5, 1.4, 'steel', 8)
dumbbell = disc(5.5, 10.5, 0.7, 'knurl', 8) + head + mirrored(head)
write(f'assets/{NS}/models/item/dumbbell.json', model(dumbbell, {
    'gui': view([25, -40, 0], [0, 0, 0], 1.2),
    'ground': view([0, 0, 0], [0, 2, 0], 0.7),
    'fixed': view([0, 0, 0], [0, 0, 0], 1.2),
    'thirdperson_righthand': view([0, 0, 0], [0, 0.5, 0.5], 0.8),
    'thirdperson_lefthand': view([0, 0, 0], [0, 0.5, 0.5], 0.8),
    'firstperson_righthand': view([0, 0, 0], [1, 3, -1], 0.7),
    'firstperson_lefthand': view([0, 0, 0], [1, 3, -1], 0.7),
}, 'rubber'))

# --- Wrist wraps: two rolled wraps standing side by side, each with its thumb loop. ---
sides = ('north', 'south', 'east', 'west')
tops = {'up': 'wrap_top', 'down': 'wrap_top'}
roll = [box([1.5, 2, 5], [7, 10, 11], 'wrap', full=sides + ('up', 'down'), faces=tops),
        box([3.2, 10, 7.5], [3.8, 13, 8.5], 'rubber'),
        box([3.2, 13, 7.5], [5.3, 13.6, 8.5], 'rubber'),
        box([4.7, 10, 7.5], [5.3, 13, 8.5], 'rubber')]
write(f'assets/{NS}/models/item/wrist_wraps.json', model(roll + mirrored(roll), {
    'gui': view([25, -30, 0], [0, 0.5, 0], 0.95),
    'ground': view([0, 0, 0], [0, 2, 0], 0.5),
    'fixed': view([0, 0, 0], [0, 0, 0], 0.9),
    'thirdperson_righthand': view([0, 0, 0], [0, 2, 1], 0.5),
    'thirdperson_lefthand': view([0, 0, 0], [0, 2, 1], 0.5),
    'firstperson_righthand': view([0, -20, 0], [1, 3, 0], 0.6),
    'firstperson_lefthand': view([0, -20, 0], [1, 3, 0], 0.6),
}, 'wrap'))

write(f'assets/{NS}/models/item/masculine_tee.json',
      {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{NS}:item/masculine_tee'}})

# --- Weight bench. Both halves are drawn for FACING=north: the head half ends at z=0. ---
PAD_FULL = ('up',)


def pair(element):
    return [element] + mirrored([element])


bench_head = ([
    box([3, 7.5, 2], [13, 10, 16], 'vinyl', full=PAD_FULL),
    box([3.5, 7, 2.5], [12.5, 7.5, 16], 'frame'),
    box([6.75, 5, 1], [9.25, 7, 16], 'frame'),
    box([0, 0, 2.75], [16, 1.25, 5.25], 'frame'),
    box([2.5, 4.5, 3.25], [13.5, 6.5, 4.75], 'frame'),
] + pair(box([0.5, 1.25, 3], [2.5, 15.6, 5], 'frame'))
  + pair(box([0.4, 15.6, 2.9], [2.6, 16, 5.1], 'rubber'))
  + pair(box([0.75, 12.5, 5], [2.25, 13.25, 7.5], 'steel'))
  + pair(box([0.75, 13.25, 6.9], [2.25, 14.5, 7.5], 'steel'))
  + pair(box([-0.3, 0, 2.65], [0, 1.35, 5.35], 'rubber')))

bench_foot = ([
    box([3, 7.5, 0], [13, 10, 13], 'vinyl', full=PAD_FULL),
    box([3.5, 7, 0], [12.5, 7.5, 12.5], 'frame'),
    box([6.75, 5, 0], [9.25, 7, 12], 'frame'),
    box([6.75, 1.25, 9.5], [9.25, 5, 12], 'frame'),
    box([2, 0, 9.25], [14, 1.25, 12.25], 'frame'),
] + pair(box([1.7, 0, 9.15], [2, 1.35, 12.35], 'rubber')))


def block_model(elements):
    data = model(elements, {}, 'frame')
    del data['display']
    data['parent'] = 'minecraft:block/block'
    return data


write(f'assets/{NS}/models/block/weight_bench_head.json', block_model(bench_head))
write(f'assets/{NS}/models/block/weight_bench_foot.json', block_model(bench_foot))

# The item shows the whole bench: the foot half moved behind the head half, then centred.
whole = []
for part, shift in ((bench_head, -8), (bench_foot, 8)):
    for e in part:
        moved = json.loads(json.dumps(e))
        moved['from'][2] = r(e['from'][2] + shift)
        moved['to'][2] = r(e['to'][2] + shift)
        whole.append(moved)
write(f'assets/{NS}/models/item/weight_bench.json', model(whole, {
    'gui': view([30, 135, 0], [0, 1.5, 0], 0.4),
    'ground': view([0, 0, 0], [0, 2, 0], 0.3),
    'fixed': view([0, 90, 0], [0, 0, 0], 0.4),
    'thirdperson_righthand': view([75, 45, 0], [0, 2.5, 0], 0.25),
    'thirdperson_lefthand': view([75, 45, 0], [0, 2.5, 0], 0.25),
    'firstperson_righthand': view([0, 135, 0], [0, 2, 0], 0.3),
    'firstperson_lefthand': view([0, 135, 0], [0, 2, 0], 0.3),
}, 'frame'))

variants = {}
for facing, y in (('north', 0), ('east', 90), ('south', 180), ('west', 270)):
    for part in ('head', 'foot'):
        variant = {'model': f'{NS}:block/weight_bench_{part}'}
        if y:
            variant['y'] = y
        variants[f'facing={facing},part={part}'] = variant
write(f'assets/{NS}/blockstates/weight_bench.json', {'variants': variants})

# Only the head half drops the bench, so breaking either half yields exactly one.
write(f'data/{NS}/loot_table/blocks/weight_bench.json', {
    'type': 'minecraft:block',
    'pools': [{
        'rolls': 1,
        'entries': [{
            'type': 'minecraft:item', 'name': f'{NS}:weight_bench',
            'conditions': [{'condition': 'minecraft:block_state_property', 'block': f'{NS}:weight_bench',
                            'properties': {'part': 'head'}}],
        }],
        'conditions': [{'condition': 'minecraft:survives_explosion'}],
    }],
})

write(f'data/{NS}/tags/item/hand_wear.json', {'values': [f'{NS}:wrist_wraps']})
