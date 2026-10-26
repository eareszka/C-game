"""Enemy 23 Olgoi-Khorkhoi, its back: the body out of the sand, lying along the ground to the right with the tip
curling up and a ridge of fin spines along its top, like the user's reference (art/_backup/23_reference_back_20261019,
2026-10-19: "have the transition between back and middle body seamless", "the back similar to the reference").

The frame is the user's first frame (23_olgoi_khorkhoi_frame0_draft.aseprite) without its sand and drops
(pixellab/23_olgoi_khorkhoi/theirs_nosand.json: their pixels whose part was the sand, a drop or the whip they took
off, dropped), widened to
200 px, with the back drawn as a guide by the first frame's own tube (pose_first's TAIL) and a fin of spines along
its top. PixelLab's edit route redraws the guide whole in the worm's style; only the back and the bend into it (MASK)
are taken from its result, so every other pixel stays the user's and the leg runs into the back in one piece.

    python art/enemies/23_olgoi_khorkhoi_back.py guide              # the guide and the mask, for looking at
    python art/enemies/23_olgoi_khorkhoi_back.py redraw [--generate] [--try N]   # PixelLab (paid with --generate)
    python art/enemies/23_olgoi_khorkhoi_back.py take N             # try N's back into 23_olgoi_khorkhoi_frame0_ground

How the back was first made. The master's back is now the user's own: they sketched its course (the body down-right
and off the screen's right edge, art/_backup/23_user_sketch_20261019) and then reshaped it by hand in frame 1 of the
spin draft (art/_backup/23_user_reshape_20261019, 2026-10-19): their pixels, with the black outline closed round them,
are in 23_olgoi_khorkhoi_frame0_ground.aseprite, so `guide` here no longer reproduces the master.
"""
from pathlib import Path
import importlib, json, math, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(HERE)]
import first_frame as ff
import pixellab_enemy as pe
A = importlib.import_module('23_olgoi_khorkhoi_pose_first')
PAL, W, H = A.PAL, A.W, A.H
D = HERE / 'pixellab/23_olgoi_khorkhoi'
OLD_SPINE = A.SPINE[len(A.TAIL):]
BEND = (100, 50)                     # the back and the bend into it: columns from here right, rows from here down
FIN = None                           # the fin runs over this stretch of the back (fractions from the tip), a spine every this many px, about this tall
PROMPT = """Redraw this frame of enemy 23 Olgoi-Khorkhoi, the Mongolian death worm, exactly 200x83 pixels, transparent background, keeping every shape where the guide has it. A giant red segmented worm: its maw of four toothed petals and whip feelers at the left, its body arching high over the top and coming down on the right, then turning and lying along the ground to the right, its back end curling up at the far right with a ridge of small pointed fin spines along the top of the back, like a sea serpent. The body bends from the arch into the back in one smooth continuous tube with the same bead segments, no seam, no line across it. Keep the same three reds, light on top, dark underneath, one-pixel black outline, flat tones, no gradients, dithering or texture."""


def back():
    """The back as the first frame's tube draws it, and its fin: {(x, y): letter} for the guide."""
    px, ticks = A.tube()
    body = A.layer([('body', px, 'solid')])[0]
    for p in ticks:
        if body.get(p) in ('D', 'M', 'L'): body[p] = 'K'
    run = ff.path(A.TAIL + OLD_SPINE[:1])
    L = run[-1][3]
    fin = {}
    a, b, step, tall = FIN or (0, 0, 1, 0)
    at = [] if FIN is None else [min(range(len(run)), key=lambda i: abs(run[i][3] - t)) for t in range(int(a * L), int(b * L), step)]
    for i in at:                                                     # a spine every `step` px along the back
        x, y, r, s = run[i]
        f = s / L
        (x0, y0), (x1, y1) = run[max(i - 2, 0)][:2], run[min(i + 2, len(run) - 1)][:2]
        n = math.hypot(x1 - x0, y1 - y0) or 1
        tx, ty = (x1 - x0) / n, (y1 - y0) / n                       # along the back, toward the leg
        nx, ny = ty, -tx
        if ny > 0 or abs(ny) < 0.3 and nx < 0: nx, ny = -nx, -ny     # the top (on the curl, the outside)
        h = tall * (0.6 + 0.4 * f) + 1                               # the spines grow toward the middle of the back
        r -= A.DEPTH + 1                                             # rooted inside the body, even in a bead's groove
        base = [(x + nx * r + tx * k, y + ny * r + ty * k) for k in (-2.0, 2.0)]
        tip = (x + nx * (r + A.DEPTH + h) - tx * 2.5, y + ny * (r + A.DEPTH + h) - ty * 2.5)   # swept back, toward the tail's tip
        tri = (base[0], base[1], tip)
        sign = lambda p, q, o: (p[0] - o[0]) * (q[1] - o[1]) - (q[0] - o[0]) * (p[1] - o[1])
        for qy in range(int(min(v[1] for v in tri)) - 1, int(max(v[1] for v in tri)) + 2):
            for qx in range(int(min(v[0] for v in tri)) - 1, int(max(v[0] for v in tri)) + 2):
                c = (qx + 0.5, qy + 0.5)
                d = [sign(c, tri[(k + 1) % 3], tri[k]) for k in range(3)]
                if all(v >= 0 for v in d) or all(v <= 0 for v in d):
                    fin[qx, qy] = 'M'
    fin = {p: c for p, c in fin.items() if p not in body or body[p] == 'K'}
    for p in list(fin):                                              # the spines' own line where they meet the air
        for dx, dy in ff.N4:
            q = (p[0] + dx, p[1] + dy)
            if q not in fin and q not in body: fin[q] = None
    fin = {p: 'K' if c is None else c for p, c in fin.items()}
    for p, c in list(fin.items()):                                   # where a spine sits on the back: the back's line through it
        if c == 'M' and any(body.get((p[0] + dx, p[1] + dy)) not in (None, 'K') for dx, dy in ff.N4): fin[p] = 'K'
    out = {p: c for p, c in body.items() if p[0] >= BEND[0] and p[1] >= BEND[1] or p[0] >= 136}
    out.update(fin)
    return out


def guide():
    base = {tuple(map(int, k.split(','))): c for k, c in json.loads((D / 'theirs_nosand.json').read_text()).items()}
    b = back()
    out = dict(base)
    for p, c in b.items():
        if p not in base or p[0] >= 104 and p[1] > 52: out[p] = c   # the leg's foot redrawn by the tube: no edge across the bend
    out = {p: c for p, c in out.items() if 0 < p[0] < W and 0 < p[1] < H}
    mask = Image.new('L', (W, H), 0)
    for p in b:
        if p[0] >= BEND[0] and p[1] >= BEND[1] or p[0] >= 136:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (p[0] + dx, p[1] + dy)
                    if 0 <= q[0] < W and 0 <= q[1] < H and not (q in base and q[0] < 104): mask.putpixel(q, 255)
    im = ff.image(out, PAL, W, H)
    im.save(D / 'source_back.png'); mask.save(D / 'mask_back.png')
    Image.new('RGBA', (W, H * 8)).save(D / 'cell_back.png')
    ff.image(base, PAL, W, H).save(D / 'ref_frame0_clean.png')
    (D / 'prompt_back.txt').write_text(PROMPT, encoding='utf-8')
    (D / 'job.json').write_text(json.dumps({'id': 23, 'name': '23-olgoi-khorkhoi', 'dir': 'art/enemies/pixellab/23_olgoi_khorkhoi',
        'description': '', 'prompts': {'back': 'prompt_back.txt'},
        'sheets': {'back': {'png': 'art/enemies/pixellab/23_olgoi_khorkhoi/cell_back.png', 'frames': 1, 'rows': True,
                            'views': ['D'], 'make': 'none', 'from': 'ref'}}}, indent=2))
    big = Image.new('RGBA', (W * 4, H * 8 + 8), (90, 96, 110, 255))
    big.alpha_composite(im.resize((W * 4, H * 4), Image.NEAREST), (0, 0))
    big.alpha_composite(mask.convert('RGBA').resize((W * 4, H * 4), Image.NEAREST), (0, H * 4 + 8))
    big.save(D / 'guide_board.png')
    return out, mask


def redraw(generate, attempt):
    guide()
    j = pe.Job(D / 'job.json')
    pe.edit(j, 'back', generate, attempt)


def take(attempt):
    """Try `attempt`'s back, on the worm's colours, into the frame: the masked pixels only."""
    base = {tuple(map(int, k.split(','))): c for k, c in json.loads((D / 'theirs_nosand.json').read_text()).items()}
    draft = Image.open(D / ('back_frame0_draft.png' if attempt == 0 else f'back_try{attempt}_draft.png')).convert('RGBA')
    mask = Image.open(D / 'mask_back.png')
    RGB = ff.rgb(PAL); inv = {v: k for k, v in RGB.items()}
    pal = [v for k, v in RGB.items() if k in 'KDMLs']
    out = {p: c for p, c in base.items() if not mask.getpixel(p)}
    for y in range(H):
        for x in range(W):
            if not mask.getpixel((x, y)): continue
            c = draft.getpixel((x, y))
            if c[3] < 128: continue
            near = min(pal, key=lambda v: sum((a - b) ** 2 for a, b in zip(v, c[:3])))
            out[x, y] = inv[near]
    for p, c in list(out.items()):                                   # a closed outline where the new part meets nothing
        if c != 'K' and mask.getpixel(p) and any((p[0] + dx, p[1] + dy) not in out for dx, dy in ff.N4): out[p] = 'K'
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'guide':
        guide(); print(D / 'guide_board.png')
    elif a[0] == 'redraw':
        redraw('--generate' in a, int(a[a.index('--try') + 1]) if '--try' in a else 1)
