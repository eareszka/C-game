"""Writes 39_ajaju.txt: the Ajaju, terror of the Garo Hills (India) -- like a
chameleon on long kneeless legs, "like bamboo stalks without nodes", with
twelve long, sharp, forked, sickle-like tongues that lick its prey's flesh
away; it lures people with a shrill "wa-o, wa-o".

A green banded chameleon with an orange casque, bulging turret eyes, a
saw-toothed dorsal crest and a tail curled down in a spiral, high on four
straight jointless bamboo-stilt legs; from across its mouth, twelve red
forked tongues. Medium tier: three frames, each one hand-drawn whole with the
pixel plugin in 39_views.aseprite (exported to 39_views.png): row 0 the
tongues hang in a row of strands, row 1 they fan out into writhing sickles,
row 2 it calls "wa-o" -- mouth open, tongues drawn in, the turret eyes
swivelling. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton); the tail's curl and the tongues' fan lie across the
screen in every view (facing_dir). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 60, 46
PAL = {'K': '000000', 'G': '4c9c3c', 'g': '2c6c28', 'L': '8cc858', 'Y': 'c8e090', 'B': 'b8c870',
       'b': '7c8c40', 'O': 'e0803c', 'E': 'e8d040', 'R': 'd83c50', 'r': '8c1c30', 'k': '3c1418'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '39_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
