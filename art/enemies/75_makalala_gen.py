"""Writes 75_makalala.txt: the Makalala (East Africa, "the noisy one"): a
giant ground bird that screams, and clubs its prey to death with the great
bony knob on its head.

A tall dark slate-grey bird on long scaly legs, three-toed feet, an S-curved
neck, a massive ivory bony club grown off the back of its head, knobbed like
a mace, a big hooked yellow beak (a lit
ridge along the top, the darker lower beak tucked under the hook), fierce yellow eyes, short wings, a shaggy
tail plume. Big tier, 8 directions: five frames, each one hand-drawn whole
with the pixel plugin in 75_views.aseprite (exported to 75_views.png),
bobbing -- frame 2 the scream: neck stretched, beak gaping, wings flared.
Laid out as one 3D skeleton turned to each view (enemy_shapes.skeleton).
This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'D': '34343e', 'G': '474751', 'L': '595965', 'B': 'e8e0c0', 'b': 'b29e5c',
       'Y': 'c9a433', 'y': '876a1f', 'g': '848694', 'E': 'f0bc3c', 'c': '792727'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '75_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
