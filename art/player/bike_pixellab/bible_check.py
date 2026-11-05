"""The bike sheet against the bible, as the enemies' bible_check.py scripts do it. The bible's
own checker (style_check.py) is not in this repo, so this runs what the repo has:
tools/first_frame.checks (game palette, eight colours plus black at most, clear of the canvas
sides and top, within its height, the outline closed, interior black reported), plus binary
alpha and specks (a colour pixel unlike all eight neighbours). Exits 1 on any failure.

    python art/player/bike_pixellab/bible_check.py [sheet.png]
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import first_frame as ff

N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
BODY_TOP = 15
FACINGS = ['down', 'up', 'left', 'right', 'down_left', 'down_right', 'up_left', 'up_right']


def main():
    sheet = Image.open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'assets', 'player_bike.png')).convert('RGBA')
    assert sheet.size == (960, 24), sheet.size
    ok, blacks = True, []
    for i in range(40):
        name = '%s %d' % (FACINGS[i // 5], i % 5)
        im = sheet.crop((i * 24, 0, i * 24 + 24, 24))
        px = im.load()
        alpha = {px[x, y][3] for y in range(24) for x in range(24)}
        cols = sorted({px[x, y][:3] for y in range(24) for x in range(24) if px[x, y][3]})
        pal = {('K' if c == (0, 0, 0) else chr(97 + n)): '%02x%02x%02x' % c for n, c in enumerate(cols)}
        inv = {v: k for k, v in pal.items()}
        g = {(x, y): inv['%02x%02x%02x' % px[x, y][:3]] for y in range(24) for x in range(24) if px[x, y][3]}
        lone = [p for p, c in g.items() if c != 'K' and all(g.get((p[0] + dx, p[1] + dy)) != c for dx, dy in N8)]
        top = BODY_TOP + (1 if i % 5 in (2, 4) else 0)         # the bounce: the rider a pixel lower
        specks = [p for p in lone if p[1] >= top]              # rows above are the walk's own head: drawn details
        try:
            lines = ff.checks(g, pal, 24, 24, cap=24)
            blacks.append([l for l in lines if l.startswith('interior black')][0])
        except AssertionError as e:
            print('FAIL', name, e); ok = False
        if alpha - {0, 255}:
            print('FAIL', name, 'alpha not binary', sorted(alpha)); ok = False
        if specks:
            print('FAIL', name, 'specks', specks); ok = False
    print('colours used across the sheet:', len({sheet.getpixel((x, y))[:3] for x in range(960) for y in range(24) if sheet.getpixel((x, y))[3]}))
    if blacks: print(blacks[0], '... (frame 0; reported, not a pass/fail rule)')
    print('PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
