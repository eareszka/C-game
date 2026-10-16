"""The villages' building sets, one strip a biome, laid out for tools/draw_views.py.

A village (src/tilemap.cpp, "Villages") is a hamlet laid afresh for every
seed from its biome's set: three houses -- small, middle, large -- and a
well, side by side in one export, each on cells of its own and standing on
the strip's bottom row; a set may add more (a barn, a field's cell). The
houses are tools/house_shapes.House in the set's wall material and roof (the
user, 2026-10-13: "the buildings in the village and the architecture and
'vibe' must match the biome the village is in"); the well is the landmark
well's round drum (landmarks/well_design.py; the user, 2026-10-14: "make
sure wells are all round") in the set's stone, a windlass of wood over it.

A set's design gives, besides the strip and its layers, where each house's
cells and door are and where the well and the extras are, for
art/structures/gen_entrance_art.py (VILLAGES -> src/village_houses.inc).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.join(HERE, '..', 'landmarks'))
from entrance_shapes import Grid, stand, depth_layers, check, weather
from house_shapes import House
from well_design import well as landmark_well

ROWS = 5                     # every strip is this many cells tall; a house stands on its bottom row


def well(tones):
    """The landmark well, two cells by two -- a round drum of courses, the
    dark of its shaft in its top, a windlass of wood -- in the set's letters
    (tones: {'L','M','D'} -> the stone's, 'x' -> the wood's; 'L' to a snow
    letter puts snow on every lit edge)."""
    g = landmark_well()
    for y in range(g.h):
        for x in range(g.w):
            g.g[y][x] = tones.get(g.g[y][x], g.g[y][x])
    return g


def field():
    """A tilled field's cell, one tile, laid flat: rows of earth with a
    furrow between every two, a sprout in the trees' light green on each
    row, laid in units as a ground is (dirt 'e' and its furrow 'f', the
    sprout 'c'). Walked over: no foot."""
    g = Grid(16, 16)
    for y in range(16):
        for x in range(16):
            g.put(x, y, 'f' if y % 4 == 3 else 'e')
    for y in (1, 5, 9, 13):
        for x in (2, 6, 10, 14):
            g.put(x, y, 'c'); g.put(x - 1, y, 'c'); g.put(x, y - 1, 'c')
    return stand(g, lambda x, y: y)


def ruin(h, name, seed, keep=()):
    """A house aged (entrance_shapes.weather): bites out of its silhouette,
    cracks of the shade across its base tone, its doorway kept whole."""
    g = h.grid(name)
    weather(g, seed, 'B', 'S', chips=14, cracks=10, keep=keep)
    return g


def strip(name, pal, houses, well_grid, extras=()):
    """The set's design: houses [(House, door or None, label[, grid])] then the
    well, then the extras [(name, grid)], each on its own cells, all standing
    on the bottom row of a strip ROWS cells tall."""
    pieces, meta, x = [], [], 0
    rows = max([ROWS] + [item[0].h // 16 for item in houses])    # the strip as tall as its tallest
    for item in houses:
        h, door, label = item[:3]
        g = item[3] if len(item) > 3 else h.grid(label)
        oy = rows * 16 - h.h
        pieces.append((x, oy, g))
        dc = h.door_cells(door) if door else [0, 0, 0]
        meta.append({'cell': x // 16, 'w': h.w // 16, 'h': h.h // 16, 'door': dc})
        x += h.w
    pieces.append((x, rows * 16 - 32, well_grid))
    wx = x // 16
    x += 32
    ex = []
    for ename, eg in extras:
        pieces.append((x, rows * 16 - eg.h, eg))
        ex.append({'name': ename, 'cell': x // 16, 'w': eg.w // 16, 'h': eg.h // 16})
        x += eg.w
    if extras:
        x += 16                          # a clear cell after a ground-like extra, off the block's edge
    g = Grid(x, rows * 16)
    for ox, oy, pg in pieces:
        for y in range(pg.h):
            for xx in range(pg.w):
                if pg.g[y][xx] != '.':
                    g.put(ox + xx, oy + y, pg.g[y][xx])
    check(g, name, objects=True)
    # one letter a colour: a set's stone may share a tone with its paint or
    # its wood, and draw_views reads the export back by colour
    canon = {}
    for k, v in pal.items():
        canon.setdefault(v, k)
    remap = {k: canon[v] for k, v in pal.items()}
    view = [''.join(remap.get(c, c) for c in r) for r in g.rows()]
    return {'pal': {k: v for v, k in canon.items()}, 'view_w': x, 'order': [name], 'views': {name: view},
            'depth': depth_layers(x, rows * 16, pieces),
            'houses': meta, 'well': {'cell': wx, 'w': 2, 'h': 2}, 'fields': ex}
