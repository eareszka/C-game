"""Writes 59_tripodero.txt: the Tripodero of the California chaparral (Cox,
Fearsome Creatures of the Lumberwoods): a small strong body on two telescopic
legs with a kangaroo's tail behind for the third foot of the tripod; its face
all nose; it rises over the brush on
its legs, sights down its snout and fires a slug with perfect aim.

A small sandy body riding high on two very long, thin, jointed stilt legs
-- the legs are nearly the whole of it -- a short kangaroo tail drooping
behind, a small head whose face is one long, thin anteater's snout curving down to
a dark bore at its tip. Medium tier: three frames, each
one hand-drawn whole with the pixel plugin in 59_views.aseprite (exported to
59_views.png), the long legs re-set like a tripod's each frame: row 0 the
legs staggered one way, row 1 both planted wide and the legs run out to
full height as it fires -- a red clay slug just off
the muzzle -- row 2 staggered the other way. Laid out as one 3D skeleton turned to each
view (enemy_shapes.skeleton). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 52, 60
PAL = {'K': '000000', 'F': 'b29e5c', 'f': '7b601d', 'L': 'cebe82', 'd': '605028', 'N': '8d6b4f',
       'P': 'd7a175', 'c': 'b6433d', 'k': '22140c'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '59_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
