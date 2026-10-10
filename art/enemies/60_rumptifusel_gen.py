"""Writes 60_rumptifusel.txt: the Rumptifusel (Cox, Fearsome Creatures of the
Lumberwoods), drawn from the user's reference: a huge thin flat pelt of a
beast, bigger than a man, that lies like a fur robe and smothers whoever
reaches out to stroke it.

Its front a low flat lobe on the ground with two small glossy black eyes at
the very edge; its back half arching up into a rounded hood and curling back
down to the ground, the shaggy dark-brown fur laid in long strands with
grooves between; under the arch its belly, purple and pocked with pores. Big
tier: five frames, each one hand-drawn whole with the pixel plugin in
60_views.aseprite (exported to 60_views.png), the hood breathing up and
down -- frame 2 reared highest, the belly bared most -- the fur rippling
front to back. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '633e1b', 'f': '3c2412', 'L': '94703d', 'r': '2b190e', 'U': '664b95',
       'h': '361f42', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '60_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
