"""Writes 54_billdad.txt: the Billdad of Boundary Pond, Maine (Cox, Fearsome
Creatures of the Lumberwoods) -- the size of a beaver, with a kangaroo's long
hind legs and short front legs, webbed hind feet, a hawk's hooked bill and a
broad flat beaver's tail; it leaps sixty rods out over the pond and stuns a
trout with one slap of the tail.

Sitting up on its haunches: a pear-shaped brown body leaning forward, long
folded hind legs on grey webbed feet, short front legs held up, a round head
with a yellow hooked bill, the dark cross-hatched tail behind as a prop.
Medium tier: three frames, each one hand-drawn whole with the pixel plugin
in 54_views.aseprite (exported to 54_views.png): row 0 crouched, row 1 it
springs -- legs straightened, off the ground, the tail flung up over its back
to slap -- row 2 it lands. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 40, 32
PAL = {'K': '000000', 'F': '815423', 'f': '583518', 'L': 'b2966a', 'Y': 'f0bc3c', 'y': 'c18a39',
       'T': '474751', 't': '292931', 'G': '848694'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '54_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
