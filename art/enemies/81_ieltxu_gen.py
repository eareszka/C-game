"""Writes 81_ieltxu.txt: the Ieltxu (Basque folklore, the caves and wells
round Gernika): a mischievous night spirit that leads travellers astray,
seen as a bird shooting flames from its mouth -- at night only its fire is
seen.

A near-black night bird hovering on slow wingbeats, nearly invisible in the
dark save two dim ember eyes. Medium tier, 8 directions (front and back
drawn turned 20 degrees off head-on): three frames of wingbeats, each one
hand-drawn whole with the pixel plugin in 81_views.aseprite (exported to
81_views.png). It only lights up when it breathes fire: that is its alt
sheet, 81_ieltxu_fire. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 62, 48
PAL = {'K': '000000', 'd': '0c0a12', 'D': '14101e', 'n': '2b1f40', 'e': '5d1e1f', 'r': '7c0a1b', 'R': 'b6433d',
       'O': 'fc9838', 'Y': 'fae488', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '81_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
