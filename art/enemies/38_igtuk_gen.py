"""Writes 38_igtuk.txt: the Igtuk, "the boomer" of the Iglulik Inuit (after the
mystic Anarqaq) -- the source of the mysterious booming in the mountains. It
"resembles no other living thing": its arms and legs are on its back, its
single large eye level with the arms, its ears in line with the eye, its
nose inside its cavernous mouth, a tuft of thick hair on its chin; the
booming is its jaws working.

The head is a lump (after our first drawing, which the user kept): the
whole front of it a cavernous maw -- red gums, peg teeth, the nose inside --
a shaggy chin tuft, one big amber eye on top flanked by ears. It sits on the
front of a body after the user's reference drawing: a big hunched,
dome-backed blue-grey body scored with wrinkles, on four long gangly jointed
legs darkening toward long feet that roll up into open loops, like a
jester's shoe -- each curl set in the plane facing the camera for its view,
rolling toward the way the creature faces (outward from straight in front or
behind), so every foot reads as a loop from every side; the legs set well
apart so the four curls stay separate in the 3/4 views. Medium
tier: three frames, each one hand-drawn whole with the pixel plugin in
38_views.aseprite (exported to 38_views.png): row 0 the jaw hangs open, row 1
it gapes wide and the body swells, row 2 the jaws slam shut -- the boom. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 76, 56
PAL = {'K': '000000', 'G': '8ca0b0', 'g': '5c7080', 'L': 'b0c4d0', 'd': '3c4c58', 'k': '2c1418', 'R': '8c3438',
       'W': 'f0e8d8', 'Y': 'e0a030', 'H': '3c3430', 'h': '5c5048', 'P': 'c08070'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '38_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
