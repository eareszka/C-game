"""Build an enemy sprite from its hand-drawn views.

    python tools/build_enemy.py art/enemies/NN_name.txt assets/enemies [preview.png]

The .txt holds #PAL (letter + hex), #BODY (row the breathing pivots on),
optional #POSE ("breathe", the default, or "splay ROW": legs from ROW down
push outward instead -- frames rest/half/full, played 0 1 2 1; the full pose
may be hand-drawn as R+ DR+ UR+ Dh+ Uh+ at the padded width; or "frames":
all three drawn, frames 1 and 2 as sections R@1 ... U@2, played 0 1 0 2),
optional #PAD
(blank columns added each side to make room for the pose), optional
#DIRS 6 (no D/U drawn; down uses 3/4 front-right, up 3/4 back-right --
same 24-frame layout), optional
#PATCHn X Y [VIEW] sections (pixels drawn onto frame n of every hand-drawn
view, or just VIEW, at X,Y in frame coordinates, mirrored with the view --
for a part that moves on its own, like a tail or a tongue),
and the hand-drawn views: R, DR, UR full width; D and U as left halves (Dh, Uh,
mirrored) or full (D, U). Left-facing views are mirrors of the right ones.

Writes OUTDIR/NN_name.aseprite + .png (24 frames, 8 directions x
rest/inhale/stance in order D DR R UR U UL L DL) and, if asked, an 8x preview with the player beside it for scale
plus an idle-loop .gif next to it.
"""
import sys, os, subprocess
from PIL import Image

ASEPRITE = r"C:\Program Files\Aseprite\Aseprite.exe"
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
HERE = os.path.dirname(os.path.abspath(__file__))

def load(f):
    S = {}; cur = None
    for ln in open(f, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if ln.startswith('#'): cur = ln[1:].strip(); S[cur] = []; continue
        if cur and ln: S[cur].append(ln)
    return S

def views(S, suffix=''):
    """The 8 directions from the hand-drawn sections (`suffix` picks a pose's set, e.g. '+')."""
    pad = '.' * int(S.get('PAD', ['0'])[0])
    side = lambda rows: rows if suffix == '+' else [pad + r + pad for r in rows]
    V = {k: [r + r[::-1] for r in (S[k + 'h' + suffix] if suffix == '+' else [pad + r for r in S[k + 'h' + suffix]])]
         if k + 'h' + suffix in S
         else side(S[k + suffix]) for k in ('D', 'U') if k + 'h' + suffix in S or k + suffix in S}
    for k in ('R', 'DR', 'UR'):
        if k + suffix not in S: continue
        V[k] = side(S[k + suffix])
        V[k.replace('R', 'L')] = [r[::-1] for r in V[k]]
    return V

def poses(g, body):
    """rest, inhale (above-body rows lift 1, body row doubled), stance (drop 1, body row removed).
    Feet rows below `body` never move."""
    blank = '.' * len(g[0]); g = [blank] + g
    b = body + 1
    return [g, g[1:b + 1] + g[b:], [blank] + g[:b] + g[b + 1:]]

def splay(g, legs):
    """Legs (rows from `legs` down) lean outward: each leg -- a run of columns
    that has pixels in the leg rows -- moves k columns away from the legs'
    centre in its k-th row, a clean 45-degree diagonal."""
    rows = g[legs:]
    used = [any(r[x] != '.' for r in rows) for x in range(len(g[0]))]
    runs, x = [], 0
    while x < len(used):
        if used[x]:
            s = x
            while x < len(used) and used[x]: x += 1
            runs.append((s, x))
        x += 1
    mid = (runs[0][0] + runs[-1][1]) / 2
    out = g[:legs]
    for k, r in enumerate(rows):
        row = ['.'] * len(r)
        for s, e in runs:
            d = k if (s + e) / 2 > mid else -k
            for x in range(s, e):
                if r[x] != '.' and 0 <= x + d < len(r): row[x + d] = r[x]
        out.append(''.join(row))
    return out

def splay_poses(g, legs, full=None):
    """rest, legs half out (a 45-degree lean), legs fully out (hand-drawn `full`
    if given). Played rest, half, full, half."""
    blank = '.' * len(g[0]); pad = lambda v: [blank] + v
    g = pad(g)
    return [g, splay(g, legs + 1), pad(full) if full else splay(g, legs + 1)]

GIF_ORDER = {'breathe': (0, 1, 0, 2), 'splay': (0, 1, 2, 1), 'frames': (0, 1, 0, 2)}

def patches(S):
    """{frame: [(x, y, rows, view or None)]} from '#PATCHn X Y [VIEW]' sections."""
    P = {}
    for k, rows in S.items():
        if k.startswith('PATCH'):
            n, x, y, *view = k[5:].split()
            P.setdefault(int(n), []).append((int(x), int(y), rows, view[0] if view else None))
    return P

def paste(g, x0, y0, rows):
    g = list(g)
    for dy, r in enumerate(rows):
        row = list(g[y0 + dy])
        for dx, c in enumerate(r):
            if c != '.': row[x0 + dx] = c
        g[y0 + dy] = ''.join(row)
    return g

def animate(S):
    """{direction: its 3 frames}. Frames are built for the hand-drawn
    directions, patched (#PATCHn: drawn onto frame n), then mirrored for the
    left-facing ones."""
    kind, *arg = S.get('POSE', ['breathe'])[0].split()
    V = views(S)
    base = tuple(d for d in ('D', 'DR', 'R', 'UR', 'U') if d in V)
    if kind == 'breathe':
        A = {d: poses(V[d], int(S['BODY'][0])) for d in base}
    elif kind == 'frames':
        top = lambda g: ['.' * len(g[0])] + g
        F1, F2 = views(S, '@1'), views(S, '@2')
        A = {d: [top(V[d]), top(F1[d]), top(F2[d])] for d in base}
    else:
        F = views(S, '+') if 'R+' in S else {}
        A = {d: splay_poses(V[d], int(arg[0]), F.get(d)) for d in base}
    for n, ps in patches(S).items():
        for d in base:
            for x, y, rows, view in ps:
                if view in (None, d): A[d][n] = paste(A[d][n], x, y, rows)
    for d in ('R', 'DR', 'UR'):
        if d in A: A[d.replace('R', 'L')] = [[r[::-1] for r in g] for g in A[d]]
    if S.get('DIRS', ['8'])[0] == '6':
        # No straight front/back view: down and up reuse the 3/4 views, so the
        # sheet keeps the same 8-direction layout as every other enemy.
        for d, src in SIX_DIR.items(): A[d] = A[src]
    return A

SIX_DIR = {'D': 'DR', 'U': 'UR'}

def build(txt, outdir):
    S = load(txt)
    pal = dict(l.split() for l in S['PAL'])
    A = animate(S)
    fr = [p for d in ORDER for p in A[d]]
    w, h = len(fr[0][0]), len(fr[0])
    bad = [i for i, g in enumerate(fr) if len(g) != h or any(len(r) != w for r in g)]
    assert not bad, f'ragged frames {bad}'
    used = {c for g in fr for r in g for c in r} - {'.'}
    assert used <= pal.keys(), f'letters missing from #PAL: {used - pal.keys()}'

    name = os.path.splitext(os.path.basename(txt))[0]
    grid = os.path.join(outdir, name + '.grid')
    with open(grid, 'w') as fh:
        fh.write(' '.join(f'{k}={v}' for k, v in pal.items()) + '\n')
        for y in range(h): fh.write(''.join(g[y] for g in fr) + '\n')
    ase = os.path.join(outdir, name + '.aseprite')
    subprocess.run([ASEPRITE, '-b', '--script-param', f'grid={grid}', '--script-param', f'out={ase}',
                    '--script', os.path.join(HERE, 'paint_grid.lua')], check=True)
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', os.path.join(outdir, name + '.png')], check=True)
    os.remove(grid)
    return name, w, h, S.get('POSE', ['breathe'])[0].split()[0]

def preview(png, w, h, out, player=None, kind='breathe'):
    """8 rows (directions) x 3 poses at 8x on pink, player sprite beside for scale."""
    im = Image.open(png).convert('RGBA')
    pw = 0
    if player:
        pl = Image.open(player).convert('RGBA').crop((0, 0, 14, 20)); pw = 16
    cv = Image.new('RGBA', (3 * (w + 2) + pw, max(8 * (h + 2), 22)), (255, 170, 200, 255))
    for i in range(24):
        cv.alpha_composite(im.crop((i * w, 0, (i + 1) * w, h)), ((i % 3) * (w + 2) + 1, (i // 3) * (h + 2) + 1))
    if player: cv.alpha_composite(pl, (3 * (w + 2) + 1, 1 + h + 2 - 20 + 1))
    cv.resize((cv.width * 8, cv.height * 8), Image.NEAREST).save(out)
    # Idle loop, all 8 directions in a row.
    gif = []
    for p in GIF_ORDER[kind]:
        row = Image.new('RGBA', (8 * (w + 2), h + 2), (255, 170, 200, 255))
        for d in range(8):
            i = d * 3 + p
            row.alpha_composite(im.crop((i * w, 0, (i + 1) * w, h)), (d * (w + 2) + 1, 1))
        gif.append(row.resize((row.width * 6, row.height * 6), Image.NEAREST).convert('RGB'))
    gif[0].save(os.path.splitext(out)[0] + '.gif', save_all=True, append_images=gif[1:],
                duration=[400, 250, 400, 250], loop=0)

if __name__ == '__main__':
    txt, outdir = sys.argv[1], sys.argv[2]
    name, w, h, kind = build(txt, outdir)
    if len(sys.argv) > 3:
        preview(os.path.join(outdir, name + '.png'), w, h, sys.argv[3], 'assets/player_small.png', kind)
    print(name, w, h)
