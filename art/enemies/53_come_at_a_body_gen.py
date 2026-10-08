"""Writes 53_come_at_a_body.txt: the Come-at-a-body of New Hampshire's White
Mountains -- a small woodchuck-like animal with fur soft and velvety as a
kitten's; it rushes at a passer-by out of the brush, stops dead a few inches
short, spits like a cat, and runs off again.

A woodchuck's build: a fat round body low on short legs, a blunt round head
with small round pink-lined ears and a pale muzzle, a pale belly, a short
bushy tail carried low; soft golden-brown fur lit along the top. Medium tier:
three frames, each one hand-drawn whole with the pixel plugin in
53_views.aseprite (exported to 53_views.png): row 0 crouched, row 1 it spits
-- fur puffed out, head thrust forward, ears flat, mouth wide and red with
white fangs, flecks of spit flying -- row 2 it settles back. Laid out as one
3D skeleton turned to each view (enemy_shapes.skeleton). This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 40, 28
PAL = {'K': '000000', 'F': '94703d', 'f': '5c4616', 'L': 'c18a39', 'C': 'cebe82', 'k': '22140c',
       'P': 'ec8476', 'R': 'b6433d', 'W': 'fcfcfc', 'w': 'c6ccda'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '53_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
