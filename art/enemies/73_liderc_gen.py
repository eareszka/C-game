"""Writes 73_liderc.txt: the Liderc (Hungarian: the will-o'-wisp hatched from
a black hen's first egg, seen as a flying fire, often a fiery bird): a ghost
hen of fire hovering in the dark.

Creepy: a skinny sooty body hunched forward, a long neck craning up and over
so the small skull of a head hangs low out in front, big staring white eyes
with pinprick red pupils, a gold hooked beak hanging open, a thin ragged
comb of flame, long spindly wings of ragged fire hunched up behind it like a
shroud and a thin streaming tail of fire (pale gold at the root, orange, red
at the tips), long spindly bird legs dangling with long hooked toes. In battle
it can only be seen the closer the player is (the battle fades it); it is
drawn as strong glow on dark so it fades cleanly. Big tier, 8 directions:
five frames, each one hand-drawn whole with the pixel plugin in
73_views.aseprite (exported to 73_views.png), the flames flickering -- frame
2 a flare-up. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'D': '1e1e24', 'd': '0c0a12', 'e': '5d1e1f', 'Y': 'fae488', 'O': 'fc9838',
       'R': 'b6433d', 'r': '7c0a1b', 'W': 'fcfcfc', 'B': 'c9a433'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '73_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
