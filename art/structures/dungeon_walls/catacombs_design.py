"""The catacombs (user): many sections. First a vast hall in stonehenge's
projection, rows of stained-glass screens down it like a church's aisles --
a pane for every enemy, leaded glass made from its battle sprite -- and in its
alcoves the doors and ladders down; below, sections laid like the
graveyard's walkways, in isometric, floored in the graveyard's brick
throughout and walled all round with dark bones and skulls (user).

    python art/structures/dungeon_walls/catacombs_design.py <design.json> [n_panes]
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/catacombs

Below (isometric, user):
    brick                64 x 64: the floor throughout, the regular graveyard's
                         red brick paving (user) less its chips, its shade 2
                         wide: an isometric floor shows a chip as a comb
    bones                two walls, 64 across and 48 tall each, as a face square to the
                         screen shows them, for the sections to alternate (user:
                         "so the player doesnt get confused what catacombs
                         theyre in"): a row of skulls over three courses of
                         long bones, then skulls all the way down. A skull
                         course is 24 tall, a skull every 16, 5 down it -- the
                         game lays those whole along each face and stands them
                         upright on the slanted ones (cat_bake)
The hall:
    flags                64 x 64: the nave's flagstones
    ashlar, ashlar_side  96 x 80 / 48 x 80: its outer walls, lit and in shade
    cap                  64 x 8: the top of a glass screen, stone
    pane_NN              64 x 64, every one (user): an enemy in leaded glass under a pointed
                         arch -- its sprite in two tones of one hue, its
                         outline and a came round it in lead, pale glass in a
                         diamond lattice behind; the hue turns pane to pane

Tones -- four a 16px cell, one palette.
"""
import glob, json, math, os, random, sys
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from interior_style import MATERIALS, bond, masonry

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')

PAL = {'K': '000000', **dict(zip('MDS', MATERIALS['stone']['tones'])),      # stone: lit, mid, shade
       **dict(zip('bo', MATERIALS['bone']['tones'])), 'J': MATERIALS['bone']['joint'],   # the walls' bone, its shade, the dark grey between
       'r': '792727', 'm': '531b1c',                                        # the graveyard's brick: shade, mortar (its face is '1')
       '1': 'b6433d', '2': 'ec8476', '3': 'd89830', '4': 'f4ce80',          # glass: red, gold,
       '5': '2c6c44', '6': '4fa667', '7': '664b95', '8': 'b69cee',          # green, violet,
       '9': '2850a0', '0': '84a7e9', 'q': '785830', 'Q': 'c18a39',          # blue, amber -- each dark, light
       'c': '3e91cc', 'w': 'dcf0ff', 'v': '5c94fc'}          # the glass behind
VW, VH = 128, 80
PANE_W = 64                          # a window's width; its glass leaves a sprite 56 across

FEMUR = [".bbbb....................bbbb...",      # 30 x 7 in a 32 x 8 cell: a knob at each end, the
         "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb..",      # shaft between, its shade under it
         "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb..",
         ".bbbbbbbbbbbbbbbbbbbbbbbbbbbb...",
         "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb..",
         "bbbbboooooooooooooooooooobbbbb..",
         ".oooo....................oooo...",
         "................................"]
SKULL = ["....bbbbbb....",                        # 14 x 14: sockets, nose and teeth black, its shade
         "..bbbbbbbbbb..",                        # under the jaw
         ".bbbbbbbbbbbb.",
         ".bbbbbbbbbbbb.",
         "bbbbbbbbbbbbbb",
         "bbKKKbbbbKKKbb",
         "bbKKKbbbbKKKbb",
         "bbKKKbbbbKKKbb",
         ".bbbbbKKbbbbb.",
         ".bbbbbKKbbbbb.",
         "..bbbbbbbbbb..",
         "..bKbKbbKbKb..",
         "..bKbKbbKbKb..",
         "...oooooooo..."]


def grid(w, h, c):
    return [[c] * w for _ in range(h)]


# ── below ────────────────────────────────────────────────────────────────
def brick():
    """The graveyard's brick, its worn bricks where they are there, less its
    chips; the shade 2 wide, as the isometric floor needs."""
    return bond(64, 64, 16, 8, '1', 'r', 'm', seed=5, edge=2, chipped=False)


def bone_wall(layout):
    """64 x 64, its top 48 the wall (the rest the dark between, as the sheet
    has always held it), a course a letter from the top: S skulls (24 tall),
    F long bones (8, every other course half a bone along). Whole pieces on the dark
    between them, in bone's base and shade: nothing the game's shear of a
    slanted wall can spoil but a skull, and those it stands upright itself."""
    g = grid(64, 64, 'J')
    y = nf = 0
    for c in layout:
        cell, h, step, x0 = (FEMUR, 8, 32, 16 * (nf % 2)) if c == 'F' else (SKULL, 24, 16, 1)
        for k in range(-1, 64 // step):
            for j, row in enumerate(cell):
                for i, ch in enumerate(row):
                    if ch != '.':
                        g[y + (0 if c == 'F' else 5) + j][(k * step + x0 + i) % 64] = ch
        nf, y = nf + (c == 'F'), y + h
    assert y == 48, layout
    return g


def bones():
    """The two walls side by side: odd sections' on the left, even ones' on the right."""
    return [a + b for a, b in zip(bone_wall('SFFF'), bone_wall('SS'))]


# ── the hall ─────────────────────────────────────────────────────────────
def flags():
    """Flagstones 32 x 16 in running bond, plain as the stonehenge's blocks
    are: a step down the stone from the walls, so the floor reads apart
    (user), their shade 2 wide, as the isometric floor shows every other row."""
    return bond(64, 64, 32, 16, 'D', 'S', 'K', edge=2, wear=False)


def ashlar(shade):
    """Big squared stones, courses 16 tall, blocks 48 long, one under two;
    the side in shade a step down the stone."""
    return bond(48 if shade else 96, 80, 48, 16, *('DS' if shade else 'MD'), 'K', wear=False)


def cap():
    return masonry(64, 8, [(0, 8, 32, 0)], 'M', 'D', 'K')


FIG = [('1', '2'), ('3', '4'), ('5', '6'), ('7', '8'), ('9', '0'), ('q', 'Q')]
BACK = ['c', 'w', 'v']                               # the glass behind: blues and the pale (user: no amber)


def enemies():
    """(id, front view RGBA) for every enemy with views: the first of five views,
    its first frame (frames stack down the sheet), shrunk to fit a pane if a
    giant's (nearest pixel: the glass is two tones anyway)."""
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'art', 'enemies', '*_views.png'))):
        n = os.path.basename(f).split('_')[0]
        if not n.isdigit():
            continue
        im = Image.open(f).convert('RGBA')
        front = im.crop((0, 0, im.width // 5, im.height))
        a = front.getchannel('A')
        rows = [a.crop((0, y, front.width, y + 1)).getbbox() is not None for y in range(front.height)]
        if True not in rows:
            continue
        y0 = rows.index(True)
        y1 = y0
        while y1 < len(rows) and rows[y1]:
            y1 += 1
        frame = front.crop((0, y0, front.width, y1))
        frame = frame.crop(frame.getchannel('A').getbbox())
        k = min(1.0, (PANE_W - 8) / frame.width, 50 / frame.height)
        if k < 1:
            frame = frame.resize((max(1, round(frame.width * k)), max(1, round(frame.height * k))), Image.NEAREST)
        out.append((int(n), frame))
    return out


def pane(sprite, k):
    """An enemy in leaded glass, W x 64, under a pointed arch."""
    fw, fh = sprite.size
    W, H = PANE_W, 64                                         # every window one size (user)
    dark, light = FIG[k % len(FIG)]
    back = 'w' if dark == '9' else BACK[k % 3]                # a blue figure on the pale
    cx = (W - 1) / 2
    arch = W // 2 + 2                                         # the arch's height
    def inside(x, y):
        if y >= arch:
            return True
        r = W * 0.85                                          # two arcs meeting at the top: a pointed arch
        a = math.hypot(x + 0.5 - (cx + 0.5 - r + W / 2), y + 0.5 - arch)
        b = math.hypot(x + 0.5 - (cx + 0.5 + r - W / 2), y + 0.5 - arch)
        return a <= r and b <= r
    g = [[back if inside(x, y) else '.' for x in range(W)] for y in range(H)]
    for y in range(H):                                        # the diamond lattice of lead behind
        for x in range(W):
            if g[y][x] == back and ((x + y) % 8 == 0 or (x - y) % 8 == 0):
                g[y][x] = 'K'
    px = sprite.load()
    lums = sorted(sum(px[i, j][:3]) for j in range(fh) for i in range(fw) if px[i, j][3] and sum(px[i, j][:3]) > 120)
    mid = lums[len(lums) // 2] if lums else 300
    x0, y0 = (W - fw) // 2, H - 4 - fh
    fig = set()
    for j in range(fh):
        for i in range(fw):
            p = px[i, j]
            if not p[3]:
                continue
            s = sum(p[:3])
            g[y0 + j][x0 + i] = 'K' if s <= 120 else (dark if s < mid else light)
            fig.add((x0 + i, y0 + j))
    for (x, y) in list(fig):                                  # a came of lead round the figure
        for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = x + i, y + j
            if (X, Y) not in fig and 0 <= X < W and 0 <= Y < H and g[Y][X] != '.':
                g[Y][X] = 'K'
    for y in range(H):                                        # the pane's own lead edge
        for x in range(W):
            if g[y][x] != '.' and any(not (0 <= x + i < W and 0 <= y + j < H) or g[y + j][x + i] == '.'
                                      for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    return g


def design(n_panes=None):
    def pad(rows):
        return [''.join(r) + '.' * (VW - len(r)) for r in rows] + ['.' * VW] * (VH - len(rows))
    v = {'brick': brick(), 'bones': bones(),
         'flags': flags(), 'ashlar': ashlar(False), 'ashlar_side': ashlar(True), 'cap': cap()}
    for k, (n, sp) in enumerate(enemies()[:n_panes]):
        v['pane_%02d' % n] = pane(sp, k)
    v = {k: pad(r) for k, r in v.items()}
    bad = []
    for name, rows in v.items():                         # four colours a cell, as the game holds them
        for cy in range(0, VH, 16):
            for cx in range(0, VW, 16):
                cell = {c for r in rows[cy:cy + 16] for c in r[cx:cx + 16]} - {'.'}
                if len(cell) > 4:
                    bad.append((name, cx, cy, ''.join(sorted(cell))))
    assert not bad, bad[:8]
    return {'pal': PAL, 'view_w': VW, 'order': list(v), 'views': v}


if __name__ == '__main__':
    json.dump(design(int(sys.argv[2]) if len(sys.argv) > 2 else None), open(sys.argv[1], 'w'))
