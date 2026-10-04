"""Writes 26_akhekh.txt: the Akhekh of Egyptian art -- an antelope (oryx) with
bird's wings on its back and a bird's head and beak crowned with three uraei,
the royal cobras; in some accounts a serpent's tail. An ally of Set.

It flies: a sandy oryx body (white belly under a dark flank stripe), its legs
tucked up under it like a leaping antelope's, Egyptian wings (a gold leading
edge, a lapis band, turquoise flight feathers), a falcon's head with a hooked
gold beak and three gold uraei with red sun discs, and a green serpent for a
tail hanging from the rump past the tucked hind legs (the same place from every
side), swinging side to side. Medium tier: three frames, each hand-drawn whole with the pixel plugin in
26_views.aseprite (exported to 26_views.png): row 0 at rest, row 1 the wings
raised as it sinks a pixel (the tail serpent swung one way, tongue out), row 2
the downstroke lifting it a pixel (the tail swung the other way). Front and back are exact mirror images. This script
only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 52, 42
PAL = {'K': '000000', 'S': 'e0c088', 's': 'b89858', 'W': 'fcfcfc', 'D': '3c2c20', 'Y': 'f8d878',
       'G': 'd8a800', 'B': '2c5cc8', 'b': '3cbcb4', 'R': 'b71c00', 'g': '4c9c50'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '26_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
