"""Writes 24_zoureg.txt: the Zoureg (de Plancy's Dictionnaire Infernal) -- a
snake "one foot in length" of the Arabian desert that goes through rocks,
trees, walls and bodies "like a hot knife through butter".

A red-hot knife of a snake: a thin flat blade of a body glowing dark red along
its underside through orange to yellow, a white-hot cutting edge along its top,
a long dagger of a head tapering to a white-hot needle point, a pointed tail;
coiled and poised to strike. Medium tier: three frames, each
one hand-drawn whole with the pixel plugin in 24_views.aseprite (exported to
24_views.png): row 0 at rest, row 1 the head drawn back and glowing hotter,
row 2 the thrust. Front and back are exact mirror images. This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 42, 28
PAL = {'K': '000000', 'R': 'b71c00', 'r': '6c1000', 'O': 'f85800', 'Y': 'f8d878', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '24_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
