"""Writes 21_asp.txt: the Asp of the medieval bestiaries -- a serpent that
"carries instantaneous death in its fangs" and, to resist the snake charmer,
presses one ear to the ground and "stops its ears with its tail".

A coiled green serpent, banded, pale-bellied, with pointed pink-lined ears and
fangs, its tail curling up out of the coils toward its ear. Medium tier: three
frames, each one hand-drawn whole with the pixel plugin in 21_views.aseprite
(exported to 21_views.png): row 0 at rest, row 1 the tail tip plugging its
ear, row 2 the head lifting with the forked tongue out. Front and back are
exact mirror images at rest. This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 40, 34
PAL = {'K': '000000', 'G': '3c6448', 'g': '24402c', 'Y': 'd0c078', 'P': 'ec8476', 'W': 'fcfcfc', 'R': 'b70000'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '21_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
