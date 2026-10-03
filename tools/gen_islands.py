"""Bake the library of elevated landforms from Mother 1's map and drawings.

    python tools/gen_islands.py [--count 150] [--big 300] [--seed 7]
    python tools/palette_pass.py --write          # always last

Sources: the whole Mother 1 overworld (art/reference/eb0map_big.png, native
size, 16 px tiles) and the user's island drawings (art/cliffs/islands/
island{1,2,3}.aseprite, exported beside them as png). Every hill in the game
is made of their sprites, pixel for pixel, in layouts that are not theirs:

  * The map's landforms are read off it (load_map): pieces of cliff-coloured
    tiles drawn in the cliff vocabulary, boxed with a tile of margin, other
    terrain in the box read as plain ground. Their walls' band direction
    settles which ground is high (settle_levels: teeth face the low side).
  * Nothing from the map is stamped as it is. The big landforms of the
    library are SPLICES: the left part of one landform beside the right part
    of another, or a top over a bottom, at a cut and offset where every 2x2
    block across the seam is a block the sources contain. The walls run on
    across the seam by construction, so the result closes; and splices are
    spliced again, so lobes of three or four sources meet in one landform.
  * The small islands are GROWN by wave function collapse from the 2x2
    blocks of the drawings, as before: a tile may take a sprite only where
    each block it lands in is one of the sources'.

Every sprite, seam and corner of every entry is therefore Mother 1's; the
shapes are new. Every entry is checked block by block before it is written.

Written:
  assets/tileset.png       one cell per distinct sprite, from row ISLAND_ROW0,
                           cell 0 the plain ground (nothing drawn); grass is
                           the sheet's key colour
  src/islands.inc          the sprites' kinds and every landform as a grid of
                           cells plus its level per tile; see write_inc()
  art/cliffs/islands.png   the library, largest first, for looking at

Tiles holding the tuft green, or any colour that is not grass, rock or ink,
are set dressing (tufts, trees, water) and are read as plain ground. Scree
is ground too: grains under the foot of a wall, to be walked among. A wall
tile is one with rock or ink on it.
"""
import argparse
import os
import sys
import time
from collections import Counter, deque

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISLAND_DIR = os.path.join(ROOT, 'art', 'cliffs', 'islands')
MAP = os.path.join(ROOT, 'art', 'reference', 'eb0map_big.png')
CLUSTER = os.path.join(ROOT, 'art', 'reference', 'cliff_reference.png')
OUT_SHEET = os.path.join(ROOT, 'assets', 'tileset.png')
OUT_INC = os.path.join(ROOT, 'src', 'islands.inc')
OUT_PNG = os.path.join(ROOT, 'art', 'cliffs', 'islands.png')

CELL = 16
SHEET_COLS = 256
ISLAND_ROW0 = 16          # first sheet row of sprite cells
ROWS_END = 176            # the cliff's region of the sheet ends here; the rest of it is cleared

KEY = (255, 0, 0)
GRASS = (168, 240, 188)
BROWN = (136, 112, 0)
INK = (0, 0, 0)
TUFT = (0, 168, 0)
UNKNOWN = -1              # a tile the picture does not show: past its edge, or under a tree or a tuft
FILL_SEED = 1             # the collapse that settles unknown tiles; one seed, so every worker reads the same sources

REFS = ('island1', 'island2', 'island3')
MIN_HIGH = 6              # enclosed ground tiles a grown island must have
BOX_W = (9, 24)           # islands are grown in boxes this size, inclusive
BOX_H = (8, 18)
GROW_BUDGET = 420         # seconds a worker may spend growing small islands

MAP_MIN_WALL = 12         # a map piece this small is a scrap
MAP_MAX_W, MAP_MAX_H = 160, 240   # a map piece bigger than this is a region, not a landform
VOCAB_SHARE = 0.9         # of a cliff piece's tiles are sprites the drawings and the cluster use
SOLID_SHARE = 0.45        # more solid rock than this is a mountain mass, not a landform
STAMP_MAX_W, STAMP_MAX_H = 80, 60   # the biggest a library entry may be
SPLICE_MIN_HIGH = 60      # plateau of a big landform
LARGE_HIGH = 150          # plateau size classes for the placement
MEDIUM_HIGH = 40


# ---------------------------------------------------------------- sprites

class Sprites:
    """Every distinct 16x16 sprite, numbered; 0 is the plain ground."""
    def __init__(self):
        self.ids = {}
        self.img = []
        self.kind = []          # 0 ground, 1 rock, 2 line
        self.id(np.full((CELL, CELL, 3), GRASS, np.uint8))

    def id(self, t):
        k = t.tobytes()
        if k not in self.ids:
            self.ids[k] = len(self.img)
            self.img.append(t.copy())
            rock = int(np.all(t == BROWN, axis=2).sum())
            ink = int(np.all(t == INK, axis=2).sum())
            # Rock always carries ink (its cracks); brown with none is scree,
            # grains on open ground, and is ground.
            self.kind.append(0 if ink == 0 else 1 if rock >= 8 else 2 if ink >= 3 else 0)
        return self.ids[k]

    def wall(self, s):
        return s >= 0 and self.kind[s] != 0

    def solid(self, s):
        im = self.img[s]
        return int((np.all(im == BROWN, axis=2) | np.all(im == INK, axis=2)).sum()) >= 224


def tile_codes(a):
    """Per tile of an image: only-cliff-colours, cliff-coloured (rock or ink
    on it, no tuft), scree (brown grains on clean ground), and plain ground
    (grass, a tuft, a few grains: nothing that could be rock underneath).
    A tile that is none of these shows something else -- a tree, water, a
    tuft standing on rock -- and what the cliff does there is unknown."""
    H, W = a.shape[0] // CELL, a.shape[1] // CELL
    code = np.zeros(a.shape[:2], np.uint8)
    for k, col in ((1, GRASS), (2, BROWN), (3, INK), (4, TUFT)):
        code[np.all(a == col, axis=2)] = k
    t = code.reshape(H, CELL, W, CELL).transpose(0, 2, 1, 3)
    clean = (t != 0).all(axis=(2, 3))
    cliffish = clean & ~(t == 4).any(axis=(2, 3)) & (((t == 2).sum(axis=(2, 3)) >= 8) | ((t == 3).sum(axis=(2, 3)) >= 3))
    scree = clean & ~cliffish & ~(t == 4).any(axis=(2, 3)) & (t == 2).any(axis=(2, 3))
    ground = clean & ~cliffish & ~scree & ((t == 2).sum(axis=(2, 3)) < 8) & ((t == 3).sum(axis=(2, 3)) < 3)
    return H, W, clean, cliffish, scree, ground


RUNS_INTO = 8             # rock pixels along a cell's edge for the rock to run on past it


def edge_rock(sp, s, side):
    """Rock pixels on one edge of sprite s: 0 top, 1 bottom, 2 left, 3 right."""
    im = sp.img[s]
    rock = np.all(im == BROWN, axis=2) | np.all(im == INK, axis=2)
    return int((rock[0], rock[15], rock[:, 0], rock[:, 15])[side].sum())


def settle_hidden(sp, grid, hidden):
    """Hidden tiles -- past the picture's edge, under a tree or a tuft --
    become UNKNOWN where a neighbouring wall's rock runs to the edge they
    share, since the wall then goes on under them, and plain ground
    everywhere else, where nothing they hide could be rock. A flank's teeth
    touch its edge by a few pixels and stand beside real ground; a band that
    fills its edge does not stop there. RUNS_INTO tells the two apart. A tile
    is UNKNOWN only where the picture may hide rock, and a splice cannot
    cross an unknown tile, so no more of them than that."""
    h, w = grid.shape
    out = grid.copy()
    for y in range(h):
        for x in range(w):
            if not hidden[y, x]:
                continue
            runs = False
            # the neighbour above faces this tile with its bottom edge, and so on
            for (dy, dx), side in (((-1, 0), 1), ((1, 0), 0), ((0, -1), 3), ((0, 1), 2)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and sp.wall(grid[ny, nx]) and edge_rock(sp, grid[ny, nx], side) >= RUNS_INTO:
                    runs = True
                    break
            out[y, x] = UNKNOWN if runs else 0
    return out


def load_island(sp, name):
    """A drawing as a grid of sprite ids with a one-tile margin, and which of
    its tiles were wiped (tufts, trees, water) so a diff can skip them.

    The margin is hidden, not ground: the picture stops there, and a wall
    that runs to its edge goes on past it. island1's bottom row holds the top
    of a front whose foot is outside the picture; read as ground, the margin
    made "front over grass" a block of the reference, and the islands grew
    that block by the hundred. So is a tile with something standing on the
    rock. What the drawing shows as plain ground is ground, and a hidden tile
    beside no wall is ground too (settle_hidden)."""
    a = np.array(Image.open(os.path.join(ISLAND_DIR, name + '.png')).convert('RGB'))
    H, W, clean, cliffish, scree, ground = tile_codes(a)
    grid = np.zeros((H + 2, W + 2), int)
    wiped = np.zeros((H + 2, W + 2), bool)
    hidden = np.ones((H + 2, W + 2), bool)
    for ty in range(H):
        for tx in range(W):
            hidden[ty + 1, tx + 1] = False
            if cliffish[ty, tx] or scree[ty, tx]:
                grid[ty + 1, tx + 1] = sp.id(a[ty * CELL:(ty + 1) * CELL, tx * CELL:(tx + 1) * CELL])
            else:
                wiped[ty + 1, tx + 1] = True
                hidden[ty + 1, tx + 1] = not ground[ty, tx]
    return settle_hidden(sp, grid, hidden), wiped


def mirror(sp, grid):
    out = np.zeros_like(grid)
    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]):
            s = grid[y, x]
            out[y, grid.shape[1] - 1 - x] = UNKNOWN if s == UNKNOWN else sp.id(sp.img[s][:, ::-1, :])
    return out


def pieces_of(mask, conn=8):
    """8-connected (or 4-connected) pieces of a mask: label grid (1-based)
    and the cells of each."""
    H, W = mask.shape
    lab = np.zeros((H, W), np.int32)
    out = []
    steps = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx] if conn == 8 else [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for y in range(H):
        for x in range(W):
            if not mask[y, x] or lab[y, x]:
                continue
            out.append([])
            q = deque([(y, x)])
            lab[y, x] = len(out)
            while q:
                p, r = q.popleft()
                out[-1].append((p, r))
                for dy, dx in steps:
                    yy, xx = p + dy, r + dx
                    if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = len(out)
                        q.append((yy, xx))
    return lab, out


def load_map(sp, vocab):
    """The map's landforms as grids, in the cliff vocabulary only.

    The map draws boulder fields and track outlines in the cliff's colours,
    so a piece of cliff-coloured tiles is cliff only when VOCAB_SHARE of it
    is sprites the drawings and the cluster reference use (measured: pieces
    are either nine tenths or under four tenths, nothing between), and when
    no more than SOLID_SHARE of it is solid rock (a mountain mass is a field
    of it; a landform's band is one solid row in three)."""
    a = np.array(Image.open(MAP).convert('RGB'))
    H, W, clean, cliffish, scree, ground = tile_codes(a)
    sid = np.full((H, W), -1, int)
    ys, xs = np.nonzero(cliffish)
    for y, x in zip(ys, xs):
        sid[y, x] = sp.id(a[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL])
    lab, pieces = pieces_of(cliffish)
    bbox = []
    iscliff = []
    for cells in pieces:
        py = [c[0] for c in cells]
        px = [c[1] for c in cells]
        bbox.append((min(py), max(py), min(px), max(px)))
        inv = sum(sid[p, r] in vocab for p, r in cells)
        solid = sum(sp.solid(sid[p, r]) for p, r in cells)
        iscliff.append(inv >= VOCAB_SHARE * len(cells) and solid <= SOLID_SHARE * len(cells))
    wall = np.zeros((H, W), bool)
    for cells, ok in zip(pieces, iscliff):
        if ok:
            for p, r in cells:
                wall[p, r] = True
    out = []
    for pi, cells in enumerate(pieces):
        if not iscliff[pi] or len(cells) < MAP_MIN_WALL:
            continue
        by0, by1, bx0, bx1 = bbox[pi]
        y0, y1, x0, x1 = by0 - 1, by1 + 2, bx0 - 1, bx1 + 2
        if y0 < 0 or x0 < 0 or y1 > H or x1 > W:
            continue
        if x1 - x0 > MAP_MAX_W or y1 - y0 > MAP_MAX_H:
            continue
        h, w = y1 - y0, x1 - x0
        # Hidden where the map hides what the cliff does: a tree or a tuft on
        # the rock, a boulder or a track in the cliff's colours, another
        # landform's wall cut by the box. Ground where nothing runs into
        # them, unknown where a wall's rock does (settle_hidden): a boulder
        # at the foot of a band is on open ground, one in the middle of a
        # band's bottom row is where the map stopped showing the band.
        grid = np.zeros((h, w), int)
        hidden = np.zeros((h, w), bool)
        for yy in range(h):
            for xx in range(w):
                my, mx = y0 + yy, x0 + xx
                if cliffish[my, mx]:
                    if not wall[my, mx]:
                        hidden[yy, xx] = True     # a boulder or a track in the cliff's colours
                        continue
                    other = lab[my, mx]
                    if other != pi + 1:
                        # another landform's wall: part of this picture only when it lies whole in the box
                        oy0, oy1, ox0, ox1 = bbox[other - 1]
                        if not (oy0 >= y0 and oy1 < y1 and ox0 >= x0 and ox1 < x1):
                            hidden[yy, xx] = True
                            continue
                    grid[yy, xx] = sid[my, mx]
                elif scree[my, mx]:
                    grid[yy, xx] = sp.id(a[my * CELL:(my + 1) * CELL, mx * CELL:(mx + 1) * CELL])
                elif not ground[my, mx]:
                    hidden[yy, xx] = True
        out.append(settle_hidden(sp, grid, hidden))
    return out


def vocabulary(sp):
    """The wall sprites of the drawings and of the cluster reference, and
    their mirrors."""
    vocab = set()
    for name in REFS:
        g, _ = load_island(sp, name)
        m = mirror(sp, g)
        for s in set(g.ravel()) | set(m.ravel()):
            if sp.wall(s):
                vocab.add(s)
    a = np.array(Image.open(CLUSTER).convert('RGB'))
    H, W, clean, cliffish, scree, ground = tile_codes(a)
    for y in range(H):
        for x in range(W):
            if cliffish[y, x]:
                t = a[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL]
                vocab.add(sp.id(t))
                vocab.add(sp.id(t[:, ::-1, :]))
    return vocab


# ------------------------------------------------------------------ levels

def tooth_foot(sp, s):
    """A band's toothed top has no rock along its top row and rock along its
    bottom; a foot the reverse."""
    im = sp.img[s]
    rock = np.all(im == BROWN, axis=2) | np.all(im == INK, axis=2)
    top, bot = int(rock[0].sum()), int(rock[15].sum())
    return (top == 0 and bot >= 12), (top >= 12 and bot == 0)


def settle_levels(sp, g):
    """The level of every tile of a landform, 0-3, from its walls.

    Regions of non-wall tiles; a toothed top votes the region above it high
    and a foot the region below it low (teeth face the low side); the border
    is low; a region across a line from a settled one takes the other side.
    Nesting depth comes from repeated floods; a high region is as high as it
    is nested, a low one two less (a pocket in a tableland is sunken)."""
    h, w = g.shape
    wm = np.array([sp.wall(s) for s in g.ravel()]).reshape(h, w)
    reg = np.zeros((h, w), int)
    nreg = 0
    for y in range(h):
        for x in range(w):
            if wm[y, x] or reg[y, x]:
                continue
            nreg += 1
            q = deque([(y, x)])
            reg[y, x] = nreg
            while q:
                p, r = q.popleft()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = p + dy, r + dx
                    if 0 <= yy < h and 0 <= xx < w and not wm[yy, xx] and not reg[yy, xx]:
                        reg[yy, xx] = nreg
                        q.append((yy, xx))
    votes = {}
    for y in range(1, h - 1):
        for x in range(w):
            if not wm[y, x]:
                continue
            th, ft = tooth_foot(sp, g[y, x])
            if th and reg[y - 1, x]:
                votes.setdefault(reg[y - 1, x], Counter())['high'] += 1
            if ft and reg[y + 1, x]:
                votes.setdefault(reg[y + 1, x], Counter())['low'] += 1
    side = {r: (1 if c['high'] >= c['low'] else -1) for r, c in votes.items()}
    outside = {reg[0, x] for x in range(w)} | {reg[h - 1, x] for x in range(w)} \
            | {reg[y, 0] for y in range(h)} | {reg[y, w - 1] for y in range(h)}
    outside.discard(0)
    for r in outside:
        side[r] = -1
    for _ in range(64):
        changed = False
        for y in range(h):
            for x in range(w):
                if not wm[y, x]:
                    continue
                nb = set()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and reg[yy, xx]:
                        nb.add(reg[yy, xx])
                known = {side[r] for r in nb if r in side}
                if len(known) == 1:
                    v = -next(iter(known))
                    for r in nb:
                        if r not in side:
                            side[r] = v
                            changed = True
        if not changed:
            break
    depth = np.zeros((h, w), int)
    frontier = np.zeros((h, w), bool)
    frontier[0, :] = frontier[-1, :] = frontier[:, 0] = frontier[:, -1] = True
    frontier &= ~wm
    for D in range(1, 6):
        reach = np.zeros((h, w), bool)
        q = deque(zip(*np.nonzero(frontier)))
        for p in q:
            reach[p] = True
        while q:
            p, r = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = p + dy, r + dx
                if 0 <= yy < h and 0 <= xx < w and not wm[yy, xx] and not reach[yy, xx]:
                    reach[yy, xx] = True
                    q.append((yy, xx))
        inner = ~wm & ~reach & (depth == D - 1)
        if not inner.any():
            break
        depth[inner] = D
        frontier = inner
    level = np.zeros((h, w), int)
    for y in range(h):
        for x in range(w):
            r = reg[y, x]
            if not r or depth[y, x] == 0:
                continue
            sd = side.get(r, 1)
            level[y, x] = depth[y, x] if sd > 0 else max(0, depth[y, x] - 2)
    return np.minimum(level, 3)


# ------------------------------------------------------------------ model

class Model:
    """The 2x2 blocks of the sources, and how they may overlap."""
    N = 2

    def __init__(self, sp, refs):
        N = self.N
        pats, weights = {}, Counter()
        for g in refs:
            h, w = g.shape
            for y in range(h - N + 1):
                for x in range(w - N + 1):
                    blk = g[y:y + N, x:x + N]
                    if (blk == UNKNOWN).any():
                        continue                  # the picture does not show this block
                    k = blk.tobytes()
                    if k not in pats:
                        pats[k] = blk.copy()
                    weights[k] += 1
        self.keys = list(pats.keys())
        self.pats = [pats[k] for k in self.keys]
        self.w = np.array([weights[k] for k in self.keys], float)
        self.P = len(self.pats)
        self.blocks = set(self.keys)
        self.K = len(sp.img) + 1
        self.bkeys = np.array(sorted({self.bkey(int(p[0, 0]), int(p[0, 1]), int(p[1, 0]), int(p[1, 1])) for p in self.pats}), np.int64)
        self.dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        self.compat = {}
        for dx, dy in self.dirs:
            def sub(p, ox, oy):
                ys = slice(max(0, oy), N + min(0, oy))
                xs = slice(max(0, ox), N + min(0, ox))
                return p[ys, xs].tobytes()
            byk = {}
            for j, q in enumerate(self.pats):
                byk.setdefault(sub(q, -dx, -dy), []).append(j)
            c = np.zeros((self.P, self.P), bool)
            for i, p in enumerate(self.pats):
                for j in byk.get(sub(p, dx, dy), []):
                    c[i, j] = True
            self.compat[(dx, dy)] = c.astype(np.float32)   # a product finds the allowed set faster than a slice
        self.top = np.array([np.all(p[0] == 0) for p in self.pats])
        self.bot = np.array([np.all(p[-1] == 0) for p in self.pats])
        self.lef = np.array([np.all(p[:, 0] == 0) for p in self.pats])
        self.rig = np.array([np.all(p[:, -1] == 0) for p in self.pats])
        self.wall00 = np.array([sp.wall(p[0, 0]) for p in self.pats])
        self.allg = np.array([np.all(p == 0) for p in self.pats])
        self.vals = np.array([p for p in self.pats])                   # P x N x N

    def bkey(self, a, b, c, d):
        K = self.K
        return (a * K + b) * K * K + c * K + d

    def propagate(self, wave, stack):
        wh, ww, _ = wave.shape
        stack = list(stack)
        while stack:
            y, x = stack.pop()
            cell = wave[y, x]
            if not cell.any():
                return False
            cf = cell.astype(np.float32)
            for dx, dy in self.dirs:
                yy, xx = y + dy, x + dx
                if not (0 <= yy < wh and 0 <= xx < ww):
                    continue
                allowed = (cf @ self.compat[(dx, dy)]) > 0
                new = wave[yy, xx] & allowed
                if new.sum() < wave[yy, xx].sum():
                    wave[yy, xx] = new
                    if not new.any():
                        return False
                    stack.append((yy, xx))
        return True

    def collapse(self, wave, rng):
        """Settle a propagated wave cell by cell, least entropy first, each
        block drawn by its weight. False if it runs into a contradiction."""
        while True:
            cnt = wave.sum(axis=2)
            if not (cnt > 1).any():
                return True
            wt = np.where(wave, self.w, 0.0)
            sw = wt.sum(axis=2)
            with np.errstate(divide='ignore', invalid='ignore'):
                ent = np.log(sw) - (wt * np.log(np.where(wt > 0, wt, 1))).sum(axis=2) / sw
            ent = np.where(cnt > 1, ent, np.inf) + rng.random(ent.shape) * 1e-4
            y, x = np.unravel_index(int(np.argmin(ent)), ent.shape)
            ks = np.flatnonzero(wave[y, x])
            k = ks[rng.choice(len(ks), p=self.w[ks] / self.w[ks].sum())]
            wave[y, x] = False
            wave[y, x, k] = True
            if not self.propagate(wave, [(y, x)]):
                return False

    def refill(self, g, y0, y1, x0, x1, rng, change=None, free=None):
        """g with the inside of the window g[y0:y1, x0:x1] collapsed afresh
        from the blocks, the window's outer ring held as it is, or None.
        `free`, a mask the window's size, narrows what is collapsed to it.
        `change`, a tile (x, y) inside, must come out different: the
        weighted collapse would otherwise mostly rebuild what was there."""
        N = self.N
        sub = g[y0:y1, x0:x1]
        if free is None:
            free = np.zeros(sub.shape, bool)
            free[1:-1, 1:-1] = True
        wh, ww = sub.shape[0] - N + 1, sub.shape[1] - N + 1
        wave = np.ones((wh, ww, self.P), bool)
        for y in range(wh):
            for x in range(ww):
                for dy in range(N):
                    for dx in range(N):
                        yy, xx = y + dy, x + dx
                        if not free[yy, xx]:
                            wave[y, x] &= self.vals[:, dy, dx] == sub[yy, xx]
                        elif change == (x0 + xx, y0 + yy):
                            wave[y, x] &= self.vals[:, dy, dx] != sub[yy, xx]
        if not self.propagate(wave, [(y, x) for y in range(wh) for x in range(ww)]) or not self.collapse(wave, rng):
            return None
        out = g.copy()
        for y in range(wh):
            for x in range(ww):
                out[y0 + y:y0 + y + N, x0 + x:x0 + x + N] = self.pats[int(np.flatnonzero(wave[y, x])[0])]
        return out

    def run(self, w, h, rng, anchors, tries=6):
        """An island in a w x h box whose border is ground and whose anchor
        tiles hold a wall, or None."""
        N = self.N
        wh, ww = h - N + 1, w - N + 1
        for _ in range(tries):
            wave = np.ones((wh, ww, self.P), bool)
            wave[0, :, ~self.top] = False
            wave[-1, :, ~self.bot] = False
            wave[:, 0, ~self.lef] = False
            wave[:, -1, ~self.rig] = False
            for ay, ax in anchors:
                wave[ay, ax, ~self.wall00] = False
            restricted = [(y, x) for y in range(wh) for x in range(ww) if not wave[y, x].all()]
            if not self.propagate(wave, restricted):
                continue
            if not self.collapse(wave, rng):
                continue
            out = np.zeros((h, w), int)
            for y in range(wh):
                for x in range(ww):
                    out[y:y + N, x:x + N] = self.pats[int(np.flatnonzero(wave[y, x])[0])]
            return out
        return None

    def check(self, g):
        h, w = g.shape
        for y in range(h - 1):
            for x in range(w - 1):
                if g[y:y + 2, x:x + 2].tobytes() not in self.blocks:
                    raise AssertionError('block at %d,%d is not a reference block' % (x, y))


def fill_unknown(model, sp, g, rng, pad, reach=2, tries=4):
    """A source with its unknown tiles settled from the sources' blocks.

    A drawing's picture stops at its edge with walls running on past it; a
    tree or a tuft stands on the rock here and there. Those tiles are UNKNOWN
    and make no blocks. They are filled here by collapse, a window at a time:
    round each unknown tile, `reach` tiles each way, the known tiles fixed and
    the unknown ones free to take whatever the blocks allow -- so a front
    whose foot the picture cut off gets the foot the drawing gives that front
    elsewhere. Windows, not the whole patch at once, because one tile the
    sources cannot settle must not leave the rest of a drawing's edge open.
    `pad` rings of unknown are laid round the grid first, the outermost ring
    ground, so a wall at a drawing's edge has room to end: a foot, then the
    grass below it. A tile no window can settle is left unknown, and nothing
    is guessed."""
    N = model.N
    if pad:
        g = np.pad(g, pad, constant_values=UNKNOWN)
        g[0, :] = g[-1, :] = g[:, 0] = g[:, -1] = 0
    g = g.copy()
    if not (g == UNKNOWN).any():
        return g
    H, W = g.shape
    for cy in range(H):
        for cx in range(W):
            if g[cy, cx] != UNKNOWN:
                continue
            y0, y1 = max(0, cy - reach), min(H, cy + reach + 1)
            x0, x1 = max(0, cx - reach), min(W, cx + reach + 1)
            wh, ww = y1 - y0 - N + 1, x1 - x0 - N + 1
            if wh < 1 or ww < 1:
                continue
            unknown = g[y0:y1, x0:x1] == UNKNOWN
            for _ in range(tries):
                wave = np.ones((wh, ww, model.P), bool)
                for y in range(wh):
                    for x in range(ww):
                        for dy in range(N):
                            for dx in range(N):
                                v = g[y0 + y + dy, x0 + x + dx]
                                if v != UNKNOWN:
                                    wave[y, x] &= model.vals[:, dy, dx] == v
                if not model.propagate(wave, [(y, x) for y in range(wh) for x in range(ww)]):
                    break                             # no blocks fit the known tiles round here
                if not model.collapse(wave, rng):
                    continue
                # Only tiles strictly inside the window are written: every
                # block a tile inside makes lies in the window and was
                # checked, while a tile on the edge makes a block with what
                # lies just outside, and that one was not. The window centred
                # on it, later, holds it against all of its neighbours.
                for y in range(wh):
                    for x in range(ww):
                        p = model.pats[int(np.flatnonzero(wave[y, x])[0])]
                        for dy in range(N):
                            for dx in range(N):
                                gy, gx = y0 + y + dy, x0 + x + dx
                                inside = y0 < gy < y1 - 1 and x0 < gx < x1 - 1
                                if unknown[y + dy, x + dx] and inside:
                                    g[gy, gx] = p[dy, dx]
                break
    return g


def widen_holes(sp, g):
    """Every wall whose rock runs into a tile still unknown becomes unknown
    too. The blocks could not end that wall the way the picture cut it, so
    the wall is asked again along with the tile: a front the picture cut
    off then gets a top that has a foot in the sources."""
    out = g.copy()
    ys, xs = np.nonzero(g == UNKNOWN)
    for y, x in zip(ys.tolist(), xs.tolist()):
        for (dy, dx), side in (((-1, 0), 1), ((1, 0), 0), ((0, -1), 3), ((0, 1), 2)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < g.shape[0] and 0 <= nx < g.shape[1] and sp.wall(g[ny, nx]) and edge_rock(sp, g[ny, nx], side) >= RUNS_INTO:
                out[ny, nx] = UNKNOWN
    return out


def fill_passes(model, sp, g, rng, pad):
    """The smallest window first, then wider ones for whatever is left. A
    small window asks only the tiles round the one being settled; a wide one
    asks more of them at once and fails whole when any of them cannot agree."""
    g = fill_unknown(model, sp, g, rng, pad, reach=1)
    for reach in (2, 3):
        if (g == UNKNOWN).any():
            g = fill_unknown(model, sp, g, rng, 0, reach=reach)
    return g


def settle_sources(sp, grids, model, pad):
    """Every grid with its unknown tiles filled, deterministically. What the
    blocks cannot fill is widened by the wall that runs into it and asked
    once more (widen_holes); a splice cannot cross a tile left unknown, so
    every one settled is landforms gained."""
    out = []
    for i, g in enumerate(grids):
        rng = np.random.RandomState(FILL_SEED + i)
        g = fill_passes(model, sp, g, rng, pad)
        if (g == UNKNOWN).any():
            g = fill_passes(model, sp, widen_holes(sp, g), rng, 0)
        out.append(g)
    return out


def sources_of(sp, refs, landforms, log=False):
    """The sources as the model and the splices use them: the drawings and the
    map's landforms with their unknown tiles settled, and their mirrors. The
    drawings get two rings of room past their edge (the picture cut a wall
    off there); the map's boxes hold their own margin. Same in every
    process: the filling is seeded once, FILL_SEED."""
    draw = refs[0::2]                             # load_refs: each drawing, then its mirror
    raw = list(landforms) + [mirror(sp, g) for g in landforms] + list(refs)
    model0 = Model(sp, raw)
    draw_f = settle_sources(sp, draw, model0, 2)
    land_f = settle_sources(sp, landforms, model0, 0)
    if log:
        for name, before, after in (('drawings', draw, draw_f), ('map landforms', landforms, land_f)):
            b = sum(int((g == UNKNOWN).sum()) for g in before)
            a = sum(int((g == UNKNOWN).sum()) for g in after)
            print('  %s: %d unknown tiles, %d settled, %d left' % (name, b, b - a, a))
    refs_f = [h for g in draw_f for h in (g, mirror(sp, g))]
    land_all = list(land_f) + [mirror(sp, g) for g in land_f]
    return refs_f, land_all + refs_f


# --------------------------------------------------------------- taller walls

STRETCH_JUMP = 2          # how far the seam may step up or down from one column to the next
STRETCH_PASSES = 3        # a column with several fronts takes one pass per front


def vertical_pairs(model):
    """(above, below) sprite pairs the sources' blocks contain, and for each
    sprite the ones that may stand under it."""
    vp = set()
    for p in model.pats:
        vp.add((int(p[0, 0]), int(p[1, 0])))
        vp.add((int(p[0, 1]), int(p[1, 1])))
    below = {}
    for a, b in vp:
        below.setdefault(a, set()).add(b)
    return vp, below


def wall_runs(sp, col):
    """(start, end) row ranges of rock down a column, top to bottom, end exclusive."""
    runs, y, h = [], 0, len(col)
    while y < h:
        if col[y] > 0 and sp.kind[col[y]] == 1:
            y0 = y
            while y < h and col[y] > 0 and sp.kind[col[y]] == 1:
                y += 1
            runs.append((y0, y))
        else:
            y += 1
    return runs


def stretch_rows(model, sp, g, vp, below, target):
    """One seam of new sprites, one per column, that makes the island a row
    taller and puts rock into the wall run `target[c]` of every column that
    has one: seam insertion, chosen by dynamic programming over the columns
    so that every 2x2 block the new sprites make is a block of the sources.
    Valid by construction; nothing is drawn by rule. Returns (grid, grown):
    the new grid, h+1 rows, and the columns whose target run got rock -- or
    None when no seam fits at all."""
    H, W = g.shape
    INF = 10 ** 9

    def insert(c, r, t):
        col = g[:, c]
        return np.concatenate([col[:r], [t], col[r:]])

    states = []
    for c in range(W):
        col = g[:, c]
        run = target[c]
        st = []
        for r in range(1, H):
            for t in below.get(int(col[r - 1]), ()):
                if (t, int(col[r])) not in vp:
                    continue
                rock = t > 0 and sp.kind[t] == 1
                if run is None:
                    cost = 0
                else:
                    inside = run[0] < r <= run[1]      # between two rows of the run, or under its foot
                    cost = 0 if (rock and inside) else 1
                st.append((r, t, cost))
        if not st:
            return None
        states.append(st)
    best = {(r, t): cost for r, t, cost in states[0]}
    backs = [None]
    for c in range(1, W):
        cur, bk = {}, {}
        cols = {}
        for s, u, cost in states[c]:
            B = insert(c, s, u)
            for (r, t), v0 in best.items():
                if abs(r - s) > STRETCH_JUMP:
                    continue
                A = cols.get((r, t))
                if A is None:
                    A = cols[(r, t)] = insert(c - 1, r, t)
                lo, hi = max(0, min(r, s) - 1), min(H, max(r, s) + 1)
                good = True
                for i in range(lo, hi):
                    if model.bkey(int(A[i]), int(B[i]), int(A[i + 1]), int(B[i + 1])) not in model.bkeyset:
                        good = False
                        break
                if good:
                    v = v0 + cost
                    if v < cur.get((s, u), INF):
                        cur[(s, u)] = v
                        bk[(s, u)] = (r, t)
        if not cur:
            return None
        best = cur
        backs.append(bk)
    k = min(best, key=best.get)
    path = [k]
    for c in range(W - 1, 0, -1):
        k = backs[c][k]
        path.append(k)
    path.reverse()
    out = np.stack([insert(c, r, t) for c, (r, t) in enumerate(path)], axis=1)
    grown = [c for c, (r, t) in enumerate(path)
             if target[c] is not None and t > 0 and sp.kind[t] == 1]
    return out, grown


def stretch(model, sp, g, vp, below):
    """The island with every wall run lengthened by one tile where the
    sources' blocks allow it: one seam per pass, each pass aimed at the
    next run down in every column that still has one to grow. Returns
    (grid, runs grown, runs in all)."""
    todo = [list(wall_runs(sp, g[:, c])) for c in range(g.shape[1])]
    total = sum(len(t) for t in todo)
    done = 0
    for _ in range(STRETCH_PASSES):
        if not any(todo):
            break
        target = [t[0] if t else None for t in todo]
        res = stretch_rows(model, sp, g, vp, below, target)
        if res is None:
            break
        g2, grown = res
        if not grown:
            break
        g = g2
        done += len(grown)
        grown = set(grown)
        # every row at or below a seam moved down one; recount what is left to grow
        for c in range(g.shape[1]):
            runs = wall_runs(sp, g[:, c])
            left = len(todo[c]) - (1 if c in grown and todo[c] else 0)
            todo[c] = runs[len(runs) - left:] if left > 0 else []
    return g, done, total


def stretch_worker(args):
    """Stretch a share of the library in a worker: its own sources and model,
    numbered the same as the parent's because load_refs is deterministic."""
    grids, extra = args
    sp, refs = load_refs()
    landforms = load_map(sp, vocabulary(sp))
    refs, sources = sources_of(sp, refs, landforms)
    model = Model(sp, sources + [np.array(e) for e in extra])
    model.bkeyset = set(int(k) for k in model.bkeys)
    vp, below = vertical_pairs(model)
    out = []
    for g in grids:
        out.append(stretch(model, sp, np.array(g), vp, below))
    return out


def stretch_all(islands, workers, extra=()):
    """Every island a tile taller where it can be, in parallel."""
    import multiprocessing
    t0 = time.time()
    jobs = [([g.tolist() for g in islands[i::workers]], [e.tolist() for e in extra]) for i in range(workers)]
    jobs = [j for j in jobs if j[0]]
    with multiprocessing.Pool(len(jobs)) as pool:
        results = pool.map(stretch_worker, jobs)
    out = [None] * len(islands)
    for w, res in enumerate(results):
        for k, r in enumerate(res):
            out[w + k * len(jobs)] = r
    full = sum(1 for g, d, t in out if t and d == t)
    part = sum(1 for g, d, t in out if 0 < d < t)
    none = sum(1 for g, d, t in out if t and d == 0)
    print('  taller walls: %d islands fully, %d partly, %d not at all (%.0fs)'
          % (full, part, none, time.time() - t0))
    return [g for g, d, t in out]


# --------------------------------------------------------------- islands

def wall_pieces(sp, g):
    """Sizes of the 8-connected pieces of wall."""
    wm = np.array([sp.wall(s) for s in g.ravel()]).reshape(g.shape)
    lab, pieces = pieces_of(wm)
    return [len(p) for p in pieces]


def high_mask(sp, g):
    """Ground the walls close off from the border: the plateau (any level)."""
    return settle_levels(sp, g) > 0


def room(sp, g, level=None):
    """The side of the largest square of plateau the landform holds: what a
    castle or anything else with a footprint can be stood on."""
    hm = (settle_levels(sp, g) if level is None else level) > 0
    h, w = hm.shape
    d = np.zeros((h + 1, w + 1), int)
    best = 0
    for y in range(h):
        for x in range(w):
            if hm[y, x]:
                d[y + 1, x + 1] = 1 + min(d[y, x + 1], d[y + 1, x], d[y, x])
                best = max(best, d[y + 1, x + 1])
    return best


FEET = 7                  # the player's feet, in art pixels: the samples across the box of
                          # include/collision.h -- (HB_X2 - HB_X1) / 2 plus the far edge


def ink_mask(sp, g):
    """Every pixel the landform's rock and line draw, at 16 px a tile."""
    h, w = g.shape
    m = np.zeros((h * CELL, w * CELL), bool)
    for y in range(h):
        for x in range(w):
            c = g[y, x]
            if c and sp.kind[c]:
                m[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL] = ~np.all(sp.img[c] == GRASS, axis=2)
    return m


def standable(ink):
    """Pixels where the feet's box, FEET on a side, meets no ink."""
    H, W = ink.shape
    p = np.zeros((H + 1, W + 1), np.int32)
    p[1:, 1:] = np.cumsum(np.cumsum(ink, axis=0), axis=1)
    out = np.zeros((H, W), bool)
    f = FEET
    tot = p[f:, f:] - p[:-f, f:] - p[f:, :-f] + p[:-f, :-f]
    out[:H - f + 1, :W - f + 1] = tot == 0
    return out


def close_ink(m):
    """The game's closing of a cell's ink (cliff_close_cell in tilemap.cpp):
    grow a pixel with a plus, shrink it back; outside the cell empty when
    growing and full when shrinking. Applied per cell, as the game does."""
    H, W = m.shape
    out = np.zeros_like(m)
    for y0 in range(0, H, CELL):
        for x0 in range(0, W, CELL):
            c = m[y0:y0 + CELL, x0:x0 + CELL]
            g = c.copy()
            g[1:, :] |= c[:-1, :]; g[:-1, :] |= c[1:, :]; g[:, 1:] |= c[:, :-1]; g[:, :-1] |= c[:, 1:]
            e = g.copy()
            e[1:, :] &= g[:-1, :]; e[:-1, :] &= g[1:, :]; e[:, 1:] &= g[:, :-1]; e[:, :-1] &= g[:, 1:]
            out[y0:y0 + CELL, x0:x0 + CELL] = e
    return out


def top_open(sp, g, level):
    """Whether the feet can walk from the flat onto the plateau.

    Enclosed at tile level, a plateau is not always enclosed at the pixel
    level the ground is closed at: where a flank's foot meets the next lobe's
    back line inside one wall tile there can be a way through. The game
    keeps such ways as they are, so the cave pass has to know: a cave is
    there to carry the player between elevations, and a plateau with its own
    way up needs none. Asked of the closed ink, with the feet's box, from
    the flat round the landform: the feet's positions are joined four ways
    (a one-pixel diagonal line parts two regions only under that), the piece
    that reaches the border is the flat, and the plateau is open if any
    pixel under one of its boxes is plateau."""
    ink = close_ink(ink_mask(sp, g))
    stand = standable(ink)
    lab, _ = pieces_of(stand, conn=4)
    H, W = lab.shape
    outside = set(lab[0, :].tolist()) | set(lab[H - FEET, :].tolist()) | set(lab[:, 0].tolist()) | set(lab[:, W - FEET].tolist())
    outside.discard(0)
    flat = np.isin(lab, list(outside))
    cov = np.zeros((H, W), bool)
    for dy in range(FEET):
        for dx in range(FEET):
            cov[dy:, dx:] |= flat[:H - dy, :W - dx]
    region = np.kron(level == 1, np.ones((CELL, CELL), bool))
    return int((cov & region).any())


def pieces_px(mask, step=4):
    """8-connected pieces of a pixel mask, sampled every `step` pixels;
    sizes in samples."""
    sub = mask[::step, ::step]
    return [len(p) for p in pieces_of(sub)[1]]


def narrow_split(sp, g, level):
    """Whether a passage too narrow for the feet cuts a level's ground in two.

    The ink is what closes the ground, pixel for pixel, so this is asked of
    the ink: where the feet's box fits, the player can stand; the standable
    part of a level's ground must be in as many pieces as the open ground
    itself, or a gap the eye reads as a way through is one the feet cannot
    take. Pieces under a tile's worth of samples do not count."""
    h, w = g.shape
    ink = ink_mask(sp, g)
    walk = ~ink
    stand = standable(ink)
    for L in range(1, int(level.max()) + 1):
        region = np.kron(level == L, np.ones((CELL, CELL), bool))
        if not region.any():
            continue
        before = sum(1 for n in pieces_px(walk & region) if n >= 16)
        after = sum(1 for n in pieces_px(stand & region) if n >= 16)
        if after > before:
            return True
    return False


def crop(sp, g):
    """The landform with a one-tile ground margin and nothing more."""
    drawn = g != 0
    ys, xs = np.nonzero(drawn)
    return np.pad(g[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 1)


SCREE_REACH = 2           # scree and tufts this many tiles from a wall piece go with it


def split_pieces(sp, g):
    """Each 8-connected wall piece of g on its own grid, with the scree and
    tufts within SCREE_REACH tiles of it. A splice of two landforms nearly
    always carries neighbouring pieces of cliff along with the one it
    joined; kept together they made an island that was another island plus
    a stray chunk, and thrown away they cost almost every big splice. Each
    piece is a landform of its own, and is checked as one from scratch. A
    lone piece is trimmed the same way: scree carried in from far off would
    only widen its box."""
    wall = np.array([sp.wall(s) for s in g.ravel()]).reshape(g.shape)
    lab, pieces = pieces_of(wall)
    other = (g != 0) & ~wall
    out = []
    for i in range(1, len(pieces) + 1):
        near = lab == i
        mine = near.copy()
        for _ in range(SCREE_REACH):
            grown = near.copy()
            grown[1:, :] |= near[:-1, :]; grown[:-1, :] |= near[1:, :]
            grown[:, 1:] |= near[:, :-1]; grown[:, :-1] |= near[:, 1:]
            near = grown
        out.append(np.where(mine | (other & near), g, 0))
    return out


def mouth_ok(sp, g, level):
    """Whether a ground cave could open in this landform: the game's search
    (cave_place in src/tilemap.cpp), asked of the library entry. A level-1
    top tile over a south wall whose foot -- the last of up to five rows of
    rock below it -- is the same row in three adjacent columns, with rock on
    that row and the one above, and two rows of the flat in front of it with
    nothing drawn that closes. A sealed landform without one could never be
    reached: the game opens a mountain only through such a wall."""
    h, w = g.shape
    rock = np.array([s > 0 and sp.kind[s] == 1 for s in g.ravel()]).reshape(h, w)

    def foot(x, y):
        f = -1
        for d in range(5):
            if y + d >= h or not rock[y + d, x]:
                break
            f = y + d
        return f
    for y in range(h - 1):
        for x in range(1, w - 1):
            if level[y, x] != 1 or level[y + 1, x] >= 1:
                continue
            f = foot(x, y + 1)
            if f < 0 or f - 1 <= y or f + 2 >= h:
                continue
            ok = True
            for c in (-1, 0, 1):
                if foot(x + c, y + 1) != f or not rock[f - 1, x + c] or not rock[f, x + c]:
                    ok = False
                    break
                for r in (1, 2):
                    s = g[f + r, x + c]
                    if level[f + r, x + c] != 0 or (s > 0 and sp.kind[s] != 0):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return True
    return False


SAME_SHAPE = 0.85         # plateaus overlapping this much of the larger (shift and mirror) are one layout
CONTAINED = 0.7           # ... or this much of the smaller: one island and the same island with lobes added
CONTAIN_SIZE = 0.6        # ... when the smaller is at least this share of the larger


def _trim(m):
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def same_shape(a, b):
    """Whether two plateau masks are one layout: their best overlap under any
    shift, and an x-mirror, is SAME_SHAPE of the larger -- or CONTAINED of
    the smaller, which is the same island with lobes added or taken away,
    and reads as the same one walking past it. Correlated by FFT."""
    a = _trim(a)
    for bb in (_trim(b), _trim(b)[:, ::-1]):
        na, nb = int(a.sum()), int(bb.sum())
        H, W = a.shape[0] + bb.shape[0], a.shape[1] + bb.shape[1]
        fa = np.fft.rfft2(a.astype(float), (H, W))
        fb = np.fft.rfft2(bb[::-1, ::-1].astype(float), (H, W))
        best = np.fft.irfft2(fa * fb, (H, W)).max() + 0.5
        if best >= SAME_SHAPE * max(na, nb):
            return True
        # containment only between islands of a size: any small blob fits
        # inside a big plateau somewhere, and that is not the same island
        if min(na, nb) >= CONTAIN_SIZE * max(na, nb) and best >= CONTAINED * min(na, nb):
            return True
    return False


SMALL_MIN = 8             # plateau tiles: anything less is a scrap, not an island
MIN_TOP_SHARE = 0.25      # plateau tiles per wall tile: the drawings hold 0.33 to 0.75; a tangle of
                          # back lines round a scrap of top (0.05 in the one that failed) is no island
MAX_UNBACKED = 0.12       # wall tops with no plateau behind them, per wall tile: the drawings hold
                          # 6-8%; the free-standing face the user flagged sat in an island at 21%

# The layouts of the last bake, numbered as its contact sheet numbers them,
# and the layouts the user has turned down. A layout is turned down by its
# number on the sheet (--reject 3,17); its plateau goes into REJECTED, and no
# later bake keeps that shape again. Whether a layout reads well is the
# user's eye: the faults found so far (a full-height wall stopping dead
# against the grass) are built of sprites and seams the drawings use too,
# so no rule here could tell them apart.
LAYOUTS = os.path.join(ROOT, 'art', 'cliffs', 'islands_layouts.npz')     # the last sheet's layouts, as grids
KEPT = os.path.join(ROOT, 'art', 'cliffs', 'islands_kept.npz')           # layouts the user approved (--keep)
REJECTED = os.path.join(ROOT, 'art', 'cliffs', 'islands_rejected.npz')


def load_arrays(path):
    if not os.path.exists(path):
        return []
    z = np.load(path)
    return [z['m%d' % i] for i in range(len(z.files))]


def save_arrays(path, masks):
    np.savez_compressed(path, **{'m%d' % i: m for i, m in enumerate(masks)})


def vet(model, sp, g):
    """A candidate landform as the library would keep it, or None: inside
    the stamp size, every 2x2 block a source block, one wall piece, a
    plateau, no passage too narrow for the feet."""
    if g.shape[1] > STAMP_MAX_W or g.shape[0] > STAMP_MAX_H or (g == UNKNOWN).any():
        return None
    try:
        model.check(g)
    except AssertionError:
        return None
    if len(wall_pieces(sp, g)) != 1:
        return None
    level = settle_levels(sp, g)
    high = int((level > 0).sum())
    if high < SMALL_MIN or narrow_split(sp, g, level):
        return None
    walls = sum(1 for s in g.ravel() if sp.wall(s))
    if high < MIN_TOP_SHARE * walls:
        return None
    if unbacked(sp, g, level) > MAX_UNBACKED * walls:
        return None
    return g


def corner_cuts(sp, g):
    """The wall tiles whose top corner is cut off square, as (x, y): plain
    ground in all three tiles above, and rock running into a side edge
    (edge_rock) with plain ground beyond. Each half is common in the
    drawings -- a bare top with the wall running on beside it, or a cut side
    under the back line that caps it -- but together they never occur there:
    the rock stops dead in the grass, top and side. The user flagged one."""
    h, w = g.shape
    out = []
    for y in range(1, h):
        for x in range(1, w - 1):
            s = g[y, x]
            if not sp.wall(s) or (g[y - 1, x - 1:x + 2] != 0).any():
                continue
            if (g[y, x - 1] == 0 and edge_rock(sp, s, 2) >= RUNS_INTO) or                (g[y, x + 1] == 0 and edge_rock(sp, s, 3) >= RUNS_INTO):
                out.append((x, y))
    return out


CUT_UP, CUT_DOWN, CUT_SIDE = 3, 6, 4   # the window refilled round a cut corner
CUT_TRIES = 20


def repair_corners(model, sp, g, rng):
    """g with every square-cut corner (corner_cuts) rebuilt from the blocks,
    or None if one cannot be. The window round the corner is collapsed
    afresh, and of the fills that leave no cut, one wall piece and nothing
    new above the corner's row -- so the wall is cut shorter and the back
    line comes in at that row to cap it, rather than the plateau growing up
    over it (the user chose this) -- the one changing fewest tiles is kept."""
    g = np.pad(g, max(CUT_UP, CUT_SIDE))  # room for a full window at the edge
    while True:
        cuts = corner_cuts(sp, g)
        if not cuts:
            return crop(sp, g)
        x, y = cuts[0]
        best = None
        for _ in range(CUT_TRIES):
            r = model.refill(g, y - CUT_UP, min(g.shape[0], y + CUT_DOWN),
                             x - CUT_SIDE, min(g.shape[1], x + CUT_SIDE + 1), rng, (x, y))
            if r is None or (r[:y] != g[:y]).any() or len(corner_cuts(sp, r)) >= len(cuts)                or (x, y) in corner_cuts(sp, r) or len(wall_pieces(sp, r)) != 1:
                continue
            n = int((r != g).sum())
            if best is None or n < best[0]:
                best = (n, r)
        if best is None:
            return None
        g = best[1]


def unbacked(sp, g, level):
    """Wall columns whose top rock tile has no raised ground within two tiles
    above it: a face with nothing behind it, stopping dead in the grass where
    the drawings run the plateau's back line in to cap it."""
    h, w = g.shape
    rock = np.array([s > 0 and sp.kind[s] == 1 for s in g.ravel()]).reshape(h, w)
    n = 0
    for y in range(h):
        for x in range(w):
            if not rock[y, x] or (y > 0 and rock[y - 1, x]):
                continue
            ys = slice(max(0, y - 3), y)
            xs = slice(max(0, x - 1), x + 2)
            if not (level[ys, xs] > 0).any():
                n += 1
    return n


def grow_one(model, sp, rng):
    """One try at an island; None on a miss."""
    w = rng.randint(BOX_W[0], BOX_W[1] + 1)
    h = rng.randint(BOX_H[0], BOX_H[1] + 1)
    # a wall on every side of the box: column 1, column w-2, row 1 and
    # row h-4 (the band hangs two rows under the rim, and the box must
    # hold them)
    anchors = [(rng.randint(2, h - 4), 1), (rng.randint(2, h - 4), w - 2),
               (1, rng.randint(2, w - 2)), (h - 4, rng.randint(2, w - 2))]
    g = model.run(w, h, rng, anchors)
    return vet(model, sp, crop(sp, g)) if g is not None else None


def grow_worker(args):
    """Grow `count` islands from one seed, from the drawings' blocks. Its
    own sprites and model: the numbering is deterministic, so every
    worker's cells mean the same."""
    seed, count, budget = args
    sp, refs = load_refs()
    refs, _ = sources_of(sp, refs, [])
    model = Model(sp, refs)
    rng = np.random.RandomState(seed)
    out, seen, misses = [], set(), 0
    t0 = time.time()
    # `budget` seconds and no more: the collapse misses often, and a
    # worker must not hold the bake for an hour over the last island
    while len(out) < count and time.time() - t0 < budget:
        g = grow_one(model, sp, rng)
        if g is None:
            misses += 1
            continue
        k = g.tobytes() + bytes(g.shape)
        if k in seen:
            misses += 1
            continue
        seen.add(k)
        out.append(g)
    return out, misses


def grow(count, seed, workers, budget=GROW_BUDGET):
    """`count` islands grown in parallel, no two alike, `budget` seconds a worker."""
    import multiprocessing
    jobs = []
    per = max(1, (count + workers - 1) // workers)
    for i in range(workers):
        n = min(per, count - i * per)
        if n > 0:
            jobs.append((seed * 1000 + i, n, budget))
    t0 = time.time()
    with multiprocessing.Pool(min(workers, len(jobs))) as pool:
        results = pool.map(grow_worker, jobs)
    out, seen, misses = [], set(), 0
    for islands, m in results:
        misses += m
        for g in islands:
            k = g.tobytes() + bytes(g.shape)
            if k in seen:
                continue
            seen.add(k)
            out.append(g)
    print('  grown %d islands, %d misses, %.0fs on %d workers' % (len(out), misses, time.time() - t0, len(jobs)))
    return out


# --------------------------------------------------------------- splices

def seam_offsets(model, colA, colB, ds):
    """Which of the offsets `ds` put A's last kept column beside B's first
    kept column with only reference blocks along the seam (B shifted down
    by the offset). All offsets are tested in one lookup."""
    ds = np.asarray(ds)
    y0 = int(ds.min()) - 1 if ds.min() < 0 else -1
    y1 = max(len(colA), len(colB) + int(ds.max()))
    ys = np.arange(y0, y1)

    def at(col, y):
        v = np.zeros(y.shape, np.int64)
        m = (y >= 0) & (y < len(col))
        v[m] = col[y[m]]
        return v
    Y = ys[None, :]
    D = ds[:, None]
    a = at(colA, np.broadcast_to(Y, (len(ds), len(ys))))
    c = at(colA, np.broadcast_to(Y + 1, (len(ds), len(ys))))
    b = at(colB, Y - D)
    e = at(colB, Y + 1 - D)
    keys = model.bkey(a, b, c, e)
    ok = np.isin(keys, model.bkeys).all(axis=1)
    return [int(d) for d, o in zip(ds, ok) if o]


def vsplice(A, xa, B, xb, d):
    """Columns [0, xa) of A beside columns [xb, ..) of B, B shifted down by d."""
    y0 = min(0, d)
    y1 = max(A.shape[0], B.shape[0] + d)
    out = np.zeros((y1 - y0, xa + (B.shape[1] - xb)), int)
    out[-y0:-y0 + A.shape[0], :xa] = A[:, :xa]
    out[d - y0:d - y0 + B.shape[0], xa:] = B[:, xb:]
    return out


SEAM_REACH = 20           # how far B may be shifted along the seam, either way
SEAM_STEP = 1             # cuts are tried this many tiles apart
SPLICE_CUTS = 48          # seams tried per pair of sources (shuffled); each splice yields several pieces
SPLICE_ROUNDS = 3         # the first round pairs the sources; later ones splice the last round's pieces


def seams(model, sp, A, B):
    """Every valid vertical seam between A and B: (xa, xb, d)."""
    out = []
    ds = np.arange(-SEAM_REACH, SEAM_REACH + 1, 2)
    wallA = [any(sp.wall(s) for s in A[:, x]) for x in range(A.shape[1])]
    for xa in range(4, A.shape[1] - 3, SEAM_STEP):
        if not wallA[xa - 1]:
            continue                       # a cut through open ground joins nothing
        colA = A[:, xa - 1]
        for xb in range(4, B.shape[1] - 3, SEAM_STEP):
            for d in seam_offsets(model, colA, B[:, xb], ds):
                out.append((xa, xb, d))
    return out


def splice_at(model, sp, A, B, ca, cb, d, transposed):
    """The landforms the splice makes, each checked: the splice's own blocks
    first, then every wall piece of it on its own (split_pieces, vet)."""
    g = vsplice(A.T, ca, B.T, cb, d).T if transposed else vsplice(A, ca, B, cb, d)
    if not (g != 0).any():
        return []
    try:
        model.check(np.pad(g, 1))
    except AssertionError:
        return []
    out = []
    for piece in split_pieces(sp, g):
        if not (piece != 0).any():
            continue
        p = vet(model, sp, crop(sp, piece))
        if p is not None:
            out.append(p)
    return out


def splice_worker(args):
    """Every splice of the A's this worker was given with every B: both
    axes, every cut, every offset within reach. Sources are rebuilt here:
    the numbering is deterministic, so every worker's cells mean the same."""
    a_idx, extra_idx, seed, cap, b_sample = args
    sp, refs = load_refs()
    landforms = load_map(sp, vocabulary(sp))
    refs, sources = sources_of(sp, refs, landforms)
    model = Model(sp, sources)
    pool = list(sources) + [np.array(e) for e in extra_idx]
    rng = np.random.RandomState(seed)
    out, seen = [], set()
    for ia in a_idx:
        A = pool[ia]
        others = [ib for ib in range(len(pool)) if ib != ia]
        if b_sample and len(others) > b_sample:
            others = [others[i] for i in rng.choice(len(others), b_sample, replace=False)]
        for ib in others:
            B = pool[ib]
            for transposed in (False, True):
                At, Bt = (A.T, B.T) if transposed else (A, B)
                if At.shape[1] < 10 or Bt.shape[1] < 10:
                    continue
                found = seams(model, sp, At, Bt)
                rng.shuffle(found)
                for ca, cb, d in found[:cap]:
                    for g in splice_at(model, sp, A, B, ca, cb, d, transposed):
                        k = g.tobytes() + bytes(g.shape)
                        if k in seen:
                            continue
                        seen.add(k)
                        out.append(g)
    return out


def splice_pool(sp, sources, want, seed, workers):
    """Big landforms spliced from the sources in parallel: every source
    with every other at every exact seam, then SPLICE_ROUNDS - 1 more
    rounds in which each piece the last round made is spliced with a sample
    of the sources. Once splices were kept whole that cost hours for little
    new shape; split into their pieces (splice_at), the pieces are small and
    every round adds layouts no source pair gives."""
    import multiprocessing
    t0 = time.time()
    out, seen = [], set()
    n = len(sources)
    last = 0
    for round_ in range(SPLICE_ROUNDS):
        if round_ == 0:
            a_idx = list(range(n))
            extra = []
            b_sample = 0                  # every source against every other
        else:
            extra = [g.tolist() for g in out[last:][:300]]
            a_idx = list(range(n, n + len(extra)))
            b_sample = 24                 # each new landform against a sample of the rest
        jobs = [(a_idx[i::workers], extra, seed * 1000 + round_ * 100 + i, SPLICE_CUTS, b_sample) for i in range(workers) if a_idx[i::workers]]
        with multiprocessing.Pool(len(jobs)) as pool:
            results = pool.map(splice_worker, jobs)
        made = 0
        for islands in results:
            for g in islands:
                k = g.tobytes() + bytes(g.shape)
                if k in seen:
                    continue
                seen.add(k)
                out.append(g)
                made += 1
        print('  splice round %d: %d new landforms (%d so far), %.0fs' % (round_ + 1, made, len(out), time.time() - t0))
        sys.stdout.flush()
        last = len(out) - made          # the next round splices what this one made
        if (want and len(out) >= want) or made == 0:
            break
    rng = np.random.RandomState(seed)
    rng.shuffle(out)
    return out[:want] if want else out


CARVE_BAND = 3                  # tiles inside a carved window's edge collapsed afresh to close it
CARVE_W, CARVE_H = (10, 20), (9, 16)
CARVE_TRIES = 3                 # collapses of the band before a window is given up


def carve(model, sp, g, rng):
    """A smaller landform cut out of g, or None: a window round one of its
    plateau tiles, everything outside it ground, and the band just inside its
    edge collapsed afresh from the blocks so the walls the window cuts end
    as the drawings end them. What lies deeper in keeps g's own tiles, so a
    lobe of a big layout becomes a small one of the same hand. Vetted."""
    ys, xs = np.nonzero(settle_levels(sp, g) > 0)
    if not len(ys):
        return None
    i = rng.randint(len(ys))
    w, h = rng.randint(*CARVE_W), rng.randint(*CARVE_H)
    pad = max(w, h)
    gp = np.pad(g, pad)
    y0, x0 = ys[i] + pad - h // 2, xs[i] + pad - w // 2
    win = np.zeros((h, w), int)
    win[1:-1, 1:-1] = gp[y0 + 1:y0 + h - 1, x0 + 1:x0 + w - 1]
    free = np.zeros((h, w), bool)
    free[1:-1, 1:-1] = True
    free[1 + CARVE_BAND:-1 - CARVE_BAND, 1 + CARVE_BAND:-1 - CARVE_BAND] = False
    for _ in range(CARVE_TRIES):
        r = model.refill(win, 0, h, 0, w, rng, free=free)
        if r is not None:
            break
    if r is None or not (r != 0).any():
        return None
    pieces = split_pieces(sp, r)          # its own scree only, as a splice's piece
    return vet(model, sp, crop(sp, pieces[0])) if len(pieces) == 1 else None


def carve_worker(args):
    """`tries` carves from this worker's share of the landforms."""
    grids, tries, seed = args
    sp, refs = load_refs()
    landforms = load_map(sp, vocabulary(sp))
    refs, sources = sources_of(sp, refs, landforms)
    model = Model(sp, sources)
    rng = np.random.RandomState(seed)
    out = []
    for _ in range(tries):
        g = carve(model, sp, np.array(grids[rng.randint(len(grids))]), rng)
        if g is not None:
            out.append(g)
    return out


def carve_pool(cands, tries, seed, workers):
    """Small and medium landforms carved out of the big candidates (carve),
    `tries` carves in all, in parallel."""
    import multiprocessing
    t0 = time.time()
    rng = np.random.RandomState(seed)
    big = [cands[i] for i in rng.permutation(len(cands))[:400]]
    jobs = [([g.tolist() for g in big[i::workers]], tries // workers, seed * 1000 + 900 + i) for i in range(workers)]
    with multiprocessing.Pool(workers) as pool:
        results = pool.map(carve_worker, jobs)
    out, seen = [], set()
    for islands in results:
        for g in islands:
            k = g.tobytes() + bytes(g.shape)
            if k not in seen:
                seen.add(k)
                out.append(g)
    print('  carved %d landforms from %d tries, %.0fs' % (len(out), tries, time.time() - t0))
    sys.stdout.flush()
    return out


def plateau_class(n):
    """0 large, 1 medium, 2 small: the classes the placement draws from."""
    return 0 if n >= LARGE_HIGH else 1 if n >= MEDIUM_HIGH else 2


def choose(model, sp, cands, own, targets, seed, workers):
    """The library's distinct layouts: targets[k] of each class, no two the
    same shape (same_shape, with mirrors), the user's drawings first. Picked
    with spares, made taller (stretch_all), then checked as the game will
    use them: still clear for the feet, and a sealed one must take a cave
    (mouth_ok). Returns (grid, level, open) per class."""
    rng = np.random.RandomState(seed)
    rest = [cands[i] for i in rng.permutation(len(cands))]
    rejected = load_arrays(REJECTED)
    picked, masks = [[], [], []], [[], [], []]
    for i, g in enumerate(own + rest):
        m = settle_levels(sp, g) > 0
        k = plateau_class(int(m.sum()))
        if i >= len(own) and len(picked[k]) >= 2 * targets[k]:
            continue
        if any(same_shape(m, pm) for pm in masks[k]):
            continue
        if i >= len(own) and any(same_shape(m, r) for r in rejected):
            continue
        picked[k].append((i < len(own), g))
        masks[k].append(m)
    flat = [x for k in range(3) for x in picked[k]]
    print('  %d / %d / %d distinct layouts found (large / medium / small), stretching them'
          % tuple(len(p) for p in picked))
    sys.stdout.flush()
    tall = stretch_all([g for _, g in flat], workers)
    final, fmasks, dropped = [[], [], []], [[], [], []], Counter()
    for (mine, _), g in zip(flat, tall):
        level = settle_levels(sp, g)
        m = level > 0
        k = plateau_class(int(m.sum()))
        if not mine:
            if len(final[k]) >= targets[k]:
                continue
            if narrow_split(sp, g, level):
                dropped['narrow once taller'] += 1
                continue
        fixed = len(corner_cuts(sp, g))
        if fixed:
            g = repair_corners(model, sp, g, rng)
            if g is None:
                dropped['corner cut, no repair'] += 1
                continue
            dropped['kept, square-cut corners rebuilt'] += 1
            level = settle_levels(sp, g)
            m = level > 0
            k = plateau_class(int(m.sum()))
            if narrow_split(sp, g, level):
                dropped['narrow once repaired'] += 1
                continue
        op = top_open(sp, g, level)
        if not mine and not op and not mouth_ok(sp, g, level):
            dropped['sealed, no wall for a cave'] += 1
            continue
        if any(same_shape(m, pm) for pm in fmasks[k]):
            dropped['same shape once taller'] += 1
            continue
        model.check(g)
        final[k].append((g, level, op, fixed))
        fmasks[k].append(m)
    if dropped:
        print('  after stretching: ' + ', '.join('%d %s' % (c, r) for r, c in dropped.items()))
    for k, name in enumerate(('large', 'medium', 'small')):
        if len(final[k]) < targets[k]:
            print('  only %d distinct %s layouts (wanted %d)' % (len(final[k]), name, targets[k]))
    return final


def write_contact_labelled(sp, uniques, path):
    """The distinct layouts, one each, labelled: class, size, plateau, and
    whether the feet walk up (open, a ramp) or a cave carries them (sealed)."""
    from PIL import ImageDraw
    ims = [paint(sp, g) for g, _, _, _ in uniques]
    cols = 5
    cw = max(im.shape[1] for im in ims) + CELL
    rows = (len(ims) + cols - 1) // cols
    rh = [max(im.shape[0] for im in ims[r * cols:(r + 1) * cols]) + 28 for r in range(rows)]
    sheet = Image.new('RGB', (cols * cw, sum(rh)), (60, 60, 60))
    dr = ImageDraw.Draw(sheet)
    y = 0
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            if i >= len(ims):
                break
            g, level, op, fixed = uniques[i]
            n = int((level > 0).sum())
            dr.text((c * cw + 4, y + 6), '%d %s %dx%d plateau %d %s%s' % (
                i + 1, ('large', 'medium', 'small')[plateau_class(n)], g.shape[1], g.shape[0], n,
                'open' if op else 'sealed+cave', ', %d corner fixed' % fixed if fixed else ''),
                fill=(255, 220, 0) if fixed else (255, 255, 255))
            sheet.paste(Image.fromarray(ims[i]), (c * cw, y + 24))
        y += rh[r]
    sheet.save(path)


# ---------------------------------------------------------------- output

def paint(sp, g):
    h, w = g.shape
    im = np.zeros((h * CELL, w * CELL, 3), np.uint8)
    for y in range(h):
        for x in range(w):
            im[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL] = (255, 0, 255) if g[y, x] == UNKNOWN else sp.img[g[y, x]]
    return im


def write_sheet(sp, path):
    sheet = np.array(Image.open(path).convert('RGB'))
    need = ROWS_END * CELL
    if sheet.shape[0] < need:
        raise SystemExit('sheet is only %d px tall, need %d' % (sheet.shape[0], need))
    sheet[ISLAND_ROW0 * CELL:ROWS_END * CELL, :SHEET_COLS * CELL] = KEY
    if len(sp.img) > (ROWS_END - ISLAND_ROW0) * SHEET_COLS:
        raise SystemExit('%d sprites do not fit the region' % len(sp.img))
    for i, im in enumerate(sp.img):
        if i == 0:
            continue                      # ground: the key, nothing drawn
        row, col = ISLAND_ROW0 + i // SHEET_COLS, i % SHEET_COLS
        cell = im.copy()
        cell[np.all(cell == GRASS, axis=2)] = KEY
        sheet[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL] = cell
    Image.fromarray(sheet).save(path)


def write_inc(sp, islands, levels, opens, layouts, path):
    """islands, levels and opens sorted largest plateau first; layouts[i] is
    the layout entry i draws, shared by a layout and its mirror."""
    sizes = [int((lv > 0).sum()) for lv in levels]
    assert all(plateau_class(a) <= plateau_class(b) for a, b in zip(sizes, sizes[1:])), 'library not sorted by class'
    large0 = next((i for i, s in enumerate(sizes) if s < LARGE_HIGH), len(sizes))
    medium0 = next((i for i, s in enumerate(sizes) if s < MEDIUM_HIGH), len(sizes))
    lines = ['// Generated by tools/gen_islands.py from art/reference/eb0map_big.png and art/cliffs/islands/.',
             '// Do not edit; rerun the tool.',
             '//',
             '// The sprites of Mother 1\'s cliffs, and a library of landforms: big ones',
             '// spliced from the map\'s landforms, small ones grown from the drawings\' 2x2',
             '// blocks. A cell is a sprite\'s number; cell 0 is the plain ground and draws',
             '// nothing. The sheet holds sprite i at row ISLAND_ROW0 + i / 256, column i % 256.',
             'static const int ISLAND_ROW0    = %d;' % ISLAND_ROW0,
             'static const int ISLAND_SPRITES = %d;' % len(sp.img),
             '// 0 ground (also scree and tufts), 1 rock, 2 line: what the sprite closes with.',
             'static const unsigned char ISLAND_KIND[ISLAND_SPRITES] = { %s };' % ', '.join(str(k) for k in sp.kind),
             '// level: 0 the flat, 1 the plateau, 2 and 3 storeys on it. high_tiles counts',
             '// the tiles above the flat; room is the side of the largest open square of them.',
             '// open: 1 when the feet can walk up onto the plateau from the flat, through a',
             '// gap in the walls at pixel level, so a cave is not needed to reach it.',
             'struct Island { int w, h, high_tiles, room, open; const unsigned short* cells; const unsigned char* level; };']
    for i, (g, lv) in enumerate(zip(islands, levels)):
        assert (g >= 0).all(), 'landform %d has a tile the sources do not show' % i
        lines.append('static const unsigned short ISLAND_%d_CELLS[%d] = { %s };'
                     % (i, g.size, ', '.join(str(int(v)) for v in g.ravel())))
        lines.append('static const unsigned char ISLAND_%d_LEVEL[%d] = { %s };'
                     % (i, g.size, ', '.join(str(int(v)) for v in lv.ravel())))
    lines.append('static const int ISLAND_COUNT = %d;' % len(islands))
    lines.append('// The library is sorted by plateau size, largest first: [0, ISLAND_LARGE0) are')
    lines.append('// the large landforms, [ISLAND_LARGE0, ISLAND_MEDIUM0) the medium, the rest small.')
    lines.append('static const int ISLAND_LARGE0  = %d;' % large0)
    lines.append('static const int ISLAND_MEDIUM0 = %d;' % medium0)
    lines.append('// Which layout each entry draws: a layout and its mirror share one, so the')
    lines.append('// placement can keep the same island, either way round, from standing close.')
    lines.append('static const unsigned char ISLAND_LAYOUT[ISLAND_COUNT] = { %s };' % ', '.join(str(v) for v in layouts))
    lines.append('static const Island ISLANDS[ISLAND_COUNT] = {')
    for i, (g, lv) in enumerate(zip(islands, levels)):
        lines.append('    { %d, %d, %d, %d, %d, ISLAND_%d_CELLS, ISLAND_%d_LEVEL },'
                     % (g.shape[1], g.shape[0], sizes[i], room(sp, g, lv), opens[i], i, i))
    lines.append('};')
    with open(path, 'w', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    return large0, medium0


def write_contact(sp, islands, path, cols=8, scale=2):
    ims = [paint(sp, g) for g in islands]
    cw = max(im.shape[1] for im in ims) + CELL
    ch = max(im.shape[0] for im in ims) + CELL
    rows = (len(ims) + cols - 1) // cols
    sheet = np.full((rows * ch, cols * cw, 3), (60, 60, 60), np.uint8)
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        sheet[r * ch:r * ch + im.shape[0], c * cw:c * cw + im.shape[1]] = im
    Image.fromarray(sheet).resize((sheet.shape[1] * scale, sheet.shape[0] * scale), Image.NEAREST).save(path)


def diff_refs(sp, name, grid, wiped):
    """The drawing painted back from its sprites must be the drawing, apart
    from the tiles that were wiped."""
    a = np.array(Image.open(os.path.join(ISLAND_DIR, name + '.png')).convert('RGB'))
    back = paint(sp, grid)[CELL:-CELL, CELL:-CELL]
    bad = 0
    for ty in range(a.shape[0] // CELL):
        for tx in range(a.shape[1] // CELL):
            if wiped[ty + 1, tx + 1]:
                continue
            if not np.array_equal(a[ty * CELL:(ty + 1) * CELL, tx * CELL:(tx + 1) * CELL],
                                  back[ty * CELL:(ty + 1) * CELL, tx * CELL:(tx + 1) * CELL]):
                bad += 1
    return bad


def load_refs():
    """The drawings and their mirrors, numbered first so that every worker
    numbers the sprites the same."""
    sp = Sprites()
    refs = []
    for name in REFS:
        g, wiped = load_island(sp, name)
        bad = diff_refs(sp, name, g, wiped)
        if bad:
            raise SystemExit('%s does not paint back from its sprites: %d tiles differ' % (name, bad))
        refs.append(g)
        refs.append(mirror(sp, g))
    return sp, refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=0, help='islands grown from the drawings (slow, yields little)')
    ap.add_argument('--grow-secs', type=int, default=GROW_BUDGET, help='seconds each worker may spend growing')
    ap.add_argument('--big', type=int, default=0, help='cap on spliced candidates; 0 keeps them all')
    ap.add_argument('--distinct', default='15,20,15', help='distinct layouts wanted: large,medium,small')
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--sheet', default=OUT_SHEET)
    ap.add_argument('--contact', default=None, help='where the labelled sheet of distinct layouts goes')
    ap.add_argument('--reject', default='', help='turn down layouts by their number on the last contact sheet, e.g. 3,17')
    ap.add_argument('--keep', action='store_true', help='approve the last contact sheet: its layouts stay in every later bake as they are')
    ap.add_argument('--carve', type=int, default=0, help='carves of smaller landforms out of the spliced ones')
    ap.add_argument('--cache', default=None, help='npz the spliced candidates are kept in between runs')
    ap.add_argument('--no-write', action='store_true')
    a = ap.parse_args()
    targets = [int(v) for v in a.distinct.split(',')]
    t0 = time.time()

    sp, refs = load_refs()
    if a.reject:
        last = load_arrays(LAYOUTS)
        turned = [settle_levels(sp, last[int(v) - 1]) > 0 for v in a.reject.split(',')]
        save_arrays(REJECTED, load_arrays(REJECTED) + turned)
        print('turned down %d layout%s (%d in all)' % (len(turned), '' if len(turned) == 1 else 's', len(load_arrays(REJECTED))))
    if a.keep:
        save_arrays(KEPT, load_arrays(KEPT) + load_arrays(LAYOUTS))
        print('kept the last sheet: %d approved layouts in all' % len(load_arrays(KEPT)))
    vocab = vocabulary(sp)
    landforms = load_map(sp, vocab)
    print('%d drawings (with mirrors), %d map landforms, %d sprites, %.0fs' % (len(refs), len(landforms), len(sp.img), time.time() - t0))
    refs, sources = sources_of(sp, refs, landforms, log=True)
    model = Model(sp, sources)
    print('%d blocks, %.0fs' % (model.P, time.time() - t0))
    sys.stdout.flush()

    if a.cache and os.path.exists(a.cache):
        big = load_arrays(a.cache)
        print('  %d spliced candidates from %s' % (len(big), a.cache))
    else:
        big = splice_pool(sp, sources, a.big, a.seed, a.workers)
        if a.cache:
            save_arrays(a.cache, big)
    small = grow(a.count, a.seed, a.workers, a.grow_secs) if a.count else []
    small += carve_pool(big, a.carve, a.seed, a.workers) if a.carve else []
    print('  %d candidate landforms (splices split into their pieces, each checked)' % (len(big) + len(small)))
    # the user's own drawings stand as they are; the map's landforms do not.
    # A drawing with a tile still unknown cannot: nothing can be drawn there.
    # Mirrors are added to every layout at the end, so only one of each pair.
    # Approved layouts (--keep) stand as they are too, after the drawings.
    own = [crop(sp, g) for g in refs[::2] if not (g == UNKNOWN).any()] + load_arrays(KEPT)
    for k, g in enumerate(refs[::2]):
        ys, xs = np.nonzero(g == UNKNOWN)
        if len(xs):
            # refs are settled drawings: 2 rings of pad round the loader's 1-tile margin
            print('  %s left out: tile%s %s could not be settled (drawing tiles, x,y)'
                  % (REFS[k], 's' if len(xs) > 1 else '', ', '.join('%d,%d' % (x - 3, y - 3) for x, y in zip(xs.tolist(), ys.tolist()))))
    final = choose(model, sp, big + small, own, targets, a.seed, a.workers)
    uniques = [x for k in range(3) for x in final[k]]
    uniques.sort(key=lambda x: -int((x[1] > 0).sum()))
    contact = a.contact or OUT_PNG
    write_contact_labelled(sp, uniques, contact)
    save_arrays(LAYOUTS, [g for g, _, _, _ in uniques])
    print('%d distinct layouts (%d large, %d medium, %d small) -> %s'
          % (len(uniques), len(final[0]), len(final[1]), len(final[2]), contact))
    # every layout and its mirror: the mirror is a free second entry, not a layout
    islands, levels, opens = [], [], []
    for g, level, op, _ in uniques:
        mg = mirror(sp, g)
        mlevel = settle_levels(sp, mg)
        model.check(mg)
        islands += [g, mg]
        levels += [level, mlevel]
        opens += [op, top_open(sp, mg, mlevel)]
    if a.no_write:
        return
    write_sheet(sp, a.sheet)
    # uniques are sorted largest first and a mirror has its layout's plateau, so the
    # pairs keep the order write_inc wants; entry i draws layout i // 2
    large0, medium0 = write_inc(sp, islands, levels, opens, [i // 2 for i in range(len(islands))], OUT_INC)
    if a.contact:
        write_contact_labelled(sp, uniques, OUT_PNG)
    sizes = [int((lv > 0).sum()) for lv in levels]
    storeys = sum(1 for lv in levels if lv.max() >= 2)
    print('wrote %d landforms: %d large, %d medium, %d small; plateaus %d to %d tiles, %d with a storey drawn in -> %s, %s, %s (%.0fs)'
          % (len(islands), large0, medium0 - large0, len(islands) - medium0, min(sizes), max(sizes), storeys,
             os.path.relpath(a.sheet, ROOT), os.path.relpath(OUT_INC, ROOT), os.path.relpath(OUT_PNG, ROOT), time.time() - t0))
    print('  open to the feet from the flat: %d of %d large, %d of %d medium, %d of %d small'
          % (sum(opens[:large0]), large0, sum(opens[large0:medium0]), medium0 - large0, sum(opens[medium0:]), len(islands) - medium0))
    print('now run: python tools/palette_pass.py --write')


if __name__ == '__main__':
    main()
