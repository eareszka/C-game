"""Asp's phase-2 satellite Medusa heads (bullets' contract, 2026-11-18): assets/enemies/21_asp_heads.png, ONE row of
8 square 16x16 frames D DR R UR U UL L DL -- each the head FACING that way (the orbit angle picks it, so they face
outward); no timing. Drawn 2x centred on the head; the face ~11 px across (its hurt radius); shots leave the frame
centre (mouth offsets printed). Hand-drawn in the Asp's palette: a gold face, green snake locks, a red fanged mouth.
D DR R UR U drawn; DL L UL = DR R UR mirrored.
Run: python -B art/enemies/anim/21_asp/heads.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
C = {'.': (0, 0, 0, 0), '#': (0, 0, 0, 255), 'g': (79, 166, 103, 255), 'd': (41, 99, 62, 255),
     'Y': (240, 188, 60, 255), 'o': (193, 138, 57, 255), 'R': (183, 0, 0, 255)}
ART = {
'D': """
...#....#....#..
..#g#..#g#..#g#.
.#gd#.#gd#.#dg#.
.#d#g##dg##g#d#.
#gd#dggddggd#dg#
#d#dYYYYYYYYd#d#
.#dY##YYYY##Yd#.
#gdYY##YY##YYdg#
#d#YR#YYYY#RY#d#
.#dYYYYooYYYYd#.
#gdoY######Yodg#
#d#oo#YRRY#oo#d#
.#.#o#RRRR#o#.#.
..#g#oo##oo#g#..
.#g#..#oo#..#g#.
.#d#...##...#d#.""",
'DR': """
..#....#....#...
.#g#..#g#..#g#..
.#dg##gd#.#dg#..
#gd#dgddg#gd#...
#d#dgddYYYYdd#..
.#gddYYYYYYYYd#.
#gd#Y##YYYY##Y#.
#d#dYY##YY##YY#.
.#gdYR#YYYY#RY#.
#gddoYYYooYYYY#.
#d#doY######YY#.
.#gdo#YRRY#oY#..
#gd#o#RRRR#o#...
#d#.#o####o#....
.#..#ooooo#.....
....#####.......""",
'R': """
..#....#........
.#g#..#g#..#....
.#dg##gd#.#g#...
#gd#dgddg##d#...
#d#dgddddgd##...
.#gddddgYYYYY#..
#gd#dgYYY####Y#.
#d#ddgYYYYYR#YY#
.#gddoYYYYYYYYY#
#gddgoYYYY######
#d#dgoYYY#YRRY#.
.#gddoYYY#RRRR#.
#gd#doYYYY####..
#d#.#ooYYYo#....
.#..#d#ooo#.....
...#g#.###......""",
'UR': """
..#....#....#...
.#g#..#g#..#g#..
.#dg##gd#.#dg#..
#gd#dgddg#gd#...
#d#dgddddgdd#...
.#ddggddggdY#...
#gdgdddggdYY#...
#d#gdgdddgYY#...
.#dgdgddddYo#...
#gdgddggggYo#...
#d#dggddddYo#...
.#.#ddddddo#....
#gd#gddddo#.....
#d#.#ddd#o#.....
.#..######......
................""",
'U': """
...#....#....#..
..#g#..#g#..#g#.
.#gd#.#gd#.#dg#.
.#d#g##dg##g#d#.
#gd#dggddggd#dg#
#d#ddggddggdd#d#
.#dgdddggdddgd#.
#gdgdgddddgdgdg#
#d#gdgddddgdg#d#
.#dgddggggddgd#.
#gddggddddggddg#
#d#.#dddddd#.#d#
.#.#gddddddg#.#.
..#g#dddddd#g#..
.#g#.######.#g#.
.#d#........#d#.""",
}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
N = 16

def grid(s):
    rows = s.strip('\n').split('\n'); assert len(rows) == N and all(len(r) == N for r in rows), [len(r) for r in rows]
    im = Image.new('RGBA', (N, N)); im.putdata([C[c] for r in rows for c in r]); return im

def frames():
    f = {k: grid(v) for k, v in ART.items()}
    f['UL'], f['L'], f['DL'] = pt.mirror(f['UR']), pt.mirror(f['R']), pt.mirror(f['DR'])
    return [f[k] for k in ORDER]

def mouth(fr):
    px = fr.load(); pts = [(x, y) for y in range(N) for x in range(N) if px[x, y] == C['R']]
    if not pts: return None
    return (sum(x for x, _ in pts) / len(pts) + .5 - N / 2) * 2, (sum(y for _, y in pts) / len(pts) + .5 - N / 2) * 2

if __name__ == '__main__':
    fs = frames(); S, gap = 8, 2
    rv = os.path.join(HERE, 'review_heads'); os.makedirs(rv, exist_ok=True)
    board = Image.new('RGBA', (8 * (N + gap) + gap, N + 2 * gap), (24, 24, 32, 255))
    for i, f in enumerate(fs): board.paste(f, (gap + i * (N + gap), gap), f)
    board.resize((board.width * S, board.height * S), Image.NEAREST).save(os.path.join(rv, 'board.png'))
    g = [Image.alpha_composite(Image.new('RGBA', (N, N), (24, 24, 32, 255)), f).convert('RGB').resize((N * S, N * S), Image.NEAREST) for f in fs]
    g[0].save(os.path.join(rv, 'facings.gif'), save_all=True, append_images=g[1:], duration=250, loop=0)
    sheet = Image.new('RGBA', (8 * N, N))
    for i, f in enumerate(fs): sheet.paste(f, (i * N, 0))
    for k, f in zip(ORDER, fs): print(k, 'mouth (screen px from centre)', mouth(f))
    out = os.path.join(ROOT, 'assets/enemies/21_asp_heads.png') if '--install' in sys.argv else os.path.join(rv, 'sheet.png')
    sheet.save(out); print('wrote', out)
