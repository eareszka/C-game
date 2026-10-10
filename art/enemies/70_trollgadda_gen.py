"""Writes 70_trollgadda.txt: the Trollgadda (the troll pike), a huge
ancient pike, old as the lake, moss grown on its back.

A long torpedo body, olive green with rows of pale spots and a white belly,
the dorsal and anal fins set far back by the forked tail as a pike's are,
orange fins striped darker, a long flat duck-bill snout, and a massive tree growing out of its mouth: the trunk
exactly as wide as its stretched-open mouth and that thick all the way up,
wedged in its jaws, running forward past the snout and up, thick boughs
spreading into a massive canopy arching over most of the fish.
It is furious about it: narrowed golden eyes under heavy brows slanting
down to the snout, teeth biting into the trunk. It floats in the
air like the game's other fish. Big tier, 6 directions (the 3/4 views stand in for
front and back, so an eye always faces the player): five frames, each
one hand-drawn whole with the pixel plugin in 70_views.aseprite (exported to
70_views.png), the tail sweeping side to side and the body bobbing -- the tree
swaying; frame 2 the jaws
strained widest.
Laid out as one 3D skeleton turned to each view (enemy_shapes.skeleton).
This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'G': '2c6c44', 'g': '163623', 'l': '4fa667', 'Y': 'd0c078', 'B': 'e8e0c0', 'b': 'b29e5c',
       'R': 'c18a39', 'r': '815423', 'M': '00881b', 'm': '05c43a', 'W': 'fcfcfc', 'c': '792727', 'E': 'f0bc3c',
       'T': '583518', 'A': '00a800', 'a': '4edc4a', 'n': '0e2016', 'w': '84a7e9'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '70_views.png'), PAL, VW, VH, frames=5)
    V = {k: v for k, v in V.items() if k.split('@')[0] not in ('D', 'U')}   # 6 directions: the 3/4 views stand in for front and back, an eye always toward the player
    write(source_path(__file__), PAL, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
