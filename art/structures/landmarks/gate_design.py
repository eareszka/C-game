"""The lone gate, the wasteland's landmark (the user, 2026-10-27, the wasteland
overhaul; it stands where the burnt wagon did -- art/concept/wasteland/).

    python art/structures/landmarks/gate_design.py --png

48x64: a doorway of the waste stone standing alone in the open, the ground seen
through it -- two piers and a lintel in the houses' projection, laid in the
stone's courses, its top lit and its east side dark -- in the top three rows;
its cache stands before it, the middle cell of the bottom row (the chest, laid
by the game: chest_design.py). --png writes gate.png without the pixel plugin.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landmark_shapes import export, main, check
from entrance_shapes import Scene

# waste stone (the causeways' and the walls' in the wasteland): lit, base, dark
PAL = {'K': '000000', 'L': '9797aa', 'M': '595965', 'D': '34343e'}


def gate():
    sc = Scene(48, 48, 45)
    sc.box(0, 4, 13, 0, 5, 0, 28)                           # the left pier
    sc.box(1, 31, 40, 0, 5, 0, 28)                          # the right pier
    sc.box(2, 4, 40, 0, 5, 28, 35)                          # the lintel across them
    g = sc.render()
    check(g, 'lone gate')
    return g


CACHE, STAMP_W = (1, 3), 3


def design():
    return export('gate', PAL, STAMP_W, 4, [(0, 0, gate())], CACHE, STAMP_W)


if __name__ == '__main__' and '--png' in sys.argv:
    from PIL import Image
    d = design()
    rows = d['views']['gate']
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.':
                h = d['pal'][c]
                im.putpixel((x, y), (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gate.png')
    im.save(out)
    print('wrote', out)
elif __name__ == '__main__':
    main(design)
