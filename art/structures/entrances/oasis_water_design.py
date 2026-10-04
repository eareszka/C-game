"""The water of an oasis pool, laid out for tools/draw_views.py.

    python art/structures/entrances/oasis_water_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/oasis_water

One 16x16 cell that repeats across every tile of an oasis's pool (COVER_OASIS
in src/tilemap.cpp). Flatter than the ponds' and rivers' foamy water: one deep
teal-blue from the palette, apart from the sky blue the world's other water
is, with two short pale ripples, kept off the cell's edges so the repeat shows
no seam.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))

PAL = {'w': '3e91cc', 'r': '84a7e9'}
CELL = [
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwrrrwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwrrrrww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
]


def design():
    assert len(CELL) == 16 and all(len(r) == 16 for r in CELL)
    return {'pal': PAL, 'view_w': 16, 'order': ['water'], 'views': {'water': CELL}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
