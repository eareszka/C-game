"""Design for Ebigane's flying sheet (assets/enemies/12_ebigane_fly.aseprite).

    python art/enemies/12_ebigane_fly_design.py <out.json>
    python tools/draw_views.py <out.json> assets/enemies/12_ebigane_fly   # through the pixel plugin

Laid out like the idle sheet (one row, 44x41 frames, directions D DR R UR U
UL L DL), four frames a direction -- idle frames 0, 1, 0, 1, so the wings
beat as it flies -- each with the legs drawn up under the body: the top two
rows of the legs stay, the hooves (the sheet's bottom two rows) move up
right under them, and the rest of the legs go. The curled tail in the side
views, left of the legs, is left alone. Played while it flies its
figure-eight in phase 2.
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IDLE = os.path.join(HERE, '..', '..', 'assets', 'enemies', '12_ebigane.png')
PAL = {'K': '000000', 'D': '2b1f40', 'M': '5e486a', 'L': '664b95', 'h': '1e1e24', 'B': 'e8e0c0',
       'w': '531b1c', 'v': 'b6433d', 'n': 'ec8476', 'W': 'fcfcfc', 'r': 'b70000'}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
FW, FH, N_IDLE = 44, 41, 3
FRAMES = [0, 1, 0, 1]
# Per view: the first row of the legs, and the columns they occupy (the side
# views keep their tail, left of x 6; mirrored views keep it right of 37).
LEG_TOP = {'D': 32, 'U': 32, 'DR': 31, 'R': 31, 'UR': 31, 'UL': 31, 'L': 31, 'DL': 31}
COLS = {'D': (0, FW), 'U': (0, FW), 'DR': (6, FW), 'R': (6, FW), 'UR': (6, FW),
        'UL': (0, FW - 6), 'L': (0, FW - 6), 'DL': (0, FW - 6)}

def frame(d, f):
    im = Image.open(IDLE).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    x0 = (ORDER.index(d) * N_IDLE + f) * FW
    return [[('.' if im.getpixel((x0 + x, y))[3] == 0 else letter[im.getpixel((x0 + x, y))[:3]])
             for x in range(FW)] for y in range(FH)]

def tuck(g, d):
    top, (c0, c1) = LEG_TOP[d], COLS[d]
    hooves = [g[FH - 2][c0:c1], g[FH - 1][c0:c1]]
    for y in range(top + 2, FH):
        for x in range(c0, c1):
            g[y][x] = '.'
    for i, row in enumerate(hooves):
        g[top + 2 + i][c0:c1] = row
    return g

def main(out):
    views, order = {}, []
    for d in ORDER:
        for i, f in enumerate(FRAMES):
            key = f'{d}{i}'
            views[key] = [''.join(r) for r in tuck(frame(d, f), d)]
            order.append(key)
    json.dump({'pal': PAL, 'view_w': FW, 'order': order, 'views': views}, open(out, 'w'))

if __name__ == '__main__':
    main(sys.argv[1])
