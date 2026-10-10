"""Writes 86_leucrocotta.txt: the Leucrocotta (Pliny; India and Ethiopia): a swift
beast the size of a wild ass, with a stag's long legs and cloven hooves, a
lion's neck, chest and tail, a badger's striped head, and a mouth slit back
to its ears holding one solid ridge of bone instead of teeth -- it mimics
human voices to lure travellers. Tawny lion body on long slender deer legs,
a tufted lion tail, a black-and-white badger head. Big tier, 8 directions,
five frames: the tail swishing, a weight shift -- frame 2 the head thrown
up, the ear-to-ear mouth gaping on its bone ridges (calling).

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 86_views.aseprite
(exported to 86_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'A': 'd89830', 'a': 'c18a39', 'b': '815423', 'h': '583518', 'W': 'e8e0c0', 'w': 'b2966a', 'k': '282828', 'm': '531b1c', 'R': 'b6433d'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '86_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
