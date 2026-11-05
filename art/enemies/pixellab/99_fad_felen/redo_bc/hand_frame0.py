"""99 Fad Felen frame 0: PixelLab's try 1 folded to 8 colours plus black, small patches merged, the frame cut snug to 88x59 (2 px all round for the breathing). No credits.

    python art/enemies/pixellab/99_fad_felen/redo_bc/hand_frame0.py
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

raw = HERE / 'idle_frame0_fold.png'
if not raw.exists():
    raw.write_bytes((HERE / 'idle_frame0_clean.png').read_bytes())
im = Image.open(raw).convert('RGBA')
px = im.load()
for y in range(im.height):
    for x in range(im.width):
        if px[x, y][3] and px[x, y][:3] == h('fce4a0'):
            px[x, y] = h('f0e880') + (255,)
im = flat(im, 6, spare={h('e8e0c0'), h('b2966a')})   # the skull keeps its teeth and shade
box = im.getbbox()
# Doubled outer outline: a black pixel on the edge with no colour among its 8 neighbours goes, until none are left.
px = im.load()
N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
def at(x, y): return px[x, y] if 0 <= x < im.width and 0 <= y < im.height else (0, 0, 0, 0)
while True:
    gone = [(x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3] and px[x, y][:3] == (0, 0, 0)
            and any(not at(x + a, y + b)[3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            and not any(at(x + a, y + b)[3] and at(x + a, y + b)[:3] != (0, 0, 0) for a, b in N8)]
    if not gone: break
    for p in gone: px[p] = (0, 0, 0, 0)
    print('thinned', len(gone))
W, H = 88, 59
out = Image.new('RGBA', (W, H))
out.paste(im, (2 - box[0], 2 - box[1]))
out.save(HERE / 'idle_frame0_clean.png')
Image.new('RGBA', (W * 10, H * 8)).save(HERE / 'base/99_fad_felen.png')

# old and new, same scale, on black and grey
old = Image.open(ROOT / 'assets/enemies/redraws/99_fad_felen.png').convert('RGBA').crop((0, 0, 76, 52))
S = 5
cw, ch = W * S, H * S
b = Image.new('RGBA', (cw * 2 + 8, ch * 2 + 8), (40, 40, 40, 255))
for r, bg in enumerate(((0, 0, 0, 255), (96, 96, 96, 255))):
    for c, f in enumerate((old, out)):
        x, y = c * (cw + 8), r * (ch + 8)
        b.paste(bg, (x, y, x + cw, y + ch))
        b.alpha_composite(f.resize((f.width * S, f.height * S), 0), (x, y + ch - f.height * S))
b.save(HERE / 'stop1_old_new.png')
c = Counter(p[:3] for p in out.get_flattened_data() if p[3])
print(out.getbbox(), [('%02x%02x%02x' % k, v) for k, v in c.most_common()])
