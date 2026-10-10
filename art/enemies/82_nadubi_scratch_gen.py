"""Writes 82_nadubi_scratch.txt: the Nadubi scratching, its alt sheet (the
idle's layout: 8 directions x 5 frames, 98x65), played while its claw-scratch
bullet patterns form: reared up on its hind legs, the spider body upright,
the barbs kept, the two front claws raking the air in turn -- 0 the left
claw high, 1 the left claw slashing down, 2 the right claw high, 3 the right
claw slashing down, 4 a beat, both claws drawn back. Drawn with the pixel
plugin in 82_scratch_views.aseprite (exported to 82_scratch_views.png). This
script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '5d1e1f', 'L': '792727', 'f': '280e10', 'C': 'e8e0c0', 'c': 'b29e5c', 'W': 'fcfcfc', 'k': '110000'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '82_scratch_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
