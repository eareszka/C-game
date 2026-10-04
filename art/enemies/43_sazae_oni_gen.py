"""Writes 43_sazae_oni.txt: the Sazae-oni of Japan -- a turban snail that,
having lived a very long time, becomes an oni; in Toriyama Sekien's picture
a monstrous face leering out of a great spiral shell.

A spiky turban shell -- olive-brown whorls stepping up to its point, pale
spiral ridges, stout pale spines round the broad lower whorls -- its opening
rimmed with mother-of-pearl, and pushing out of it on a pale fleshy neck a
red horned oni head with glowing yellow eyes and a fanged grin, the snail's
foot spread on the ground beneath. Medium tier: three frames, each one
hand-drawn whole with the pixel plugin in 43_views.aseprite (exported to
43_views.png): row 0 at rest, row 1 it leans out further, grinning wide,
row 2 it shrinks back to peek from the shell. Laid out as one 3D skeleton
turned to each view (enemy_shapes.skeleton). This script only lays them out
for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 52, 50
PAL = {'K': '000000', 'S': '8c7c4c', 's': '5c4c2c', 'L': 'b8a870', 'P': 'd8c8a0', 'k': '241814',
       'Q': 'e8d8e8', 'q': 'a898b8', 'F': 'e0c0a8', 'f': 'a88470', 'R': 'c84c3c', 'r': '8c2c24',
       'W': 'f0e8d8', 'Y': 'f8e040'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '43_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
