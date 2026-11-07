"""Whether a PixelLab room meets the feet exactly as the old one did: the
ground of both layers pixel by pixel, and the cell map, against
art/structures/interiors/<old>_design.py and include/interiors.h.

    python tools/interior_parity.py N OLD_DESIGN NEW_DESIGN
"""
import importlib.util, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load(p):
    s = importlib.util.spec_from_file_location('d%d' % abs(hash(p)), p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.design()


n, old_p, new_p = int(sys.argv[1]), sys.argv[2], sys.argv[3]
old, new, W = load(old_p), load(new_p), 320
bad = 0
for name, i in (('room', 0), ('furniture', 1)):
    sets = [{(x, y) for y, row in enumerate(d['depth']['foot']) for x, c in enumerate(row[i * W:(i + 1) * W]) if c == '#'}
            for d in (old, new)]
    print('%s ground: %d only old, %d only new' % (name, len(sets[0] - sets[1]), len(sets[1] - sets[0])))
    bad += len(sets[0] ^ sets[1])
h = open(os.path.join(os.path.dirname(__file__), '..', 'include', 'interiors.h')).read()
m = re.search(r'interior_%d_coll\[IMAP_H\] = \{(.*?)\};' % n, h, re.S)
same = re.findall(r'"([^"]*)"', m.group(1)) == open(os.path.join(os.path.dirname(__file__), '..', 'assets', 'interiors', 'room_%d.txt' % n)).read().split('\n')[:15]
print('cell map same:', same)
sys.exit(0 if same and not bad else 1)
