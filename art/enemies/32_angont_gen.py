"""Writes 32_angont.txt: the Angont of Huron lore -- a monstrous venomous
serpent of damp places (lakes, swamps, dark woods) whose poison brought
sickness and death.

A big enemy (5 frames): a swamp serpent coiled in a mound of three coils, its
thick neck rising out of them (the top coil wrapped in front) into a broad
viper's head -- murky olive scales in rows, dark diamond blotches, a sickly
yellow belly down the front of the neck, heavy brows over acid-green eyes,
white fangs dripping venom; the thin end of its tail trails out of the bottom
coil. Five frames, each hand-drawn whole with the pixel plugin in
32_views.aseprite (exported to 32_views.png), one cycle: the head sways
forward and back and rears, the tongue flicks, the jaws gape and the venom
drips, the coils breathe, and poison skulls drift up off its skin -- three
of them a phase apart, each rising, wobbling and shrinking away. Front and
back are mirror images but for the skulls and the one tail. This script only lays them out
for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'O': '6c7438', 'o': '444c24', 'L': '9ca45c', 'B': '2c3018', 'Y': 'd0cc78',
       'y': '9c984c', 'E': 'd8f040', 'V': '9cf040', 'W': 'fcfcfc', 'P': '8c3c4c', 'R': 'b70000'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '32_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
