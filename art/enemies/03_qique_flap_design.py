"""Design for Qique's wing-flap frames (assets/enemies/03_qique_flap.aseprite).

    python art/enemies/03_qique_flap_design.py <out.json>
    python tools/draw_views.py <out.json> assets/enemies/03_qique_flap   # through the pixel plugin

Laid out like the idle sheet: one row, 20x20 frames, directions D DR R UR U UL
L DL, four frames each -- wings up, mid, down, mid -- played in a loop while
Qique flies to its next spot. Every frame starts from idle frame 0 of its
direction (read from assets/enemies/03_qique.png), so the head, body and legs
do not move between the idle and the flap; only the arms are redrawn, beating
from the shoulder (row 9, the arms' height in every view). Down is the idle
arm itself. L, DL, UL mirror R, DR, UR.
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IDLE = os.path.join(HERE, '..', '..', 'assets', 'enemies', '03_qique.png')
PAL = {'K': '000000', 'D': '2b1f40', 'M': '423c70', 'W': 'fcfcfc', 'S': 'c6ccda',
       'C': 'b6433d', 'T': 'fc9838', 'Y': 'f0bc3c', 'P': 'ec8476'}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
N_IDLE = 3                                    # idle frames per direction on the idle sheet

def idle_frame0(d):
    im = Image.open(IDLE).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    x0 = ORDER.index(d) * N_IDLE * 20
    return [[('.' if im.getpixel((x0 + x, y))[3] == 0 else letter[im.getpixel((x0 + x, y))[:3]])
             for x in range(20)] for y in range(20)]

def put(g, x0, y0, rows):
    """Lay rows over g at x0, y0; '.' leaves what is there, '_' clears it."""
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '_': g[y0 + y][x0 + x] = '.'
            elif c != '.': g[y0 + y][x0 + x] = c

def mirror(rows):
    return [r[::-1] for r in rows]

# Per hand-drawn view: what takes the idle arm away (the body's own edge where
# the arm hid it), and the up and mid arms laid over that. Each is (x, y, rows).
# D and U: the left arm; the right is its mirror (x -> 19 - x).
FRONT = {
    'erase': [(0, 9, ['___K', '____K', '____K', '____K', '____K'])],
    'up':    [(0, 4, ['KWKWK',
                      'KTKTK',
                      'KTTKK',
                      'KTKTK',
                      '.KTTK',
                      '..KTT'])],
    'mid':   [(0, 8, ['KKKK',
                      'KWTKT',
                      'KWTKT',
                      'KKKK'])],
}
# Side views: the near wing. Up, it rises as a fan from the shoulder between
# the tail plume and the head, feather tips white; mid, it sweeps back level
# along the top of the body. dy moves it with the view's shoulder.
def side_up(dy):
    return [(4, 2 + dy, ['.KKK',
                         'KWKWK',
                         'KTKTK',
                         'KTKTK',
                         'KTTTK',
                         '.KTTTK',
                         '..KTTTKK',
                         '....KKTTTK',
                         '.......KKK'])]

def side_mid(dy):
    return [(4, 8 + dy, ['..KKKKKKKK',
                         '.KTTTTTTTTK',
                         'KWKTKTKTTTK',
                         'KWKWKKKKKK'])]

VIEWS = {
    'D': FRONT, 'U': FRONT,
    'R': {
        'erase': [(13, 9, ['.__']), (13, 10, ['K____']), (12, 11, ['_______']),
                  (12, 12, ['_______']), (13, 13, ['_____'])],
        'up':    side_up(0),
        'mid':   side_mid(0),
    },
    'UR': {
        'erase': [(13, 9, ['____']), (17, 9, ['_']), (13, 10, ['______']), (12, 11, ['_______']),
                  (12, 12, ['______']), (13, 9, ['K'])],
        'up':    side_up(-1),
        'mid':   side_mid(-1),
    },
    'DR': {
        # the near arm (right) as R; the far one (left) folds away behind the tail when up
        'erase': [(13, 9, ['K____']), (18, 9, ['_']), (2, 10, ['KMMMM']), (13, 10, ['______']),
                  (1, 11, ['_KMMMM']), (13, 11, ['______']), (0, 12, ['___KMM']), (12, 12, ['K____']),
                  (1, 13, ['_'])],
        'up':    side_up(0),
        'mid':   side_mid(0) + [
                  (0, 10, ['KKKK',
                           'KWTT',
                           'KKKK'])],
    },
}

def frames(d):
    """[up, mid, down, mid] for one hand-drawn view."""
    spec, base = VIEWS[d], idle_frame0(d)
    sym = d in ('D', 'U')
    def lay(g, key):
        for x, y, rows in spec[key]:
            put(g, x, y, rows)
            if sym: put(g, 20 - x - max(len(r) for r in rows), y,
                        [r.ljust(max(len(r) for r in rows), '.')[::-1] for r in rows])
    bare = [r[:] for r in base]
    lay(bare, 'erase')
    up, mid = [r[:] for r in bare], [r[:] for r in bare]
    lay(up, 'up'); lay(mid, 'mid')
    return [up, mid, base, mid]

def main(out):
    F = {d: frames(d) for d in ('D', 'DR', 'R', 'UR', 'U')}
    for r, l in (('R', 'L'), ('DR', 'DL'), ('UR', 'UL')):
        F[l] = [[row[::-1] for row in f] for f in F[r]]
    views, order = {}, []
    for d in ORDER:
        for i, f in enumerate(F[d]):
            views[f'{d}{i}'] = [''.join(row) for row in f]
            order.append(f'{d}{i}')
    json.dump({'pal': PAL, 'view_w': 20, 'order': order, 'views': views}, open(out, 'w'))

if __name__ == '__main__':
    main(sys.argv[1])
