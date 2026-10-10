"""Writes 97_ro.txt: the Ro (the Mandaean books, Iraq and Iran): a dragon
with a winged body and a long scaly tail and a malign, near-human cunning;
it laid traps to lure and devour people until seven heroes blinded and
silenced it with arrows and shut it in a pit, where it still howls and
stirs the waters round it. A huge dark-red dragon reared up on its hind
legs, a long neck and horned head, great leathery wings spread wide, a
long scaly tail curling round its feet, a pale golden belly, burning eyes.
Giant tier, 8 directions, eight frames: the wings beating slowly -- frames
3-4 the wings thrown high, the head raised, jaws wide, howling.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), wing
membranes as flat panels behind it (rough.membrane); plain lit-edge
shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 97_views.aseprite
(exported to 97_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 128, 80
PAL = {'K': '000000', 'R': 'b6433d', 'r': '792727', 'q': '5d1e1f', 'Q': '421618', 'M': '7c0a1b', 'm': '531b1c', 'G': 'f0bc3c', 'g': 'd89830', 'T': 'e8e0c0', 'Y': 'fae488', 'k': '280e10'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '97_views.png'), PAL, VW, VH, frames=8)
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
