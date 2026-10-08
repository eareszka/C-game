"""Writes 56_moskitto.txt: the Moskitto of Paul Bunyan's camps -- the giant
Chippewa River mosquitos, big enough to straddle a stream, crossed with the
fighting bumblebees Bunyan brought in to fight them: a hybrid with a stinger
at both ends.

A big enemy (5 frames, 96 x 64), always aloft: a hovering giant with a
bumblebee's fat fuzzy body banded yellow and black, a mosquito's long black
needle proboscis in front and a bee's pale stinger behind, great red
faceted compound eyes, two pairs of glassy blue-veined wings, three pairs of
long thin legs dangling. Five frames, each hand-drawn whole with the pixel
plugin in 56_views.aseprite (exported to 56_views.png), one cycle: it never
lands -- it bobs on a sine in the air, the wings beating twice to each bob,
the proboscis probing. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'Y': 'f0bc3c', 'y': 'c9a433', 'L': 'fae488', 'D': '292931', 'd': '14101e',
       'E': 'b6433d', 'e': '7c0a1b', 'W': 'c6ccda', 'w': '84a7e9', 'G': '595965', 'S': 'e8e0c0'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '56_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
