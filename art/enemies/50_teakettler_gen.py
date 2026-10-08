"""Writes 50_teakettler.txt: the Teakettler of the American lumber camps -- a
small dog-like beast with a cat's ears that walks backwards, and steam puffs
from its nose and mouth with the whistle of a teakettle on the boil.

Drawn on the Cu Sith's outline (the user's call: the same dog as our other
dog cryptid, just not green): the French bulldog build, bat ears, the tail
coiled over its back -- here in plain brown fur, with 1x1 black eyes. Medium
tier: three frames, each one hand-drawn whole with the pixel plugin in
50_views.aseprite (exported to 50_views.png): row 0 at rest, row 1 it
whistles -- head up, mouth open, a puff of steam rising off to its left --
row 2 it settles, the puff drifting higher and thinning. This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 30, 28
PAL = {'K': '000000', 'F': '8d6b4f', 'f': '583518', 'L': 'b2966a', 'k': '22140c',
       'P': 'ec8476', 'R': 'b6433d', 'W': 'fcfcfc', 'w': 'c6ccda'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '50_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
