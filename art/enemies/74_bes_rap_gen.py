"""Writes 74_bes_rap.txt: the Bes Rap, the pig spirit of the Jah Hut
(Malaysia), drawn from the user's reference: it lives at the roots of the
pokok ara fig and blows its saliva at fruit-gatherers, who fall sick,
frothing at the mouth.

A big, skinny, creepy pig ghoul: bare pink pig skin, the same pink as its snout, with red-brown shadows,
crouched on its haunches with its knees up high on long-toed human feet lying flat
on the ground, built in the model so they turn with it, long thin arms set wide,
reaching down to the ground on flat palms with long fingers, a long skinny neck lifting a big
long pig head -- a pink snout disc, small sunken eyes, a too-human grin of
square teeth the length of its jaw -- a row of sharp pale-grey spines down
its back. Big tier, 8 directions (front and back drawn turned 25 degrees off head-on,
where the long snout would hide the face): five frames, each one hand-drawn whole with
the pixel plugin in 74_views.aseprite (exported to 74_views.png), breathing
-- frame 2 the head lunging, jaw dropped, a spray of foamy spit (its curse).
Laid out as one 3D skeleton turned to each view (enemy_shapes.skeleton).
This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': 'ec8476', 'L': 'f0b890', 'f': 'b6433d', 'S': '595965', 's': 'a4aaba',
       'T': 'e8e0c0', 'm': '421618', 'P': 'fc74b4', 'p': '7c0a1b', 'w': 'fcfcfc', 'b': 'c6ccda'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '74_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
