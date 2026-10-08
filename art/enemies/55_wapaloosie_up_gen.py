"""Writes 55_wapaloosie_up.txt: the Wapaloosie's other idle -- reared up on
its back legs like a weasel keeping watch. Hind legs planted on their
woodpecker feet, the long skinny body rising and leaning forward, front paws
held up before its chest, the long pointed ears up (laid a little back to fit
the frame), the spiked tail lying along the ground behind as a prop.

Same frame and layout as 55_wapaloosie.png (the battle's alt sheet: the idle
in another pose), three frames, each one hand-drawn whole with the pixel
plugin in 55_up_views.aseprite (exported to 55_up_views.png): row 0 at rest,
row 1 it draws a breath -- chest up, ears pricked -- row 2 it settles. This
script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 58, 32          # the idle's canvas, so the two sheets swap frame for frame
PAL = {'K': '000000', 'F': '664b95', 'f': '3b2a58', 'L': 'b69cee', 'G': '848694', 'g': '474751',
       'S': 'e8e0c0', 'k': '14101e'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '55_up_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
