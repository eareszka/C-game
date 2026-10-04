"""Writes 44_itqiirpak.txt: the Itqiirpak of Yup'ik folklore (Scammon Bay) -- a
crimson fireball flickering over the western sea, or a giant hand with a
mouth on each fingertip and one great mouth in its palm; an omen of
disaster, it once burned into a men's house to drag off bad-mannered
children.

A giant enemy (8 frames, 128 x 80), after the user's reference drawing:
an actual hand -- since it always faces the player (every direction shows
the palm) it is drawn flat, as a hand is drawn: a palm square across the
knuckles, rounding underneath into the heel of the hand in one curve from
the thumb round to the far side, four thick,
tapering, jointed fingers of different lengths (the middle longest) lying
close with dark gaps between them, a thick jointed thumb angled up and out
from the lower side of the palm (its underside filled smoothly into the heel), one
outline round the lot, knuckle and joint creases; a round toothed mouth on
each fingertip pad (the thumb's too), and a vast mouth in the palm with big
white teeth, wrinkles arcing above and below it. Eight frames,
each hand-drawn whole with the pixel plugin in 44_views.aseprite (exported
to 44_views.png), one cycle: the fingers spread and the mouths gape, then
the fingers curl in and the mouths clamp shut, the hand bobbing as it hovers.
The sheet is laid out one row per direction (#ROWS). This script only lays them out
for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 128, 80
PAL = {'K': '000000', 'F': 'e0b8a8', 'f': 'a07868', 'L': 'f4dcd0', 'P': 'c86070', 'R': 'a83040',
       'k': '4c0c14', 'W': 'f0ecd8'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '44_views.png'), PAL, VW, VH, frames=8)
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
