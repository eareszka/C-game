"""Writes 58_agropelter.txt: the Agropelter (Cox, Fearsome Creatures of the
Lumberwoods), which lives in hollow dead trees and hurls branches down on any
logger who passes, with arms like whiplashes. Drawn after the user's
reference.

A big enemy (5 frames, 96 x 64): a shaggy grey-brown monkey squatting on
wide haunches, its body an hourglass -- a broad upper chest and shoulders,
wider than the middle of the chest, a pinched waist, wide hips -- big pale
human feet with five toes, a big round head, and a face half human, half
wolf: a heavy shadowed brow over deep sockets, small glowing white eyes, a
flat dark nose, a short muzzle and a screaming mouth with white fangs, round
ears out at the sides. Its arms are enormously long and skinny, hairless,
pink and ringed with wrinkles, lanky and flailing all over, each rooted in a
shoulder and ending in a long three-fingered hand. The face is a fixed shape,
front on and side on. Five frames, each hand-drawn whole with the pixel
plugin in 58_views.aseprite (exported to 58_views.png), one cycle: the arms
flail, waves running down them out to the hands, each through its own wide
arc, the mouth screaming wider and back. The feet are fixed shapes too, one
per angle -- toes face on, turned at 3/4, heel to toe side on, heels from
behind (at 3/4 back only the foot at the body's edge shows) -- set where
the legs put them. Laid out as one 3D skeleton turned
to each view (enemy_shapes.skeleton). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '967448', 'f': '605028', 'L': 'b2966a', 'S': 'f0b890', 's': 'd7a175',
       'd': '8d6b4f', 'G': 'a4aaba', 'g': '595965', 'M': '5e486a', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '58_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
