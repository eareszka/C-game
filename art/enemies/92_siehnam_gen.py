"""Writes 92_siehnam.txt: the Siehnam (Chorote, the Gran Chaco): a deer with huge
antlers that came into the villages after midnight, stabbing people with
its antlers and biting the throats of those asleep on their backs, four
each night, until a shaman wrestled it down. A big gaunt night deer, dark
brown, a lean neck, glowing pale eyes, a bloodied muzzle, and an enormous
crown of many-tined bone antlers wider than its body. Big tier, 8
directions, five frames: a slow wary breath, the head turning -- frame 2
the head dropped low, the antlers levelled forward to stab.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 92_views.aseprite
(exported to 92_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'C': '815423', 'c': '633e1b', 'd': '3c2412', 'w': 'b2966a', 'T': 'e8e0c0', 't': 'b29e5c', 'Y': 'f0e880', 'R': 'b6433d', 'k': '282828'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '92_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
