"""Writes 34_anaye.txt: the Anaye (Naayee') of Navajo lore -- the alien
monsters the Hero Twins hunted down; this one their giant, after Ye'iitsoh.

A hulking, hunched brute: reddish skin, a barrel chest armored in rows of
flint scales with chipped white edges, a red loincloth, long black hair down
its back, a white band painted across its glowing red eyes, tusks jutting
from the jaw, and a flint-headed war club in its right fist. Giant tier
(128 x 80): eight frames, each one hand-drawn whole with the pixel plugin in
34_views.aseprite (exported to 34_views.png), one cycle -- it breathes,
hefts the club up over its shoulder, roars at the top of the swing and
settles; every part lit along its top-left, shaded along its bottom-right.
The pose was laid out as one 3D skeleton turned to each view, so the body
stays in perspective from every side; the club stays in its right hand
except in the mirrored left-facing views. The sheet is laid out one row per
direction (#ROWS), being too wide for one texture in a single row. This
script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 128, 80
PAL = {'K': '000000', 'N': '9c5c3c', 'M': 'c07c54', 'n': '6c3c24', 'A': '6c7088', 'a': '44485c', 'w': 'c8ccd8',
       'H': '1c1c24', 'h': '3c3c4c', 'B': '6c4c2c', 'F': '8c8c9c', 'f': '5c5c6c', 'W': 'fcfcfc',
       'E': 'e83c28', 'k': '2c1414', 'C': 'a83c3c', 'c': '742424'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '34_views.png'), PAL, VW, VH, frames=8)
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
