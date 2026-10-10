"""Writes 62_hugag.txt: the Hugag (Fearsome Creatures, the north woods), drawn
from the user's reference: a huge beast on four very tall, pale, jointless
legs (it cannot lie down; it leans on trees to sleep), its body buried in a
long shaggy green coat hanging in broad flaps down its sides and rump,
fading to golden-brown at their ragged tips, a bald wrinkled pink head hung forward on a short neck, a
heavy drooping moose-like upper lip, small ears, small sunken eyes.

Big tier, 8 directions (front and back drawn turned 25 degrees off
head-on): five frames, each one hand-drawn whole with the pixel plugin in
62_views.aseprite (exported to 62_views.png), swaying, the fringe swinging
-- frame 2 the head lifted, the lip flapped open in a bellow. Laid out as one
3D skeleton turned to each view (enemy_shapes.skeleton). This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'G': '2c6c44', 'g': '235436', 'l': '4fa667', 'B': 'c18a39', 'b': '785830',
       'P': 'f0b890', 'p': 'd7a175', 'Q': 'ec8476', 'q': 'b6433d', 'm': '421618'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '62_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
