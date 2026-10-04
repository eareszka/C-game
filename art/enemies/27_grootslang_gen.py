"""Writes 27_grootslang.txt: the Grootslang ("great snake") of South Africa --
an enormous serpent with an elephant's head, lurking in a cave said to be full
of diamonds.

A big enemy (5 frames): a grey-scaled serpent coiled in a tall mound of three
coils, its neck -- as thick as a coil -- rising out of the mound like a snake's,
the top coil wrapped in front of it, up into an elephant's head -- big ears (a light rim, a darker fold, pink at the
heart; plain grey from behind), curving ivory tusks and a long, wrinkle-ringed trunk tapering to a flared, curling tip. The head
and ears turn with the view: from the side the ear flap lies over the side of
the head behind the eye and the trunk hangs from the front of the face; 3/4
front, the near ear big over the head, the far one small behind it; from
behind, the backs of the ears out either side of the head. Five frames, each
hand-drawn whole with the pixel plugin in 27_views.aseprite (exported to
27_views.png), one cycle: the trunk sways, the ears fan, the top coil breathes
and the rattle shakes -- a rattlesnake's tail rising tall out of the coils,
seen from every side (behind the coils from the front and side, nearer them
from behind).
Front and back are mirror images at rest but for the tail. This script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'E': '9797aa', 'e': '595965', 'L': 'c6ccda', 'I': 'f0e8c8', 'i': 'c8b888',
       'P': 'c88888'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '27_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
