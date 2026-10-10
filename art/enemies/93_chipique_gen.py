"""Writes 93_chipique.txt: the Chipique (the Zambezi above Victoria Falls): a
river serpent some thirty feet long with a small slate-grey head and a
heavy body winding in black coils; it rules the river by night, so no one
goes near the falls after dark, and it can seize a canoe and hold it fast.
A long heavy black serpent swimming in arching loops, each loop rising out
of and diving into a ring of white water, a small grey head reared up in
front, seen from a little above. Big tier, 8 directions, five frames: the
loops rolling forward -- frame 2 the head darting forward, jaws open.

One rough 3D skeleton, pitched to be seen from a little above (pose_view),
turned to each view (enemy_shapes.skeleton); plain lit-edge shading (the
rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 93_views.aseprite
(exported to 93_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'B': '34343e', 'b': '1e1e24', 'k': '0c0a12', 'G': '848694', 'g': '595965', 'C': '3e91cc', 'c': '84a7e9', 'w': 'dcf0ff', 'm': '531b1c', 'Y': 'f0e880'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '93_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
