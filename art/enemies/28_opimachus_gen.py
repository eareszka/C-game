"""Writes 28_opimachus.txt: the Opimachus (ophiomachus, "snake-fighter") of the
medieval encyclopedias -- small and weak beside a serpent but bold and skilled,
it wins by latching on just below the snake's head; by the Ortus Sanitatis it
had become a small four-legged griffin with a long pointed beak and big
rabbit's ears.

A small, chunky, bold griffin: a round feathered body, a puffed cream breast,
folded brown wings, bird talons in front and lion legs behind, a tufted lion
tail, a long gold beak and tall pink-lined rabbit ears. Medium tier: three
frames, each one hand-drawn whole with the pixel plugin in 28_views.aseprite
(exported to 28_views.png): row 0 at rest, row 1 both ears flick and the wings
lift, row 2 the beak jabs forward. Front and back are exact mirror images.
This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 48, 38
PAL = {'K': '000000', 'F': 'c89858', 'f': '8c6a3c', 'C': 'f0d8a8', 'P': 'ec8476', 'Y': 'e8b830',
       'y': 'a87818', 'B': '6c4c2c'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '28_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
