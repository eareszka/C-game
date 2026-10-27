"""The wasteland's new props: twelve more for its roster, one function each, in its three
groups that never mix -- the volcano groves, the rubble by the void, and the remains.

    python art/structures/props/wasteland/waste_design.py              # every prop
    python art/structures/props/wasteland/waste_design.py red_figure   # one

Each writes art/structures/props/wasteland/<name>.png. The list was approved by the user on
2026-10-27 (sizes in cells, looks, drops); PixelLab drafts under pixellab-out/waste-new-*/
gave the shapes. The volcanoes and rubble already there are volcano_design.py and
rubble_design.py.

Objects keep the objects' rule (OVERWORLD_STYLE.md): one black line round the silhouette,
three colours and black, the light sparse and high on the left, the dark massed low and on
the right. The overhaul's materials (art/concept/wasteland/): the volcanoes' red rock, the
waste stone a step darker than the towns', bone, rust, and the void's glow -- a purple
light, the one new material. The fallen wall and the snapped pillar are built, in the
houses' projection. No cell holds more than four colours, black among them (keep4).
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.join(HERE, '..', 'forest'))
sys.path.insert(0, os.path.join(HERE, '..', 'snow'))
from entrance_shapes import Scene
from forest_design import blank, outline, typed, stroke, ellipse, write
from snow_design import piece, keep4, shard

# tools/overworld_style.py MATERIALS
RED = ('ec8476', 'b70000', '7c0a1b')        # red rock
STONE = ('9797aa', '595965', '34343e')      # waste stone
BONE = ('e8e0c0', 'b2966a', '8d6b4f')
RUST = ('764c20', '3e1c0e')
GLOW = ('b69cee', '664b95')                 # void glow

P_RED = {'l': RED[0], 'm': RED[1], 'd': RED[2], 'K': '000000'}
P_STONE = {'l': STONE[0], 'm': STONE[1], 'd': STONE[2], 'K': '000000'}
P_BONE = {'l': BONE[0], 'm': BONE[1], 'd': BONE[2], 'K': '000000'}


def blob(W, H, cx, cy, rx, ry, flat=None, lit=-0.9, dark=0.5):
    """An ellipse lit at its upper left, its lower right in shade; flat: the row it is cut at."""
    p = blank(W, H)
    inside = ellipse(cx, cy, rx, ry)
    for y in range(H):
        for x in range(W):
            if inside(x, y) and (flat is None or y <= flat):
                u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                p[y][x] = 'l' if u + v < lit else 'd' if u + v > dark or (flat is not None and y >= flat) else 'm'
    return p


# ---------------------------------------------------------------- volcano groves
def fissure_vent():
    """A low cracked mound of red rock, a black fissure zigzagging down its middle."""
    W = H = 16
    g = blank(W, H)
    piece(g, blob(W, H, 8, 13, 6.5, 8, flat=13))
    for x, y in ((7, 6), (8, 6), (8, 7), (7, 8), (8, 8), (7, 9), (8, 9), (8, 10), (9, 10), (8, 11),
                 (9, 11), (9, 12), (10, 12), (9, 13), (10, 13)):            # the fissure, two wide
        g[y][x] = 'K'
    for x, y in ((6, 6), (6, 7), (6, 8), (6, 9), (7, 10), (7, 11)):          # its left lip catching the light
        g[y][x] = 'l'
    return keep4(outline(g), P_RED), P_RED


def cinder_shards():
    """Jagged shards of dark red volcanic glass breaking out of the ground."""
    W = H = 16
    g = blank(W, H)
    piece(g, shard(W, H, 9, 13, 13, 13, 6))
    piece(g, shard(W, H, 2, 6, 13, 2, 5))
    piece(g, shard(W, H, 5, 10, 13, 8, 2))
    piece(g, shard(W, H, 9, 12, 13, 10, 9))
    return keep4(outline(g), P_RED), P_RED


def scorched_boulder():
    """A wide low slab of red rock, cracked across and pitted."""
    W, H = 32, 16
    g = blank(W, H)
    piece(g, blob(W, H, 17, 11, 13, 7, flat=13))
    piece(g, blob(W, H, 6, 12, 4, 3.2, flat=13))
    for x, y in ((14, 7), (15, 8), (15, 9), (16, 10), (17, 11), (17, 12)):    # a crack
        g[y][x] = 'K'
    for x, y in ((21, 8), (24, 10), (11, 10), (26, 7)):                        # pits
        g[y][x] = 'K'
    return keep4(outline(g), P_RED), P_RED


# ---------------------------------------------------------------- rubble by the void
def stone_tones(g):
    return [[{'L': 'l', 'M': 'm', 'D': 'd'}.get(c, c) for c in r] for r in g.rows()]


def fallen_wall():
    """A long length of the maze's wall lying toppled: its face in courses toward us, its top
    lit, its right end in shade, both ends broken off."""
    sc = Scene(48, 16, base=14)
    sc.break_off([0], 3, 12, 5, 2, 3)                          # its left end broken down
    sc.box(0, 3, 41, 0, 3, 0, 9)
    g = stone_tones(sc.render())
    for x, y in ((40, 13), (41, 13), (42, 13), (43, 13), (41, 12), (42, 12)):   # a fallen block at its end
        if g[y][x] == '.':
            g[y][x] = 'd'
    return keep4(outline(g), P_STONE), P_STONE


def snapped_pillar():
    """A round column snapped off at chest height, its broken top jagged, on a square plinth."""
    sc = Scene(16, 32, base=29)
    sc.break_off([1], 4, 11, 12, 3, 7)                         # snapped, jagged
    sc.box(0, 3, 11, 0, 2, 0, 3, front='M')                        # the plinth
    sc.box(1, 5, 10, 1, 1, 3, 22, front='column')                  # the shaft
    g = stone_tones(sc.render())
    return keep4(outline(g), P_STONE), P_STONE


def void_rock():
    """A grey rock the void has seeped into, purple light running in its cracks."""
    W = H = 16
    g = blank(W, H)
    piece(g, blob(W, H, 8, 10, 6.5, 5, flat=13, lit=-2))
    for x, y in ((3, 8), (4, 8), (5, 9), (6, 9), (7, 10), (8, 10), (9, 11), (10, 12), (10, 13),
                 (8, 7), (8, 6), (9, 6), (10, 6), (11, 7), (12, 8), (6, 11), (5, 12)):
        g[y][x] = 'v'                                          # veins of the void's light
    pal = {'m': STONE[1], 'd': STONE[2], 'v': GLOW[0], 'K': '000000', 'l': STONE[1]}
    return keep4(outline(g), pal), pal


def bone_pile():
    """A small heap of bones, long ones crossed, a skull on top."""
    W = H = 16
    g = blank(W, H)
    bone = lambda x, y, t, side: 'l' if side < 0.2 else 'd'
    for pts in ([(3, 13, 2.0), (12, 11, 2.0)], [(3.5, 10, 2.0), (12, 13, 2.0)], [(5, 12, 1.8), (11, 9, 1.8)]):
        part = blank(W, H)
        stroke(part, pts, 'm', bone)
        piece(g, part)
    skull = [list(r) for r in [".KKKKK.",
                   "KlllmdK",
                   "KKlKKdK",
                   "KKlKKdK",
                   ".KmdmK.",
                   "..KKK.."]]
    for j, r in enumerate(skull):
        for i, c in enumerate(r):
            if c != '.':
                g[3 + j][5 + i] = c
    return keep4(outline(g), P_BONE), P_BONE


# ---------------------------------------------------------------- remains
def spine_arch():
    """A giant creature's backbone arching out of the ground and back into it: vertebrae
    along the arc, a spike rising from each, the nearer drawn over the farther."""
    W, H = 48, 32
    g = blank(W, H)
    cx, cy, rx, ry = 24, 31, 20, 22
    n = 11
    for k in range(n):
        a = math.pi * (k + 0.5) / n
        x, y = cx - rx * math.cos(a), cy - ry * math.sin(a)
        r = 3.2 - 0.9 * abs(k - n / 2) / (n / 2)
        spike = blank(W, H)
        nx, ny = -math.cos(a) * 0.35, -1.0                          # the spike leans up and back
        stroke(spike, [(x, y, 1.8), (x + nx * 5, y + ny * 5, 0.8)], 'm',
               lambda x_, y_, t, side: 'l' if side < 0 else 'd')
        piece(g, spike)
        part = blob(W, H, x, y, r, r * 0.85, lit=-0.7, dark=0.6)
        piece(g, part)
    for y in range(H):                                             # sunk in the ground
        if y >= 30:
            g[y] = ['.'] * W
    return keep4(outline(g), P_BONE), P_BONE


def red_figure():
    """A faceless red figure standing still, thin, arms at its sides -- a statue from the
    dream (the reference board's red figures)."""
    g = typed(["................",
               "......KKKK......",
               ".....KllmmK.....",
               ".....KlmmdK.....",
               ".....KlmmdK.....",
               "......KmdK......",
               ".....KKmdKK.....",
               "....KlmmmmdK....",
               "...KlmmmmmddK...",
               "...KlmmmmmddK...",
               "...KlKmmmmKdK...",
               "...KlKmmmmKdK...",
               "...KlKmmmmKdK...",
               "...KlKmmmmKdK...",
               "...KlKmmmmKdK...",
               "...KmKmmmmKdK...",
               "...KKKmmmdKKK...",
               ".....KmmmdK.....",
               ".....KmmmdK.....",
               ".....KmKmdK.....",
               ".....KmKmdK.....",
               ".....KmKmdK.....",
               ".....KmKmdK.....",
               ".....KmKmdK.....",
               ".....KmKmdK.....",
               ".....KmKmdK.....",
               ".....KmKmdK.....",
               ".....KdKddK.....",
               "....KKdKddKK....",
               "....KKKKKKKK....",
               "................",
               "................"])
    return keep4(g, P_RED), P_RED


def void_lantern():
    """A squat stone lantern, the void's light in its window: a cap with a knob, the lamp box,
    a post, a broad foot."""
    g = typed(["................",
               "................",
               "................",
               "................",
               "................",
               "................",
               "................",
               "........K.......",
               ".......KlK......",
               "......KlmmK.....",
               "....KKllmmmKK...",
               "...KlllmmmmmdK..",
               "...KKKKKKKKKKK..",
               "....KlKvvvKdK...",
               "....KlKvwvKdK...",
               "....KlKvvvKdK...",
               "....KKKKKKKKK...",
               "...KllmmmmmmdK..",
               "...KKKKKKKKKKK..",
               "......KlmdK.....",
               "......KlmdK.....",
               "......KlmdK.....",
               "......KlmdK.....",
               ".....KKlmdKK....",
               "....KllmmmmdK...",
               "...KlmmmmmmmdK..",
               "...KmmmmmmmddK..",
               "...KKKKKKKKKKK..",
               "................",
               "................",
               "................",
               "................"])
    # three tones: the stone lit and in shade, the glow -- its window one bright purple
    pal = {'l': STONE[0], 'm': STONE[0], 'd': STONE[1], 'v': GLOW[0], 'w': GLOW[0], 'K': '000000'}
    return keep4(g, pal), pal


def glyph_obelisk():
    """A tall dark obelisk, cracked, faint purple glyphs cut down its face."""
    W, H = 16, 48
    g = blank(W, H)
    for y in range(5, 46):
        t = (y - 5) / 40
        half = 2.6 + 1.6 * t
        for x in range(W):
            dx = x + 0.5 - 8
            if abs(dx) <= half:
                g[y][x] = 'm' if dx < half * 0.35 else 'd'
    for x, y in ((8, 2), (7, 3), (8, 3), (9, 3), (7, 4), (8, 4), (9, 4)):          # its point
        g[y][x] = 'm' if x < 9 else 'd'
    for y in (45, 46):                                            # its foot
        for x in range(3, 13):
            g[y][x] = 'd'
    for x, y in ((6, 10), (7, 10), (7, 11), (6, 15), (7, 15), (6, 16), (7, 17), (6, 22), (7, 23), (6, 23),
                 (6, 29), (7, 29), (7, 30), (6, 31), (6, 36), (7, 37), (6, 37)):   # the glyphs
        g[y][x] = 'v'
    for x, y in ((9, 19), (10, 20), (10, 21), (9, 22), (10, 33), (9, 34)):         # cracks
        g[y][x] = 'K'
    pal = {'m': STONE[1], 'd': STONE[2], 'v': GLOW[0], 'K': '000000'}
    return keep4(outline(g), pal), pal


def spike_row():
    """A crooked row of rusted iron stakes, each a different height, leaning."""
    W, H = 32, 16
    g = blank(W, H)
    for x0, top, lean in ((3, 5, 0), (8, 2, 1), (13, 6, -1), (18, 3, 0), (23, 7, 1), (27, 4, 0)):
        part = blank(W, H)
        stroke(part, [(x0 + 0.5, 14, 2.2), (x0 + 0.5 + lean, top + 1.5, 1.6), (x0 + 0.5 + lean, top, 0.4)], 'm',
               lambda x, y, t, side: 'l' if side < -0.1 else 'd')
        piece(g, part)
    pal = {'l': STONE[0], 'm': STONE[1], 'd': RUST[0], 'K': '000000'}   # iron lit grey, rust down its shaded side
    return keep4(outline(g), pal), pal


PROPS = [
    ('fissure_vent', fissure_vent), ('cinder_shards', cinder_shards), ('scorched_boulder', scorched_boulder),
    ('fallen_wall', fallen_wall), ('snapped_pillar', snapped_pillar), ('void_rock', void_rock),
    ('bone_pile', bone_pile), ('spine_arch', spine_arch), ('red_figure', red_figure),
    ('void_lantern', void_lantern), ('glyph_obelisk', glyph_obelisk), ('spike_row', spike_row),
]

if __name__ == '__main__':
    want = sys.argv[1:]
    for name, make in PROPS:
        if want and name not in want:
            continue
        try:
            g, pal = make()
        except AssertionError as e:
            print(name, 'FAILED:', e)
            continue
        write(g, pal, os.path.join(HERE, name + '.png'))
        print(name)
