"""Writes 49_physeter.txt: the Physeter of the old sea charts (Olaus Magnus's
Carta Marina, the bestiaries) -- the ship-sinking whale-monster that rears
out of the sea and spouts water from its head in two great plumes.

Dajna-sized (a 300 x 165 view, drawn at 2x, filling the top of the arena),
drawn flat in the manner of a sea-chart engraving: a colossal head looming
at the player -- a wide jutting jaw gaping with jagged fangs, two great
bloodshot eyes with slit pupils under scowling brows, curling horns, a
crest of spines, barnacles on the brow, spines along the jaw -- twin water
spouts plumed up and curling outward from its blowholes, great spined fan
fins spreading either side, and behind, its scaled serpent body humping
away to a raised tail fluke; hatched with engraved lines. Its body holds
this one pose from every side -- only the eyes turn, to look where the
player is: all eight directions are drawn (no mirroring). Eight frames,
each hand-drawn whole with the pixel plugin in 49_views.aseprite (exported
to 49_views.png), one cycle: the spouts flow, the jaws work, the fins flex,
the fluke sways. The sheet is laid out one row per direction (#ROWS). This
script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 300, 165
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
PAL = {'K': '000000', 'S': '3c5060', 's': '24343c', 'L': '6c8890', 'h': '18242c', 'P': 'c8b894',
       'p': '8c7c60', 'R': '9c242c', 'r': '5c1018', 'k': '200808', 'W': 'f0e8d0', 'w': 'b8ac90',
       'E': 'f4ecd8', 'Y': 'e8b830', 'B': 'd8ecf8', 'b': '88b0d0', 'H': 'd8c8a0'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '49_views.png'), PAL, VW, VH,
                     frames=8, order=ORDER)
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
