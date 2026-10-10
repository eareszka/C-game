"""Writes 87_corocotta.txt: the Corocotta (Pliny, Ethiopia): a cross of hyena and
wolf, or dog, that mimics human speech to call men out at night, with a
single unbroken tooth in each jaw that never wears and eyes that change
colour. A big grey hyena-wolf, the back sloping down from tall shoulders to
low haunches, a dark bristling mane down the neck and spine, a heavy black
muzzle, a bushy tail. Big tier, 8 directions, five frames: breathing, the
mane bristling, the eyes shifting colour -- frame 2 the jaws thrown wide on
the white blades of its two great teeth.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 87_views.aseprite
(exported to 87_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'G': '9797aa', 'g': '848694', 'n': '595965', 'o': '474751', 'k': '282828', 'W': 'fcfcfc', 'm': '531b1c', 'Y': 'f0bc3c', 'R': 'ec8476', 'C': '3e91cc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '87_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
