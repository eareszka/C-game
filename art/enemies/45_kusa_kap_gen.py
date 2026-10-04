"""Writes 45_kusa_kap.txt: the Kusa Kap of the Torres Strait (Dauan and
Mabuiag) -- the sea-eagle hatched from the egg of Giz, a shape-shifting
dogai, that grew to a gigantic size and seized dugongs in its talons,
carrying them off; travellers in New Guinea told of a bird with a 16-22 ft
wingspan whose wings roared like a steam engine.

A huge white-bellied sea-eagle in flight: white head and breast, a brown
back, broad dark-brown wings of feathers trailing back and down (so they read
as wings from every side) with long fingered primaries, a white tail fan, a
hooked yellow beak and a fierce yellow eye, and gripped in its yellow
talons a grey dugong, snout and fluked tail. Medium tier: three frames, each
one hand-drawn whole with the pixel plugin in 45_views.aseprite (exported to
45_views.png): a wingbeat -- row 0 the wings in a shallow V, row 1 raised
high, row 2 swept down -- the body bobbing with it. Laid out as one 3D
skeleton turned to each view (enemy_shapes.skeleton). This script only lays
them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 76, 58
PAL = {'K': '000000', 'B': '5c402c', 'b': '342418', 'T': '8c6848', 'W': 'f0f0e8', 'w': 'b8b8b0',
       'Y': 'f0c830', 'y': 'b08820', 'G': '8c949c', 'g': '5c646c', 'E': 'f8e040'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '45_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
