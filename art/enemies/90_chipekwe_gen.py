"""Writes 90_chipekwe.txt: the Chipekwe (Lake Bangweulu, Zambia): a massive
reptile with sleek, dark, hairless skin and a single horn gleaming like
polished ivory; it smashes canoes, kills their crews, and tears the throats
out of hippos. A huge heavy rhino-reptile, dark slate skin, a thick neck
and broad head carrying one long curved ivory horn, pillar legs, a heavy
dragging tail. Big tier, 8 directions, five frames: a heavy breath, the
tail swaying -- frame 2 the head dropped, the horn thrust forward to gore.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 90_views.aseprite
(exported to 90_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'L': '595965', 'l': '474751', 'd': '34343e', 'k': '1e1e24', 'T': 'e8e0c0', 't': 'b29e5c', 'Y': 'f0bc3c', 'm': '531b1c'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '90_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
