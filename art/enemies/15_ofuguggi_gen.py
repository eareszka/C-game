"""Writes 15_ofuguggi.txt: the Ofuguggi, the Reverse-Fin Trout -- "a normal
brown trout with the exception of reversed fins", jet-black outside with red
flesh, that "swims backwards with its tail first and the head following".

So it leads with its tail: facing right, the tail points right and the head
trails; head-on you see the tail fin edge-on, from behind you see its face.
Fins sweep toward the tail. A grey sheen on the back keeps the black body
readable on a black screen; red gills and a red flank line show the flesh.
The five rest views and the open mouths are hand-drawn with the pixel plugin
in 15_views.aseprite (exported to 15_views.png); front and back are exact
mirror images. Idle: it bobs, and gasps on the way down."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, float_frame, write, source_path

VW, VH = 30, 20           # one drawn view
W, H = 32, 22             # the frame: a spare column/row all round, room for the bob
PAL = {'K': '000000', 'D': '474751', 'M': '34343e', 'S': '848694', 'R': 'b70000', 'r': '7c0a1b',
       'P': 'ec8476', 'G': '9797aa'}
ORDER = ('D', 'DR', 'R', 'UR', 'U')
BOB = (1, 0, 2)
# Open mouths: (box in 15_views.png, where it goes on the view). Only where the face shows:
# the side (head trailing on the left), 3/4 back (head trailing toward you), and from behind.
MOUTH = {'R': ((0, 21, 3, 3), (2, 11)), 'UR': ((4, 21, 4, 3), (6, 12)), 'U': ((9, 21, 6, 3), (12, 12))}

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '15_views.png'), PAL)
VIEWS = {k: grab(i * VW, 0, VW, VH) for i, k in enumerate(ORDER)}
OPEN = {k: (grab(*box), at) for k, (box, at) in MOUTH.items()}

def main():
    V = {}
    for suffix, n in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({view + suffix: float_frame(VIEWS[view], n, OPEN.get(view), (W, H), BOB) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
