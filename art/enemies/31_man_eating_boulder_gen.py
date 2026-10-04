"""Writes 31_man_eating_boulder.txt: the Man-Eating Boulder -- the rolling
rock of Plains tales, that chases down whoever wrongs it and crushes them.

A lumpy grey boulder with moss and lichen on its crown and cracks across it:
two small glowing eyes sunk in the cracks and a wide jagged maw of stone
teeth with a dark red gullet; no legs, it rolls. Medium tier: three frames,
each one hand-drawn whole with the pixel plugin in 31_views.aseprite
(exported to 31_views.png): row 0 at rest (the maw ajar), row 1 the maw
gapes and the rock heaves up, row 2 it snaps shut. Front and back are mirror
images. This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 44, 40
PAL = {'K': '000000', 'R': '8c8478', 'r': '5c564c', 'l': 'b8b0a0', 'M': '6c8c3c', 'm': '4c6428',
       'G': '8c2c2c', 'g': '4c1414', 'T': 'e8e0c8', 'E': 'f8a800'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '31_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
