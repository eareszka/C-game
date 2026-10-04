"""Writes 40_slide_rock_bolter.txt: the Slide-Rock Bolter, a "fearsome
critter" of Colorado -- an enormous whale-like beast of the steep
mountainsides; it hooks the split end of its tail over the ridgeline and
waits, then lets go and toboggans down the slope, its huge mouth wide open,
scooping up whoever is below. Small eyes, all mouth.

A big enemy (5 frames, 96 x 64): a slate-grey whale of a body, mottled like
weathered rock, with a pale belly and a vast mouth across its blunt front and
back along both sides of the head (red gums, white teeth), tiny yellow eyes
high behind it, and the tail rising up behind into a pair of curved bony
grapnel hooks. Five frames, each hand-drawn whole with the pixel plugin in
40_views.aseprite (exported to 40_views.png), one cycle: the jaws work open
and wide, the body lurches forward to slide, the hooks flex open and closed.
Laid out as one 3D skeleton turned to each view (enemy_shapes.skeleton); the
hooks curve across the screen in every view (facing_dir). This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'G': '7c8494', 'g': '4c5464', 'L': 'a8b0bc', 'P': 'c8c0b0', 'k': '2c1418',
       'R': '8c3c44', 'W': 'f0e8d8', 'w': 'b8b098', 'Y': 'f0d040'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '40_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
