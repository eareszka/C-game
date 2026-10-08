"""Writes 57_dingbat.txt: the Dingbat of Rice Lake, Wisconsin, one of the
lumberjacks' fearsome critters -- a hybrid of bird and mammal, a short
feathered body, short deer's antlers and large wings, like a very fast owl;
it eats bullets out of the air.

A big enemy (5 frames, 96 x 64), 6 directions (the 3/4 views stand in for
front and back): a squat owl's body in barred brown, a pale face disc with
huge round yellow eyes (one fixed shape from every side, ringed black, big
black pupils) and a strong hooked beak, two short branching antlers,
talons tucked under, a short square tail -- and very long wings, barred, the
flight feathers' tips pale along the trailing edge, swept back so they show
from the side too. Five frames, each hand-drawn whole with the pixel plugin
in 57_views.aseprite (exported to 57_views.png), one cycle: a full beat of
the long wings as it hangs in the air, the body bobbing against it. Laid out
as one 3D skeleton turned to each view (enemy_shapes.skeleton). This script
only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'F': '967448', 'f': '5c4616', 'L': 'cebe82', 'C': 'e8e0c0', 'Y': 'f0bc3c',
       'G': '595965', 'A': 'd7a175', 'a': '8d6b4f'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '57_views.png'), PAL, VW, VH, frames=5)
    V = {k: v for k, v in V.items() if k.split('@')[0] not in ('D', 'U')}   # 3/4 views stand in for front and back
    write(source_path(__file__), PAL, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
