"""Writes 52_sannaja.txt: the Sannaja (the Arabic and Persian wonder-books, set in
Tibet): the greatest of beasts, whose look kills -- any animal that sees it
dies at once, but if it sees the animal first, the sannaja itself dies; so
the Tibetan beasts come at it with their eyes shut, and it dies and feeds
them for weeks. One manuscript paints it with six stubby legs, a
segmented, shelled, turtle-like body and a red spiderish head with two
great staring eyes. A colossal armoured beast: a long domed body of
overlapping bone-ochre shell plates, six short thick legs, a red spider
head low in front with mandibles and two huge round staring eyes. The
biggest enemy in the game (352x224 frames, eight frames; too big to see whole), 8 directions:
breathing, the plates heaving, the legs shifting -- frames 3-4 the head
lifted, the eyes blazing wide (the killing gaze). It always faces the
player: the front drawing in every direction.

One rough 3D skeleton turned to each view (enemy_shapes.skeleton), plain
lit-edge shading (the rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 52_views.aseprite
(exported to 52_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 352, 224
PAL = {'K': '000000', 'B': 'b2966a', 'b': '8d6b4f', 'o': '463422', 'R': 'ec8476', 'r': 'b6433d', 'q': '792727', 'W': 'fcfcfc', 'w': 'c6ccda', 'k': '1e1e24', 'Y': 'fae488', 'L': '967448', 'l': '633e1b'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '52_views.png'), PAL, VW, VH, frames=8)
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
