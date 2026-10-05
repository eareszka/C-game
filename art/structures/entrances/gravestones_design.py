"""The gravestones a graveyard is scattered with, laid out for tools/draw_views.py.

    python art/structures/entrances/gravestones_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/gravestones

Six stones side by side, one 16x16 cell each -- a gravestone is a one-tile
resource node, and src/resource_node.cpp picks a stone per node from its
position so a yard is a mix. Each stands on a plinth on the ground line, lit on
its left, its right edge and the short side face behind it in shade, in the
ruins' grey stone. The plinth is the ground it stands on, and the stone stands
in the middle of it: whoever is behind that is behind the stone.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, stand, depth_layers

PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda'}
E = "................"

STONES = {
    'headstone': [E, E,
        "......KKKK......",
        ".....KLLLLDK....",
        "....KLLMMMMDK...",
        "....KLMMDMMDK...",
        "....KLMDDDMDK...",
        "....KLMMDMMDK...",
        "....KLMMDMMDK...",
        "....KLMMMMMDK...",
        "....KLMMMMMDK...",
        "....KLMMMMMDK...",
        "...KKKKKKKKKKK..",
        "...KLLLLLLLLDK..",
        "...KKKKKKKKKKK..", E],
    'cross': [E,
        ".....KKKK.......",
        ".....KLMDK......",
        "..KKKKLMDKKKK...",
        "..KLLLLMMMMDK...",
        "..KDDDLMDDDDK...",
        "..KKKKLMDKKKK...",
        ".....KLMDK......",
        ".....KLMDK......",
        ".....KLMDK......",
        ".....KLMDK......",
        ".....KLMDK......",
        "...KKKKKKKKK....",
        "...KLLLLLLDK....",
        "...KKKKKKKKK....", E],
    'tablet': [E, E, E, E,
        "...KKKKKKKKK....",
        "...KLLLLLLLKK...",
        "...KLMMMMMMDK...",
        "...KLMDDDDMDK...",
        "...KLMMMMMMDK...",
        "...KLMDDDMMDK...",
        "...KLMMMMMMDK...",
        "...KLMMMMMMDK...",
        "..KKKKKKKKKKKK..",
        "..KLLLLLLLLLDK..",
        "..KKKKKKKKKKKK..", E],
    'obelisk': [E,
        ".......KK.......",
        "......KLDK......",
        ".....KLMDK......",
        ".....KLMMDK.....",
        ".....KLMMDK.....",
        ".....KLMMDK.....",
        ".....KLMMDK.....",
        ".....KLMMDK.....",
        ".....KLMMDK.....",
        ".....KLMMDK.....",
        "....KKKKKKKK....",
        "...KLLLLLLLDK...",
        "...KDDDDDDDDK...",
        "...KKKKKKKKKK...", E],
    'broken': [E, E, E, E,
        "....KK..........",
        "....KLK.........",
        "....KLMKK.......",
        "....KLMMDKK.....",
        "....KLMMMDDK....",
        "....KLMDMMDK....",
        "....KLMMDMDK....",
        "....KLMMMMDK....",
        "...KKKKKKKKKK...",
        "...KLLLLLLLDK...",
        "...KKKKKKKKKK...", E],
    'marker': [E, E, E, E, E, E, E,
        "......KKKK......",
        ".....KLLLLK.....",
        "....KLLMMMDK....",
        "....KLMMMMDK....",
        "....KLMDDMDK....",
        "...KKKKKKKKKK...",
        "...KLLLLLLLDK...",
        "...KKKKKKKKKK...", E],
}


def standing(g):
    """The plinth -- its last three rows, end to end -- is stood on; the plinth
    lies on the ground, each pixel on its own row, and the stone stands on the
    plinth's middle row."""
    bottom = max(y for y in range(16) if any(c != '.' for c in g.g[y]))
    foot = set()
    for y in range(bottom - 2, bottom + 1):
        xs = [x for x in range(16) if g.g[y][x] != '.']
        foot |= {(x, y) for x in range(min(xs), max(xs) + 1)}
    return stand(g, lambda x, y: bottom - 1, foot)


def design():
    order = list(STONES)
    grids = []
    for k in order:
        g = Grid(16, 16)
        assert len(STONES[k]) == 16 and all(len(r) == 16 for r in STONES[k]), k
        g.g = [list(r) for r in STONES[k]]
        check(g, 'gravestone ' + k)
        grids.append(standing(g))
    return {'pal': PAL, 'view_w': 16, 'order': order, 'views': STONES,
            'depth': depth_layers(16 * len(order), 16, [(16 * i, 0, g) for i, g in enumerate(grids)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
