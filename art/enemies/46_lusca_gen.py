"""Writes 46_lusca.txt: the Lusca of the Bahamas -- the monster of the blue
holes, said to be half shark and half octopus, dragging swimmers and divers
down.

The front half a grey-blue shark rising up -- pale belly, a tall dorsal fin,
pectoral fins, gill slits, a black eye and jaws full of white teeth -- the
back half eight red-brown octopus tentacles with pale suckers, spreading out
round it and curling up at the tips. Medium tier: three frames, each one
hand-drawn whole with the pixel plugin in 46_views.aseprite (exported to
46_views.png): row 0 at rest, row 1 the jaws gape and the tentacles writhe
one way, row 2 they writhe back. Laid out as one 3D skeleton turned to each
view (enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 72, 56
PAL = {'K': '000000', 'S': '6c849c', 's': '44586c', 'L': '9cb0c4', 'W': 'e8ecf0', 'O': 'a84838',
       'o': '702c24', 'p': 'e0a898', 'k': '2c1014', 'R': '9c2c3c'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '46_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
