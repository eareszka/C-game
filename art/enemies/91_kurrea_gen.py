"""Writes 91_kurrea.txt: the Kurrea (Gamilaraay, Boobera Lagoon, New South
Wales): an enormous serpentine reptile living in the bottomless deep of the
lagoon; it cannot cross dry land, so it gouges channels along the banks,
and it devours anyone who fishes, swims or paddles there -- no weapon harms
it; it fears only the bumble tree. A huge olive-mud serpent, heavy coils
piled on the ground, the forebody reared high in an S, a broad blunt
reptile head, a pale ridged belly, a crest of low scutes along the back.
Big tier, 8 directions, five frames: swaying, the coils shifting -- frame 2
the head drawn back, jaws open to strike.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 91_views.aseprite
(exported to 91_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'O': 'b29e5c', 'o': '7b601d', 'q': '5c4616', 'Q': '362a0e', 'P': 'e8e0c0', 'm': '531b1c', 'R': 'b6433d', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '91_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
