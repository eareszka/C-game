"""Writes 33_tsenagahi.txt: the Tse'nagahi ("Traveling Rock") of Navajo lore --
one of the monsters slain by the Hero Twins, a rock that rolled after
travelers to crush them.

An angular, faceted mass of red banded sandstone, wavy strata running across
it, each facet shaded by which way it faces; pale petroglyphs carved into it
-- spiral eyes and a zigzag mouth on its face, a sun circle on its back. No
legs: it rolls. Medium tier: three frames, each one hand-drawn whole with the
pixel plugin in 33_views.aseprite (exported to 33_views.png): row 0 at rest,
row 1 it rolls forward, row 2 back -- facets, strata and carvings turning
with it (from the front and back, rocking toward and away from you). Front
and back are mirror images. This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 44, 42
PAL = {'K': '000000', 'R': 'c0603c', 'r': '8c3c24', 'o': 'e09060', 'b': '5c2814', 'S': 'd8a070', 'G': 'f0e0c0'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '33_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
