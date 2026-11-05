"""34 Anaye frame 0: PixelLab's try 1 folded to 8 colours plus black, thick black thinned to one-pixel lines. No credits.

    python art/enemies/pixellab/34_anaye/redo_bc/hand_frame0.py
Writes idle_frame0_fold.png (the plain fold) and idle_frame0_clean.png, and a review on black and grey.
"""
import ast
from collections import Counter
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
src36 = (ROOT / 'art/enemies/pixellab/36_cu_sith/views.py').read_text(encoding='utf-8')
exec(ast.get_source_segment(src36, next(n for n in ast.parse(src36).body if isinstance(n, ast.FunctionDef) and n.name == 'flat')))

def h(s): return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
K = (0, 0, 0)
FOLD = {h('14101e'): K, h('474751'): h('595965'), h('4edc4a'): h('058f3a'), h('5e486a'): h('664b95')}
GAP = h('34343e')             # steel's dark tone: plate gaps that part one fill from itself
FILLS = {h('595965'), h('848694'), h('664b95')}
BONE = h('e8e0c0')
EYES = ((59, 66), (60, 67), (61, 68), (59, 67), (60, 68))   # brow and a 2 px eye, left of the image; mirrored about x = 63.5
MASK = (56, 56, 74, 76)      # x0 y0 x1 y1: the face keeps its own lines
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

draft = HERE / 'idle_frame0_draft_raw_clean.png'
if not draft.exists():
    draft.write_bytes((HERE / 'idle_frame0_clean.png').read_bytes())
im = Image.open(draft).convert('RGBA')
px = im.load()
W, H = im.size
for y in range(H):
    for x in range(W):
        if px[x, y][3] and px[x, y][:3] in FOLD:
            px[x, y] = FOLD[px[x, y][:3]] + (255,)
im.save(HERE / 'idle_frame0_fold.png')

def opaque(x, y): return 0 <= x < W and 0 <= y < H and px[x, y][3] > 0
def black(x, y): return opaque(x, y) and px[x, y][:3] == K
def in_mask(x, y): return MASK[0] <= x < MASK[2] and MASK[1] <= y < MASK[3]
def outline(x, y): return any(not opaque(x + a, y + b) for a, b in N4)
def recolour(x, y):
    n = Counter(px[x + a, y + b][:3] for a in (-1, 0, 1) for b in (-1, 0, 1)
                if opaque(x + a, y + b) and px[x + a, y + b][:3] != K)
    if not n: return False
    px[x, y] = n.most_common(1)[0][0] + (255,)
    return True

for _ in range(6):           # any 2x2 of black keeps only what the outline needs
    changed = False
    for y in range(H - 1):
        for x in range(W - 1):
            sq = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
            if all(black(*p) for p in sq):
                for p in sq:
                    if not outline(*p) and not in_mask(*p) and recolour(*p):
                        changed = True
                        break
    if not changed: break

im = flat(im, 6, spare={h('058f3a')})
px = im.load()

# Lines that part one fill from the same fill are plate gaps, not parts: the dark steel tone, not black. Face and crest keep theirs.
for x, y in [(x, y) for y in range(58, H) for x in range(W) if black(x, y) and not outline(x, y) and not in_mask(x, y)]:
    pairs = (((x - 1, y), (x + 1, y)), ((x, y - 1), (x, y + 1)))
    if any(opaque(*p) and opaque(*q) and px[p][:3] in FILLS and px[p][:3] == px[q][:3] for p, q in pairs):
        px[x, y] = GAP + (255,)

# The eyes: each a 2 px mark under a black brow, the mask's slits drawn too heavy by PixelLab.
for y in range(66, 69):
    for x in range(58, 70):
        if black(x, y): px[x, y] = BONE + (255,)
for x, y in EYES:
    px[x, y] = K + (255,)
    px[127 - x, y] = K + (255,)
im.save(HERE / 'idle_frame0_clean.png')
S = 6
box = im.getbbox()
out = Image.new('RGBA', (W * S * 2, H * S), (0, 0, 0, 255))
out.paste((96, 96, 96, 255), (W * S, 0, W * S * 2, H * S))
big = im.resize((W * S, H * S), 0)
out.alpha_composite(big, (0, 0)); out.alpha_composite(big, (W * S, 0))
out.save(HERE / 'idle_frame0_review.png')
cnt = Counter(p[:3] for p in im.get_flattened_data() if p[3]); tot = sum(cnt.values())
L = lambda c: (max(c) + min(c)) / 2 / 255 * 100
for c, n in cnt.most_common(): print('%02x%02x%02x' % c, n, '%.1f%%' % (100 * n / tot), 'L%.0f' % L(c))
print('bbox', box, 'under L25 %.0f%%' % (100 * sum(n for c, n in cnt.items() if L(c) < 25) / tot))
