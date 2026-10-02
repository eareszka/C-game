"""How varied the island library is.

    python tools/island_census.py [src/islands.inc]

Reads the baked library and reports entries per size class, how many
entries are an exact mirror of another, how many distinct layouts there are
(plateaus overlapping SAME_SHAPE or more under shift and mirror count as one,
the bake's own test), and how many sealed entries could take a ground cave
(mouth_ok, the game's cave search). Nothing is written.
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_islands import LARGE_HIGH, MEDIUM_HIGH, mouth_ok, same_shape  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Kinds:
    """Just enough of gen_islands.Sprites for mouth_ok: the sprites' kinds."""
    def __init__(self, kind):
        self.kind = kind


def load(path):
    s = open(path).read()
    kind = [int(v) for v in re.search(r'ISLAND_KIND\[ISLAND_SPRITES\] = \{([^}]*)\}', s).group(1).split(',')]
    arrays = {}
    for m in re.finditer(r'ISLAND_(\d+)_(CELLS|LEVEL)\[\d+\] = \{([^}]*)\}', s):
        arrays[(int(m.group(1)), m.group(2))] = np.array([int(v) for v in m.group(3).split(',')])
    out = []
    for m in re.finditer(r'\{ (\d+), (\d+), (\d+), (\d+), (\d+), ISLAND_(\d+)_CELLS', s):
        w, h, opn, i = int(m.group(1)), int(m.group(2)), int(m.group(5)), int(m.group(6))
        out.append((arrays[(i, 'CELLS')].reshape(h, w), arrays[(i, 'LEVEL')].reshape(h, w), opn))
    return Kinds(kind), out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'src', 'islands.inc')
    sp, lib = load(path)
    names = ('large', 'medium', 'small')
    klass = [0 if (lv > 0).sum() >= LARGE_HIGH else 1 if (lv > 0).sum() >= MEDIUM_HIGH else 2 for _, lv, _ in lib]
    print('%d entries: %s' % (len(lib), ', '.join('%d %s' % (klass.count(k), names[k]) for k in range(3))))

    # exact mirrors: the same plateau and walls, flipped (cells are mirrored sprites, so compare levels)
    mirrored = sum(1 for i, (_, a, _) in enumerate(lib) for j, (_, b, _) in enumerate(lib)
                   if i < j and a.shape == b.shape and np.array_equal(a, b[:, ::-1]))
    print('%d exact mirror pairs' % mirrored)

    reps = [[] for _ in range(3)]
    for (g, lv, _), k in zip(lib, klass):
        m = lv > 0
        if not any(same_shape(m, r) for r in reps[k]):
            reps[k].append(m)
    print('%d distinct layouts: %s' % (sum(len(r) for r in reps),
                                       ', '.join('%d %s' % (len(reps[k]), names[k]) for k in range(3))))

    sealed = [(g, lv) for g, lv, o in lib if not o]
    ok = sum(1 for g, lv in sealed if mouth_ok(sp, g, lv))
    print('%d sealed entries, %d of them can take a ground cave' % (len(sealed), ok))


if __name__ == '__main__':
    main()
