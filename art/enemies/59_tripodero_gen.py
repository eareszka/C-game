"""Writes 59_tripodero.txt: the Tripodero of the California chaparral (Cox,
Fearsome Creatures of the Lumberwoods): a small strong body on two telescopic
legs with a kangaroo's tail behind for the third foot of the tripod; its face
all nose, a pouch of clay slugs in its left jaw; it rises over the brush on
its legs, sights down its snout and fires a slug with perfect aim.

A stout sandy body on two thin jointed stilt legs, the thick tail swept well
back to the ground, a small head whose face is one long gun-barrel snout with
a dark bore, a pale cheek pouch bulging on its left jaw. Medium tier: three
frames, each one hand-drawn whole with the pixel plugin in 59_views.aseprite
(exported to 59_views.png): row 0 standing, row 1 its legs telescoped out to
full height as it fires -- the cheek pouch emptied, a red clay slug just off
the muzzle -- row 2 sinking back. Laid out as one 3D skeleton turned to each
view (enemy_shapes.skeleton). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 48, 44
PAL = {'K': '000000', 'F': 'b29e5c', 'f': '7b601d', 'L': 'cebe82', 'd': '605028', 'N': '8d6b4f',
       'P': 'd7a175', 'c': 'b6433d', 'k': '22140c'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '59_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
