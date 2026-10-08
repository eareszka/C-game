"""Writes 68_shuyu.txt: the Shuyu of the Shanhaijing -- shaped like a chicken
with red feathers, three tails, six legs and four heads.

A plump red chicken lit along the top and darker beneath, four heads on
necks fanned out from its breast (two forward, two higher behind), each with
a crimson comb, a yellow beak and its own eye; three dark sickle tails fanned
and arching behind; six thin yellow legs, three a side. Medium tier: three
frames, each one hand-drawn whole with the pixel plugin in 68_views.aseprite
(exported to 68_views.png): row 0 at rest, rows 1 and 2 its heads pluck at
the air, each its own way -- forward, out to the side, up -- beaks gaping, two
at a time while the other two hang back. Its red wings lie folded at its
sides (they beat in its second phase: 68_shuyu_flap). Laid out as one
3D skeleton turned to each view (enemy_shapes.skeleton). This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 48, 40
PAL = {'K': '000000', 'F': 'b6433d', 'f': '792727', 'L': 'ec8476', 'C': 'b70000', 'Y': 'f0bc3c',
       'y': 'c9a433', 'D': '531b1c'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '68_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
