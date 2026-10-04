"""Writes 37_celestial_stag.txt: the Celestial Stag of Chinese lore -- a stag
spirit trapped deep in the mines, which begs miners to carry it up to the
surface, offering to lead them to precious metal in return.

A slender stag with a night-sky hide -- indigo scattered with stars, lit
along the top -- branching golden antlers, glowing golden eyes and a white
scut. A prancing stride, after the user's reference: the near foreleg raised
high (forearm forward, hoof hanging back), the far foreleg planted straight,
the near hind leg stepping under the belly with its hoof lifted, the far hind
planted back, the neck rising steeply, the tail flicked up -- and the head
turned on the neck to look straight at the player from every direction.
Medium tier: three frames, each one hand-drawn whole
with the pixel plugin in 37_views.aseprite (exported to 37_views.png): row 0
at rest, row 1 its stars twinkle and the antler tips glow, row 2 it dips its
head, bargaining. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton).

Six directions, like the Snawfus (the user's call): no straight-on front or
back -- facing you it shows its 3/4 front, facing away its 3/4 back (the
build reuses DR for D and UR for U). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 56, 63
PAL = {'K': '000000', 'N': '4048a0', 'n': '2c3070', 'I': '7078d0', 'S': 'f8f8d0', 'G': 'f0c840',
       'g': 'b08820', 'Y': 'fff0a0', 'W': 'e8e8f8'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '37_views.png'), PAL, VW, VH)
    V = {k: v for k, v in V.items() if k.split('@')[0] not in ('D', 'U')}   # 3/4 views stand in for front and back
    write(source_path(__file__), PAL, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
