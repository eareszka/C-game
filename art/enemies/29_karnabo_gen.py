"""Writes 29_karnabo.txt: the Karnabo, a bogey of the French Ardennes -- son of
an itinerant sorcerer and a ghoul, it lurks in a sealed slate quarry; "almost
human in shape, but it has basilisk eyes and a long, trunk-like nose", and its
nasal whistling paralyzes anyone who comes near.

A hunched, gaunt ghoul in a ragged dark cloak with a torn hem: grey-green skin,
thin bent legs, white claws, glowing yellow basilisk eyes and a long wrinkled
trunk of a nose; a sorcerer's son, he leans on a crooked wooden cane. Medium tier: three frames, each one hand-drawn whole with the
pixel plugin in 29_views.aseprite (exported to 29_views.png): row 0 at rest
(the nose drooping), row 1 the eyes blaze and the nose lifts, row 2 the
whistle -- nose raised, the free hand up (the other stays on the cane). Front
and back are mirror images but for the cane. This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 42, 46
PAL = {'K': '000000', 'G': '4fa667', 'g': '2c6c44', 'C': '5e486a', 'c': '361f42', 'Y': 'f0e880',
       'O': 'fc9838', 'W': 'fcfcfc', 'b': '967448'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '29_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
