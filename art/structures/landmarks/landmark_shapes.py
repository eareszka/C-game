"""Shared by the landmarks' designs (art/structures/landmarks/<name>_design.py).

A landmark's export is its block -- stamp_w cells across, as tall as it stands
-- with the cell its cache stands in left empty: every cache is the one chest
(chest_design.py), laid there by the game (gen_entrance_art.py LANDMARKS).
Each piece in it is either built (a Scene or a House) or an object typed as
its fills: obj() lays the black line round it and stands it on its bottom
rows, as the desert's things are stood (entrances/desert_design.py).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, stand, outline, depth_layers

CELL = 16


def obj(rows, name, lying=False):
    """An object from its fills (letters; '.' nothing, 'K' a line inside it):
    padded for its line and a clear pixel past it, outlined, and stood on its
    bottom three rows -- or lying, each pixel on its own row, walked over."""
    w = max(len(r) for r in rows) + 4
    g = Grid(w, len(rows) + 3)
    g.g = [['.'] * w for _ in range(2)] + [list('..' + r.ljust(w - 4, '.') + '..') for r in rows] + [['.'] * w]
    outline(g)
    check(g, name)
    if lying:
        return stand(g, lambda x, y: y)
    bottom = g.h - 1
    foot = set()
    for y in range(bottom - 2, bottom + 1):
        xs = [x for x in range(g.w) if g.g[y][x] != '.']
        if xs:
            foot |= {(x, y) for x in range(min(xs), max(xs) + 1)}
    return stand(g, lambda x, y: bottom, foot)


def at(g, cell_x, cell_y, cells_w=1, lift=1):
    """Where g goes to stand centred in its cells, its bottom line `lift`
    rows up from the bottom of cell row cell_y."""
    return cell_x * CELL + (cells_w * CELL - g.w) // 2, (cell_y + 1) * CELL - lift - g.h


def export(name, pal, cols, rows, pieces, cache, stamp_w):
    """The design gen_entrance_art.py and draw_views.py read: one view, its
    depth layers, and where its cache is. Pieces [(x, y, grid)] may not
    overlap, nor anything be drawn in the cache's cell (cache None: none)."""
    W, H = cols * CELL, rows * CELL
    canvas = [['.'] * W for _ in range(H)]
    for x0, y0, g in pieces:
        for y in range(g.h):
            for x in range(g.w):
                if g.g[y][x] != '.':
                    assert canvas[y0 + y][x0 + x] == '.', '%s: pieces overlap at %d,%d' % (name, x0 + x, y0 + y)
                    canvas[y0 + y][x0 + x] = g.g[y][x]
    if cache:
        assert all(canvas[y][x] == '.' for y in range(cache[1] * CELL, cache[1] * CELL + CELL)
                   for x in range(cache[0] * CELL, cache[0] * CELL + CELL)), name + ": drawn in the cache's cell"
    for y in range(H):
        for cx in range(cols):
            n = {canvas[yy][x] for yy in range(y // CELL * CELL, y // CELL * CELL + CELL)
                 for x in range(cx * CELL, cx * CELL + CELL)} - {'.'}
            assert len({pal[c] for c in n}) <= 4, '%s: cell %d,%d has %d colours' % (name, cx, y // CELL, len(n))
    return {'pal': pal, 'view_w': W, 'order': [name], 'views': {name: [''.join(r) for r in canvas]},
            'depth': depth_layers(W, H, pieces), 'cache': cache, 'stamp_w': stamp_w}


def main(design):
    """A design file's __main__: write the json for draw_views, print the view."""
    d = design()
    if len(sys.argv) > 1:
        json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views'][d['order'][0]]:
        print(r)
