"""Writes 99_fad_felen.txt: the Fad Felen, the Yellow Plague (Wales, sixth
century): a column of watery cloud joining the earth to the sky, or a hag
with baleful eyes, or a scaly clawed beast with foul breath; anything
living caught in it sickened or died, its victims turned a livid
bloodless yellow, and even the physicians who treated them died -- it took
King Maelgwn Gwynedd. A towering pillar of sickly yellow vapour, billowing
puffs from a swirl on the ground up past the top of the frame's reach, a
gaunt hag face sunk in it with hollow baleful eyes, two long wispy clawed
arms of mist reaching out. Big tier, 8 directions, five frames: the column
churning -- frame 2 the arms flung wide, the mouth gaping, the cloud
swelling.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 99_views.aseprite
(exported to 99_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'Y': 'f0e880', 'y': 'c9a433', 'o': '887000', 'O': '5c4616', 'F': 'fae488', 'k': '241c0a', 'R': 'b70000', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '99_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
