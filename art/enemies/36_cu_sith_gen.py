"""Writes 36_cu_sith.txt: the Cu Sith of the Scottish Highlands -- the fairy
hound, dark green, with a long tail braided in a plait and coiled up over its
back; its three barks carry for miles, and whoever hears the third is taken
by terror.

Built like a French bulldog (the user's call): compact, thin legs on small
neat paws, a broad deep chest narrowing to the hips, a smooth dark-green coat, a big
round head with a flat wrinkled snout and jowls, tall bat ears tapering to sharp points (pink
inside from the front, plain from behind), pale glowing eyes -- and the
plaited tail coiled in a ring over its rump. Small -- about the size of the
player (the user's call), so its coat is kept to flat green with a lit top
edge. Medium tier: three frames, each
one hand-drawn whole with the pixel plugin in 36_views.aseprite (exported to
36_views.png): row 0 at rest, row 1 it barks -- head up, jaw dropped, red
mouth and white fangs -- row 2 it settles, the plait swaying. Laid out as one
3D skeleton turned to each view (enemy_shapes.skeleton). This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 30, 28
PAL = {'K': '000000', 'F': '2c6c44', 'f': '184028', 'L': '5c9c64', 'D': '102c1c', 'k': '141c18',
       'Y': 'e8f080', 'R': '9c2c34', 'W': 'f0f0e0', 'P': 'c87078'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '36_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
