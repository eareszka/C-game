"""Writes 82_nadubi.txt: the Nadubi (western Arnhem Land, Kunwinjku rock art):
malevolent spirits with barbs like stingray spines growing from their
elbows and knees, which they shoot into people to kill them.

Very scary, at the user's asking, and ON ALL FOURS: a gaunt dark red-ochre
spirit crawling like a spider-man -- a long low arched torso slung between
long spindly limbs sprawled wide, elbows and knees jutting high above its
back, clawed hands planted far forward, its elongated skull thrust forward
low, black empty eye sockets with a tiny burning pupil in each, a long
gaping toothed mouth; long sharp bone barbs from its elbows, shoulders and
knees and a crest of them along its spine. Big tier, 8
directions (front and back drawn turned 15 degrees): five frames, each one
hand-drawn whole with the pixel plugin in 82_views.aseprite (exported to
82_views.png), swaying, the barbs bristling -- frame 2 the head reared, one claw raised,
the crest flared, the mouth gaping, as it looses its barbs.
Laid out as one 3D skeleton turned to each view (enemy_shapes.skeleton);
plain lit-edge shading, no repeating textures (the rough-sprite rules).
This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '5d1e1f', 'L': '792727', 'f': '280e10', 'C': 'e8e0c0', 'c': 'b29e5c', 'W': 'fcfcfc', 'k': '110000'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '82_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
