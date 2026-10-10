"""Writes 78_zankallala.txt: the Zankallala (Hausa folklore, West Africa): a
tiny boastful trickster who rides a jerboa, carries a snake as a
walking-stick, wears scorpions as spurs and a swarm of bees as a hat -- the
Dodo swallowed it three times and it burst out of its head.

A big sandy jerboa (huge ears, a long low body leaning into a hop, long hind
legs, a long dark-tufted tail) with the tiny dark-brown big-eared rider
perched on its back: a green snake staff, red scorpion spurs, a little swarm
of yellow bees for a hat. Medium tier, 8 directions (front and back drawn
turned 20 degrees off head-on): three frames, each one hand-drawn whole with
the pixel plugin in 78_views.aseprite (exported to 78_views.png): 0 at rest,
1 the snake staff raised in a boast, 2 the jerboa's ears twitching. Its run
is a separate sheet (78_zankallala_run). Laid out as one 3D skeleton turned
to each view (enemy_shapes.skeleton); plain lit-edge shading, no repeating
textures (the rough-sprite rules). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 56, 52
PAL = {'K': '000000', 'J': 'cebe82', 'j': 'b29e5c', 'I': 'f4ce80', 'w': 'e8e0c0', 'D': '633e1b', 'd': '3c2412', 'E': '815423',
       'G': '2c6c44', 'g': '163623', 'Y': 'f0bc3c', 'R': 'b6433d', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '78_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
