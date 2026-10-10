"""Writes 88_amixsak.txt: the Amixsak (Yupik, the Bering Sea): a walrus skin left
behind on the ice sinks and becomes a vengeful monster that rises under a
skin boat, reaches its flippers over the gunwales and pulls it down. An
empty walrus hide risen upright out of the water: a sagging, wrinkled,
hollow brown body, a drooping head with two long tusks and dark empty eye
holes, two big fore-flippers reaching forward, ragged edges dripping
seawater, floating with nothing underneath. Big tier, 8 directions, five
frames: bobbing, the flippers groping -- frame 2 both flippers flung high
to seize, the empty mouth gaping.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 88_views.aseprite
(exported to 88_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'P': 'd7a175', 'p': '8d6b4f', 'q': '463422', 'k': '1e1e24', 'T': 'e8e0c0', 't': 'b2966a', 'C': '3e91cc', 'c': 'dcf0ff'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '88_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
