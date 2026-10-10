"""Writes 51_aspidochelone.txt: the Aspidochelone (the Physiologus and the bestiaries):
a sea turtle so huge that its rough back, risen from the water, gathers
sand and plants until it looks like a small island; sailors anchor, land
and light a fire on it, and it feels the heat and dives, dragging ship and
crew down; its breath smells sweet, luring fish into its mouth. A colossal
turtle half sunk in a ring of white water: a domed rock-grey shell turned
into an island -- a sandy shore, a green hilltop, two palm trees and a
little campfire smoking on it -- a great wrinkled head and two broad
flippers breaking the water, seen from a little above. Giant tier, 8
directions, eight frames: breathing, flippers paddling, the palms swaying --
frames 3-4 the head raised, the jaws wide (the sweet breath that lures).

One rough 3D skeleton, the sea seen from a little above (pose_view),
turned to each view (enemy_shapes.skeleton); plain lit-edge shading (the
rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 51_views.aseprite
(exported to 51_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 128, 80
PAL = {'K': '000000', 'A': '8d6b4f', 'a': '605028', 'q': '463422', 'S': 'f4ce80', 's': 'd0c078', 'G': '4fa667', 'g': '2c6c44', 'p': '058f3a', 't': '815423', 'C': '3e91cc', 'c': '84a7e9', 'w': 'dcf0ff', 'F': 'fc9838', 'm': '531b1c', 'Y': 'f0bc3c', 'n': 'a4aaba'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '51_views.png'), PAL, VW, VH, frames=8)
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
