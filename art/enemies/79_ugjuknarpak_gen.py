"""Writes 79_ugjuknarpak.txt: the Ugjuknarpak (Kodiak Island lake monster;
ugjuk = the bearded seal, -narpak = huge): a giant bearded seal that
capsizes kayaks.

A huge blubbery grey seal with a pale belly standing on four thick clawed
legs, a narrow neck lifting a small round head with big glossy black eyes,
long pale whiskers fanned up and out, two big sharp white tusks curving down
from the left and right of its jaw and a row of very pointy fangs between
them (lower fangs bared as it roars); small fanned
flippers on its tail. Big tier, 8 directions (front and back drawn turned 25
degrees off head-on): five frames, each one hand-drawn whole with the pixel
plugin in 79_views.aseprite (exported to 79_views.png), reared up on its
braced hind legs the whole time, clawing at the air with its front paws
swiping up and down in turn, roaring -- the mouth widest on frame 2. Laid out as one 3D
skeleton turned to each view (enemy_shapes.skeleton); plain lit-edge
shading, no repeating textures (the rough-sprite rules). This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '848694', 'L': 'a4aaba', 'f': '595965', 'B': 'bcbeca', 'd': '474751', 'W': 'e8e0c0',
       'm': '421618', 'V': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '79_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
