"""Writes 24_zoureg_three.txt: the Zoureg's three heads, its alt sheet (played
in phase 2 while it sits in the middle firing three lasers): the red-hot
knife snake coiled, its head split into three red-hot needle heads fanned
apart and reared up, glowing -- one for each laser. The Zoureg's own
colours (dark red underside through orange to yellow, a white-hot edge,
white-hot needle points). Medium tier, 8 directions, three frames like its
idle (a gentle sway, frame 1 glowing hottest), each one drawn whole with
the pixel plugin in 24_three_views.aseprite (exported to
24_three_views.png); its frame is wider than the idle's (60x35 against
44x29) to fit the three heads. Laid out as one 3D skeleton turned to each
view (enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 58, 34
PAL = {'K': '000000', 'R': 'b71c00', 'r': '6c1000', 'O': 'f85800', 'Y': 'f8d878', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '24_three_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
