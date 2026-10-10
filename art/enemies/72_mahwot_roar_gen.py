"""Writes 72_mahwot_roar.txt: the Mahwot's roar (atomic breath), its alt idle,
played instead of the idle while it stops at the end of a run, turns to the
player and breathes a beam from its mouth.

Stopped, reared steeply up toward the front, a big head thrust forward, jaws
held very wide, thin rims round a gape that is all open mouth, the full V from
the hinge to both tips: dark all through, along both jaws and no
further than the line from tip to tip, white teeth on both rims (the beam leaves the mouth); only
the near eye shows in the turned front and back views, arms thrown forward, its back plates flared and
glowing blue, pulsing, a little shake. Same canvas and layout as the idle
(72_mahwot): big tier, 8 directions (front and back turned 25 degrees), five
frames, each one hand-drawn whole with the pixel plugin in
72_roar_views.aseprite (exported to 72_roar_views.png). The mouth sits at
(64,27) D, (72,27) DR, (83,27) R, (72,27) UR, (64,27) U in the 98x65 frame,
+-1 px of shake; the left views mirror (x -> 97 - x). This script only lays
them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'G': '235436', 'g': '142e1f', 'l': '2c6c44', 'B': 'b29e5c', 'b': '7b601d',
       'P': 'c6ccda', 'p': '848694', 'E': 'f0bc3c', 'W': 'fcfcfc', 'c': '792727', 'h': '84a7e9', 'H': 'dcf0ff', 'm': '421618'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '72_roar_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
