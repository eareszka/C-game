"""The steam off a hot spring, laid out for tools/draw_views.py.

    python art/structures/entrances/steam_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/steam

Three 16x16 frames side by side, played in a loop over the water of an oasis
in snow (src/tilemap.cpp, draw_hot_spring_steam) on the world's ambient beat
(src/core.h: three frames a second each, the graveyard roots' -- the user,
2026-10-29): a puff leaves the water, swells as it rises, thins and is gone.
No line round it -- steam has no edge -- white where it is thick, the palest
grey where it thins. One piece a frame. A fourth cell stays on the sheet,
empty: the strips packed after it keep their places (gen_entrance_art.py
SPRITES).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check

PAL = {'S': 'fcfcfc', 'L': 'c6ccda'}
E = "................"


def pad(top, rows):
    return [E] * top + rows + [E] * (16 - top - len(rows))


# Plain white puffs (the user: "keep the steam normal"), the palest grey only
# as a puff thins out at the top. They read against the oasis's flat water.
FRAMES = [
    pad(10, [".......SS.......",
             "......SSSS......",
             "......SSSS......",
             ".......SS......."]),
    pad(5, ["......SSS.......",
            ".....SSSSS......",
            ".....SSSSSS.....",
            "......SSSSS.....",
            ".......SSS......"]),
    pad(1, [".......LLL......",
            "......LSSSL.....",
            ".....LSSSSL.....",
            "......LSSL......",
            ".......LL......."]),
    pad(0, []),                                  # the fourth cell, kept empty
]


def design():
    for i, rows in enumerate(FRAMES):
        g = Grid(16, 16)
        g.g = [list(r) for r in rows]
        if i < 3:
            check(g, 'steam %d' % i)
    return {'pal': PAL, 'view_w': 16, 'order': ['f0', 'f1', 'f2', 'f3'],
            'views': {'f%d' % i: rows for i, rows in enumerate(FRAMES)}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
