"""The things to mine, laid out for tools/draw_views.py.

    python art/structures/nodes/nodes_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/nodes/nodes

Two 16x16 objects (OVERWORLD_STYLE.md: one black line round each, three
tones and black, one ramp placed by form, flat fills), in a strip:
  rock  the overworld's stone (TILE_ROCK, on grass), in stone's ore ramp
  vein  the rock one flat grey cut by black cracks, nuggets of ore in it: the
        overworld's gold ore (TILE_GOLD_ORE, on high plateaus) in kharvite's
        tones (the gold icon's), and a cave's node (src/dungeon.cpp
        place_cave_nodes) in its own ore's -- tools/gen_cave_tiles.py swaps
        G for the ore's lit tone and g for its base (the user, 2026-10-15:
        "same shape but instead of gold vein its whatever material the cave offers")
  vein_a, vein_b, vein_c  the vein with one nugget flared, its twinkle's frames
K/S/B/L are the stone key tones -- line, shade, base, lit (gen_cave_entrances.py
TONES), as in art/items/items_design.py; G/g an ore's lit and base, here kharvite's.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, stand, depth_layers

PAL = {'K': '000000', 'S': '474751', 'B': '848694', 'L': 'bcbeca',
       'g': 'c9a433', 'G': 'fae488'}

VIEWS = {
    # a broken boulder: a lit top facet, its front in the base, a shaded right
    # facet, a crack down the front
    'rock': [
        '................',
        '................',
        '................',
        '................',
        '.....KKKKKK.....',
        '...KKLLLLBBKK...',
        '..KLLLLBBBBBBK..',
        '..KLBBBBKBBBSSK.',
        '.KBBBBBBBKBBSSK.',
        '.KBBBBBBKBBBSSSK',
        '.KBBBBBBKBBSSSSK',
        'KBBBBBBBBKBSSSSK',
        'KSBBBBBBBKSSSSSK',
        'KSSSBBBBKSSSSSK.',
        '.KKSSSSSSSSSKKK.',
        '...KKKKKKKKKK...'],
    # the rock one flat tone cut by black, the ore in it lit and base
    'vein': [
        '................',
        '................',
        '................',
        '................',
        '.....KKKKKK.....',
        '...KKBBBBBBKK...',
        '..KBBBBBBBBBBK..',
        '..KBBGgBBBBKBBK.',
        '.KBBBGggBBBBKBK.',
        '.KBBBBgBBBBGBBBK',
        '.KBBBBBBBBGggBBK',
        'KBBGBBBBBKBgBBBK',
        'KBGggBBBKBBBBBBK',
        'KBBgBBBBKBBBBBK.',
        '.KKBBBBBBBBBKKK.',
        '...KKKKKKKKKK...'],
}


def flare(rows, cx, cy):
    """The vein with one nugget flared: a cross of its lit tone on (cx, cy)."""
    g = [list(r) for r in rows]
    for x, y in ((cx, cy), (cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
        assert g[y][x] in 'BgG', (x, y)              # inside the outline, off the cracks
        g[y][x] = 'G'
    return [''.join(r) for r in g]


# The vein twinkling (the user, 2026-10-15: "the specs or veins should twinkle
# similar to the parallax background used in cave systems" -- the cross the
# cave's glints flare into): a nugget at a time, plain then each in turn.
for _k, _at in (('vein_a', (5, 7)), ('vein_b', (11, 9)), ('vein_c', (3, 11))):
    VIEWS[_k] = flare(VIEWS['vein'], *_at)
ORDER = ['rock', 'vein', 'vein_a', 'vein_b', 'vein_c']


def stood(rows):
    """A cell as the game meets it, as the desert's things are stood: solid on
    its bottom three rows, walked behind above them (entrance_shapes.stand)."""
    g = Grid(16, 16)
    g.g = [list(r) for r in rows]
    bottom = max(y for y in range(16) if rows[y].strip('.'))
    foot = set()
    for y in range(bottom - 2, bottom + 1):
        xs = [x for x in range(16) if rows[y][x] != '.']
        foot |= {(x, y) for x in range(min(xs), max(xs) + 1)}
    return stand(g, lambda x, y: bottom, foot)


def design():
    for k, rows in VIEWS.items():
        assert len(rows) == 16 and all(len(r) == 16 for r in rows), k
        # one silhouette: a cave's node takes its feet from the overworld's cells (src/dungeon.cpp)
        assert [[c != '.' for c in r] for r in rows] == [[c != '.' for c in r] for r in VIEWS['rock']], k
    return {'pal': PAL, 'view_w': 16, 'order': ORDER, 'views': VIEWS,
            'depth': depth_layers(16 * len(ORDER), 16, [(16 * i, 0, stood(VIEWS[k])) for i, k in enumerate(ORDER)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
