"""Writes 63_hidebehind.txt: the Hidebehind (Fearsome Creatures, the north
woods), drawn from the user's reference: it always hides behind something,
so no one has ever seen it.

A tall faceless cone of long shaggy brown fur, leaning a little forward, its
long forearms raised before it on shaggy paws, four long hooked pale ivory
claws on each fanned out so every claw reads, short thick clawed legs, a long curling bushy tail. Big
tier, 8 directions (front and back drawn turned 20 degrees off head-on):
five frames, each one hand-drawn whole with the pixel plugin in
63_views.aseprite (exported to 63_views.png), swaying, the claws flexing --
frame 2 reared up, claws raised to swipe. Laid out as one 3D skeleton turned
to each view (enemy_shapes.skeleton). This script only lays them out for
the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '633e1b', 'L': '815423', 'f': '3c2412', 'd': '2b190e', 'C': 'e8e0c0'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '63_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
