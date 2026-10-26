"""The buried wagon, desert scenery: the covered wagon abandoned and half sunk in sand.

    python art/structures/props/wagon_buried_design.py

48x32, three cells by two: the covered wagon (wagon_covered_design.py), the same
build in the same projection and materials, left to the desert. The sand has
closed over it to the hubs, higher on the right where it drifts -- the sprite
simply ends at a wandering line, as the sunken stone head's does, the ground
being the sand. Its canvas survives over the front half, torn off ragged at the
back and hanging in a ragged hem (after the PixelLab draft
pixellab-out/wagon-buried/sprites/v1); behind that the bare hoops stand over
the bed in wood. Where torn canvas and bare wood meet in one cell, the canvas's
shade gives way first, then the wood's light and shade (four colours a cell).
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, HERE)
from entrance_shapes import Scene, rect, fill, check, four_per_cell
import wagon_covered_design as wc

PAL = wc.PAL
TEAR = 21.0                         # the canvas ends about here, x along the wagon


def torn(x, z):
    """Does canvas still hang at x along the wagon, z up? A ragged back edge, a ragged hem."""
    edge = TEAR + 2.2 * math.sin(z * 1.7) + 1.3 * math.sin(z * 0.6 + 1)
    return x <= edge


def bonnet(sc):
    x0, x1, d0, d1, z0, rise = wc.HOOD
    dm, rad = (d0 + d1) / 2, (d1 - d0) / 2 + 0.6
    arch = lambda d: z0 + rise * max(0.0, 1 - ((d - dm) / rad) ** 2) ** 0.5
    step = 0.25
    cloth, hoops = [], []
    d = d0
    while d <= d1:
        z = arch(d)
        steep = abs(arch(min(d + step, d1)) - arch(max(d - step, d0))) / (2 * step) > 1.1
        x = x0
        while x <= x1:
            if torn(x, z):
                hoop = any(abs(x - h) < 0.5 for h in wc.HOOPS)
                cloth.append((x, d, z, 'c' if hoop else ('b' if steep and d < dm else 'a')))
            x += step
        for h in wc.HOOPS + (wc.HOOD[1],):
            if not torn(h, z):
                hoops.append((h, d, z, 'M' if d < dm else 'D'))     # a bare hoop, lit toward the front
        d += step
    # the front face hangs to a hem that tears up into the cloth now and then
    hem = lambda x: z0 + (1.2 if int(x * 1.3) % 3 == 0 else 0)
    cloth += [(x, d0, z, 'b') for x in [x0 + i * step for i in range(int((x1 - x0) / step) + 1)]
              for z in [z0 + j * step for j in range(int((arch(d0) - z0) / step) + 1)]
              if torn(x, z) and z >= hem(x)]
    sc.points(10, cloth)
    sc.points(12, hoops)


def wagon():
    sc = Scene(48, 32, wc.BASE)
    x0, x1, d0, d1, z0, z1 = wc.BED
    sc.box(0, x0, x1, d0, d1, z0, z1, front='M')
    bonnet(sc)
    sc.flat(3, wc.wheel(11.5), -1)
    sc.flat(4, wc.wheel(30.5), -1)
    sc.ground(x0, x1, d0, d1)
    g = sc.render()
    for y in range(g.h):                      # the bed's boards, as the covered wagon's
        for x in range(g.w):
            if sc.pid[y][x] == 0 and g.g[y][x] == 'M' and (y == 19 or x in (x0 + 1, 21, x1 - 1)):
                g.g[y][x] = 'D'
    # with the canvas gone the bed shows open: its inside in shade, a lit rim round it
    top = {(x, y) for y in range(16) for x in range(g.w) if sc.pid[y][x] == 0 and g.g[y][x] == 'L'}
    for x, y in top:
        if all((x + dx, y + dy) in top for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            g.g[y][x] = 'D'
    # the sand closing over it: nothing below a wandering line, higher on the right; a black
    # line along it where the wagon goes under
    sand = lambda x: round(26.5 - 3.5 * (x / 47) ** 1.4 + 0.8 * math.sin(x * 0.45))
    for x in range(g.w):
        s = sand(x)
        for y in range(s, g.h):
            g.g[y][x] = '.'
        if g.g[s - 1][x] != '.':
            g.g[s - 1][x] = 'K'
    for y in range(g.h):                      # line the cut left with nothing to go round
        for x in range(g.w):
            if g.g[y][x] == 'K' and not any(0 <= x + dx < g.w and 0 <= y + dy < g.h and g.g[y + dy][x + dx] not in '.K'
                                            for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                g.g[y][x] = '.'
    for y in range(g.h):                      # what the cut left loose: a pixel with nothing beside it
        for x in range(g.w):
            if g.g[y][x] != '.' and all(not (0 <= x + dx < g.w and 0 <= y + dy < g.h) or g.g[y + dy][x + dx] == '.'
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g.g[y][x] = '.'
    # canvas and bare wood in one cell: the canvas keeps its two tones, the hoops their mid
    four_per_cell(g, [('c', 'b'), ('L', 'M'), ('D', 'M')], by_count=False)
    check(g, 'buried wagon', objects=True)
    return g


if __name__ == '__main__':
    g = wagon()
    from PIL import Image
    im = Image.new('RGBA', (g.w, g.h), (0, 0, 0, 0))
    for y in range(g.h):
        for x in range(g.w):
            c = g.g[y][x]
            if c != '.':
                im.putpixel((x, y), tuple(int(PAL[c][i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    im.save(os.path.join(HERE, 'wagon_buried.png'))
    for r in g.rows():
        print(r)
