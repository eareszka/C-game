"""Writes 85_nanabolele.txt: the Nanabolele (Sotho, southern Africa): river dragons
living in flooded caves, their skin covered in scales that glow in the dark
-- the Sotho hero Hlabakoane crossed their river to cut a shining hide for
a shield. A long low armoured crocodile-dragon, dark river-green, on four
sprawled clawed legs, a ridge of spines down its back and long tail, rows of
glowing yellow-green scale lights along its flanks, glowing eyes. Big tier,
8 directions, five frames: the tail sweeping, the lights pulsing -- frame 2
the jaws gaping, every light blazing.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 85_views.aseprite
(exported to 85_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'D': '29633e', 'd': '235436', 'e': '142e1f', 'B': '2c6c44', 'G': 'a8f0bc', 'g': '4fa667', 'Y': 'f0e880', 'm': '531b1c', 'T': 'e8e0c0'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '85_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
