"""Roperite's sprint (the user, 2026-11-18: "use the sprite" -- the newer 39x52 still, animated; SIDE ONLY, R drawn,
L baked in as its mirror, the side view in every direction; 5 x 260 ms):
  0 1 3 4 the sprint (PixelLab animate of the still's side view, run-01 02 03 04)   2 THE LASSO THROW (k-lasso2)
The rattle: PixelLab flattened it into a striped patch on the rump; that patch goes back to the body's tan and the
still's own stick-up rattle (cut from the still) is pasted behind the rump on every frame (the user: "a raised tail").
Ghosts (phase 2's herd, bullets' spawner contract): one row of 10 square cells, R f0-f4 then L f0-f4 (mirrored),
tinted pale blue-white at partial alpha -- all baked in.
Run: python -B art/enemies/anim/61_roperite/build_side.py  (superseded: the user chose the front still, build.py)"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
PL = os.path.join(HERE, 'pixellab')
SPRINT = ['run-01', 'run-02', 'k-lasso2', 'run-03', 'run-04']
MS, LASSO = 260, 2
TAN = (178, 158, 92, 255)
RATTLE_BOX = (0, 6, 9, 19)       # the still's stick-up rattle (x <= 8: the body starts at 9)
RATTLE_ROOT = (7, 16)            # where it goes into the rump, in the still

def hot(p): return p[3] and p[0] > 170 and p[2] < 110 and abs(p[0] - p[1]) > 60

def rattle():
    s = Image.open(os.path.join(HERE, 'original_sprite.png')).convert('RGBA')
    return s.crop(RATTLE_BOX)

def side(n):
    P = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    fr = Image.open(os.path.join(PL, n + '.png')).convert('RGBA'); px = fr.load()
    patch = [(x, y) for y in range(fr.height) for x in range(fr.width) if px[x, y][3] > 128 and hot(px[x, y])]
    for q in patch: px[q] = TAN                                   # the flattened rattle: body again
    fr = pt.tidy(pt.snap(fr, P))
    ax, ay = min(x for x, _ in patch) + 2, min(y for _, y in patch) + 2    # the rump, where the patch was
    r = rattle(); out = Image.new('RGBA', fr.size, pt.CLEAR)
    out.alpha_composite(r, (ax - (RATTLE_ROOT[0] - RATTLE_BOX[0]), ay - (RATTLE_ROOT[1] - RATTLE_BOX[1])))
    out.alpha_composite(fr)                                      # the body over the rattle's root
    return out

def frames():
    fs = [side(n) for n in SPRINT]
    bs = [f.getbbox() for f in fs]; box = (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    W, H = box[2] - box[0], box[3] - box[1]; W += W % 2; H += H % 2
    box = (box[0], box[3] - H, box[0] + W, box[3])
    return [f.crop(box) for f in fs]

def ghost(fr):
    """Pale blue-white at partial alpha: each px's lightness kept, tinted, alpha 150 (outline 190)."""
    out = Image.new('RGBA', fr.size, pt.CLEAR); s, o = fr.load(), out.load()
    for y in range(fr.height):
        for x in range(fr.width):
            p = s[x, y]
            if not p[3]: continue
            if p[:3] == (0, 0, 0): o[x, y] = (70, 90, 140, 190); continue
            l = (p[0] * 3 + p[1] * 6 + p[2]) / 10
            o[x, y] = (int(150 + l * 0.35), int(175 + l * 0.3), 255, 150)
    return out

def ghost_sheet(fs, path):
    """Bullets' spawner sheet: ONE row of square cells, R f0-f4 then L f0-f4 (mirrored), the drawing centred, ghosted."""
    W, H = fs[0].size; S = max(W, H); seq = fs + [pt.mirror(f) for f in fs]
    sheet = Image.new('RGBA', (S * len(seq), S), pt.CLEAR)
    for i, f in enumerate(seq): sheet.alpha_composite(ghost(f), (i * S + (S - W) // 2, (S - H) // 2))
    sheet.save(path); return S

def side_sheet(fs, path):
    """8 directions x 5: the side view everywhere, L (UL L DL) its mirror, baked in."""
    W, H = fs[0].size; views = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
    sheet = Image.new('RGBA', (W * 8 * len(fs), H), pt.CLEAR)
    for d, v in enumerate(views):
        for i, f in enumerate(fs): sheet.paste(pt.mirror(f) if v in ('UL', 'L', 'DL') else f, ((d * len(fs) + i) * W, 0))
    sheet.save(path)

def gif(fs, ms, path, S=4):
    W, H = fs[0].size
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).convert('RGB').resize((W * S, H * S), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, disposal=2)

if __name__ == '__main__':
    fs = frames(); W, H = fs[0].size; gap = 4
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    b = Image.new('RGBA', (5 * (W + gap) + gap, 2 * (H + gap) + gap), (24, 24, 32, 255))
    for i, f in enumerate(fs): b.alpha_composite(f, (gap + i * (W + gap), gap)); b.alpha_composite(pt.mirror(f), (gap + i * (W + gap), 2 * gap + H))
    b.resize((b.width * 4, b.height * 4), Image.NEAREST).save(os.path.join(rv, 'side_board.png'))
    gif(fs, MS, os.path.join(rv, 'side_260.gif'))
    print('frame %dx%d' % (W, H))
    t = os.path.join(rv, 'check.png'); side_sheet(fs, t)
    print(*pt.check_frames(t, 5, W, H, views=(('R', 2), ('L', 6))), sep=chr(10)); os.remove(t)
    if '--install' in sys.argv:
        side_sheet(fs, os.path.join(ROOT, 'assets/enemies/redraws/61_roperite.png'))
        print('ghost cell', ghost_sheet(fs, os.path.join(ROOT, 'assets/enemies/61_roperite_ghosts.png')))
