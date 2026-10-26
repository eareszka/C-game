"""The old fence, desert scenery: what is left of a ranch's rail fence, three ways.

    python art/structures/props/desert/fence_post_design.py

48x32, three single tiles, each two cells tall. Not a new drawing but the yard
fence's own parts (entrances/yard_walls_design.py wood) left to the desert, so
a post out here is a post in town: the stout end post 3 by 3 and 13 high, rails
nailed at 2 and 7 up, in the houses' projection and the interiors' wood -- tops
lit, fronts mid, sides turned east dark. A: a lone post, a rail's broken stub
still nailed to it. B: two posts, the upper rail still across them, the lower
one fallen and lying in the sand. C: a post fallen flat. Each built in a Scene,
so the lines between parts are the fence's own.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from entrance_shapes import Scene, check
from prop_paint import save

CELL, H, BASE = 16, 32, 28
WOOD = {'L': '967448', 'M': '785830', 'D': '493712'}


def lone():
    sc = Scene(CELL, H, BASE)
    sc.box(0, 5, 7, 0, 2, 0, 13, 'M')                      # the stout post
    sc.box(1, 8, 12, -1, -1, 7, 8, 'M')                    # a rail's stub, broken off short
    g = sc.render()
    g.g[BASE - 13][8] = 'K' if g.g[BASE - 13][8] != '.' else '.'
    return g


def pair():
    sc = Scene(CELL, H, BASE)
    sc.box(0, 3, 4, 0, 1, 0, 11, 'M')                      # two posts, the fence's own
    sc.box(2, 10, 11, 0, 1, 0, 10, 'M')
    sc.box(1, 3, 12, -1, -1, 7, 8, 'M')                    # the upper rail, still across them
    sc.box(3, 5, 11, -3, -3, 0, 1, 'M')                    # the lower rail, fallen in the sand
    return sc.render()


def fallen():
    sc = Scene(CELL, H, BASE)
    sc.box(0, 2, 11, 0, 2, 0, 2, 'M')                      # the post lying on its side
    return sc.render()


if __name__ == '__main__':
    rows = [[] for _ in range(H)]
    for name, make in (('lone post', lone), ('pair', pair), ('fallen post', fallen)):
        g = make()
        check(g, name, objects=True, speck=4)
        for y in range(H):
            rows[y] += g.g[y]
    save(rows, os.path.join(HERE, 'fence_post.png'), 'wood', WOOD)
