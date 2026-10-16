"""The interior style bible's measurable half (art/direction/INTERIOR_STYLE.md):
the materials every interior draws with, the textures laid from them, and the
checker.

    python tools/interior_style.py                   # every type: PASS/FAIL a rule, a row a swatch
    python tools/interior_style.py graveyard tree    # some
    python tools/interior_style.py --board out.png   # the swatches side by side, their verdicts under them

Measured from the two interiors the user is happy with -- the graveyard and
the stonehenge barrow -- whose design scripts draw through this file.
"""
import glob, importlib, os, random, sys
from dungeon_walls import RIM_KINDS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
WALLS = os.path.join(ROOT, 'art', 'structures', 'dungeon_walls')
ROOMS = os.path.join(ROOT, 'art', 'structures', 'interiors')

# A material: its tones from lit to dark, and its joint. A plane takes two
# tones next to each other (its base and its shade); a side in shade takes the
# next two down.
MATERIALS = {
    'brick': {'tones': ('b6433d', '792727', '5d1e1f'), 'joint': '531b1c'},   # the houses' red
    'stone': {'tones': ('c6ccda', '9797aa', '595965'), 'joint': '000000'},   # the stonehenge stones' greys
    'wood':  {'tones': ('967448', '785830', '493712'), 'joint': '493712'},
    'grass': {'tones': ('4fa667', '235436'), 'joint': '000000'},             # the overworld's, moonlit
    'bone':  {'tones': ('b2966a', '8d6b4f'), 'joint': '34343e'},             # the catacombs' walls, the dark between
    'sandstone': {'tones': ('f4ce80', 'b29e5c', '967448'), 'joint': '785830'},   # the desert pyramid's; its floor the two lower tones
    'heartwood': {'tones': ('815423', '633e1b', '3c2412', '22140c'), 'joint': '000000'},   # the giant tree's
    'soil':  {'tones': ('2b190e', '22140c'), 'joint': '000000'},
    'fungus': {'tones': ('d7a175', 'b2966a', '8d6b4f'), 'joint': '000000'},
    'dirt':  {'tones': ('583518', '3c2412'), 'joint': '000000'},
    'bark':  {'tones': ('605028', '463422', '2d230c'), 'joint': '000000'},
    'rock':  {'tones': ('5c4616', '2d230c'), 'joint': '000000'},             # the oasis's, the cliffs' in a darker olive
    'dark stone': {'tones': ('34343e', '292931', '1e1e24'), 'joint': '000000'},   # the ruins' walls (user: almost surreal darkness)
    'slate': {'tones': ('474751', '34343e'), 'joint': '000000'},             # the step pyramid's floor (user: "dark slate"); the mark inside the brick outlines on the ruins' black one
    # the caves' rock as its sheet is drawn; in the game each ore's own tones (tools/gen_cave_tiles.py)
    'cave rock': {'tones': ('9797aa', '474751', '292931'), 'joint': '000000'},
    'cave gem': {'tones': ('dcf0ff',), 'joint': '000000'},   # a gem set in the rock: in the game its ore's lit tone
}


def unit_tone(i, r, uw, ch, base, shade, joint, edge=1):
    """The tone at column i, row r of a uw x ch unit: its joint its bottom row
    and right column, its shade the `edge` pixels inside those (the light is
    from the upper left), the rest its base."""
    if r == ch - 1 or i == uw - 1:
        return joint
    return shade if r >= ch - 1 - edge or i >= uw - 1 - edge else base


def masonry(w, h, courses, base, shade, joint, edge=1, worn=None):
    """Units laid in courses -- courses is [(y0, height, unit width, x offset),
    ...], each pixel its unit_tone(); worn(course, unit) puts a whole unit in
    shade. Rows of tones, w x h; a course running off the grid is cut there."""
    g = [[base] * w for _ in range(h)]
    for k, (y0, ch, uw, off) in enumerate(courses):
        for y in range(max(y0, 0), min(y0 + ch, h)):
            for x in range(w):
                c = unit_tone((x - off) % uw, y - y0, uw, ch, base, shade, joint, edge)
                g[y][x] = shade if c == base and worn and worn(k, (x - off) // uw) else c
    return g


def chip(g, x, y, line='K'):
    """A unit's chipped upper-left corner: 3, 2, 1 pixels of line."""
    for dy, n in ((0, 3), (1, 2), (2, 1)):
        for i in range(n):
            g[y + dy][(x + i) % len(g[0])] = line


def crack(g, x, y0, y1, line='K'):
    """A crack down a block from (x, y0) to the row above y1: one connected
    line, wandering a pixel."""
    for y in range(y0, y1):
        g[y][x % len(g[0])] = line
        x += 1 if y % 5 == 0 else -1 if y % 7 == 0 else 0


def bond(w, h, uw, ch, base, shade, joint, seed=0, edge=1, wear=True, chipped=True):
    """A running bond of uw x ch units tiling w x h. wear is brick's (the
    graveyard's): one unit in four whole in shade, three in ten with a chipped
    corner. Stone goes without, as the stonehenge's blocks do. chipped=False
    keeps the worn units and leaves the chips out: an isometric floor shows a
    chip as a comb (the catacombs' brick)."""
    rng = random.Random(seed)
    n, worn, chips = w // uw, {}, []
    for c in range(h // ch):
        for u in range(n):
            worn[(c, u)] = wear and rng.random() < 0.25
            if wear and rng.random() < 0.3 and chipped:
                chips.append(((u * uw + uw // 2 * (c % 2)) % w, c * ch))
    g = masonry(w, h, [(c * ch, ch, uw, uw // 2 * (c % 2)) for c in range(h // ch)], base, shade, joint, edge,
                worn=lambda c, u: worn[(c, u % n)])
    for x, y in chips:
        chip(g, x, y)
    return g


def planks(w, h, base, shade, gap, line='K'):
    """Planks across, 8 tall, a dark gap between, their ends staggered, nail
    heads at each end, grain in the shade."""
    g = [[base] * w for _ in range(h)]
    for y in range(h):
        if y % 8 >= 6:
            g[y] = [gap if y % 8 == 7 else shade] * w            # the gap, its shadowed edge
    for p in range(h // 8):
        end = (p * 23) % w                                       # each plank's butt joint
        for y in range(p * 8, p * 8 + 7):
            g[y][end] = gap
        for nx in ((end + 2) % w, (end - 3) % w):
            g[p * 8 + 2][nx] = line; g[p * 8 + 3][nx] = line     # nail heads
        for x in range(0, w, 9):                                 # grain
            for i in range(3):
                g[p * 8 + 1 + (x // 9) % 4][(x + p * 5 + i) % w] = shade
    return g


# ---------------------------------------------------------------- the checker

# type: (design module, its design() arguments, the views that are texture --
# None: all of them; the rest is drawn decoration, which the rules leave be).
# A house room is in its house's own brick, as its outside wall is (user,
# 2026-10-12: left as it is), so the two rules read off MATERIALS pass it by.
TYPES = {
    'graveyard':    ('graveyard_design', (), ('brick', 'board', 'face_brick_s', 'face_brick_e', 'face_board_s',
                                              'face_board_e', 'wall_brick', 'wall_board', 'under_brick', 'under_board')),
    'stonehenge':   ('barrow_design', (), ('front', 'top', 'side')),
    'catacombs':    ('catacombs_design', (0,), ('brick', 'bones', 'flags', 'ashlar', 'ashlar_side', 'cap')),
    'ruins':        ('ruins_design', (), None),
    # a pyramid's stair pieces are cut from a strip across several planes, and
    # the Mayan faces are carved all over: neither is a swatch of one texture
    'pyramid':      ('pyramid_design', ('egypt',), ('band0', 'band1', 'band2') + RIM_KINDS + ('side_l', 'side_r')),
    'pyramid_maya': ('pyramid_design', ('maya',), RIM_KINDS + ('side_l', 'side_r')),
    # the tree's _shade swatches are its lit ones a tone down, and a lip is an
    # edge 8 px tall holding two planes: the swatches they come from are checked
    'tree':         ('tree_design', (), ('heart', 'soil', 'soil_deep', 'fungus', 'dirt', 'bark')),
    'oasis':        (None, (), None),                # no design: the rock the game bakes (tools/gen_oasis.py rock())
    'cave':         (None, (), None),                # the pieces of cave_rock_design.py, a cell each
}
HOUSES = [os.path.basename(f)[:-3] for f in sorted(glob.glob(os.path.join(ROOMS, '*_design.py')))]
TYPES.update({m[:-7]: (m, (), ('room',)) for m in HOUSES})
REFERENCE = ('graveyard', 'stonehenge')
RULES = {'pal': 'off palette', 'col': 'over 4 colours', 'speck': 'specks', 'ramp': 'undeclared colours', 'lit': 'highlight'}


SPECK = 0.007   # lone pixels a swatch may hold, of its own: the reference's worst is 0.6% (the clod under the brick)
LIT = 0.30      # the least of a material its lightest tone covers: the reference's least is 33% (the boardwalk's posts)


def crop(px):
    """A view cut to what is drawn in it."""
    ys = [y for y, r in enumerate(px) if any(r)]
    xs = [x for x in range(len(px[0])) if any(r[x] for r in px)]
    return [r[xs[0]:xs[-1] + 1] for r in px[ys[0]:ys[-1] + 1]]


def swatches(name):
    """A type's texture views as {view: rows of 'rrggbb' or None}."""
    for p in (WALLS, ROOMS, os.path.join(ROOT, 'art', 'structures')):
        if p not in sys.path:
            sys.path.insert(0, p)
    mod, args, views = TYPES[name]
    if name == 'oasis':
        import gen_oasis
        tone = dict(zip('210', MATERIALS['rock']['tones'] + (MATERIALS['rock']['joint'],)))
        return {'rock': [[tone[c] for c in r] for r in gen_oasis.rock()]}
    if name == 'cave':                               # its pieces as drawn (the sheet the user edits), a cell each
        from PIL import Image
        from cave_rock_design import CELLS, SIZE
        im = Image.open(os.path.join(WALLS, 'cave_rock.png')).convert('RGBA')
        cut = lambda cx, cy, w, h: [[('%02x%02x%02x' % im.getpixel((x, y))[:3]) if im.getpixel((x, y))[3] else None
                                     for x in range(cx * 16, (cx + w) * 16)] for y in range(cy * 16, (cy + h) * 16)]
        return {k: cut(cx, cy, *SIZE.get(k, (1, 1))) for k, (cx, cy) in CELLS.items()}
    d = importlib.import_module(mod).design(*args)
    out = {k: [[d['pal'].get(c) for c in r] for r in d['views'][k]] for k in views or d['order']}
    return {k: px for k, px in out.items() if any(any(r) for r in px)}


def check(px, own=False, materials=MATERIALS, speck=SPECK):
    """A swatch against the rules -> {rule: how many pixels, cells or
    materials break it; 0 a pass}. own: its colours are its own, not
    MATERIALS' (a house room). materials, speck: the table and the lone-pixel
    share it is held to (the overworld's pieces have their own,
    tools/overworld_style.py)."""
    from collections import Counter
    sys.path.insert(0, os.path.join(ROOT, 'art', 'direction'))
    from fcremap import PALETTE
    palette = {'%02x%02x%02x' % p for p in PALETTE}
    cells = sum(1 for cy in range(0, len(px), 16) for cx in range(0, len(px[0]), 16)    # on the sheet's own grid
                if len({c for r in px[cy:cy + 16] for c in r[cx:cx + 16]} - {None}) > 4)
    # a cell over a quarter clear is a piece cut from a texture (a cave's sloped
    # edges): which of its tones there is most of is the cut's doing, not a highlight
    piece = sum(c is None for r in px for c in r) > len(px) * len(px[0]) // 4
    px = crop(px)
    h, w = len(px), len(px[0])
    count = Counter(c for r in px for c in r if c)
    known = {t for d in materials.values() for t in d['tones'] + (d['joint'],)} | {'000000'}
    tiles = sum(count.values()) == w * h         # drawn to every edge: it repeats, so its edges are neighbours
    def at(x, y):
        return px[y % h][x % w] if tiles else px[y][x] if 0 <= y < h and 0 <= x < w else None
    # black alone is a mark -- a bolt, a nail head, an eye socket; a tone alone is a speck
    lone = sum(1 for y in range(h) for x in range(w) if px[y][x] not in (None, '000000') and not any(
        at(x + i, y + j) == px[y][x] for j in (-1, 0, 1) for i in (-1, 0, 1) if i or j))
    dim = 0                                      # a lightest tone that is only a highlight
    for d in materials.values():
        here = [count[t] for t in d['tones'] if count[t]]
        dim += bool(here) and here[0] < LIT * sum(here)
    return {'pal': sum(n for c, n in count.items() if c not in palette),
            'col': cells,
            'speck': lone if lone > speck * sum(count.values()) else 0,
            'ramp': 0 if own else sum(n for c, n in count.items() if c not in known),
            'lit': 0 if own or piece else dim}


def verdict(name, view, px):
    """The rules a type's swatch breaks, by their names."""
    return [RULES[k] for k, n in check(px, TYPES[name][0] in HOUSES).items() if n]


def board(names, out, swatches=swatches, verdict=verdict, reference=REFERENCE, cut=(256, 136)):
    """Every swatch at one scale (2x, its inked part, cut at 256 x 136), a row
    a type, what it breaks written under it."""
    from PIL import Image, ImageDraw
    Z, GAP, LABEL, BG = 2, 12, 100, (40, 40, 48)
    wide = lambda im, bad: max(im.width, 70, 6 * len(', '.join(bad)))
    rows = []
    for name in names:
        row = []
        for view, px in swatches(name).items():
            ink = crop(px)
            im = Image.new('RGB', (min(len(ink[0]), cut[0]), min(len(ink), cut[1])), BG)
            for y in range(im.height):
                for x in range(im.width):
                    if ink[y][x]:
                        im.putpixel((x, y), tuple(int(ink[y][x][i:i + 2], 16) for i in (0, 2, 4)))
            bad = verdict(name, view, px)
            row.append((view, im.resize((im.width * Z, im.height * Z), Image.NEAREST), bad))
        while row:                               # a type with many pieces runs on to further lines
            n, x = 0, LABEL
            while n < len(row) and (n == 0 or x + wide(row[n][1], row[n][2]) <= 1400):
                x += wide(row[n][1], row[n][2]) + GAP
                n += 1
            rows.append((name, row[:n]))
            name, row = '', row[n:]
    W = LABEL + max(sum(wide(im, bad) + GAP for _, im, bad in row) for _, row in rows)
    H = sum(max(im.height for _, im, _ in row) + 36 for _, row in rows)
    sheet = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    y = 0
    for name, row in rows:
        dr.text((4, y + 4), name + ('\n(reference)' if name in reference else ''), fill=(255, 255, 255))
        x = LABEL
        for view, im, bad in row:
            sheet.paste(im, (x, y + 4))
            dr.text((x, y + im.height + 6), view, fill=(200, 200, 200))
            dr.text((x, y + im.height + 18), ', '.join(bad) or 'pass', fill=(255, 120, 120) if bad else (120, 255, 120))
            x += wide(im, bad) + GAP
        y += max(im.height for _, im, _ in row) + 36
    sheet.save(out)


if __name__ == '__main__':
    args = sys.argv[1:]
    out = args.pop(args.index('--board') + 1) if '--board' in args else None
    names = [a for a in args if a != '--board'] or list(TYPES)
    if out:
        board(names, out)
        sys.exit()
    fails = 0
    print('%-28s' % 'swatch' + ''.join('%7s' % r for r in RULES))
    for name in names:
        for view, px in swatches(name).items():
            res = check(px, TYPES[name][0] in HOUSES)
            fails += any(res.values())
            print('%-28s' % (name + '/' + view) + ''.join('%7s' % (res[r] or '.') for r in RULES))
    print('FAIL: %d swatches' % fails if fails else 'PASS')
    sys.exit(1 if fails else 0)
