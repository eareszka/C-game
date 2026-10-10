"""Writes 83_beast_of_barrisdale.txt: the Beast of Barrisdale (Knoydart, the
Scottish Highlands): a roaring flying beast with great wings and three legs,
reported by stalkers in the 1800s.

A massive, muscular dark beast -- a deep barrel chest, hunched shoulder
humps, a thick bull neck carrying a big head low and forward -- standing on
three massive clawed legs, two planted wide at the front and one under its
rear like a tripod -- huge swept-back leathery bat
wings (dark finger bones, flat purple membranes between them), great pale
curving horns, a big jaw, small burning eyes, a short tail. Big
tier, 8 directions (front and back drawn turned 20 degrees): five frames,
each one hand-drawn whole with the pixel plugin in 83_views.aseprite
(exported to 83_views.png), the wings beating slowly -- frame 2 rearing,
wings thrown high, roaring. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton), the membranes drawn as flat panels between the
fingers; plain lit-edge shading, no repeating textures (the rough-sprite
rules). Its flight is a separate sheet (83_beast_of_barrisdale_fly). This script
only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '474751', 'L': '595965', 'f': '282828', 'M': '5e486a', 'm': '361f42',
       'H': 'bcbeca', 'h': '848694', 'c': '421618', 'E': 'fc9838'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '83_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
