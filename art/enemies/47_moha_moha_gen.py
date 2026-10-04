"""Writes 47_moha_moha.txt: the Moha-moha of Queensland (reported by Sarah
Lane at Sandy Cape, 1890) -- a giant turtle-like sea creature with a very
long neck and a small turtle head, a vast shell striped in black and white
bands, flippers, and a long tail.

A big enemy (5 frames, 96 x 64): a broad domed shell banded black and white
(the bands running over the dome, curving with it), a pale underside, four
green paddle flippers, a long tapering tail, and a very long neck raised
high to a small hook-beaked turtle head with bright eyes. Five frames, each
hand-drawn whole with the pixel plugin in 47_views.aseprite (exported to
47_views.png), one cycle: the long neck sways forward and back and the
flippers paddle. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'W': 'e8e4d8', 'w': 'a8a498', 'D': '2c2c30', 'd': '4c4c54', 'Y': 'd8c890',
       'G': '7c8c6c', 'g': '4c5c44', 'L': 'a8b890', 'E': 'f0d040', 'B': 'c8b880'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '47_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
