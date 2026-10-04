"""The steam off a hot spring, laid out for tools/draw_views.py.

    python art/structures/entrances/steam_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/steam

Four 16x16 frames side by side, played in a loop over the water of an oasis in
snow (src/tilemap.cpp, draw_hot_spring_steam): a puff leaves the water,
swells as it rises, thins and is gone. No line round it -- steam has no edge --
white where it is thick, the palest grey where it thins. One piece a frame.
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
    pad(11, [".......SS.......",
             "......SSSS......",
             "......SSSS......",
             ".......SS......."]),
    pad(7, ["......SSS.......",
            ".....SSSSS......",
            ".....SSSSSS.....",
            "......SSSSS.....",
            ".......SSS......"]),
    pad(3, [".......LLL......",
            "......LSSSL.....",
            ".....LSSSSL.....",
            "......LSSL......",
            ".......LL......."]),
    pad(1, ["........LL......",
            ".......LLLL.....",
            "........LL......"]),
]


def design():
    for i, rows in enumerate(FRAMES):
        g = Grid(16, 16)
        g.g = [list(r) for r in rows]
        check(g, 'steam %d' % i)
    return {'pal': PAL, 'view_w': 16, 'order': ['f0', 'f1', 'f2', 'f3'],
            'views': {'f%d' % i: rows for i, rows in enumerate(FRAMES)}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
