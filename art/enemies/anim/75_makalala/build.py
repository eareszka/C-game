"""Makalala's animation. PixelLab from its 26x43 NES still (pixellab/base.png, 64x64).
Four views (the fight's four_views(): it turns to the player at the clap warning and holds it):
  D = the still (3/4 front, facing left), R = PixelLab's east view, U = its north view, L = R mirrored.
  idle (5 x 260 ms, breath_frame 2 = the scream / clap pose: wings flung out, beak gaping):
       D idled-00 01 02 03 04;  R idler-00 01 03 02 04;  U idleu-00 01 03 02 04
  flap (phase 2, side only, left mirrored; 4 frames per 0.28 s wingbeat): wing-00 raised, 02 level,
       04 lowered, 02 level -- each frame shifted so the ivory club sits still (shots leave it)
Every view is cropped to its own drawing and set in one shared frame (the flap sheet uses the idle's
frame size): standing views feet down and centred, fly frames centred on the club's column.
Run: python -B art/enemies/anim/75_makalala/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
IDLE = {'down': ['idled-%02d' % i for i in (0, 1, 2, 3, 4)],
        'right': ['idler-%02d' % i for i in (0, 1, 3, 2, 4)],
        'up': ['idleu-%02d' % i for i in (0, 1, 3, 2, 4)]}
FLY = ['wing-%02d' % i for i in (0, 2, 4, 2)]
FLY_MS, IDLE_MS = 70, 260

def pal():
    return pt.palette_of(os.path.join(HERE, 'original_sprite.png'))

def ivory(p): return p[3] and p[0] > 200 and p[1] > 190 and p[2] > 150

def club_at(fr):
    px = fr.load(); pts = [(x, y) for y in range(fr.height) for x in range(fr.width) if ivory(px[x, y])]
    return (sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)) if pts else None

def frames():
    P = pal(); L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n + '.png')), P))
    idle = {v: [L(n) for n in ns] for v, ns in IDLE.items()}
    fly = [L(n) for n in FLY]
    c0 = club_at(fly[0])                              # pin the club: shift each frame onto frame 0's club
    fly = [pt.jolt(f, round(c0[0] - c[0]), round(c0[1] - c[1])) for f in fly for c in [club_at(f)]]
    def union(fs):
        bs = [f.getbbox() for f in fs]
        return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    boxes = {v: union(fs) for v, fs in idle.items()}; fb = union(fly)
    W = max([b[2] - b[0] for b in boxes.values()] + [fb[2] - fb[0]])
    H = max([b[3] - b[1] for b in boxes.values()] + [fb[3] - fb[1]])
    def place(fs, b, feet):
        out = []
        for f in fs:
            c = Image.new('RGBA', (W, H), pt.CLEAR); part = f.crop(b)
            c.paste(part, ((W - part.width) // 2, H - part.height if feet else (H - part.height) // 2), part)
            out.append(c)
        return out
    idle = {v: place(fs, boxes[v], True) for v, fs in idle.items()}
    idle['up'] = [fix_back_head(f, idle['up'][0]) for f in idle['up']]
    return idle, place(fly, fb, False), W, H

def fix_back_head(f, f0):
    """From behind, PixelLab turned the scream's head into a hollow yellow ring (no club): frame 0's head
    (club and the neck's top) goes back over every row down to the ring's lowest pixel."""
    px = f.load(); low = max([y for y in range(f.height) for x in range(f.width)
                              if px[x, y][3] and (ivory(px[x, y]) or (px[x, y][0] > 200 and px[x, y][2] < 120))], default=-1)
    p0 = f0.load(); low0 = max(y for y in range(f0.height) for x in range(f0.width) if ivory(p0[x, y]))
    if low <= low0 + 1: return f                    # its club is where frame 0's is: leave it
    out = f.copy(); po = out.load()
    for y in range(low + 1):
        for x in range(f.width): po[x, y] = p0[x, y]
    return pt.tidy(out)

def gif(fs, ms, path):
    W, H = fs[0].size
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).convert('RGB').resize((W * 4, H * 4), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, disposal=2)

if __name__ == '__main__':
    idle, fly, W, H = frames(); gap = 4
    rows = [idle['down'], idle['right'], idle['up'], fly]
    board = Image.new('RGBA', (5 * (W + gap) + gap, 4 * (H + gap) + gap), (24, 24, 32, 255))
    for r, fs in enumerate(rows):
        for i, fr in enumerate(fs): board.paste(fr, (gap + i * (W + gap), gap + r * (H + gap)), fr)
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    board.resize((board.width * 4, board.height * 4), Image.NEAREST).save(os.path.join(rv, 'board.png'))
    for v in ('down', 'right', 'up'): gif(idle[v], IDLE_MS, os.path.join(rv, 'idle_%s.gif' % v))
    gif(fly, FLY_MS, os.path.join(rv, 'fly.gif'))
    print('frame %dx%d' % (W, H))
    off = lambda c: '(%.1f, %.1f)' % ((c[0] + 0.5 - W / 2) * 2, (c[1] + 0.5 - H / 2) * 2) if c else 'none'
    for v in ('down', 'right', 'up'): print('club', v, [off(club_at(f)) for f in idle[v]])
    print('club fly', [off(club_at(f)) for f in fly])
    if '--install' in sys.argv:
        P = {'down': {'idle': idle['down'], 'flap': fly}, 'up': {'idle': idle['up'], 'flap': fly},
             'right': {'idle': idle['right'], 'flap': fly}}
        d = os.path.join(ROOT, 'assets/enemies/redraws')
        pt.sheet(P, 'idle', os.path.join(d, '75_makalala.png'), W, H)
        pt.sheet(P, 'flap', os.path.join(d, '75_makalala_fly.png'), W, H)
        for n, k in (('75_makalala.png', 5), ('75_makalala_fly.png', 4)):
            print(n, *pt.check_frames(os.path.join(d, n), k, W, H, views=(('down', 0), ('right', 2), ('up', 4))), sep='\n  ')
