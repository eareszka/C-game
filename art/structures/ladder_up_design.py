"""The way out of a dungeon entered down a hole (the cave, the stonehenge
pit, the oasis), seen from inside: the exterior pit's ladder
(cave_entrance.png) standing against the north wall at the way out, fully on
the wall's face, as the user's reference draws a ladder up a cliff. Two
cells, stacked by src/dungeon.cpp to the face's height:

    MID   a length of ladder, nothing behind it, so the rock face shows
    BASE  the face's lowest row: the ladder's foot, its shadow at the wall's foot

    python art/structures/ladder_up_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/ladder_up

Drawn in the cave's stone tones (K line, s shade, b base, l lit);
gen_cave_entrances.py swaps them for each material's, as it does the pit's.
"""
import json, sys

PAL = {'K': '000000', 's': '474751', 'b': '848694', 'l': 'bcbeca'}

RUNG = ["....KlK..KlK....",
        "....KlbbbblK....",          # a rung
        "....KlKKKKlK....",          # its shadow
        "....KlK..KlK...."]

MID = RUNG * 4
BASE = RUNG * 3 + ["....KlK..KlK....",
                   "....KlK..KlK....",
                   "....KsK..KsK....",
                   "...KKKKKKKKKK..."]   # its feet's shadow along the wall's foot


def design():
    cells = {'mid': MID, 'base': BASE}
    for k, rows in cells.items():
        assert len(rows) == 16 and all(len(r) == 16 for r in rows), k
    return {'pal': PAL, 'view_w': 16, 'order': ['mid', 'base'], 'views': cells}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
