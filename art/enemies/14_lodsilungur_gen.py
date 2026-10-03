"""Writes 14_lodsilungur.txt: the Lodsilungur, Iceland's hairy trout --
"a trout-like shape", "covered with fine, downy, cottony-white hair", small
deeply-recessed eyes ahead of a bulbous skull, a short snout with an overbite
and pitch-black teeth, and "a beard of reddish hair on its lower jaw and neck".

It floats. The five rest views and the open mouths are hand-drawn with the
pixel plugin in 14_views.aseprite (exported to 14_views.png); front and back
are exact mirror images. This script only adds the idle animation: it bobs up
and down, gaping its black-toothed mouth on the way down."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, float_frame, write, source_path

VW, VH = 30, 20           # one drawn view
W, H = 32, 22             # the frame: a spare column/row all round, room for the bob
PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda', 'W': 'fcfcfc', 'R': 'b6433d', 'P': 'ec8476'}
ORDER = ('D', 'DR', 'R', 'UR', 'U')
BOB = (1, 0, 2)           # where the view sits in the frame: rest, up, down
# Open mouth for the gape frame: (box in 14_views.png, where it goes on the view). No mouth from behind.
MOUTH = {'R': ((0, 21, 5, 4), (21, 10)), 'D': ((6, 21, 8, 4), (11, 11)), 'DR': ((15, 21, 5, 4), (19, 11))}

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '14_views.png'), PAL)
VIEWS = {k: grab(i * VW, 0, VW, VH) for i, k in enumerate(ORDER)}
OPEN = {k: (grab(*box), at) for k, (box, at) in MOUTH.items()}

def frame(view, n):
    return float_frame(VIEWS[view], n, OPEN.get(view), (W, H), BOB)

def main():
    V = {}
    for suffix, n in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({view + suffix: frame(view, n) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
