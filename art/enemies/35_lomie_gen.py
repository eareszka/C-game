"""Writes 35_lomie.txt: the Lomie (the "Lossie" of the forests of Bohemia,
after Heylyn and Topsell) -- a moose-like beast with a sac-like bladder under
its neck; hunted, it fills the bladder at water, heats it to boiling as it
runs, and vomits the scalding, poisonous water over the hunters and dogs.

After the user's reference drawing: a moose with a blue-grey hide
scattered with dark spots, a pale belly and legs pale toward the hooves, a
strong neck rising high, a long head and bulbous muzzle (tan beneath, the
mouth a little open; brows, eyes and nostrils drawn in on the face toward
you), pink-eared, big dark-brown antlers -- broad palms sweeping out and
back, four long tines fanning off each, tips well apart -- a pale stub tail -- and the bladder: warty tan skin hanging from the
jaw down to the chest. Medium tier: three frames, each one hand-drawn whole with the pixel
plugin in 35_views.aseprite (exported to 35_views.png): row 0 at rest, row 1
the bladder swells and boils (bubbles in it, the head lifts), row 2 the head
drops and a scalding glob spills from its jaw, steam curling off it. Laid
out as one 3D skeleton turned to each view (enemy_shapes.skeleton), so it
stays in perspective from every side. This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 60, 66
PAL = {'K': '000000', 'F': '6c8ca8', 'f': '3c5468', 'L': '9cb4c8', 'D': '2c3c4c', 'G': 'c4d4dc',
       'g': '849cac', 'A': '8c603c', 'a': '543420', 'k': '3c4450', 'P': 'e0b088', 'p': 'b08058',
       'Q': 'f4d4b0', 'B': 'c0e8f0', 'W': 'f0f8f8', 'M': '7c2c2c', 'E': 'e8b0a8'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '35_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
