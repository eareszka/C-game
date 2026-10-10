"""Writes 72_mahwot.txt: the Mahwot, from the user's description: a mini
swimming Godzilla, all scales and fins (drawn bolder than first sketched so it reads at
battle size).

A slim reptile body thrown into a fast swimming S-wave (side to side,
with an up-and-down ripple riding it), a blunt angry dinosaur head with
small yellow eyes under heavy brows, a row of big jagged green plates down
its back tipped bone-white, biggest mid-back, a green finned tail, little limbs tucked
back as it swims; charcoal-green scales flecked darker, a tan belly. It
floats in the air like the game's other swimmers. Big tier, 8 directions (front and back drawn turned 25 degrees off
head-on, where its spines would stack up and hide it):
five frames, each one hand-drawn whole with the pixel plugin in
72_views.aseprite (exported to 72_views.png), the swim wave running head to
tail -- frame 2 the jaws open in a roar. Laid out as one 3D skeleton turned
to each view (enemy_shapes.skeleton). This script only lays them out for
the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'G': '235436', 'g': '142e1f', 'l': '2c6c44', 'B': 'b29e5c', 'b': '7b601d',
       'P': 'c6ccda', 'p': '848694', 'E': 'f0bc3c', 'W': 'fcfcfc', 'c': '792727'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '72_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
