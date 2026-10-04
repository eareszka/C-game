"""Writes 48_bjarndyrakongur.txt: the Bjarndyrakongur, "king of the polar
bears" of Icelandic folklore -- a huge polar bear marked out by a horn (or a
shining light) on its forehead; the other bears obey it.

A massive white polar bear -- long body without a hump, a long neck, a long
bear's muzzle with a big black nose, small black eyes, heavy paws with dark
claws -- and on its brow a long curved ivory horn, spiral-ridged, its tip
glowing gold. Medium tier: three frames, each one hand-drawn whole with the
pixel plugin in 48_views.aseprite (exported to 48_views.png): row 0 at rest,
row 1 the head comes up in a roar and the horn blazes pale, row 2 a heavy
forward step. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 70, 54
PAL = {'K': '000000', 'F': 'e8eef0', 'f': 'a8b4bc', 'L': 'ffffff', 'D': '7c8894', 'M': 'c8d0d4',
       'k': '1c1c24', 'W': '3c4048', 'R': '8c2c34', 'G': 'f0c040', 'Y': 'fff4b0', 'w': 'f0ece0'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '48_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
