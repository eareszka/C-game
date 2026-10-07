"""Design for the Crowing Crested Cobra's slither frames
(assets/enemies/05_crowing_crested_cobra_slither.aseprite).

    python art/enemies/05_crowing_crested_cobra_slither_design.py <out.json> [preview.png]
    python tools/draw_views.py <out.json> assets/enemies/05_crowing_crested_cobra_slither

Laid out like the idle sheet: one row, 26x24 frames, directions D DR R UR U UL
L DL, four frames each, played in a loop while it chases the player in phase
2 (Enemy::flap_phase). The coil is let out: the body lies along the ground
in an S that travels from head to tail, a quarter wave a frame, tapering to
the tail. The head is the idle sheet's own (frame 0 of the same direction,
crest to jaw), held a little above the ground on a short neck. L, DL, UL
mirror R, DR, UR.
"""
import json, math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IDLE = os.path.join(HERE, '..', '..', 'assets', 'enemies', '05_crowing_crested_cobra.png')
PAL = {'K': '000000', 'M': 'd0c078', 'D': '967448', 'L': 'e8e0c0', 'R': 'b70000', 'P': 'ec8476'}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
W, H = 26, 24
N_IDLE, FRAMES = 3, 4
HEAD_ROWS = range(1, 9)        # crest to jaw on the idle sheet

def idle_head(d):
    """Frame 0 of direction d, rows HEAD_ROWS, cropped to the head's columns."""
    im = Image.open(IDLE).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    x0 = ORDER.index(d) * N_IDLE * W
    g = [[('.' if im.getpixel((x0 + x, y))[3] == 0 else letter[im.getpixel((x0 + x, y))[:3]])
          for x in range(W)] for y in HEAD_ROWS]
    # the head's columns only: those joined to the crest (the tail tip on the
    # left of the coil reaches these rows too)
    red = [x for x in range(W) if any(r[x] == 'R' for r in g)]
    cols = [x for x in range(W) if any(r[x] != '.' for r in g) and red[0] - 3 <= x <= red[-1] + 3]
    return [r[cols[0]:cols[-1] + 1] for r in g]

# Per view: the way it travels on screen (unit vector; the ground is seen at a
# slant, so up/down runs are shorter) and where the head sits.
VIEWS = {
    'R':  dict(u=(1.0, 0.0),    head=(17, 4), length=19),
    'DR': dict(u=(0.75, 0.55),  head=(15, 8), length=17),
    'UR': dict(u=(0.75, -0.55), head=(15, 1), length=17),
    'D':  dict(u=(0.0, 1.0),    head=(9, 13), length=20),
    'U':  dict(u=(0.0, -1.0),   head=(9, 0),  length=13),
}

def body_mask(u, base, length, phase):
    """The spine from the neck back, swinging side to side; a disc per step."""
    ux, uy = u
    n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
    px, py = -uy, ux
    mask = set()
    spine = []
    steps = 60
    for i in range(steps + 1):
        s = length * i / steps
        swing = 2.6 * math.sin(2 * math.pi * s / 14.0 - phase) * min(1.0, s / 5.0)
        x = base[0] - ux * s + px * swing
        y = base[1] - uy * s * (0.8 if abs(uy) > 0.9 else 1.0) + py * swing * 0.7
        r = 2.1 - 1.2 * max(0.0, (s - length * 0.5) / (length * 0.5))
        spine.append((x, y))
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                if (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= r * r:
                    mask.add((xx, yy))
    return mask, spine

def frame(view, f):
    v = VIEWS[view]
    head = idle_head(view)
    hw, hh = len(head[0]), len(head)
    hx, hy = v['head']
    g = [['.'] * W for _ in range(H)]
    # neck base: under the head's middle, a few rows below its jaw
    base = (hx + hw / 2.0, hy + hh + 2.5)
    mask, spine = body_mask(v['u'], base, v['length'], f * math.pi / 2)
    # the neck: a short column from the jaw down to the body
    for yy in range(hy + hh - 1, int(base[1]) + 1):
        for xx in range(int(base[0]) - 1, int(base[0]) + 2):
            mask.add((xx, yy))
    mask = {(x, y) for x, y in mask if 0 <= x < W and 0 <= y < H}
    for x, y in mask:
        g[y][x] = 'M'
    for x, y in mask:                      # lit along the top edge
        if (x, y - 1) not in mask and (x, y + 1) in mask:
            g[y][x] = 'L'
    run = 0.0                              # the scale bands: a dark scale every 3 px down the back
    for (x0, y0), (x1, y1) in zip(spine, spine[1:]):
        run += math.hypot(x1 - x0, y1 - y0)
        if run >= 3.0 and (int(x1), int(y1)) in mask and g[int(y1)][int(x1)] == 'M':
            g[int(y1)][int(x1)] = 'D'; run = 0.0
    for y in range(H):                     # outline
        for x in range(W):
            if (x, y) in mask: continue
            if any((x + dx, y + dy) in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    # the head over the body (from behind, the body is nearer: drawn back over it)
    behind = view in ('U', 'UR')
    hg = [r[:] for r in g]
    for y, r in enumerate(head):
        for x, c in enumerate(r):
            if c != '.' and 0 <= hy + y < H and 0 <= hx + x < W:
                hg[hy + y][hx + x] = c
    if behind:
        for x, y in mask:
            if y > hy + hh - 2: hg[y][x] = g[y][x]
    return [''.join(r) for r in hg]

def design():
    views, order = {}, []
    for d in ORDER:
        src = d.replace('L', 'R') if d in ('UL', 'L', 'DL') else d
        for f in range(FRAMES):
            rows = frame(src, f)
            if src != d: rows = [r[::-1] for r in rows]
            views[f'{d}{f}'] = rows
            order.append(f'{d}{f}')
    return {'pal': PAL, 'view_w': W, 'order': order, 'views': views}

def preview(dsg, out):
    """8 directions down, 4 frames across, 6x, on grey -- plus the idle head row for scale."""
    pal = {k: tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) + (255,) for k, v in dsg['pal'].items()}
    im = Image.new('RGBA', (W * FRAMES, H * 8), (70, 70, 70, 255))
    for i, k in enumerate(dsg['order']):
        d, f = i // FRAMES, i % FRAMES
        for y, r in enumerate(dsg['views'][k]):
            for x, c in enumerate(r):
                if c != '.': im.putpixel((f * W + x, d * H + y), pal[c])
    im.resize((im.width * 6, im.height * 6), Image.NEAREST).save(out)

if __name__ == '__main__':
    dsg = design()
    json.dump(dsg, open(sys.argv[1], 'w'))
    if len(sys.argv) > 2: preview(dsg, sys.argv[2])
