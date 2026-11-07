"""PixelLab art in a room: the NES-style interiors (art/interiors_nes/).

A room is still laid out by tools/interior_room.py -- its shell, its door,
the boxes its furniture stands in, so the feet meet it as before -- and then
PixelLab's drawings are put over it: textures filling a surface, furniture
drawn over its box, decorations on the walls and the floor. Each drawing is
snapped to a few of the room's tones (K and two more for a sprite, as the NES
draws one), so the four-colours-a-tile rule of finish() still holds.

The room no longer goes into the tile sheet: export() writes
assets/interiors/room_<n>.png (the room, and beside it the furniture's layer,
at 320x240 each) and room_<n>_depth.png (per pixel: R the room's drop to its
floor row, G the furniture's, 255 for nothing; B bit 0 the room's ground,
bit 1 the furniture's), and room_<n>.txt (the 20x15 cells: ' ' outside,
'#' solid, '.' some floor, 'E' the way out), read by src/interior.cpp.

    python tools/interior_nes.py N art/interiors_nes/<name>_design.py
"""
import glob, importlib.util, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
from interior_room import *          # noqa: F401,F403 -- the room's parts, for the designs
import interior_room as IR

PIX = os.path.join(ROOT, 'art', 'interiors_nes', 'pixellab')
IR.FURNITURE_TONES = 4      # the user, 2026-11-06: three a tile cut PixelLab's furniture in half; four, as the room's


def game_palette():
    out = []
    for line in open(os.path.join(ROOT, 'art', 'direction', 'game_palette.gpl')):
        p = line.split()
        if len(p) >= 3 and all(v.isdigit() for v in p[:3]):
            out.append(tuple(int(v) for v in p[:3]))
    return out


PALETTE = game_palette()


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def snap(h):
    """The game palette's colour nearest h."""
    c = rgb(h)
    best = min(PALETTE, key=lambda p: sum((a - b) ** 2 for a, b in zip(p, c)))
    return '%02x%02x%02x' % best


def art(name):
    """A PixelLab drawing by its --name (the CLI writes it as name with '-')."""
    hits = glob.glob(os.path.join(PIX, '*', name.replace('_', '-') + '.png'))
    assert hits, 'no PixelLab drawing named ' + name
    return Image.open(sorted(hits)[-1]).convert('RGBA')


def to_tones(im, tones, force=None):
    """Each pixel of im -- clear below half alpha -- as the letter of tones
    {letter: hex} nearest it, by brightness first so light stays light;
    force {source hex: letter} where the nearest is the wrong part (a grey
    mortar joint nearer the brick's red than the mortar's cream)."""
    force = {rgb(k): v for k, v in (force or {}).items()}
    cols = {k: rgb(v) for k, v in tones.items()}
    lum = lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    def near(c):
        return min(cols, key=lambda k: 2 * (lum(cols[k]) - lum(c)) ** 2 + sum((a - b) ** 2 for a, b in zip(cols[k], c)))
    p, out = im.load(), {}
    memo = {}
    for y in range(im.height):
        for x in range(im.width):
            q = p[x, y]
            if q[3] < 128:
                continue
            out[(x, y)] = force.get(q[:3]) or memo.setdefault(q[:3], near(q[:3]))
    return out


class NesRoom(IR.Room):
    def __init__(self):
        super().__init__()
        self.tones = {}

    def keep(self, tones):
        for k, v in tones.items():
            assert self.tones.get(k, v) == v, 'tone %s given two colours' % k
            self.tones[k] = v


def new_room(windows=((80, 15), (160, 15)), door=True):
    """door=False: an upstairs, whose way out is its stairs."""
    r = NesRoom()
    IR.shell(r)
    for x, y in windows:
        IR.window(r, x, y)
    if door:
        IR.door(r)
    return r


def texture(r, im, tones, where, ox=0, oy=0, force=None):
    """Fill the room's pixels for which where(x, y) holds with im tiled, its
    colours as tones. The floor row of each stays the room's."""
    r.keep(tones)
    t = to_tones(im, tones, force)
    w, h = im.size
    for (x, y) in list(r.c):
        if where(x, y):
            c = t.get(((x - ox) % w, (y - oy) % h))
            if c:
                r.c[(x, y)] = c


def clear_furniture(r, box):
    """Take off the furniture's layer what lies in box (x0, y0, x1, y1), keeping
    the floor rows it stood on, for a drawing to go in its place."""
    x0, y0, x1, y1 = box
    rows = {}
    for q in [q for q in r.fc if x0 <= q[0] <= x1 and y0 <= q[1] <= y1]:
        rows[q] = r.ffy[q]
        del r.fc[q], r.ffy[q]
        r.near.pop(q, None)
    return rows


def sprite(r, im, x0, y0, tones, fy, rows=None, foot=None, cut=None):
    """A drawing on the furniture's layer, its top left at (x0, y0): each
    pixel stands on floor row fy, or the row rows gives that pixel (what
    stood there before); foot a list of (x, y) of ground it covers; cut a
    function (x, y) of the drawing's own pixels to leave out."""
    r.keep(tones)
    rows = rows or {}
    bb = im.getbbox()
    for (x, y), c in to_tones(im, tones).items():
        if cut and cut(x, y):
            continue
        q = (x0 + x - bb[0], y0 + y - bb[1])
        r.fc[q], r.ffy[q] = c, rows.get(q, fy)
        r.near[q] = r.ffy[q]
    if foot:
        r.foot |= set(foot)


STAIRS_W = 12                                     # a staircase slot's width along its wall
STAIRS_RIGHT, STAIRS_LEFT = 222, 22               # its first column: far right (downstairs), far left (upstairs), each 39-50 px out from its back corner


def stairs_slot(r, x0, up=True, w=STAIRS_W):
    """A staircase as Mother 1 draws one (the user's reference, 982.png): a
    tall slot in a side wall from the ceiling to the floor line, black jambs,
    the steps at its foot. Which way is plain from two things at once:
      up   -- the steps climb into the wall, higher at each step back, lit
              treads striped cream and black; light falls in from the floor
              above, the slot's top a lit grey (I) over the dark (N);
      down -- the steps start low at the front and drop below the floor line
              going back, dim treads; the slot darkens to a black pit (K) at
              its foot.
    x0: its first column; the wall (left or right) follows from x0. In the
    room's layer, part of the wall, as the door is."""
    right = x0 > IR.BX1
    front = x0 + w - 1 if right else x0                     # the column nearest the room
    f0 = IR.foot_of(front)
    SINK = 10                                               # down: how far the notch drops under the floor line
    for i in range(w):
        x = x0 + i
        a = (w - 1 - i) if right else i                         # columns back from the slot's front edge
        f = IR.foot_of(x)
        k = a // 3                                              # the step: four, 3 columns each
        if up:
            # each tread flat across its step, 7 px higher at each step back
            tread = f0 - 4 - 7 * k
            for y in range(0, f + 1):
                if i in (0, w - 1) or y == f:
                    c = 'K'                                     # the jambs, the foot
                elif y < tread - 1:
                    c = 'I' if y < f * 2 // 5 else 'N'          # light from upstairs over the dark
                elif y == tread - 1:
                    c = 'K'                                     # the step's nosing
                elif y == tread:
                    c = 'm'                                     # the tread, lit
                elif a % 3 == 0:
                    c = 'K'                                     # the riser
                else:
                    c = 'K' if (x + y) % 3 == 0 else 'm'        # striped as Mother's
                r.put(x, y, c, f)
            continue
        # down: the slot dark to the floor, and on through it -- a notch at the
        # wall's foot where the steps go under the floor line: the first tread
        # level with the floor, each after it 3 px lower and darker, then black
        tread = f + 3 * k if k else f
        for y in range(0, f + SINK + 1):
            if i in (0, w - 1) or y == f + SINK:
                c = 'K'                                         # the jambs, the notch's edge
            elif y < tread - 1:
                c = 'N' if y < f - 6 else 'K'                   # the slot, black near the floor
            elif y == tread - 1:
                c = 'K'                                         # the step's nosing
            elif y == tread:
                c = ('m', 'I', 'N', 'K')[k]                     # lit, dim, dark, gone
            elif a % 3 == 0:
                c = 'K'                                         # the riser
            elif k == 0:
                c = 'K' if (x + y) % 3 == 0 else 'm'
            else:
                c = 'K' if (x + y) % 2 == 0 or k > 1 else 'N'
            r.put(x, y, c, f if y <= f else y)                  # the notch lies on the floor: its own row


STAIRS_PAD = 8                                    # the sprite's margin round the slot, room to widen it


def stairs_sprite_origin(x0, w=STAIRS_W):
    return x0 - STAIRS_PAD, 0


def stairs_from_sprite(r, path, x0, w=STAIRS_W):
    """A staircase drawn by hand (the user's, in Aseprite): the PNG saved by
    save_stairs_sprite, its top left at stairs_sprite_origin(x0). Transparent
    leaves the wall; every other pixel keeps the user's own colour (on the
    game palette), on the furniture's layer -- four colours a tile there, all
    the user's -- standing on its wall's floor row (or below the wall's foot,
    the notch, on its own), so behind anyone before it. Returns the slot's
    columns (first, width) as drawn, for its trigger."""
    im = Image.open(path).convert('RGBA')
    ox, oy = stairs_sprite_origin(x0, w)
    letter = {v: k for k, v in r.tones.items()}
    def name(h):
        if h not in letter:
            k = next(l for l in LETTERS if l not in r.tones and l not in IR.BASE)
            r.tones[k] = h
            letter[h] = k
        return letter[h]
    p = im.load()
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3] < 128:
                continue
            h = snap('%02x%02x%02x' % c[:3])
            k = 'K' if h == '000000' else name(h)
            X, Y = ox + x, oy + y
            f = IR.foot_of(X)
            q = (X, Y)
            r.fc[q], r.ffy[q] = k, (f if Y <= f else Y)
            r.near[q] = r.ffy[q]
    bb = im.getbbox()
    return ox + bb[0], bb[2] - bb[0]


def stairs_cols(name, x0, w=STAIRS_W):
    """The slot's columns (first, width) as the user drew it in
    art/interiors_nes/<name>.png, placed for a slot at x0."""
    im = Image.open(os.path.join(ROOT, 'art', 'interiors_nes', name + '.png')).convert('RGBA')
    bb = im.getbbox()
    ox, _ = stairs_sprite_origin(x0, w)
    return ox + bb[0], bb[2] - bb[0]


def save_stairs_sprite(path, x0, up, pal, w=STAIRS_W):
    """The coded staircase written out as a PNG for hand editing."""
    r = NesRoom()
    stairs_slot(r, x0, up=up, w=w)
    ox, oy = stairs_sprite_origin(x0, w)
    W = w + 2 * STAIRS_PAD
    H = max(y for _, y in r.c) + 1 + STAIRS_PAD
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (x, y), k in r.c.items():
        im.putpixel((x - ox, y - oy), rgb(pal[k]) + (255,))
    im.save(path)


def stairs_trigger(to, x0, arrive_x0, w=STAIRS_W, arrive_w=STAIRS_W):
    """STAIRS entry for a slot at x0: the feet before it, against its wall,
    and where they arrive in room `to` -- out from that room's slot at
    arrive_x0, a step clear of it."""
    def box(x0):
        x1 = x0 + w - 1
        if x0 > IR.BX1:                                         # the right wall: the floor runs down to the right
            return x0 - 4, IR.foot_of(x0), x1, IR.foot_of(x1) + 3
        return x0, IR.foot_of(x1), x1 + 4, IR.foot_of(x0) + 3
    def arrive(x0):
        mid = x0 + (arrive_w - 1) / 2
        out = -14 if x0 > IR.BX1 else 14                        # out from the wall, at 45 degrees
        return mid + out, IR.foot_of(mid) + 14
    return (to,) + box(x0) + arrive(arrive_x0)


LETTERS = '0123456789ABDEGHJLMOQSVXY!@$%&*+=?'       # the rich sprites' own; designs name theirs in lower case and K F P T U N I W Z R C


def sprite_rich(r, im, x0, y0, fy, rows=None, foot=None, cut=None, keep_black=True, most=4, choices=None, room=False):
    """sprite(), but each 16x16 tile of the screen it falls on picks its own
    two colours (and the black) from the drawing -- the pair, from the game
    palette, that loses the least -- so a piece keeps its shading where a
    tone set for the whole piece would flatten it."""
    rows = rows or {}
    bb = im.getbbox()
    p = im.load()
    def pal_of(c):
        return min(PALETTE, key=lambda q: sum((a - b) ** 2 for a, b in zip(q, c)))
    dist = lambda a, b: sum((u - v) ** 2 for u, v in zip(a, b))
    lum = lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    tiles = {}
    for y in range(bb[1], bb[3]):
        for x in range(bb[0], bb[2]):
            q = p[x, y]
            if q[3] < 128 or (cut and cut(x, y)):
                continue
            fx, fyy = x0 + x - bb[0], y0 + y - bb[1]
            t = ((fx + IR.OX) // 16, (fyy + IR.OY) // 16)
            tiles.setdefault(t, []).append((fx, fyy, q[:3]))
    letter = {v: k for k, v in r.tones.items()}
    def name(c):
        h = '%02x%02x%02x' % c
        if h not in letter:
            k = next(l for l in LETTERS if l not in r.tones and l not in IR.BASE)
            r.tones[k] = h
            letter[h] = k
        return letter[h]
    pick = [rgb(h) for h in choices] if choices else None
    for t, px in tiles.items():
        ink = [c for _, _, c in px if not (keep_black and lum(c) < 40)]
        from collections import Counter
        if pick:
            # one mapping for the whole piece, so its tiles agree; a tile with
            # too many merges its rarest into the nearest it keeps
            near = {c: min(pick, key=lambda b: dist(c, b)) for c in set(ink)}
            count = Counter(near[c] for c in ink)
            keep = [c for c, _ in count.most_common()]
            while len(keep) > most - 1:
                gone = keep.pop()
                for c in near:
                    if near[c] == gone:
                        near[c] = min(keep, key=lambda b: dist(gone, b))
            best = None
        else:
            from itertools import combinations_with_replacement
            cand = [c for c, _ in Counter(pal_of(c) for c in ink).most_common(8)]
            best, err = (), None
            for pair in combinations_with_replacement(cand, most - 1):
                e = sum(min(dist(c, b) for b in pair) for c in ink)
                if err is None or e < err:
                    best, err = pair, e
        for fx, fyy, c in px:
            if keep_black and lum(c) < 40 or (not pick and not best):
                k = 'K'
            else:
                k = name(near[c] if pick else min(best, key=lambda b: dist(c, b)))
            q = (fx, fyy)
            if room:                                 # into the room's layer: shelves built into a wall
                r.put(fx, fyy, k, rows.get(q, fy))
                continue
            r.fc[q], r.ffy[q] = k, rows.get(q, fy)
            r.near[q] = r.ffy[q]
    if foot:
        r.foot |= set(foot)


def colours_of(im, n=5, drop_dark=True):
    """The n colours a drawing uses most, on the game palette: a piece's own
    set for sprite_rich(choices=...)."""
    from collections import Counter
    lum = lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    cnt = Counter(snap('%02x%02x%02x' % q[:3]) for q in im.getdata()
                  if q[3] >= 128 and not (drop_dark and lum(q[:3]) < 40))
    return [h for h, _ in cnt.most_common(n)]


def piece(r, draw, im, choices=None, n=5):
    """An old box drawn for its place, its feet and its floor rows -- so the
    feet meet it exactly as before -- then PixelLab's drawing of it put where
    it stood, every tile from the piece's own colours."""
    before = set(r.fc)
    draw()
    mine = [q for q in r.fc if q not in before]
    box = (min(x for x, _ in mine), min(y for _, y in mine), max(x for x, _ in mine), max(y for _, y in mine))
    rows = clear_furniture(r, box)
    sprite_rich(r, im, box[0], box[1], box[3], rows=rows, choices=choices or colours_of(im, n))
    return box


def fit_tiles(r, pal):
    """Where pieces laid one over another leave a tile with more colours than
    its layer may have (4 the room's, IR.FURNITURE_TONES the furniture's),
    its rarest colour goes to the nearest it keeps; black always stays."""
    from collections import Counter
    for cells, most in ((r.c, 4), (r.fc, IR.FURNITURE_TONES)):
        tiles = {}
        for (x, y), k in cells.items():
            tiles.setdefault(((x + IR.OX) // 16, (y + IR.OY) // 16), []).append((x, y))
        for qs in tiles.values():
            while True:
                cnt = Counter(cells[q] for q in qs)
                if len(cnt) <= most:
                    break
                gone = min((k for k in cnt if k != 'K'), key=lambda k: cnt[k])
                to = min((k for k in cnt if k not in (gone, 'K')),
                         key=lambda k: sum((a - b) ** 2 for a, b in zip(rgb(pal[k]), rgb(pal[gone]))))
                for q in qs:
                    if cells[q] == gone:
                        cells[q] = to


def finish(r, name, pal):
    pal = dict(pal, **r.tones)
    fit_tiles(r, dict(IR.BASE, **pal))
    return IR.finish(r, name, {k: snap(v) for k, v in dict(IR.BASE, **pal).items()})


# ---- the export the game reads ------------------------------------------

def export(n, design, out=os.path.join(ROOT, 'assets', 'interiors')):
    os.makedirs(out, exist_ok=True)
    pal, W, H = design['pal'], IR.W, IR.H
    img = Image.new('RGBA', (2 * W, H), (0, 0, 0, 0))
    p = img.load()
    for i, key in enumerate(design['order']):
        for y, row in enumerate(design['views'][key]):
            for x, c in enumerate(row):
                if c != '.':
                    p[i * W + x, y] = rgb(pal[c]) + (255,)
    img.save(os.path.join(out, 'room_%d.png' % n))
    d = design['depth']
    dep = Image.new('RGB', (W, H), (255, 255, 0))
    q = dep.load()
    for y in range(H):
        for x in range(W):
            drops, bits = [], 0
            for i in range(2):
                fy = d['footy'][y][i * W + x]
                drops.append(255 if fy < 0 or not p[i * W + x, y][3] else min(254, max(0, fy - y)))
                if d['foot'][y][i * W + x] == '#':
                    bits |= 1 << i
            q[x, y] = (drops[0], drops[1], bits)
    dep.save(os.path.join(out, 'room_%d_depth.png' % n))
    exits = {tuple(e) for e in design.get('exit', [])}
    coll = []
    for cy in range(H // 16):
        row = ''
        for cx in range(W // 16):
            cell = [(x, y) for y in range(cy * 16, cy * 16 + 16) for x in range(cx * 16, cx * 16 + 16)]
            ink = any(p[x, y][3] for x, y in cell)
            row += (' ' if not ink else 'E' if (cx, cy) in exits
                    else '.' if any(d['foot'][y][x] != '#' for x, y in cell) else '#')
        coll.append(row)
    open(os.path.join(out, 'room_%d.txt' % n), 'w').write('\n'.join(coll) + '\n')
    return img


def export_anim(n, designs, png, txt):
    """A room with something on its wall that moves (a fire): the region where
    its frames differ, every frame side by side, which layer and where. The
    game shows them on the world's ambient beat (core.h: AMBIENT_FRAMES of
    AMBIENT_FRAME_MS each), over that layer. Only one layer may move, and
    what moves must stand behind everyone (at the back wall)."""
    W, H = IR.W, IR.H
    def layer(d, i):
        pal, rows = d['pal'], d['views'][d['order'][i]]
        return [[None if c == '.' else rgb(pal[c]) for c in row[:W]] for row in rows]
    lays = [[layer(d, i) for i in range(2)] for d in designs]
    moving = [i for i in range(2) if any(l[i] != lays[0][i] for l in lays)]
    assert len(moving) == 1, 'frames must differ in exactly one layer'
    li = moving[0]
    lay = [l[li] for l in lays]
    diff = [(x, y) for y in range(H) for x in range(W) if any(l[y][x] != lay[0][y][x] for l in lay)]
    x0, y0 = min(x for x, _ in diff), min(y for _, y in diff)
    x1, y1 = max(x for x, _ in diff) + 1, max(y for _, y in diff) + 1
    w, h = x1 - x0, y1 - y0
    img = Image.new('RGBA', (w * len(lay), h), (0, 0, 0, 0))
    p = img.load()
    for i, l in enumerate(lay):
        for y in range(h):
            for x in range(w):
                c = l[y0 + y][x0 + x]
                if c:
                    p[i * w + x, y] = c + (255,)
    img.save(png)
    open(txt, 'w').write(' '.join(map(str, (li, x0, y0, w, h, len(lay)))) + chr(10))


if __name__ == '__main__':
    n, path = int(sys.argv[1]), sys.argv[2]
    spec = importlib.util.spec_from_file_location('design', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    stairs = os.path.join(ROOT, 'assets', 'interiors', 'room_%d_stairs.txt' % n)
    if getattr(mod, 'STAIRS', None):
        # (to, x0, y0, x1, y1, ax, ay): the feet's box on the stairs and where
        # they arrive in room `to`, in the room's art pixels -> screen pixels
        sc = lambda v, o: 2 * (v + o)
        open(stairs, 'w').write(''.join('%d %g %g %g %g %g %g' % (t, sc(x0, IR.OX), sc(y0, IR.OY), sc(x1 + 1, IR.OX),
                                        sc(y1 + 1, IR.OY), sc(ax, IR.OX), sc(ay, IR.OY)) + chr(10)
                                        for t, x0, y0, x1, y1, ax, ay in mod.STAIRS))
    elif os.path.exists(stairs):
        os.remove(stairs)
    frames = getattr(mod, 'FRAMES', 1)
    base = mod.design(frame=0) if frames > 1 else mod.design()
    export(n, base)
    anim_png = os.path.join(ROOT, 'assets', 'interiors', 'room_%d_anim.png' % n)
    anim_txt = anim_png[:-3] + 'txt'
    if frames > 1:
        export_anim(n, [base] + [mod.design(frame=f) for f in range(1, frames)], anim_png, anim_txt)
    else:
        for f in (anim_png, anim_txt):
            if os.path.exists(f):
                os.remove(f)
    print('room %d written' % n)
