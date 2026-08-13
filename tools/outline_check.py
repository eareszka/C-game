"""Is a plateau's outline shaped like a landform, or like something ruled?

band_width.py and flank_width.py measure how thick the rock is. This measures
the shape of the edge it is drawn along, which is a different question and the
one a design critique keeps raising: the outline runs too straight, turns
through ninety degrees when it turns, and has had every small inset and
protrusion filtered out of it.

Reads a SHOT_MASK picture — the whole world, one pixel to the tile — so it is
measuring the elevation mask itself rather than the art cut from it. That is
deliberate: the art can only draw the shape it is given.

    SHOT_MASK=1 shot.exe <seed> mask.png
    python tools/outline_check.py mask.png

Reports, per level:

  straight runs   how far the edge goes before it steps, in tiles. A ruled edge
                  has a long tail here; the reference steps every few tiles.
  diagonal share  of the steps the edge takes, how many are single-tile steps
                  that continue in the same direction — a 45 degree run — as
                  against square corners that turn and stay turned.
  protrusions     tiles of edge that stick out one or two from their neighbours,
                  which the reference has and a filtered mask does not.
  pieces          connected regions of high ground, and how many are small
                  enough to read as litter rather than as a landform.
"""
import sys
import numpy as np
from PIL import Image

# The colours SHOT_MASK writes, as RGB. It builds them as 0xAARRGGBB literals
# into an RGBA32 surface, which is byte order, so they come out reversed.
LEVEL = {1: (240, 144, 64), 2: (240, 240, 64), 3: (255, 255, 255)}


def runs_of(seq):
    """Lengths of the maximal constant runs in a sequence."""
    out, i = [], 0
    while i < len(seq):
        j = i
        while j < len(seq) and seq[j] == seq[i]:
            j += 1
        out.append(j - i)
        i = j
    return out


def edge_profile(mask, axis):
    """For each line across `axis`, where the mask's boundary sits.

    One number per line — the first set index — so a column of the plateau's
    north edge gives the row the edge is on. Lines with nothing in them are
    dropped, and so are lines whose edge jumps more than a few tiles from the
    previous one, which is a different landform rather than a step in this one.
    """
    m = mask if axis == 0 else mask.T
    prof = []
    for k in range(m.shape[1]):
        idx = np.nonzero(m[:, k])[0]
        prof.append(int(idx[0]) if idx.size else None)
    return prof


def segments(prof, jump=6):
    """Split a profile into stretches that belong to one continuous edge."""
    out, cur = [], []
    for v in prof:
        if v is None or (cur and abs(v - cur[-1]) > jump):
            if len(cur) > 8:
                out.append(cur)
            cur = []
        if v is not None:
            cur.append(v)
    if len(cur) > 8:
        out.append(cur)
    return out


def label(mask):
    """Connected components, eight-way. Written out so the tools need nothing
    but numpy and pillow, as the rest of them do."""
    out = np.zeros(mask.shape, dtype=np.int32)
    n = 0
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if out[y0, x0]:
            continue
        n += 1
        stack = [(y0, x0)]
        out[y0, x0] = n
        while stack:
            y, x = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]
                            and mask[ny, nx] and not out[ny, nx]):
                        out[ny, nx] = n
                        stack.append((ny, nx))
    return out


def report(name, mask):
    if mask.sum() < 200:
        print('%-10s nothing to measure' % name)
        return

    flat, steps, diag, prot = [], 0, 0, 0
    for axis in (0, 1):
        for seg in segments(edge_profile(mask, axis)):
            r = runs_of(seg)
            flat.extend(r)
            # A step of one tile that is followed by another step the same way
            # is a diagonal; a step that is followed by a long flat is a corner.
            d = np.diff(np.array(seg))
            nz = np.nonzero(d)[0]
            steps += nz.size
            for i in range(len(nz) - 1):
                if nz[i + 1] - nz[i] <= 2 and d[nz[i]] * d[nz[i + 1]] > 0:
                    diag += 1
            # A run of one or two tiles that returns the way it came is a
            # protrusion or an inset, not a step in a direction.
            for i in range(len(nz) - 1):
                if nz[i + 1] - nz[i] <= 2 and d[nz[i]] * d[nz[i + 1]] < 0:
                    prot += 1

    # How much shape the edge has at each scale, which is the question a single
    # roughness number cannot answer. An edge can step every tile and still be
    # a ruled line at twenty — that is jitter laid on a straight edge, and it is
    # what a fine noise octave gives you if it is the only one. Subtracting a
    # moving average of width W leaves what the edge does at scales below W, so
    # the difference between two columns is the shape living between them.
    scales = (4, 8, 16, 32)
    rough = {w: [] for w in scales}
    for axis in (0, 1):
        for seg in segments(edge_profile(mask, axis)):
            a = np.array(seg, dtype=float)
            for w in scales:
                if a.size < w * 2:
                    continue
                k = np.ones(w) / w
                sm = np.convolve(a, k, mode='valid')
                d = a[w // 2: w // 2 + sm.size] - sm
                rough[w].append(d)

    f = np.array(flat, dtype=float)
    lab = label(mask)
    sizes = np.bincount(lab.ravel())[1:]
    print('%-10s straight runs: median %2d  mean %5.1f  p90 %3d  longest %3d tiles'
          % (name, int(np.median(f)), f.mean(),
             int(np.percentile(f, 90)), int(f.max())))
    print('%-10s of %d steps in the edge, %4.1f%% continue as a diagonal, '
          '%4.1f%% turn straight back' % ('', steps,
                                          100.0 * diag / max(steps, 1),
                                          100.0 * prot / max(steps, 1)))
    parts = []
    for w in scales:
        if rough[w]:
            parts.append('under %2d: %4.2f' % (w, np.concatenate(rough[w]).std()))
    print('%-10s wander, in tiles, at each scale — %s' % ('', '   '.join(parts)))
    print('%-10s %d pieces of high ground, %d of them under 120 tiles'
          % ('', sizes.size, int((sizes < 120).sum())))


def main():
    m = np.array(Image.open(sys.argv[1]).convert('RGB'))
    above = np.zeros(m.shape[:2], dtype=bool)
    for lv in (3, 2, 1):
        above |= np.all(m == LEVEL[lv], axis=2)
        report('level %d+' % lv, above.copy())


if __name__ == '__main__':
    main()
