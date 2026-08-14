"""Count the degenerate shapes in an elevation mask.

    python tools/holes_check.py <mask.png> [limb_min]

Reads a whole-world render from `SHOT_MASK=1 ./shot.exe <seed> mask.png` — one
pixel to the tile, coloured by level — and reports, per level, the two shapes a
landform should never have:

  ENCLOSED  a region of ground below the level that the level surrounds on every
            side. The band is only ever drawn on a south, west or east edge, so
            an enclosed hole is the one case that forces rock onto a north-facing
            wall, and that is what reads as a crater.

  THIN      tiles whose highland is at most `limb_min` wide, measured as the
            shorter of the horizontal and vertical run through them. A one-tile
            highland strip still carries a one-tile flank each side, so it draws
            three tiles of rock and looks like a pillar standing in the grass.

"Gone" is meant to be a number here rather than an impression, and the same
number before and after says whether a change fixed anything. Both are counted on
`level >= L` for each L, which is the mask the band is actually cut from.

No scipy in this environment: the flood fill is PIL's, which is C, and the run
lengths are numpy sweeps. Both are seconds on a nine-million-tile map.
"""
import sys
import numpy as np
from PIL import Image

# What tools/shot.cpp writes per level under SHOT_MASK. Bytes land R,G,B in
# SDL_PIXELFORMAT_RGBA32, so 0xFF4090F0 is (240,144,64).
LEVEL_RGB = {
    1: (240, 144, 64),
    2: (240, 240, 64),
    3: (255, 255, 255),
}


def level_grid(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im)
    lv = np.zeros(a.shape[:2], dtype=np.uint8)
    for L, rgb in LEVEL_RGB.items():
        lv[np.all(a == np.array(rgb, dtype=np.uint8), axis=-1)] = L
    return lv


def enclosed_regions(mask):
    """Sizes of the connected low regions that `mask` completely surrounds.

    Run-length connected components, 4-connected: each row's low runs become
    nodes, runs that overlap vertically are unioned, and a component that never
    touches the map edge is enclosed by construction.

    Two other ways were tried and are worth not repeating. PIL's
    ImageDraw.floodfill is a silent no-op in Pillow 12 — it still exists and
    still returns, it just does not fill, so the outside comes back looking like
    one eight-million-tile hole. And walking the hole tiles with a per-component
    rescan is nine million cells times a few hundred components. There are only
    a few tens of thousands of runs on a 3000x3000 map, so this is the cheap
    axis to work on."""
    h, w = mask.shape
    low = ~mask.astype(bool)

    parent = []

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    run_size = []
    run_edge = []
    prev = []
    for y in range(h):
        row = low[y].view(np.int8)
        d = np.diff(np.concatenate(([np.int8(0)], row, [np.int8(0)])))
        starts = np.flatnonzero(d == 1).tolist()
        ends = np.flatnonzero(d == -1).tolist()      # exclusive
        cur = []
        for s, e in zip(starts, ends):
            rid = len(parent)
            parent.append(rid)
            run_size.append(e - s)
            run_edge.append(y == 0 or y == h - 1 or s == 0 or e == w)
            cur.append((s, e, rid))
        # link runs that overlap the row above
        i = j = 0
        while i < len(prev) and j < len(cur):
            ps, pe, pid = prev[i]
            cs, ce, cid = cur[j]
            if pe > cs and ce > ps:
                union(pid, cid)
            if pe < ce:
                i += 1
            else:
                j += 1
        prev = cur

    total = {}
    edged = {}
    for rid in range(len(parent)):
        r = find(rid)
        total[r] = total.get(r, 0) + run_size[rid]
        edged[r] = edged.get(r, False) or run_edge[rid]
    return sorted((v for k, v in total.items() if not edged[k]), reverse=True)


def run_lengths(mask):
    """For every set tile, the horizontal and vertical run of set tiles through it."""
    m = mask.astype(bool)

    def sweep(m):
        # consecutive set tiles ending at each column, and starting at each
        left = np.zeros(m.shape, dtype=np.int32)
        acc = np.zeros(m.shape[0], dtype=np.int32)
        for x in range(m.shape[1]):
            acc = np.where(m[:, x], acc + 1, 0)
            left[:, x] = acc
        right = np.zeros(m.shape, dtype=np.int32)
        acc = np.zeros(m.shape[0], dtype=np.int32)
        for x in range(m.shape[1] - 1, -1, -1):
            acc = np.where(m[:, x], acc + 1, 0)
            right[:, x] = acc
        return left + right - 1

    run_h = sweep(m)
    run_v = sweep(m.T).T
    return run_h, run_v


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    limb_min = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    lv = level_grid(path)
    print(f"{path}   {lv.shape[1]}x{lv.shape[0]} tiles")
    print(f"{'level':>5} {'area':>9} {'enclosed':>9} {'holetiles':>10} "
          f"{'biggest':>8} {'thin<=%d' % limb_min:>9}")

    tot_holes = tot_thin = 0
    for L in (1, 2, 3):
        mask = (lv >= L).astype(np.uint8)
        area = int(mask.sum())
        if area == 0:
            print(f"{L:>5} {0:>9} {0:>9} {0:>10} {0:>8} {0:>9}")
            continue
        sizes = enclosed_regions(mask)
        run_h, run_v = run_lengths(mask)
        thin = int((mask.astype(bool) & (np.minimum(run_h, run_v) <= limb_min)).sum())
        tot_holes += len(sizes)
        tot_thin += thin
        print(f"{L:>5} {area:>9} {len(sizes):>9} {sum(sizes):>10} "
              f"{(max(sizes) if sizes else 0):>8} {thin:>9}")

    print(f"\nTOTAL enclosed regions {tot_holes}, thin tiles {tot_thin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
