"""68 Shuyu's back views built from its front ones (PixelLab's rotate drew U and UR with their faces still
turned to us; the user: make the change). From behind a body's outline is its front's mirrored: U is frame 0
mirrored, UR the DR view (the mirror of DL), each with its faces off -- the beaks to feather red, and the
black of the eyes beside them too. Combs, necks and the lines between them stay. Its three tails, which the
front views show off to one side, come off that side and go on as a fan over the lower back, drawn over
everything (the user: "tail should be drawn on top of everything if back faced"). PixelLab's views are kept
as idle_view_*_rotated.png.

    python art/enemies/pixellab/68_shuyu/backs.py
"""
from pathlib import Path
import shutil
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
BEAK = {(0xf0, 0xbc, 0x3c), (0xc9, 0xa4, 0x33)}
RED, BLACK = (0xb6, 0x43, 0x3d), (0, 0, 0)
PAL = {'K': (0, 0, 0), 'D': (0x79, 0x27, 0x27), 'd': (0x53, 0x1b, 0x1c), 'M': RED}
HEADS = 21            # the heads and necks are above this row; the feet below are yellow too
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FAN = [               # the three tails from behind, fill only (outlined where it is drawn)
    'D...D...D',
    'DD.dDd.DD',
    'dDDdDdDDd',
    '.dDDDDDd.',
    '..ddddd..',
]
# Each view: the columns its side tail sits in (cleared), rows TAIL, and where the fan's top left goes.
TAIL = range(22, 35)


def face_off(im):
    out = im.copy()
    beaks = [(x, y) for y in range(HEADS) for x in range(im.width) if im.getpixel((x, y))[3] and im.getpixel((x, y))[:3] in BEAK]
    for x, y in beaks:
        out.putpixel((x, y), RED + (255,))
        for dx, dy in N4:                                       # the eyes either side of a beak
            p = (x + dx, y + dy)
            q = im.getpixel(p)
            ring = [im.getpixel((p[0] + ex, p[1] + ey)) for ex, ey in N4]
            if q[3] and q[:3] == BLACK and all(r[3] for r in ring):   # inside the head, not its outline
                out.putpixel(p, RED + (255,))
    return out


def outline(im):
    """Black on every clear pixel beside a coloured one."""
    out = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] and p[:3] != BLACK:
                for dx, dy in N4:
                    q = (x + dx, y + dy)
                    if 0 <= q[0] < im.width and 0 <= q[1] < im.height and not im.getpixel(q)[3]:
                        out.putpixel(q, BLACK + (255,))
    return out


def untail(im, cols):
    """The side tail cleared (its columns, rows TAIL), the body's edge outlined again."""
    out = im.copy()
    for y in TAIL:
        for x in cols:
            out.putpixel((x, y), (0, 0, 0, 0))
    return outline(out)


def fan(im, at):
    """The tail fan over everything, its own outline drawn over what is under it."""
    g = {(at[0] + x, at[1] + y): c for y, r in enumerate(FAN) for x, c in enumerate(r) if c != '.'}
    out = im.copy()
    for (x, y) in g:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in g:
                out.putpixel(q, BLACK + (255,))
    for p, c in g.items():
        out.putpixel(p, PAL[c] + (255,))
    return out


VIEWS = {   # view: (its front, the side tail's columns on that front, the fan's top left)
    'U': (lambda: ImageOps.mirror(untail(Image.open(HERE / 'idle_frame0_clean.png').convert('RGBA'), range(35, 50))), (18, 27)),
    'UR': (lambda: untail(Image.open(HERE / 'idle_view_DR.png').convert('RGBA'), range(0, 21)), (21, 27)),
}

if __name__ == '__main__':
    for v, (front, at) in VIEWS.items():
        keep = HERE / f'idle_view_{v}_rotated.png'
        if not keep.exists():
            shutil.copy(HERE / f'idle_view_{v}.png', keep)
        im = fan(face_off(front()), at)
        im.save(HERE / f'idle_view_{v}.png')
        shutil.copy(HERE / f'idle_view_{v}.png', HERE / f'flap_view_{v}.png')
        print(v, im.getbbox())
