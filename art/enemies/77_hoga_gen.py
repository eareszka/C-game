"""Writes 77_hoga.txt: the Hoga, the lake monster of Lake Metztitlan
(Mexico): half ox, half fish.

A big slate-blue fish body with a pale belly, a forked tail, dorsal, belly
and side fins all tapering to points, and on its front a bull's head on a
thick neck -- pale curved horns, a broad pink muzzle with nostrils, small
ears, dark eyes. It floats like the game's other water creatures. Big tier,
8 directions (front and back drawn turned 25 degrees off head-on): five
frames, each one hand-drawn whole with the pixel plugin in 77_views.aseprite
(exported to 77_views.png), the tail sweeping, the body bobbing -- frame 2 a
bellow, the head lifted, the mouth open. Laid out as one 3D skeleton turned
to each view (enemy_shapes.skeleton); plain lit-edge shading, no repeating
textures (the rough-sprite rules). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'G': '375a94', 'g': '37387b', 'l': '3e91cc', 'B': 'a4aaba', 'F': '8d6b4f', 'f': '583518',
       'L': 'b2966a', 'H': 'e8e0c0', 'h': 'b29e5c', 'P': 'd7a175', 'k': '22140c', 'm': '421618'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '77_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
