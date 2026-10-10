"""Writes 81_ieltxu_fire.txt: the Ieltxu breathing fire, its alt sheet (the
same layout as 81_ieltxu): lit up by its own fire -- 0 drawing breath, the
chest glowing red, a lick of flame at the beak; 1 a jet of fire from its
beak lighting its whole body orange; 2 the flame trailing off. Drawn with
the pixel plugin in 81_fire_views.aseprite (exported to 81_fire_views.png).
This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 62, 48
PAL = {'K': '000000', 'd': '0c0a12', 'D': '14101e', 'n': '2b1f40', 'e': '5d1e1f', 'r': '7c0a1b', 'R': 'b6433d',
       'O': 'fc9838', 'Y': 'fae488', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '81_fire_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
