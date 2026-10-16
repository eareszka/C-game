"""The overworld cave entrances, laid out for tools/draw_views.py.

    python art/structures/cave_entrance_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/cave_entrance
    python art/structures/gen_cave_entrances.py --stamp

    x  0..47, y 0..31   the wall mouth, 3x2 cells, laid over the foot of a
                        south cliff wall
    x 48..63, y 0..15   the pit: a hole with a ladder, for a cave on flat
                        ground or a storey top (1 cell)

The mouth is the arch a cave's way in is seen as from inside
(dungeon_walls/cave_rock_design.py, its `arch`: a 16-wide opening with a round
top, a two-pixel rim of the deep tone, cut in the user's cobble) -- the user,
2026-10-13: "have the cave entrance match the interior cave entrance ... the
rim entrance". Read from that drawing and centred so the opening is exactly
the middle cell, the one walked into (src/tilemap.cpp is_cave_opening_cell);
of the cobble round it only a ring stays, the mountain's own painted rock
showing beyond. The arch's tones are mapped as tools/gen_cave_tiles.py lays
the rock: base, shade (the deep tone too), black. The pit is the one already
drawn, read back unchanged, so the holes that share it do not move.

Drawn in the stone master tones gen_cave_entrances.py swaps per material.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from entrance_shapes import Grid, read_sprite, outline

PAL = {'K': '000000', 'D': '474751', 'b': '848694', 'l': 'bcbeca'}
CAVE_ROCK = {'K': '000000', 'M': '9797aa', 'D': '474751', 'S': '292931', 'F': '595965', 'G': 'dcf0ff'}
TONE = {'K': 'K', 'M': 'b', 'D': 'D', 'S': 'D', 'G': 'l', 'F': '.', '.': '.'}
RING = 5          # cobble kept round the rim, in pixels


def arch():
    """The interior arch (cave_rock.png cells 0..1 of its row 4), in the
    master tones."""
    rows = read_sprite('dungeon_walls/cave_rock.png', 0, 64, 32, 32, CAVE_ROCK)
    return [[TONE[c] for c in r] for r in rows]


def opening(a):
    """The arch's opening: on each row, the black between the rim's two
    sides (the rim is the deep tone, two pixels, either side of it)."""
    h, w = len(a), len(a[0])
    rows = read_sprite('dungeon_walls/cave_rock.png', 0, 64, 32, 32, CAVE_ROCK)
    hole = set()
    for y in range(h):
        rim = [x for x in range(w) if rows[y][x] == 'S']
        left = [x for x in rim if x < w // 2]
        right = [x for x in rim if x >= w // 2]
        if left and right:
            hole |= {(x, y) for x in range(max(left) + 1, min(right)) if a[y][x] == 'K'}
    return hole


def mouth():
    a = arch()
    hole = opening(a)
    near = lambda x, y: any((x - hx) ** 2 + (y - hy) ** 2 <= RING * RING for hx, hy in hole)
    g = Grid(48, 32)
    for y in range(32):
        for x in range(32):
            if a[y][x] != '.' and near(x, y):
                g.put(x + 8, y, a[y][x])
    outline(g)
    return g


def design():
    g = Grid(64, 32)
    m = mouth()
    for y in range(32):
        for x in range(48):
            g.put(x, y, m.g[y][x])
    pit = read_sprite('cave_entrance.png', 48, 0, 16, 16, PAL)
    for y, r in enumerate(pit):
        for x, c in enumerate(r):
            g.put(48 + x, y, c)
    return {'pal': PAL, 'view_w': 64, 'order': ['entrances'], 'views': {'entrances': g.rows()}}


if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views']['entrances']:
        print(r)
