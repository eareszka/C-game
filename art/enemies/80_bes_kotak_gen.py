"""Writes 80_bes_kotak.txt: the Bes Kotak, the "box spirit" of the Jah Hut
(Malaysia): a box-shaped river spirit in the muddy hollows of rivers that
weighs divers down into the mud until they drown.

Blocky, at the user's asking: a heavy mud-caked wooden box for a body with a
lid set askew, glowing yellow square eyes, a dark slot of a mouth, blocky
arms reaching forward with muddy block hands to grab, nothing at all
underneath -- it floats, bobbing. Big tier, 8 directions: five frames,
each one hand-drawn whole with the pixel plugin in 80_views.aseprite
(exported to 80_views.png), bobbing -- frame 2 the lid lifting
off, the mouth slot gaping, the arms reaching up. Drawn by its own small box
renderer (flat-shaded faces, a slight downward tilt so the tops show) in
place of the skeleton tool's tubes and balls. This script only lays them out
for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'T': 'b2966a', 'F': '8d6b4f', 'S': '583518', 'u': '785830', 'U': '633e1b', 'd': '3c2412',
       'k': '22140c', 'Y': 'f0bc3c', 'O': 'fc9838'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '80_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
