"""Writes 57_dingbat_catch.txt: the Dingbat catching -- the alt idle it shows
whenever it perches still in the air and catches the player's shots to throw
them back (the lore: it eats bullets out of the air). It should read as
"don't shoot me now".

Its very long wings swept forward and cupped round its front like a net,
talons thrown forward and open, eyes staring wide (a pale rim round a small
pupil), beak agape. The same layout as 57_dingbat.png -- 5 frames, 96 x 64,
6 directions -- so the battle swaps it in frame for frame. Five frames, each
hand-drawn whole with the pixel plugin in 57_catch_views.aseprite (exported
to 57_catch_views.png), one cycle: a hover in the catch, the cupped wings
fluttering, frame 2 a short downstroke (the wing-gust fires on it). Laid out
as one 3D skeleton turned to each view (enemy_shapes.skeleton). This script
only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '967448', 'f': '5c4616', 'L': 'cebe82', 'C': 'e8e0c0', 'Y': 'f0bc3c',
       'G': '595965', 'A': 'd7a175', 'a': '8d6b4f'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '57_catch_views.png'), PAL, VW, VH, frames=5)
    V = {k: v for k, v in V.items() if k.split('@')[0] not in ('D', 'U')}   # 3/4 views stand in for front and back
    write(source_path(__file__), PAL, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
