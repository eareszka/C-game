"""Writes 25_myrmecoleon.txt: the Myrmecoleon, the ant-lion of the medieval
bestiaries -- the forepart of a lion, the hindpart of an ant; it starves, the
lion half eating only meat, the ant half only grain.

A big enemy (5 frames): a gaunt lion forequarter (dark mane, ribs showing)
joined at a narrow ant waist to a segmented chitin abdomen; two lion forelegs
and four jointed ant legs. Five frames, each one hand-drawn whole with the
pixel plugin in 25_views.aseprite (exported to 25_views.png), one cycle: the
ant legs march in place in an alternating tripod gait, the abdomen pulses, and
the lion winds up and roars -- head lunging, jaws gaping on red with fangs top
and bottom, the mane bristling, brows down. Drawn like the other sprites:
each part (head, mane, body, near foreleg, ant abdomen and waist) its own
outlined shape; three-tone hide with clean rib lines, the mane in locks, the
chitin in segments with a shine. Front and back are exact mirror images. This
script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 68
PAL = {'K': '000000', 'L': 'f0d098', 'T': 'd8a860', 't': 'a87838', 'M': '9c5a28', 'm': '6c3a18', 'C': '4a2a20',
       'c': '2a1810', 'H': '8c6a5a', 'R': 'b71c00', 'r': '6c1000', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '25_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
