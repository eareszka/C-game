"""Writes 95_witkes.txt: the Witkes (Ket, the Yenisei): a spirit of the depths of
rivers and lakes with no fixed shape, though sometimes seen as a man or a
woman; it digs holes and channels in the riverbed, drowns whoever enters
its whirlpools, and sometimes invites guests down under the water to drink
tea. A tall half-shaped figure of dark river water: a hunched body and
long dripping arms rising out of a turning whirlpool, its lower half
melting into the swirl, a pale hollow face with glowing eyes, one hand
holding out a little cup of tea. Big tier, 8 directions, five frames: the
whirlpool turning, the body swaying -- frame 2 both arms spread wide, the
pool surging up.

One rough 3D skeleton, the pool seen from a little above (pose_view),
turned to each view (enemy_shapes.skeleton); plain lit-edge shading (the
rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 95_views.aseprite
(exported to 95_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'B': '3e91cc', 'b': '2850a0', 'n': '375a94', 'd': '181224', 'c': '84a7e9', 'w': 'dcf0ff', 'F': 'c6ccda', 'Y': 'fae488', 'T': 'fcfcfc', 'h': '8d6b4f'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '95_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
