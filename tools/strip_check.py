"""Check the cave run-end outline (31:0) only ever lands on bare rock.

The strip is a solid half-tile bar drawn into the cell NEXT to a tall face, so
the one thing that can go wrong invisibly is which cells it covers. This mirrors
cave_wall_classify()'s band_edge rules in Python, from a DNGSHOT_DUMP map, and
predicts the exact screen rect of every strip cell -- the same "know the answer
before you look at the render" approach the rest of this directory uses.

It carries BOTH rules on purpose:

  old   whatever the previous build drew, so a before/after diff has something
        to predict against.
  new   the current rule: no floor in the cell's four CARDINAL neighbours (so
        no band and no trim), and no face at y+1/y+2 bleeding up onto it.
        Diagonals are deliberately not checked -- crossing a corner nub is
        allowed.

Keeping the old one lets `diff` assert the thing that made replacing it safe:
the new rule removes a superset of what the old one removed and adds nothing, so
the render can only ever LOSE pixels. A changed pixel outside a predicted drop
rect is then a real bug rather than something to squint at.

The map needs margin -- classify reaches three tiles up and two down past the
camera window, so dump a window larger than the one rendered and pass its origin.

Usage:
  python tools/strip_check.py predict <map.txt> <map_ox> <map_oy> <cam_tx> <cam_ty> <tw> <th>
  python tools/strip_check.py diff    <map.txt> <map_ox> <map_oy> <cam_tx> <cam_ty> <tw> <th> <before.png> <after.png>
"""
import sys

TILE = 32
HALF = TILE // 2


def load(path):
    with open(path) as f:
        return [ln.rstrip('\n') for ln in f if ln.strip()]


class Map:
    """Floor lookup over the dumped window. Anything outside the dump is
    unknown, not off-map -- raise rather than quietly answering 'wall', which is
    what cave_floor_at() returns for a real out-of-bounds read and would hide a
    predictor reaching further than the margin allows."""

    def __init__(self, rows, ox, oy):
        self.rows, self.ox, self.oy = rows, ox, oy
        self.h, self.w = len(rows), len(rows[0])

    def floor(self, x, y):
        lx, ly = x - self.ox, y - self.oy
        if not (0 <= lx < self.w and 0 <= ly < self.h):
            raise IndexError(f"tile ({x},{y}) outside dumped window -- dump more margin")
        return self.rows[ly][lx] == '.'


def draws_band(m, x, y):
    """cave_draws_band(): this wall tile draws a band piece of its own, either
    the 3-cell face or the standalone node."""
    if m.floor(x, y):
        return False
    fs, fn = m.floor(x, y + 1), m.floor(x, y - 1)
    fe, fw = m.floor(x + 1, y), m.floor(x - 1, y)
    return fs or (fs + fn + fe + fw) >= 3


def is_tall_face(m, x, y):
    return not m.floor(x, y) and m.floor(x, y + 1) and not m.floor(x, y - 1)


def lands_on_bare_rock(m, x, y):
    """The band-round rule, superseded by lands_on_blank(). Kept so `diff` can
    still show what the previous build drew."""
    if m.floor(x, y):
        return False
    if draws_band(m, x, y):
        return False
    return not is_tall_face(m, x, y + 1) and not is_tall_face(m, x, y + 2)


def lands_on_blank(m, x, y):
    """cave_strip_lands_on_bare_rock(): the cell draws no band and no trim.

    Sorting cave_wall_classify()'s pieces by trigger splits them cleanly: band
    and the four cardinal trims need floor in a CARDINAL neighbour, the four nubs
    need floor on a DIAGONAL. So the cardinal scan is exactly "no band, no trim",
    and the diagonals are left out on purpose -- the strip is allowed to cross an
    8x8 corner bead. Then the only thing left is a face at y+1/y+2 bleeding up."""
    if m.floor(x, y):
        return False
    if (m.floor(x, y + 1) or m.floor(x, y - 1)
            or m.floor(x + 1, y) or m.floor(x - 1, y)):
        return False
    return not is_tall_face(m, x, y + 1) and not is_tall_face(m, x, y + 2)


def band_tiles(m, cam_tx, cam_ty, tw, th):
    """Yield (tx, ty) for every tile that draws a stacked face, i.e. owns a strip.

    Iterates dungeon_draw()'s OWN tile range, not the visible window: it starts a
    tile before the camera and runs three past it, and a band tile just outside
    the window still paints its strip half a tile INTO it. Scanning only the
    visible window silently misses those and reports their pixels as strays."""
    ty0, tx0 = cam_ty - 1, cam_tx - 1
    for ty in range(ty0, ty0 + th + 3):
        for tx in range(tx0, tx0 + tw + 3):
            if m.floor(tx, ty):
                continue
            fs, fn = m.floor(tx, ty + 1), m.floor(tx, ty - 1)
            fe, fw = m.floor(tx + 1, ty), m.floor(tx - 1, ty)
            if not (fs or (fs + fn + fe + fw) >= 3):
                continue
            if fn:                      # standalone node owns no strip
                continue
            yield tx, ty


def node_tiles(m, cam_tx, cam_ty, tw, th):
    """Yield (tx, ty, rect) for every standalone rock node in the render window.

    Not a strip concern, but a node tile gained a floor backdrop in the same
    round, so its whole cell legitimately changes. Reported as its own category
    rather than folded into the strip drops -- tools/node_check.py is what
    actually asserts WHAT changed there."""
    for ty in range(cam_ty, cam_ty + th):
        for tx in range(cam_tx, cam_tx + tw):
            if m.floor(tx, ty):
                continue
            fs, fn = m.floor(tx, ty + 1), m.floor(tx, ty - 1)
            fe, fw = m.floor(tx + 1, ty), m.floor(tx - 1, ty)
            if (fs or (fs + fn + fe + fw) >= 3) and fn:
                yield tx, ty, ((tx - cam_tx) * TILE, (ty - cam_ty) * TILE, TILE, TILE)


def cells(m, cam_tx, cam_ty, tw, th):
    """Yield (tx, ty, side, k, nx, ny, old, new, rect) for every candidate cell."""
    for tx, ty in band_tiles(m, cam_tx, cam_ty, tw, th):
        sx, sy = (tx - cam_tx) * TILE, (ty - cam_ty) * TILE
        for side, nx, px in (('w', tx - 1, sx - HALF), ('e', tx + 1, sx + TILE)):
            for k in range(3):
                ny = ty - k
                old = lands_on_bare_rock(m, nx, ny)
                new = lands_on_blank(m, nx, ny)
                yield tx, ty, side, k, nx, ny, old, new, (px, sy - k * TILE, HALF, TILE)


def main():
    mode = sys.argv[1]
    rows = load(sys.argv[2])
    ox, oy, cam_tx, cam_ty, tw, th = (int(a) for a in sys.argv[3:9])
    m = Map(rows, ox, oy)
    all_cells = list(cells(m, cam_tx, cam_ty, tw, th))
    old = [c for c in all_cells if c[6]]
    new = [c for c in all_cells if c[7]]
    drop = [c for c in all_cells if c[6] and not c[7]]
    added = [c for c in all_cells if c[7] and not c[6]]

    if mode == 'predict':
        for tx, ty, side, k, nx, ny, o, n, rect in all_cells:
            if not o and not n:
                continue
            tag = 'KEEP' if (o and n) else ('DROP' if o else 'ADDED!')
            print(f"band({tx},{ty}) {side} k={k} -> cell({nx},{ny}) {tag} rect={rect}")
        print(f"\nold rule {len(old)} cells, new rule {len(new)}, "
              f"drop {len(drop)}, added {len(added)}")
        return

    import numpy as np
    from PIL import Image
    before = np.array(Image.open(sys.argv[9]).convert('RGB')).astype(np.int16)
    after = np.array(Image.open(sys.argv[10]).convert('RGB')).astype(np.int16)
    if before.shape != after.shape:
        print(f"FAIL: size {before.shape} vs {after.shape}")
        sys.exit(1)
    changed = np.any(before != after, axis=2)
    H, W = changed.shape

    def paint(rects):
        mask = np.zeros_like(changed)
        for x, y, w, h in rects:
            x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
            if x0 < x1 and y0 < y1:
                mask[y0:y1, x0:x1] = True
        return mask

    nodes = list(node_tiles(m, cam_tx, cam_ty, tw, th))
    allowed = paint([c[8] for c in drop] + [n[2] for n in nodes])
    stray = changed & ~allowed
    n_stray = int(stray.sum())

    print(f"old {len(old)} cells -> new {len(new)}   drop {len(drop)}   ADDED {len(added)}")
    print(f"changed px {int(changed.sum())}   outside drop rects + {len(nodes)} node tiles: {n_stray}")
    if added:
        # The whole safety argument is that the new rule only ever removes.
        for tx, ty, side, k, nx, ny, o, n, rect in added[:8]:
            print(f"  ADDED band({tx},{ty}) {side} k={k} -> cell({nx},{ny})")
    if n_stray:
        ys, xs = np.nonzero(stray)
        for i in range(min(12, n_stray)):
            px, py = int(xs[i]), int(ys[i])
            print(f"  stray px ({px},{py}) tile ({cam_tx + px // TILE},{cam_ty + py // TILE})")

    silent = 0
    for c in drop:
        x, y, w, h = c[8]
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
        if x0 < x1 and y0 < y1 and not changed[y0:y1, x0:x1].any():
            silent += 1
    print(f"predicted-drop cells that did not change: {silent}/{len(drop)}")
    ok = n_stray == 0 and not added
    print("OK" if ok else "FAIL")
    if not ok:
        sys.exit(1)


main()
