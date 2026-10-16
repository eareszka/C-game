"""The chest, every cache's one drawing, laid out for tools/draw_views.py.

    python art/structures/landmarks/chest_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/landmarks/chest

32x16: the chest shut in the left cell, the same chest open -- its lid thrown
back, the dark of it empty -- in the right. The user, 2026-10-14: every cache
on the overworld and every openable in the dungeons is "one sprite that more
detailed and a flag is set once opened"; asked, a treasure chest, struck open,
shown open after. Laid by the landmarks into their cache's cell and drawn by
the dungeons at their chests (gen_entrance_art.py CHEST).

An object (the overworld bible): one black line round it and between its
parts, three tones and black -- the wood's base and shade, the iron of its
bands, corners and lock plate catching the light -- light high on the left,
the shade low and on the right.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landmark_shapes import obj, at, export, main

# tools/overworld_style.py MATERIALS: wood (base, shade), stone (base: the iron)
PAL = {'K': '000000', 'm': '785830', 'd': '493712', 'i': '9797aa'}

SHUT = [
    "..mimmmmim..",
    ".mmimmmmimd.",
    "immimmmmimdi",
    "iddidiididdi",
    "KKKiKiiKiKKK",
    "immiiKKiimdi",
    "immimiimimdi",
    "dddiddddiddd",
    "immimmmmimdi",
    "iimimmmmimii",
    "iididdddidii",
]

OPEN = [
    "..diddddid..",
    ".ddiddddidd.",
    ".ddiddddidd.",
    "iiiiiiiiiiii",
    "iKKKKKKKKKKi",
    "iKKKKKKKKKKi",
    "immiiiiiimdi",
    "immimmmmimdi",
    "dddiddddiddd",
    "immimmmmimdi",
    "iimimmmmimii",
    "iididdddidii",
]



def design():
    shut, opened = obj(SHUT, 'chest'), obj(OPEN, 'chest open')
    return export('chest', PAL, 2, 1, [(*at(shut, 0, 0), shut), (*at(opened, 1, 0), opened)], None, 2)


if __name__ == '__main__':
    main(design)
