"""45 Kusa Kap's views against the bible (the bible checks the user asked of every enemy since 85, 2026-10-29).
The bible's own checker (style_check.py) lives on the sprites worktree, not here, so this runs what the repo has:
first_frame.checks (game palette, eight colours plus black, clear of the canvas sides and top, its height, the
outline closed, interior black against the 9-14% reference), plus binary alpha and specks (a pixel unlike all
eight neighbours: dither and noise; a one-pixel diagonal line is an edge, not a speck; the teeth, single white
pixels, are drawn details and listed apart). Eyes and the chibi head are judged by eye at review.

    python art/enemies/pixellab/85_nanabolele/bible_check.py [files...]
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
import first_frame as ff

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
TEETH = 'ffffff'          # (nothing lone to spare)
files = sys.argv[1:] or ['idle_frame0_clean.png'] + [f'idle_view_{v}.png' for v in ('DR', 'R', 'UR', 'U')]
ok = True
for f in files:
    im = Image.open(HERE / f).convert('RGBA')
    px = im.load()
    alpha = {px[x, y][3] for y in range(im.height) for x in range(im.width)}
    cols = sorted({px[x, y][:3] for y in range(im.height) for x in range(im.width) if px[x, y][3]})
    pal = {('K' if c == (0, 0, 0) else chr(97 + i)): '%02x%02x%02x' % c for i, c in enumerate(cols)}
    inv = {v: k for k, v in pal.items()}
    g = {(x, y): inv['%02x%02x%02x' % px[x, y][:3]] for y in range(im.height) for x in range(im.width) if px[x, y][3]}
    lone = [p for p, c in g.items() if c != 'K' and all(g.get((p[0] + dx, p[1] + dy)) != c for dx, dy in N8)]
    teeth = [p for p in lone if pal[g[p]] == TEETH]
    specks = [p for p in lone if p not in teeth]
    print(f'== {f}')
    try:
        for line in ff.checks(g, pal, im.width, im.height, cap=im.height):
            if 'hue' not in line: print('  ' + line)
    except AssertionError as e:
        print('  FAIL', e); ok = False
    print(f'  alpha: {"binary" if alpha <= {0, 255} else "NOT binary " + str(sorted(alpha))}')
    print(f'  specks: {len(specks)} lone pixels' + (f' {[(p, pal[g[p]]) for p in specks]}' if specks else '') + f'; teeth {len(teeth)}')
    ok &= alpha <= {0, 255}
print('PASS' if ok else 'FAIL')
