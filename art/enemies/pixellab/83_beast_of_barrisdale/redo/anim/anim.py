"""83 redo: PixelLab's animations of the approved key frames on the battle palette, every frame flattened, one outline,
tidied. Frame 0 of each sheet is the approved key itself.
The user, 2026-11-02: approved, but "too good/smooth for the game compared to the other sprites animations". So it
steps like the cast: five poses, each held two cells of the 10-cell sheets, so the fight's beats (on even frames) and
its timing do not change.
  idle   poses 0 2 4 6 8 of PixelLab's frames, 260 ms each: breathing, two wingbeats, feet held on the ground row.
  fly    poses 0 2 4 6 8, 260 ms each: a strong beat, the body bobbing with it.
Then: "the same amount of choppyness as dingbat". Dingbat's idle is 5 poses at 260 ms (42-100% of pixels change a
frame): idle and fly above already match. Its catch sheet barely moves, 6-11% a frame, A B C B A:
  block  7 frames across the 2.0 s hang (0.29 s each): closing, the approved wrapped key A B C B A, opening. B and C are
         A with one and two rows taken out of the wings (the top settles down), feet still. Catching starts at 0.35 s,
         just after the closing frame.

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/anim/anim.py  # writes idle_N fly_N block_N .png, review.png, *.gif
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import tidy as tidy_mod
W, H = 100, 65
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
PAL = [(0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x47, 0x47, 0x51), (0xec, 0x84, 0x76), (0xb6, 0x43, 0x3d), (0xf0, 0xb8, 0x90), (0x42, 0x16, 0x18)]
GROUND = 62


def pngs(name):
    return [l.strip() for l in (HERE / f'{name}.log').read_text().splitlines() if l.strip().endswith('.png')]


def fold(p):
    if max(p) < 0x14: return K
    return min(PAL, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


def flat(g, most=2):
    seen, out = set(), dict(g)
    for p, c in g.items():
        if p in seen: continue
        piece, todo = {p}, [p]
        while todo:
            a = todo.pop()
            for dx, dy in N4:
                q = (a[0] + dx, a[1] + dy)
                if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
        seen |= piece
        if c == K or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def biggest(g):
    left, best = set(g), set()
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (a[0] + dx, a[1] + dy)
                    if q in left: left.discard(q); todo.append(q)
        if len(piece) > len(best): best = piece
    return {p: g[p] for p in best}


def lone(im):
    """Pixels unlike all eight neighbours, left by tidy where only black surrounds them, take the neighbours' colour."""
    px = im.load()
    N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] == K: continue
            near = [px[x + a, y + b] for a, b in N8]
            if any(n[3] and n[:3] == c[:3] for n in near): continue
            pick = Counter(n[:3] for n in near if n[3]).most_common(1)
            if pick: px[x, y] = pick[0][0] + (255,)
    return im


def clean(path, ground=None):
    im = Image.open(path).convert('RGBA')
    g = {(x, y - 2): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = biggest(flat(g))
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    dy = ground - max(y for x, y in g) if ground is not None else 0
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y + dy < H: out.putpixel((x, y + dy), c + (255,))
    return lone(tidy_mod.tidy(out))


idle_r, fly_r, block_r, close_r = pngs('idle'), pngs('fly'), pngs('block'), pngs('close')
SHEETS = {
    'idle': [Image.open(HERE / 'key_idle.png').convert('RGBA')] + [clean(p, GROUND) for p in idle_r[1:10]],
    'fly': [Image.open(HERE / 'key_fly.png').convert('RGBA')] + [clean(p) for p in fly_r[1:10]],
}
HELD = (0, 0, 2, 2, 4, 4, 6, 6, 8, 8)
for n in ('idle', 'fly'): SHEETS[n] = [SHEETS[n][i] for i in HELD]
c2, c3 = clean(close_r[2]), clean(close_r[3])
s = [clean(p) for p in block_r[1:5]]


def settled(rows):
    """The approved wrapped key with these rows removed, everything above them moved down: a small breath of the wings."""
    key = Image.open(HERE / 'key_block.png').convert('RGBA')
    out = Image.new('RGBA', (W, H))
    y_out = H - 1
    for y in range(H - 1, -1, -1):
        if y in rows: continue
        out.paste(key.crop((0, y, W, y + 1)), (0, y_out)); y_out -= 1
    return out


A, B, C = settled(()), settled((28,)), settled((28, 14))
SHEETS['block'] = [c3, A, B, C, B, A, c3]
for n, fr in SHEETS.items():
    for i, f in enumerate(fr): f.save(HERE / f'{n}_{i}.png')
S, G = 3, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 10, H * S * 3), G)
for r, n in enumerate(SHEETS):
    for i, f in enumerate(SHEETS[n]): b.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, r * H * S))
b.save(HERE / 'review.png')
for n, ms in (('idle', 130), ('fly', 130), ('block', 290)):
    big = []
    for f in SHEETS[n]:
        bg = Image.new('RGBA', (W, H), G); bg.alpha_composite(f); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
    big[0].save(HERE / f'{n}.gif', save_all=True, append_images=big[1:], duration=ms, loop=0)
