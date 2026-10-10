"""Writes 64_dungavenhooter.txt: the Dungavenhooter (Fearsome Creatures,
Maine): it has no mouth -- it lies in wait by the logging trails, pounds its
victims to vapour with its clubbed tail, and sniffs them up through its
nostrils.

A squat mossy olive-brown crocodilian, scaly all over (a diamond lattice of
plates), a lit back, one continuous pale belly
line from chin to tail, short splayed legs, a long mouthless snout ending in a bulb of big pink-rimmed flaring
nostrils, yellow slit eyes on bumps, a heavy tail ending in a big knobbly grey
bone club. Big tier, 8 directions (front and back drawn turned 25 degrees off head-on),
eight frames (its fight is one tail slap, looped, so it gets the smoother
eight), each one hand-drawn whole with the pixel plugin in 64_views.aseprite
(exported to 64_views.png): 0 rest, 1 lifting, 2 rising, 3 overhead, 4 the
peak, 5 swinging down, 6 IMPACT -- a tan dust crown bursting out round the
club, plumes rising, grit flung up -- 7 the dust spreading and settling.
The splash centre sits at (35,61) D, (30,61) DR, (21,61) R, (30,61) UR,
(35,61) U in the 98x65 frame; the left views mirror (x -> 97 - x). Laid out as one 3D skeleton turned to
each view (enemy_shapes.skeleton). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '685018', 'L': '876a1f', 'f': '362a0e', 'B': 'cebe82', 'w': 'b29e5c', 'k': '22140c',
       'P': 'ec8476', 'E': 'f0bc3c', 'C': 'a4aaba', 'c': '595965', 'v': 'c6ccda', 'V': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '64_views.png'), PAL, VW, VH, frames=8)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
