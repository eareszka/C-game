"""Writes 55_wapaloosie.txt: the Wapaloosie of the Pacific Coast forests
(Cox, Fearsome Creatures of the Lumberwoods) -- as big as a dachshund, with
velvety fur, woodpecker feet and a spike-tipped tail; it climbs the tallest
trees like an inchworm, humping its long body, to feed on bracket fungus.

A skinny, very long, low body in violet velvet lit along the top, short thin legs
on grey woodpecker feet (toes forward and back), a small head with a long
snout and very long pointed ears standing up, a long tail ending in a
pale bony spike. Medium
tier: three frames, each one hand-drawn whole with the pixel plugin in
55_views.aseprite (exported to 55_views.png): row 0 stretched out long and
low, row 1 humped up in an inchworm's arch -- feet drawn together, the
spiked tail cocked -- row 2 easing back down. Laid out as one 3D skeleton
turned to each view (enemy_shapes.skeleton). This script only lays them out
for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 58, 32
PAL = {'K': '000000', 'F': '664b95', 'f': '3b2a58', 'L': 'b69cee', 'G': '848694', 'g': '474751',
       'S': 'e8e0c0', 'k': '14101e'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '55_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
