"""Writes 22_cactus_cat.txt: the Cactus Cat, a fearsome critter of the American
Southwest -- "bobcat-like ... covered in hair-like thorns", with "its armored,
branching tail" and forelegs whose bones end in "two sharp, knife-like blades"
for slashing cacti; it comes back to drink the fermented sap.

Drawn like the Snawfus (the user's call): six directions -- side, 3/4 front,
3/4 back; down and up reuse the 3/4 views -- slim graceful legs with one
foreleg lifted mid-step, body and legs still. A green, thorn-spotted bobcat
with tall ears and half-shut tipsy eyes, a tail branching like a saguaro and
bone blades on its forelegs. Medium tier: three frames, each one hand-drawn
whole with the pixel plugin in 22_views.aseprite (exported to 22_views.png):
row 0 at rest, rows 1-2 the head bobbing up / down as the tail bends one way /
the other. This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 44, 34
PAL = {'K': '000000', 'G': '6aa84a', 'g': '3c7a34', 'Y': 'e8e0a0', 'S': 'd7c890', 'W': 'fcfcfc', 'P': 'ec8476'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '22_views.png'), PAL, VW, VH,
                     order=('DR', 'R', 'UR'))
    write(source_path(__file__), PAL, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
