#!/usr/bin/env python3
"""Look for tile seams in a screenshot of the game window.

Two independent checks, because a seam can show up two ways:

  clear   The renderer clears to (10,10,20) and the ground covers every pixel
          of the frame, so that colour inside the picture is ground that was
          never painted.  Exact, and the only thing the original report showed.

  hair    A row one pixel tall that differs from the row above and below it,
          which are the same as each other.  Catches a seam whose stray content
          happens to be opaque -- a neighbouring atlas cell that is not keyed
          out -- where the clear colour never appears.  One art texel is at
          least two pixels tall at any zoom the game offers, so a one-pixel
          band is never art.

Usage:  python tools/seamcheck.py shot*.png [--no-viewport]

--no-viewport scans the whole image; without it the SDL logical-size
letterbox bars are excluded, since the clear colour belongs there.
"""
import sys, glob

from PIL import Image

LOGICAL_W, LOGICAL_H = 640, 480
CLEAR = (10, 10, 20)
# A seam runs the width of a tile at least, which is 32 logical px and never
# fewer than 32 on screen at any scale the game presents at. Glyph strokes in
# the HUD are also one pixel and also sit between two matching rows, but they
# come in runs of a dozen or two, so the test is the longest unbroken run
# rather than the total.
HAIR_MIN = 32


def viewport(w, h):
    """Where SDL_RenderSetLogicalSize puts the picture inside the window."""
    scale = min(w / float(LOGICAL_W), h / float(LOGICAL_H))
    vw, vh = int(LOGICAL_W * scale), int(LOGICAL_H * scale)
    return (w - vw) // 2, (h - vh) // 2, vw, vh


def longest_run(flags):
    best = run = 0
    for f in flags:
        run = run + 1 if f else 0
        if run > best:
            best = run
    return best


def hairlines(px, x0, y0, x1, y1, horizontal):
    """Rows (or columns) that are a one-pixel band between two matching sides."""
    out = []
    if horizontal:
        for y in range(y0 + 1, y1 - 1):
            n = longest_run(px[x, y] != px[x, y - 1] and px[x, y - 1] == px[x, y + 1]
                            for x in range(x0, x1))
            if n >= HAIR_MIN:
                out.append((y, n))
    else:
        for x in range(x0 + 1, x1 - 1):
            n = longest_run(px[x, y] != px[x - 1, y] and px[x - 1, y] == px[x + 1, y]
                            for y in range(y0, y1))
            if n >= HAIR_MIN:
                out.append((x, n))
    return out


def check(path, use_viewport):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    px = im.load()
    if use_viewport:
        vx, vy, vw, vh = viewport(w, h)
    else:
        vx, vy, vw, vh = 0, 0, w, h
    x0, y0, x1, y1 = vx, vy, vx + vw, vy + vh

    clear_rows = {}
    for y in range(y0, y1):
        n = sum(1 for x in range(x0, x1) if px[x, y] == CLEAR)
        if n:
            clear_rows[y] = n
    hair_rows = hairlines(px, x0, y0, x1, y1, True)
    hair_cols = hairlines(px, x0, y0, x1, y1, False)

    bad = bool(clear_rows) or bool(hair_rows) or bool(hair_cols)
    if bad:
        print('%s  %dx%d  viewport %d,%d %dx%d' % (path, w, h, vx, vy, vw, vh))
        if clear_rows:
            print('   clear colour inside the picture on %d rows: %s'
                  % (len(clear_rows), sorted(clear_rows.items())[:12]))
        if hair_rows:
            print('   one-pixel horizontal bands: %s' % (hair_rows[:12],))
        if hair_cols:
            print('   one-pixel vertical bands:   %s' % (hair_cols[:12],))
    return bad


def main(argv):
    use_viewport = '--no-viewport' not in argv
    paths = []
    for a in argv:
        if a.startswith('--'):
            continue
        paths.extend(sorted(glob.glob(a)) or [a])
    if not paths:
        print('no images'); return 2
    bad = 0
    for p in paths:
        if check(p, use_viewport):
            bad += 1
    print('%d/%d frames with seams' % (bad, len(paths)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
