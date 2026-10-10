"""Writes 61_roperite.txt: the Roperite (Fearsome Creatures, California), drawn
from the user's reference, always dashing.

A lean olive-tan runner with a ridged scaly back, leaning forward on two big
running bird legs with long clawed feet, its snout drawn out into a long
rope that loops up and back over its body like a lasso, an orange segmented
rattle on its tail, a small arm dangling. Big tier, 8 directions (front and
back drawn turned 25 degrees off head-on, where it would be a thin stack):
five frames, each one hand-drawn whole with the pixel plugin in
61_views.aseprite (exported to 61_views.png), a sprint cycle with speed
streaks trailing behind -- frame 2 the rope lasso flicked out. Laid out as
one 3D skeleton turned to each view (enemy_shapes.skeleton). This script
only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '967448', 'L': 'b29e5c', 'f': '5c4616', 'r': '785830', 'D': '815423', 'd': '583518',
       'R': 'cebe82', 'O': 'd89830', 'o': '876a1f', 'C': 'e8e0c0', 'b': 'c6ccda'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '61_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
