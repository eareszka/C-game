"""Writes 41_sasnalkahi.txt: the Sasnalkahi, "the Bear that Pursues" / Tracking
Bear of the Navajo -- one of the Anaye, a monstrous bear living in a
cross-shaped cave at Tse'bahastsit, "the Rock that Frightens"; once it took
up a trail, its prey had no hope of escape.

A big enemy (5 frames, 96 x 64): a huge hulking bear, grizzled dark brown
(pale-tipped guard hairs along its top, scattered flecks), a heavy shoulder
hump, its head held low on the trail, small round ears (drawn over the neck, so
their outline shows from every side), glowing red eyes, long white claws.
Five frames, each hand-drawn whole with the pixel plugin in 41_views.aseprite
(exported to 41_views.png), one cycle: it stalks on the scent -- the head
sniffs down to the ground and swings up snarling, jaws open on red and white
fangs, while the near forepaw lifts in a stalking step and the body
breathes. Laid out as one 3D skeleton turned to each view
(enemy_shapes.skeleton). This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '5c3c24', 'f': '3c2414', 'L': '8c6444', 'D': '241810', 'M': '7c5c40',
       'k': '140c08', 'E': 'e83c28', 'W': 'f0e8d8', 'R': '8c2c2c'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '41_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
