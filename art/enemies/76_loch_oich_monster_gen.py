"""Writes 76_loch_oich_monster.txt: the Loch Oich Monster (Scotland), from the
user's description: a dog's face on a Loch Ness body.

A long slippery eel-like body in the dog's own brown skin -- a pale wet
sheen along its top, a pale belly -- rippling in low humps to a tapering
tail, no legs, two fins near the front, a long neck, floating like the
game's other water creatures -- and on the end of the neck a big dog's head: brown, a
pale boxy muzzle, a black nose, long floppy ears, eyes with a glint. Big
tier, 8 directions (front and back drawn turned 25 degrees off head-on):
five frames, each one hand-drawn whole with the pixel plugin in
76_views.aseprite (exported to 76_views.png), bobbing, the body rippling, the fins
paddling, the neck swaying -- frame 2 a bark: head up, jaw open, tongue out. Laid out as one 3D
skeleton turned to each view (enemy_shapes.skeleton). This script only lays
them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '94703d', 'f': '633e1b',
       'L': 'c18a39', 'M': 'd7a175', 'k': '22140c', 'P': 'ec8476', 'm': '421618', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '76_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
