"""Writes 71_namungumi.txt: the Namungumi, drawn from the user's reference: a
flat, blanket-like beast of the dark, its near-black hide arched over itself
like a cloak and webbed all over with pale veins; under the arch a red membrane skirt hangs from each side's edge,
scalloped between its four white-clawed corners; its head a rounded snout
pushed out past the cloak's front, a glowing node on its brow like an eye, a
red gum line under it and a comb of long hooked white fangs hanging below.

Big tier, 6 directions (the 3/4 views stand in for front and back): five
frames, each one hand-drawn whole with the pixel plugin in 71_views.aseprite
(exported to 71_views.png), the hump breathing, the skirt rippling, the
eye pulsing -- frame 2 reared highest, the glow brightest. Laid out as one
3D skeleton turned to each view (enemy_shapes.skeleton). This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'D': '14101e', 'L': '2b1f40', 'w': 'c6ccda', 'W': 'fcfcfc', 'h': '84a7e9',
       'R': 'b6433d', 'r': '792727', 'C': 'bcbeca'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '71_views.png'), PAL, VW, VH, frames=5)
    V = {k: v for k, v in V.items() if k.split('@')[0] not in ('D', 'U')}   # 6 directions: the 3/4 views stand in for front and back
    write(source_path(__file__), PAL, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
