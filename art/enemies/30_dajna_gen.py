"""Writes 30_dajna.txt: the Dajna of Maltese lore -- a titanic primordial
"thunder camel", with the head and neck of a camel but ten times the size of
an elephant; it could not fit into Noah's Ark, but survives in the netherworld.

In the game the player finds what looks like a pyramid dungeon; when they
touch the entrance this rises out of the ground -- the pyramid is its hump. It
towers over the top of the battle arena (a 300 x 165 view, drawn at 2x). Its body
always stands the same way, 3/4 front facing down-right (after the reference
drawing: a shaggy bactrian build, long belly fringe, a long neck sweeping down
and forward then curling up, thick legs on big toed feet, a thin tufted tail),
and only its head turns to look at the player.

The pieces are hand-drawn with the pixel plugin in 30_views.aseprite (exported
to 30_views.png): rows 0-7 the body through one idle cycle (it breathes, the
pyramid rising and settling with it, the fringe sways, the tail swishes, the
neck bobs), row 8 the head from five
sides. This script sets the head on the neck for each of the 8 directions
(the left-facing heads are mirrors; the body never is) and writes all 8 x 8
frames; the sheet is laid out one row per direction (#ROWS), being too wide
for one texture in a single row."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, blank, stamp, write, source_path

VW, VH = 300, 165         # the body view (tall: the pyramid towers over the back)
HW, HH = 56, 44           # one head
ANCHOR = (22, 38)         # where a (right-facing) head meets the neck
NECK_TIP = (266, 77)      # the top of the neck in the body view, at rest
FRAMES = 8
PAL = {'K': '000000', 'T': 'b8986c', 't': '7c6444', 'L': 'd8c0a0', 'M': '5c4a34', 'Y': 'f8f8a8',
       'W': 'fcfcfc', 'P': '8c5c4c', 'S': 'e8c880', 's': 'b89458', 'D': '7c6038', 'k': '2c2014', 'n': 'd0c8b8'}
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
HEAD_OF = {'D': ('D', False), 'DR': ('DR', False), 'R': ('R', False), 'UR': ('UR', False), 'U': ('U', False),
           'UL': ('UR', True), 'L': ('R', True), 'DL': ('DR', True)}      # (drawn head, mirrored)
def bob(n): return round(1.5 * math.sin(2 * math.pi * n / FRAMES - 0.8))   # the neck's bob -- as drawn in the body rows

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '30_views.png'), PAL)
BODY = [grab(0, n * VH, VW, VH) for n in range(FRAMES)]
HEADS = {k: grab(i * HW, FRAMES * VH, HW, HH) for i, k in enumerate(('D', 'DR', 'R', 'UR', 'U'))}

def frame(view, n):
    g = blank(VW, VH)
    stamp(g, 0, 0, BODY[n])
    name, flip = HEAD_OF[view]
    rows = [r[::-1] for r in HEADS[name]] if flip else HEADS[name]
    ax = (HW - 1 - ANCHOR[0]) if flip else ANCHOR[0]
    stamp(g, NECK_TIP[0] - ax, NECK_TIP[1] + bob(n) - ANCHOR[1], rows)   # the head on the neck, turned to the player
    return ['.' + ''.join(r) + '.' for r in g]

def main():
    V = {}
    for n in range(FRAMES):
        V.update({view + (f'@{n}' if n else ''): frame(view, n) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
