"""Writes 67_lagopus.txt: the Lagopus -- Pliny's "hare-foot", the ptarmigan,
named for feet feathered as shaggy as a hare's.

A plump white grouse in its winter plumage, shaded soft grey underneath, a
small round head with a short dark bill and a red comb over each eye, black
outer tail feathers, standing on great furry hare's feet -- and beating large
white wings, the flight feathers split by short grey lines along their
trailing edge. Medium tier, 6 directions (the 3/4 views stand in for front
and back): three frames, each one hand-drawn whole with the pixel plugin in
67_views.aseprite (exported to 67_views.png): its wings always spread wide,
only rippling in the wind -- row 0 at rest, row 1 the tips lift, row 2 the
tips dip; the body holds still. Laid out as one
3D skeleton turned to each view (enemy_shapes.skeleton). This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 60, 44
PAL = {'K': '000000', 'W': 'fcfcfc', 'w': 'c6ccda', 'G': '848694', 'R': 'b6433d', 'D': '1e1e24', 'k': '292931'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '67_views.png'), PAL, VW, VH)
    V = {k: v for k, v in V.items() if k.split('@')[0] not in ('D', 'U')}   # 3/4 views stand in for front and back
    write(source_path(__file__), PAL, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
