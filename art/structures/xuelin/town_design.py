"""Xuelin as one drawing: its wall and every building drawn so far, each in
its place, for the sheet (gen_entrance_art.py XUELIN) and town_2's overlay.

    python tools/town2_layout.py . <preview.png>            # the plan: layout.json
    python art/structures/xuelin/town_design.py             # this: town.png, town.aseprite
    python art/structures/gen_entrance_art.py --tables --xuelin
    python tools/town2_layout.py . <preview.png> --write    # the overlay from town.png
    python tools/palette_pass.py --write

One drawing, so that where one thing stands in front of another -- the east
wall before the lots behind it, the gate tower before the inn -- the nearer
wins pixel by pixel, as inside any one building (House.put), and each cell
of the sheet is what the eye sees there. A building is its own design
(<name>_design.py draw), shifted to its lot; the wall is drawn here.

The drawing is the town's footprint from CANVAS's top left cell in the
houses' projection: a point x across, d back and z up lands at
(x + d, B - z - d). A street going back, at k = x + y in the footprint, is
x = kx(k) here, whatever the row; row y's ground is d = dy(y) to dy(y) + 15.

The wall (the user, 2026-10-28): 32 high all round, battlements along its
outer edge, a two-storey gate tower over the gate and a tower on each corner
(after PixelLab's pixellab-out/xuelin-wall/sprites/v1 and v2).
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, HERE)
from house_shapes import House, brick_tone
import courtyard_design, shophouse_design, bookshop_design, inn_design, drumtower_design, shrine_design, elder_design
from courtyard_design import TILES, timber
from shophouse_design import PAL, MERGE

PIECES = {'courtyard': courtyard_design, 'shophouse': shophouse_design, 'bookshop': bookshop_design, 'inn': inn_design,
          'drumtower': drumtower_design, 'shrine': shrine_design, 'elder': elder_design}
WALL, MERLON = 32, (6, 4, 5)        # the wall's height; a merlon's width, the gap, how far it stands up
PARAPET = 3                          # the parapet under the merlons, high and deep
GATE_W = 40                          # the arch, its opening across


def plan():
    return json.load(open(os.path.join(HERE, 'layout.json')))


def box(h, x0, x1, d0, d1, z0, z1, front=brick_tone, east=brick_tone, top='W', foot=False):
    """A block of the wall: its front face (at d0), its east face (at x1),
    its top at z1, each a tone or tone(along, down) -- the top's (across, back);
    black round its edges.
    A front tone of None leaves that pixel clear (the gate's arch)."""
    B = h.B
    tone = lambda t, a, b: t(a, b) if callable(t) else t
    for z in range(z0, z1):
        for x in range(x0, x1 + 1):
            c = 'K' if x == x0 or z == 0 or z == z1 - 1 and z0 else tone(front, x - x0, z1 - 1 - z)
            h.put(x + d0, B - z - d0, c, B - d0)
    for d in range(d0 + 1, d1 + 1):
        for z in range(z0, z1):
            c = 'K' if d in (d0 + 1, d1) or z == 0 else tone(east, d - d0, z1 - 1 - z)
            h.put(x1 + d, B - z - d, c, B - d)
    for d in range(d0, d1 + 1):
        for x in range(x0, x1 + 1):
            h.put(x + d, B - z1 - d, 'K' if x in (x0, x1) or d in (d0, d1) else tone(top, x - x0, d - d0), B - d)
    if foot:
        h.stood({(x + d, B - d) for x in range(x0, x1 + 1) for d in range(d0, d1 + 1)})


def battlements(h, x0, x1, d0, d1, z, along='x'):
    """A parapet PARAPET high on the wall's top at z, x0..x1 by d0..d1, and
    its merlons, running across (along 'x') or back ('d')."""
    box(h, x0, x1, d0, d1, z, z + PARAPET)
    w, gap, up = MERLON
    if along == 'x':
        for x in range(x0, x1 - w + 2, w + gap):
            box(h, x, x + w - 1, d0, d1, z + PARAPET, z + PARAPET + up)
    else:
        for d in range(d0, d1 - w + 2, w + gap):
            box(h, x0, x1, d, d + w - 1, z + PARAPET, z + PARAPET + up)


def rampart(h, x0, x1, d0, d1, outer):
    """A run of the wall, its battlements on its outer side: 'front' or
    'back' for a wall across, 'west' or 'east' for one going back."""
    box(h, x0, x1, d0, d1, 0, WALL, foot=True)
    p = PARAPET
    if outer == 'front':
        battlements(h, x0, x1, d0, d0 + p, WALL)
    elif outer == 'back':
        battlements(h, x0, x1, d1 - p, d1, WALL)
    elif outer == 'west':
        battlements(h, x0, x0 + p, d0, d1, WALL, 'd')
    else:
        battlements(h, x1 - p, x1, d0, d1, WALL, 'd')


def corner(h, x0, x1, d0, d1):
    """A corner tower: a block of the wall standing over the corner, higher
    than the wall, and on it a pavilion under a Chinese roof."""
    z = WALL + 10
    box(h, x0, x1, d0, d1, 0, z, foot=True)
    h.hall(x0 + 8, x1 - 8, d1 - d0 - 18, 14, 10, d0=d0 + 9, eave=4, lift=4, ridge=2, tiles=TILES,
           front=timber, z0=z, snow=0.3)


def gate_tower(h, cx, d0, d1):
    """The gate: a bastion across the front wall, standing forward of it and
    higher, an arched passage through it GATE_W wide at cx; on it the tower,
    two storeys, each with its own roof -- the lower's eaves wide, the upper
    smaller and steeper."""
    B, z = h.B, WALL + 8
    x0, x1 = cx - 64, cx + 64
    r, spring = GATE_W // 2, 10

    def face(rx, ry):
        zz, ax = z - 1 - ry, rx - (cx - x0)
        q = ax * ax + max(0, zz - spring) ** 2
        if abs(ax) < r and (zz < spring or q < r * r):
            return None                                  # the passage
        if abs(ax) < r + 3 and q < (r + 3) ** 2:
            return 'K' if q >= (r + 2) ** 2 or q < (r + 1) ** 2 else 'M'     # the arch's ring of stones
        return brick_tone(rx, ry)
    box(h, x0, x1, d0, d1, 0, z, front=face)
    for d in range(d0, d1 + 1):                          # inside the passage: its west wall, and the
        for zz in range(spring):                         # vault over it, seen through the arch (the user,
            h.put(cx - r + d, B - zz - d, 'K' if zz == spring - 1 or d == d1 else 'S', B - d)    # 2026-10-30)
        for ax in range(-r, r + 1):                      # the vault: dark, solid up to its curve
            for zz in range(spring, spring + round((r * r - ax * ax) ** 0.5) + 1):
                h.put(cx + ax + d, B - zz - d, 'K', B - d)
    h.stood({(x + d, B - d) for x in range(x0, x1 + 1) for d in range(d0, d1 + 1) if abs(x - cx) >= r})
    battlements(h, x0, x1, d0, d0 + PARAPET, z)
    h.hall(x0 + 16, x1 - 16, d1 - d0 - 10, 18, 8, d0=d0 + 6, eave=6, lift=5, ridge=2, tiles=TILES,
           front=timber, z0=z, snow=0.3)
    h.hall(x0 + 32, x1 - 32, d1 - d0 - 20, 14, 14, d0=d0 + 11, eave=5, lift=6, tiles=TILES,
           front=timber, z0=z + 18 + 5)


PINE = (18, 0)                # the snow pine's cells on the sheet (src/tilemap.cpp tree_col): canopy, then trunk
PINE_PAL = {'000000': 'K', '235436': 'G', '058f3a': 'g', 'fcfcfc': 'W'}


def cell_ground(h, X0, Y0):
    """The ground point (x, d) near the foot of the screen cell X0, Y0."""
    d = h.B - (Y0 + 10)
    return X0 + 8 - d, d


def pine(h, X0, Y0):
    """A snow pine in the screen cell X0, Y0 (its canopy in the cell above),
    as the country's are drawn: the sheet's own pine, on a low mound of snow
    in the projection, black round it, in its own cell -- only the pine's own
    four colours there. Solid at its foot."""
    from PIL import Image
    x, d = cell_ground(h, X0, Y0)
    box(h, x - 3, x + 3, d - 3, d + 3, 0, 2, front='W', east='W', top='W', foot=True)
    sheet = Image.open(os.path.join(HERE, '..', '..', '..', 'assets', 'tileset.png')).convert('RGBA')
    im = sheet.crop((PINE[0] * 16, PINE[1] * 16, PINE[0] * 16 + 16, PINE[1] * 16 + 32))
    for j in range(32):
        for i in range(16):
            r, g_, b, a = im.getpixel((i, j))
            if a and (r, g_, b) != (255, 0, 0):
                h.put(X0 + i, Y0 - 16 + j, PINE_PAL['%02x%02x%02x' % (r, g_, b)], h.B - d + 1)


def stone_lantern(h, X0, Y0):
    """A stone lantern in the screen cell X0, Y0: a post, a lamp box -- its
    window dark by day -- a cap of snow."""
    x, d = cell_ground(h, X0, Y0)
    box(h, x - 1, x + 2, d - 1, d + 2, 0, 8, front='B', east='B', top='B', foot=True)
    box(h, x - 1, x + 2, d - 1, d + 2, 8, 13, front=lambda a, r: 'K' if 1 <= a <= 2 and 1 <= r <= 3 else 'M',
        east='B', top='B')
    box(h, x - 2, x + 3, d - 2, d + 3, 13, 15, front='B', east='B', top='W')


SNOW_PROPS = os.path.join(HERE, '..', 'props', 'snow')
EXTRA = {}                    # the snow props' own colours -> letters of their own, added to the palette


def letter(hexc):
    """A letter for a colour: the palette's own if it has it, else one of its own."""
    for k, v in list(PAL.items()) + list(EXTRA.items()):
        if v == hexc:
            return k
    k = '0123456789abcefhijklnopqrstuxyz'[len(EXTRA)]
    EXTRA[k] = hexc
    return k


SWAY = (0, 1, -1)              # a hanging lantern's sway, the roots' sine sampled round its loop (core.h's beat)


def lantern_post(h, X0, Y0, side, frame=0):
    """A red lantern post on a street's edge (after PixelLab pixellab-out/
    xuelin-props/sprites/v1): a dark wooden post, an arm reaching over the
    street from its top, the lantern hanging from its end on a short black
    cord -- swaying SWAY[frame] across, three frames on the world's ambient
    beat (src/core.h; the user, 2026-10-29: "this applies to ambient town 2
    props")."""
    from shophouse_design import lantern
    x, d = cell_ground(h, X0, Y0)
    s = 1 if side == 'w' else -1                      # its arm reaches toward the street's middle
    # 24 high, so all of it stands in its cell and the one over it: the cell
    # over that is a step back and west, where the next lot's eaves are
    box(h, x, x + 1, d, d + 1, 0, 24, front='v', east='v', top='v', foot=True)
    a0, a1 = (x, x + 7) if s > 0 else (x - 6, x + 1)
    box(h, a0, a1, d, d + 1, 22, 24, front='v', east='v', top='v')
    end, dx = x + 6 * s, SWAY[frame]
    for z, ox in ((21, 0), (20, dx // 2 if dx > 0 else -((-dx) // 2))):   # the cord, from the arm's end
        h.put(end + ox + d, h.B - z - d, 'K', h.B - d + 1)
    lantern(h, end + dx, 14, d)


def firewood(h, X0, Y0):
    """Split firewood stacked on the street before a house: the logs' ends
    to the street -- pale wood ringed darker -- snow on top."""
    x, d = cell_ground(h, X0, Y0)
    ends = lambda a, r: 'K' if a % 4 == 0 or r % 4 == 3 else 'w' if (a % 4 == 2 and r % 4 == 1) else 'v'
    box(h, x - 5, x + 5, d - 2, d + 2, 0, 9, front=ends, east='v', top='W', foot=True)


def cart(h, X0, Y0):
    """A wooden hand cart (after the PixelLab draft): a plank bed with snow
    lying on it, two wheels, its shafts reaching back."""
    B = h.B
    x, d = cell_ground(h, X0, Y0)
    box(h, x - 5, x + 4, d - 3, d + 3, 4, 7, front='w', east='v', top=lambda a, r: 'W' if a % 3 else 'w', foot=True)
    for dd in (-2, 2):                                # the shafts
        box(h, x - 10, x - 6, d + dd, d + dd, 5, 6, front='v', east='v', top='v')
    for wd in (d - 3, d + 3):                         # the wheels, on its east side
        for j in range(-3, 4):
            for i in range(-3, 4):
                q = i * i + j * j
                if q <= 10:
                    h.put(x + 5 + wd + i, B - 4 - wd + j, 'K' if q > 5 or q == 0 else 'v', B - wd + 1)


def snow_prop(h, X0, Y0, name):
    """One of the snow country's own props, as drawn (art/structures/props/
    snow), its foot on the cell's floor; solid where it stands."""
    from PIL import Image
    im = Image.open(os.path.join(SNOW_PROPS, name + '.png')).convert('RGBA')
    w, ht = im.size
    top = Y0 + 16 - ht
    for j in range(ht):
        for i in range(w):
            r, g_, b, a = im.getpixel((i, j))
            if a and (r, g_, b) != (255, 0, 0):
                h.put(X0 + i, top + j, letter('%02x%02x%02x' % (r, g_, b)), Y0 + 15)
                if j >= ht - 4:
                    h.stood({(X0 + i, top + j)})


POSTS = []                    # (X0, Y0, side, x, y) of each lantern post drawn in the last town()


def dressing(h, p, CX0, CY0, frame=0, skip=()):
    """The streets' dressing, each in its cell (town2_layout.py DRESS). A
    lantern post at its lantern's frame (all of them the same in one
    drawing; the game gives each its own phase), unless it is one of `skip`
    -- those whose cells would hold more than four colours with it in some
    frame, so lose its red to the roof's (built()). Anything else only where
    nothing is drawn yet in its cell or the one over it (an eave over the
    street)."""
    for kind, x, y in p.get('dress', []):
        X0, Y0 = (x - CX0) * 16, (y - CY0) * 16
        if kind.startswith('post'):
            if (x, y) not in skip:
                lantern_post(h, X0, Y0, kind[-1], frame)
                POSTS.append((X0, Y0, kind[-1], x, y))
            continue
        if any((px, py) in h.c for py in range(Y0 - 16, Y0 + 16) for px in range(X0, X0 + 16)):
            continue
        if kind == 'firewood':
            firewood(h, X0, Y0)
        elif kind == 'cart':
            cart(h, X0, Y0)
        else:
            snow_prop(h, X0, Y0, kind)


def square(h, p, CX0, CY0):
    """The square's own drawing (the user, 2026-10-29): its ground is the
    town's roads and snow, and its walls the game's yard walls
    (town2_layout.py), so only its pines -- one in each top quarter -- and
    the stone lanterns by its front gates are drawn."""
    for x, y in p['square']['pines']:
        pine(h, (x - CX0) * 16, (y - CY0) * 16)
    for x, y in p['square']['lanterns']:
        stone_lantern(h, (x - CX0) * 16, (y - CY0) * 16)


def town(frame=0, skip=()):
    """The whole town drawn, its lantern posts at `frame`, those in `skip` left out."""
    del POSTS[:]
    p = plan()
    CX0, CY0, CW, CH = p['canvas']
    KW, KE, BACK, FRONT = p['walls']
    h = House(CW, CH, brick_tone)
    kx = lambda k: (k - CX0 - CY0 - CH + 1) * 16
    dy = lambda y: (CY0 + CH - 1 - y) * 16
    # the buildings, each its own design shifted to its lot; its feet kept on the lot
    for name, lot, opts in p['drawn']:
        _, k0, k1, y0, y1 = p['lots'][lot]
        mod = PIECES[name]
        bx = k0 - y1
        h.shift((bx - CX0) * 16, (y1 - CY0 + 1 - CH) * 16)
        before, drawn = set(h.foot), set(h.c)
        if hasattr(mod, 'size'):
            mod.draw(h, k1 - k0 + 1, **opts)             # drawn to its lot's width
        else:
            mod.draw(h)
        h.shift(0, 0)
        for fx, fy in h.foot - before:
            x, y = CX0 + fx // 16, CY0 + fy // 16
            assert y0 <= y <= y1 and k0 <= x + y <= k1, '%s stands off its lot at (%d,%d)' % (name, x, y)
        top = min((py for px_, py in set(h.c) - drawn), default=None)       # and rises no higher than the street behind
        assert top is None or CY0 + top // 16 >= y0 - 2, '%s on lot %d reaches past the street behind' % (name, lot)
    square(h, p, CX0, CY0)
    # the wall: its runs between the corners, the towers over the corners, the gate
    wx0, wx1 = kx(KW) - 8, kx(KW + 2) - 9
    ex0, ex1 = kx(KE - 1) - 8, kx(KE + 1) - 9
    bd0, bd1 = dy(BACK + 1), dy(BACK) + 15               # the corners' and the gate's two rows
    fd0, fd1 = dy(FRONT + 1), dy(FRONT) + 15
    bt0, ft1 = bd1 - 15, fd0 + 15                        # the runs across one row deep, their outer rows: two read
                                                         # thicker than the sides do slanted (the user, 2026-10-30)
    cx = kx(p['main']) + 16                              # the main street's middle, through the gate
    rampart(h, wx0, ex1, bt0, bd1, 'back')
    rampart(h, wx0, wx1, ft1 + 1, bt0 - 1, 'west')
    rampart(h, ex0, ex1, ft1 + 1, bt0 - 1, 'east')
    rampart(h, wx0, cx - 65, fd0, ft1, 'front')
    rampart(h, cx + 65, ex1, fd0, ft1, 'front')
    for x0, x1 in ((wx0, wx1), (ex0, ex1)):
        for d0, d1 in ((bd0, bd1), (fd0, fd1)):
            corner(h, x0 - 8, x1 + 8, d0 - 8, d1 + 8)
    gate_tower(h, cx, fd0 - 4, fd1)
    for x, y in p.get('entry_pines', []):                # the row of pines inside the front wall, each alone
        X0, Y0 = (x - CX0) * 16, (y - CY0) * 16          # in its cells: none where the gate or a corner stands
        if not any((px, py) in h.c for py in range(Y0 - 16, Y0 + 16) for px in range(X0, X0 + 16)):
            pine(h, X0, Y0)
    # behind the front wall the ground its top hides on the screen -- WALL
    # back from its back edge -- is its own, stood on: the feet meet its top as
    # they come down to it. The main street alone runs on through to the gate.
    md1 = ft1 + WALL
    h.stood({(x + d, h.B - d) for x in range(wx1, ex0 + 1) for d in range(ft1 + 1, md1 + 1)
             if abs(x - cx) >= GATE_W // 2})
    dressing(h, p, CX0, CY0, frame, skip)                # last: it sees all the rest
    return h


_BUILT = {}


def built():
    """The town drawn at each of the lantern posts' three frames (the world's
    ambient beat, src/core.h): a post whose cells would hold more than four
    colours in some frame -- its lantern under an eave -- is left out, so no
    lantern loses its red to a roof's. -> [(House, its finished grid)] by frame."""
    if not _BUILT:
        from collections import Counter
        first = [town(f) for f in range(3)]
        bad = set()
        for X0, Y0, side, x, y in list(POSTS):
            for f, h in enumerate(first):
                lone = House(h.w // 16, h.h // 16, brick_tone)
                lantern_post(lone, X0, Y0, side, f)
                for cx, cy in {(px // 16, py // 16) for px, py in lone.c}:
                    tones = {h.c[(px, py)] for py in range(cy * 16, cy * 16 + 16)
                             for px in range(cx * 16, cx * 16 + 16) if (px, py) in h.c}
                    if len(tones) > 4:
                        bad.add((x, y))
        drawn = []
        for f in range(3):
            h = town(f, bad) if bad else first[f]
            drawn.append((h, h.grid('xuelin', MERGE, objects=True)))
        _BUILT['frames'], _BUILT['posts'], _BUILT['left out'] = drawn, list(POSTS), sorted(bad)
    return _BUILT['frames']


def design():
    from entrance_shapes import depth_layers
    h, g = built()[0]
    return {'pal': dict(PAL, **EXTRA), 'view_w': h.w, 'order': ['house'], 'views': {'house': g.rows()},
            'depth': depth_layers(h.w, h.h, [(0, 0, g)])}


def anim():
    """The cells that change between the frames, each with the post it is of
    and its frames 1 and 2 cut from the town drawn at them (with whatever
    else stands there, the nearer pixel winning) -> [(canvas cell, post's
    cell, [frame 1 Grid, frame 2 Grid])]."""
    from entrance_shapes import Grid
    frames = built()
    h0, g0 = frames[0]
    # each cell any post touches in any frame, and the post: posts sharing a
    # cell are one group, on one phase, so the cell they share is whole in
    # every frame -- the group named by its first post
    touches, group = {}, {}
    find = lambda q: q if group[q] == q else find(group[q])
    for X0, Y0, side, x, y in _BUILT['posts']:
        group[(x, y)] = (x, y)
        for f in range(3):
            lone = House(h0.w // 16, h0.h // 16, brick_tone)
            lantern_post(lone, X0, Y0, side, f)
            for cell in {(px // 16, py // 16) for px, py in lone.c}:
                if cell in touches:
                    group[find((x, y))] = find(touches[cell])
                else:
                    touches[cell] = (x, y)
    out = []
    for (cx, cy), first in sorted(touches.items()):
        post = find(first)
        rows = lambda g: [g.g[cy * 16 + yy][cx * 16:cx * 16 + 16] for yy in range(16)]
        if all(rows(g) == rows(g0) for _, g in frames[1:]):
            continue
        cut = []
        for _, fg in frames[1:]:
            c = Grid(16, 16)
            c.g = rows(fg)
            c.footy = [[None if fg.footy[cy * 16 + yy][cx * 16 + xx] is None else
                        fg.footy[cy * 16 + yy][cx * 16 + xx] - cy * 16 for xx in range(16)] for yy in range(16)]
            c.foot = {(px - cx * 16, py - cy * 16) for px, py in fg.foot
                      if cx * 16 <= px < cx * 16 + 16 and cy * 16 <= py < cy * 16 + 16}
            c.way = set()
            cut.append(c)
        out.append(((cx, cy), post, cut))
    return out


def anim_design():
    """town_anim.png's design (art/structures/xuelin/town_anim_design.py): a
    column a cell, frame 1 above, frame 2 below; and town_anim.json, where
    each cell lies in the town and the post it is of."""
    from entrance_shapes import depth_layers
    cells = anim()
    pieces, rows = [], [['.'] * (16 * len(cells)) for _ in range(32)]
    for i, (_, _, cut) in enumerate(cells):
        for f, c in enumerate(cut):
            pieces.append((16 * i, 16 * f, c))
            for yy in range(16):
                rows[16 * f + yy][16 * i:16 * i + 16] = c.g[yy]
    json.dump([{'cell': list(c), 'post': list(p)} for c, p, _ in cells],
              open(os.path.join(HERE, 'town_anim.json'), 'w'), indent=1)
    return {'pal': dict(PAL, **EXTRA), 'view_w': 16 * len(cells), 'order': ['house'],
            'views': {'house': [''.join(r) for r in rows]},
            'depth': depth_layers(16 * len(cells), 32, pieces)}


def export(d, base):
    """The drawing to base.png, as draw_views exports one, and base.aseprite."""
    import subprocess
    from PIL import Image
    pal, rows = d['pal'], d['views']['house']
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.':
                px[x, y] = tuple(int(pal[c][i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    im.save(base + '.png')
    subprocess.run([r'C:\Program Files\Aseprite\Aseprite.exe', '-b', base + '.png', '--save-as', base + '.aseprite'], check=True)


if __name__ == '__main__':
    export(design(), os.path.join(HERE, 'town'))
    export(anim_design(), os.path.join(HERE, 'town_anim'))
    print('wrote', os.path.join(HERE, 'town.png'), 'and town_anim.png')
