"""The half-buried statue, a landmark of the sand, laid out for tools/draw_views.py.

    python art/structures/landmarks/statue_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/landmarks/statue

48x32: a great stone head sunk to its lip in the sand in the left two
columns; its cache stands at its foot in the third (the chest, laid by the
game: chest_design.py). An object (the overworld bible): one black line round
it, three tones and black, light high on the left, dark low on the right, in
the stonehenge's greys.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landmark_shapes import obj, at, export, main

# tools/overworld_style.py MATERIALS: stone (lit, base, shade)
PAL = {'K': '000000', 'L': 'c6ccda', 'M': '9797aa', 'D': '595965'}

HEAD = [
    ".........LLLLLLLL.........",
    ".......LLLMMMMMMMMMM......",
    ".....LLLMMMMMMMMMMMMMD....",
    "....LLMMMMMMMMMMMMMMMMD...",
    "...LLMMMMMMMMMMMMMMMMMDD..",
    "...LMMMMMMMMMMMMMMMMMMDD..",
    "..LLMMMMMMMMMMMMMMMMMMMDD.",
    "..LMMDDDDDDMMMMDDDDDDMMDD.",
    "..LMDKKKKKDMMMMDKKKKKDMDD.",
    "..LMMDKKKDMMLMMMDKKKDMMDD.",
    "..LMMMMMMMMMLMDMMMMMMMMDD.",
    "..LMMMMMMMMLLMDMMMMMMMDDD.",
    "..LMMMMMMMMLMMDDMMMMMMDDD.",
    "..LMMMMMMMLLMMMDMMMMMMDDD.",
    "..LMMMMMMMDDDDDDMMMMMDDDD.",
    "..LMMMMMMMMMMMMMMMMMMDDDD.",
    "..DDDDDDDDDDDDDDDDDDDDDDD.",            # where the sand closes over it
]


CACHE, STAMP_W = (2, 1), 3


def design():
    head = obj(HEAD, 'statue head')
    return export('statue', PAL, STAMP_W, 2, [(*at(head, 0, 1, 2), head)], CACHE, STAMP_W)


if __name__ == '__main__':
    main(design)
