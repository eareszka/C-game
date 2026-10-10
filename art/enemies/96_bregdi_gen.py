"""Writes 96_bregdi.txt: the Bregdi (Shetland): a malicious sea monster with long
fins that chases boats, wraps its fins round a vessel and dives with it --
driven off only by slashing the fins with a knife or throwing an amber bead
at it. A huge dark sea beast surfacing out of a ring of white water: a
broad slate-grey back, a thick neck and a heavy finned head with amber
eyes, and two enormous long fins like wings, ribbed and webbed, sweeping up
and round to wrap. Giant tier, 8 directions, eight frames: the fins
sweeping slowly back and forth -- frames 3-4 both fins swung right round
in front, closing to wrap, the jaws open.

One rough 3D skeleton, the sea seen from a little above (pose_view),
turned to each view (enemy_shapes.skeleton); plain lit-edge shading (the
rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 96_views.aseprite
(exported to 96_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 128, 80
PAL = {'K': '000000', 'L': '595965', 'l': '474751', 'd': '34343e', 'k': '1e1e24', 'M': '423c70', 'n': '37387b', 'P': 'a4aaba', 'C': '3e91cc', 'c': '84a7e9', 'w': 'dcf0ff', 'Y': 'f0bc3c', 'm': '531b1c', 'T': 'e8e0c0'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '96_views.png'), PAL, VW, VH, frames=8)
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
