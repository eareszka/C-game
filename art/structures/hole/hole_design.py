"""The hole: the starter cave's mouth from the story's turn on (src/story.cpp).
Three pieces, drawn through the pixel plugin by tools/draw_views.py into this
folder; each .aseprite is the source, the PNG beside it the export.

    python art/structures/hole/hole_design.py          # draw, check, review.png + portal_turn.gif
    python art/structures/hole/hole_design.py --review # check and the board again, no redraw

ring.png    48x48   the mouth: a black hole in a ring of broken earth, black
                    cracks running out into the wasteland. 3x3 tiles, the
                    mouth tile the middle cell, so it covers the ladder hole.
portal.png  512x32  the portal, 4 frames of 128x32 side by side: an oval of
                    blue rings swirling about a pale core, the rim dark, a
                    black line round it. 8 tiles wide, 2 tall, hung 5 tiles
                    above the mouth; the swirl turns a quarter band a frame.
page.png    12x8    a page, 2 frames of 6x8: flat, and turning edge-on.

Sheet resolution: 16 px a tile, drawn at 2x by the game like the tileset and
the player. Colours from game_palette.gpl only. The ring keeps the bible's
rock rule in the wasteland's tones (base, shade, black cracks, no lit tone);
the portal is an object: a three-tone blue ramp and black; the page white
with a grey crease and its line.
"""
import json, math, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TOOLS = os.path.join(ROOT, 'tools')
sys.path.insert(0, TOOLS)
from entrance_shapes import Grid

# ── the ring ────────────────────────────────────────────────────────────────
RING_PAL = {'K': '000000', 'M': '341e10', 'D': '110000'}     # black; wasteland fill; its crack tone as shade
RING_W = 48
HOLE_R, RIM_R = 7.0, 15.5           # the hole; the black ring's outer edge

# The slabs of broken earth round the hole, placed by hand: (from, to) in
# degrees clockwise from the right (the first wraps through 0), (inner,
# outer) radius. Ten degrees of black between them, none of the gaps on an
# axis, the widest slab split across.
CHUNKS = [
    (330, 15, 8.0, 14.0), (25, 50, 8.5, 13.0), (60, 100, 8.0, 14.5), (110, 135, 8.0, 13.5),
    (145, 195, 8.0, 11.5), (145, 195, 12.5, 14.5),
    (205, 230, 8.5, 13.0), (240, 285, 8.0, 14.0), (295, 320, 8.0, 13.5),
]
# The cracks: a direction, then the bends (radius, degrees off it). Each ends
# a pixel inside the drawing. (at, from which bend, degrees off, length):
# a short branch.
CRACKS = [
    (22, [(15, 0), (18, 3), (21, -2), (25, 1)]),
    (60, [(15, 0), (19, -4), (23, 2), (27, -1)]),
    (95, [(15, 0), (18, 2), (22, -3)]),
    (130, [(15, 0), (19, 3), (24, -2), (29, 1)]),
    (172, [(15, 0), (18, -3), (21, 1)]),
    (210, [(15, 0), (19, 2), (23, -3), (27, 0)]),
    (255, [(15, 0), (18, -2), (22, 2)]),
    (300, [(15, 0), (19, -3), (24, 1), (28, -2)]),
    (340, [(15, 0), (18, 2), (21, -2)]),
]
BRANCHES = [(1, 2, 25, 4), (3, 2, -30, 4), (5, 1, 30, 3), (7, 2, -25, 4)]


def line(g, x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x1 > x0 else -1), (1 if y1 > y0 else -1)
    err = dx - dy
    while True:
        g.put(x0, y0, c)
        if (x0, y0) == (x1, y1):
            return
        e2 = 2 * err
        if e2 > -dy:
            err -= dy; x0 += sx
        if e2 < dx:
            err += dx; y0 += sy


def ring():
    g = Grid(RING_W, RING_W)
    c = (RING_W - 1) / 2.0
    polar = lambda r, a: (int(round(c + r * math.cos(math.radians(a)))), int(round(c + r * math.sin(math.radians(a)))))
    # the furthest a crack may go in a direction and stay a pixel inside
    lim = lambda a: min(c / max(abs(math.cos(math.radians(a))), 1e-6), c / max(abs(math.sin(math.radians(a))), 1e-6)) - 1.0
    chunk = {}
    for y in range(RING_W):
        for x in range(RING_W):
            r = math.hypot(x - c, y - c)
            if r <= RIM_R:
                g.put(x, y, 'K')
            a = math.degrees(math.atan2(y - c, x - c)) % 360
            for i, (a0, a1, r0, r1) in enumerate(CHUNKS):
                if (a - a0) % 360 <= (a1 - a0) % 360 and r0 <= r <= r1:
                    chunk[(x, y)] = i
    for (x, y), i in chunk.items():               # base, its shade along its bottom and right
        g.put(x, y, 'D' if chunk.get((x + 1, y)) != i or chunk.get((x, y + 1)) != i else 'M')
    pts_of = []
    for a, bends in CRACKS:
        pts = [polar(min(r, lim(a + da)), a + da) for r, da in bends]
        pts_of.append(pts)
        for p, q in zip(pts, pts[1:]):
            line(g, *p, *q, 'K')
    for k, at, da, n in BRANCHES:
        a = CRACKS[k][0] + da
        x, y = pts_of[k][at]
        line(g, x, y, int(round(x + n * math.cos(math.radians(a)))), int(round(y + n * math.sin(math.radians(a)))), 'K')
    return g


# ── the portal ──────────────────────────────────────────────────────────────
PORTAL_PAL = {'K': '000000', 'C': 'dcf0ff', 'L': '5c94fc', 'D': '2850a0'}   # line; core; the rings' light and dark
PW, PH, FRAMES = 128, 32, 4
CORE, RIM, BANDS = 0.22, 0.88, 4      # the core's reach, where the dark rim begins, rings between


def portal(phase):
    """One frame: phase 0..1 turns the swirl one ring inward."""
    g = Grid(PW, PH)
    cx, cy, a, b = (PW - 1) / 2.0, (PH - 1) / 2.0, PW / 2.0 - 1, PH / 2.0 - 1
    ink = set()
    for y in range(PH):
        for x in range(PW):
            u, v = (x - cx) / a, (y - cy) / b
            rho = math.hypot(u, v)
            theta = math.atan2(v, u) / (2 * math.pi) % 1.0
            rho += 0.05 * math.sin(2 * math.pi * (3 * theta + phase))        # the rings wobble, scribbled
            if rho >= 1.0:
                continue
            ink.add((x, y))
            if rho < CORE:
                g.put(x, y, 'C')
            elif rho > RIM:
                g.put(x, y, 'D')
            else:
                band = int(math.floor((rho - CORE) / (RIM - CORE) * BANDS + theta + phase))
                g.put(x, y, 'L' if band % 2 == 0 else 'D')
    # a ring one pixel wide where its curve runs straight down the oval's
    # tips is a sliver: it takes its neighbours' tone (the sliver rule)
    for y in range(PH):
        for x in range(1, PW - 1):
            l, r = g.g[y][x - 1], g.g[y][x + 1]
            if g.g[y][x] in 'LD' and l == r and l in 'LD' and l != g.g[y][x]:
                g.g[y][x] = l
    for x, y in list(ink):                        # the line round it, outside the oval
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in ink:
                g.put(x + dx, y + dy, 'K')
    return g


# ── the page ────────────────────────────────────────────────────────────────
PAGE_PAL = {'K': '000000', 'W': 'fcfcfc', 'G': 'c6ccda'}
PAGES = {
    'flat': [".KKKK.",
             "KWWWWK",
             "KWWWWK",
             "KWWWWK",
             "KGGGGK",
             "KWWWWK",
             "KWWWWK",
             ".KKKK."],
    'turn': ["..KK..",
             ".KWWK.",
             ".KWWK.",
             ".KWWK.",
             ".KGGK.",
             ".KWWK.",
             ".KWWK.",
             "..KK.."],
}


# ── drawing, checking, the review ───────────────────────────────────────────
def designs():
    r = ring()
    return {
        'ring':   {'pal': RING_PAL, 'view_w': RING_W, 'order': ['ring'], 'views': {'ring': r.rows()}},
        'portal': {'pal': PORTAL_PAL, 'view_w': PW, 'order': ['f%d' % i for i in range(FRAMES)],
                   'views': {'f%d' % i: portal(i / FRAMES).rows() for i in range(FRAMES)}},
        'page':   {'pal': PAGE_PAL, 'view_w': 6, 'order': ['flat', 'turn'], 'views': PAGES},
    }


def draw(ds):
    import draw_views
    for name, d in ds.items():
        js = os.path.join(HERE, '_%s.json' % name)
        json.dump(d, open(js, 'w'))
        draw_views.main(js, os.path.join(HERE, name).replace('\\', '/'))
        os.remove(js)


def check():
    """The bible's checker on the three, each held to its kind; then the
    palette on the exports. Non-zero exit on a fail."""
    import overworld_style as ov
    ov.MATERIALS['portal'] = {'tones': ('dcf0ff', '5c94fc', '2850a0'), 'joint': '000000'}
    ov.MATERIALS['page'] = {'tones': ('fcfcfc', 'c6ccda'), 'joint': '000000'}
    ov.PIECES['hole ring'] = ('art/structures/hole/ring.png', 'built', ('wasteland',))
    for i in range(FRAMES):
        ov.PIECES['hole portal %d' % i] = (('art/structures/hole/portal.png', PW * i, 0, PW, PH), 'object', ('portal',))
    for i, n in enumerate(PAGES):
        ov.PIECES['hole page ' + n] = (('art/structures/hole/page.png', 6 * i, 0, 6, 8), 'object', ('page',))
    names = [n for n in ov.PIECES if n.startswith('hole ')]
    fails = 0
    print('%-18s' % 'piece' + ''.join('%7s' % r for r in ov.RULES))
    for n in names:
        res = ov.check(n)
        fails += any(res.values())
        print('%-18s' % n + ''.join('%7s' % (res[r] or '.') for r in ov.RULES))
    print('FAIL: %d pieces' % fails if fails else 'PASS')
    pngs = [os.path.join(HERE, n + '.png') for n in ('ring', 'portal', 'page')]
    rc = subprocess.call([sys.executable, os.path.join(TOOLS, 'palette_check.py')] + pngs)
    return fails == 0 and rc == 0


def review():
    """review.png: the pieces at 4x on black beside the player, and a mock of
    the hole in its wasteland with the portal above and pages falling."""
    from PIL import Image, ImageDraw
    S = 4
    ring_im = Image.open(os.path.join(HERE, 'ring.png')).convert('RGBA')
    portal_im = Image.open(os.path.join(HERE, 'portal.png')).convert('RGBA')
    page_im = Image.open(os.path.join(HERE, 'page.png')).convert('RGBA')
    player = Image.open(os.path.join(ROOT, 'assets', 'player_small.png')).convert('RGBA').crop((0, 0, 14, 20))
    sheet = Image.open(os.path.join(ROOT, 'assets', 'tileset.png')).convert('RGBA')
    grass = [sheet.crop(((18 + i % 3) * 16, (2 + i // 3) * 16, (19 + i % 3) * 16, (3 + i // 3) * 16)) for i in range(6)]
    waste_im = Image.open(os.path.join(ROOT, 'art', 'ground', 'wasteland.png')).convert('RGBA')
    waste = [waste_im.crop(((i % 3) * 16, (i // 3) * 16, (i % 3 + 1) * 16, (i // 3 + 1) * 16)) for i in range(6)]
    ladder = Image.open(os.path.join(ROOT, 'art', 'structures', 'cave_entrance.png')).convert('RGBA').crop((48, 0, 64, 16))
    frames = [portal_im.crop((PW * i, 0, PW * (i + 1), PH)) for i in range(FRAMES)]
    pages = [page_im.crop((6 * i, 0, 6 * (i + 1), 8)) for i in range(2)]

    # the mock, at sheet resolution: 13x9 tiles of grass, the wasteland disc
    # (radius 6) round the mouth, the ladder cell under the ring
    TW, TH, mx, my = 13, 9, 6, 7
    scene = Image.new('RGBA', (TW * 16, TH * 16))
    for ty in range(TH):
        for tx in range(TW):
            cells = waste if (tx - mx) ** 2 + (ty - my) ** 2 <= 36 else grass
            scene.paste(cells[(tx * 2 + ty * 3) % 6], (tx * 16, ty * 16))
    scene.alpha_composite(ladder, (mx * 16, my * 16))
    scene.alpha_composite(ring_im, ((mx - 1) * 16, (my - 1) * 16))
    pcx, pcy = mx * 16 + 8, (my - 5) * 16 + 8
    scene.alpha_composite(frames[0], (pcx - PW // 2, pcy - PH // 2))
    for i in range(16):                               # a few pages on the way down
        t = (i * 0.37 + 0.1) % 1.0
        x = pcx + (i % 7 - 3) * 9 + int(math.sin(t * 9.0 + i) * 5 * (1 - t))
        y = pcy + 14 + int(t * (my * 16 + 4 - pcy - 14))
        scene.alpha_composite(pages[i % 2], (x - 3, y - 4))
    scene.alpha_composite(player, (mx * 16 + 30, my * 16 - 8))

    patch = Image.new('RGBA', (48, 48))              # the ring on its own ground, where it is read
    for i in range(9):
        patch.paste(waste[(i * 5) % 6], ((i % 3) * 16, (i // 3) * 16))
    patch.alpha_composite(ladder, (16, 16))
    patch.alpha_composite(ring_im, (0, 0))

    up = lambda im, s=S: im.resize((im.width * s, im.height * s), Image.NEAREST)
    gif = os.path.join(HERE, 'portal_turn.gif')
    up(frames[0]).save(gif, save_all=True, append_images=[up(f) for f in frames[1:]], duration=120, loop=0)
    W = max(PW * S + 16 + 14 * S + 16, TW * 16 * S + 16)
    rows = [('PORTAL  key frame (1 of %d), 128x32, with the player' % FRAMES, [up(frames[0]), up(player)]),
            ('frames 2-%d at 2x: the swirl turns a quarter ring a frame (portal_turn.gif)' % FRAMES, [up(f, 2) for f in frames[1:]]),
            ('RING 48x48 (3x3 tiles) on its wasteland | bare | the ladder hole it covers | PAGE 6x8: flat, turning | player',
             [up(patch), up(ring_im), up(ladder), up(pages[0]), up(pages[1]), up(player)]),
            ('in place: wasteland disc on grass, portal 5 tiles up, pages falling (mock, not the game)', [up(scene)])]
    H = sum(16 + max(im.height for im in ims) + 8 for _, ims in rows) + 8
    board = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(board)
    y = 8
    for label, ims in rows:
        d.text((8, y), label, fill=(200, 200, 200, 255))
        y += 16
        x = 8
        for im in ims:
            board.alpha_composite(im, (x, y))
            x += im.width + 16
        y += max(im.height for im in ims) + 8
    out = os.path.join(HERE, 'review.png')
    board.save(out)
    return out


if __name__ == '__main__':
    ds = designs()
    if '--print' in sys.argv:
        for n, d in ds.items():
            for k in d['order']:
                print(n, k)
                print('\n'.join(d['views'][k]))
        sys.exit()
    if '--review' not in sys.argv:              # --review: the board again from the exports as they are
        draw(ds)
    ok = check()
    print('review:', review())
    sys.exit(0 if ok else 1)
