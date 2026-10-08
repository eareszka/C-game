"""Writes 66_ayotochtli.txt: the Ayotochtli -- Nahuatl for "turtle-rabbit",
the armadillo as the Aztecs named it: a rabbit in a turtle's shell.

A banded armoured shell over its back (tan plates lit along the top, a dark
seam between each band), long upright rabbit's ears lined pale pink, a
pointed snout, short pink-tan legs on clawed feet, a ringed armoured tail.
Medium tier: three frames, each one hand-drawn whole with the pixel plugin in
66_views.aseprite (exported to 66_views.png): row 0 at rest, row 1 it hunches
into its shell -- the bands bunch up, head and ears drawn down, tail tucked --
row 2 it eases back out. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 46, 34
PAL = {'K': '000000', 'L': 'cebe82', 'F': 'b29e5c', 'f': '785830', 'S': 'd7a175', 's': '8d6b4f',
       'P': 'f0b890', 'k': '22140c'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '66_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
