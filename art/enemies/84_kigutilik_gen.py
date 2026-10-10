"""Writes 84_kigutilik.txt: the Kigutilik (Inuit, the central Arctic).

A huge hairless violet beast standing high on four long knobby-kneed stilt
legs, shaggy brown fur hanging down the backs of its legs and along its
back, two curling tentacle tails, a heavy walrus head with a fanged
underbite and two long downward tusks, a cup-shaped bowl growing on a stalk
from the top of its head (from the user's reference). Big tier, 8 directions
(front and back drawn turned 25 degrees): five frames, each one hand-drawn
whole with the pixel plugin in 84_views.aseprite (exported to 84_views.png),
the tails curling, a slow sway -- frame 2 the head raised, the jaws open.
This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'V': 'b69cee', 'v': '664b95', 'u': '3b2a58', 'F': '967448', 'f': '785830', 'h': '463422',
       'T': 'fcfcfc', 't': 'c6ccda', 'm': '301b5a', 'P': 'fc74b4'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '84_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
