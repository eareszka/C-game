"""Design for the Qiqirn's frightened gallop (assets/enemies/17_qiqirn_run.aseprite).

    python art/enemies/17_qiqirn_run_design.py <out.json>
    python tools/draw_views.py <out.json> assets/enemies/17_qiqirn_run   # through the pixel plugin

The Qiqirn is a huge hairless dog that is terrified of people; in its fight
it keeps running to stay across the screen from the player. Laid out like
the idle sheet: one row, 42x34 frames, directions D DR R UR U UL L DL (the
way it runs), four frames each, a seamless loop (the battle's flap path).

Every frame starts from idle frame 0 of its direction (assets/enemies/
17_qiqirn.png), so the hand-drawn body, head and tail stay pixel for pixel;
only the legs move. Its legs are thin strokes, so each pair is leaned whole:
every pixel below the hip row moved sideways in proportion to how far down
the leg it is, a straight slant from the hip to the paw. Side and 3/4 views:
the front and hind pairs swing as a gallop -- stretched (fronts reaching,
hinds pushing), gathering, gathered (bunched under the belly), and airborne,
the whole dog a pixel off the ground. Front and back: the pairs lift in turn.
L, DL, UL mirror R, DR, UR.
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IDLE = os.path.join(HERE, '..', '..', 'assets', 'enemies', '17_qiqirn.png')
PAL = {'K': '000000', 'S': 'f0b890', 's': 'd7a175', 'd': '8d6b4f', 'W': 'fcfcfc', 'L': 'c6ccda', 'P': 'ec8476'}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
FW, FH, N_IDLE, FRAMES = 42, 34, 3, 4
FOOT = FH - 1

# Per view: the row the legs start below, and the leg groups by column --
# (first column, last column, group); the tail's columns are left alone.
GROUPS = {
    'R':  (22, [(10, 20, 'hind'), (21, 31, 'front')]),
    'DR': (22, [(10, 20, 'hind'), (21, 31, 'front')]),
    'UR': (22, [(10, 20, 'hind'), (21, 31, 'front')]),
    'D':  (23, [(0, 20, 'left'), (21, 41, 'right')]),
    'U':  (23, [(0, 18, 'left'), (23, 41, 'right')]),      # the tail hangs down the middle
}
# Per frame: how far (px, at the paw) each group leans -- + toward the head --
# and how far it lifts; and the whole dog's rise off the ground.
GALLOP = [
    ({'front': 4, 'hind': -4}, {}, 0),                    # stretched
    ({'front': 1, 'hind': -1}, {}, 0),                    # gathering
    ({'front': -3, 'hind': 3}, {}, 0),                    # gathered under
    ({'front': 0, 'hind': 0}, {}, 1),                     # airborne
]
TROT = [                                                  # end-on: the pairs lift in turn
    ({}, {'left': 2}, 0),
    ({}, {}, 0),
    ({}, {'right': 2}, 0),
    ({}, {}, 1),
]

def idle_frame0(d):
    im = Image.open(IDLE).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    x0 = ORDER.index(d) * N_IDLE * FW
    return [[('.' if im.getpixel((x0 + x, y))[3] == 0 else letter[im.getpixel((x0 + x, y))[:3]])
             for x in range(FW)] for y in range(FH)]

def running(d, k):
    g = idle_frame0(d)
    top, groups = GROUPS[d]
    lean, lift, rise = (TROT if d in ('D', 'U') else GALLOP)[k]
    out = [r[:] for r in g]
    for y in range(top, FH):                              # lift the legs out ...
        for x0, x1, _ in groups:
            for x in range(x0, x1 + 1): out[y][x] = '.'
    for x0, x1, name in groups:                           # ... and lay them back leaned and lifted
        s, up = lean.get(name, 0), lift.get(name, 0)
        for y in range(top, FH):
            for x in range(x0, x1 + 1):
                c = g[y][x]
                if c == '.': continue
                nx = x + round(s * (y - top) / (FOOT - top))
                ny = y - up
                if ny >= top and 0 <= nx < FW: out[ny][nx] = c
    if rise:                                              # airborne: the whole dog off the ground
        out = out[rise:] + [['.'] * FW for _ in range(rise)]
    return [''.join(r) for r in out]

def main(path):
    F = {d: [running(d, k) for k in range(FRAMES)] for d in ('D', 'DR', 'R', 'UR', 'U')}
    for r, l in (('R', 'L'), ('DR', 'DL'), ('UR', 'UL')):
        F[l] = [[row[::-1] for row in f] for f in F[r]]
    views, order = {}, []
    for d in ORDER:
        for k, f in enumerate(F[d]):
            views[f'{d}{k}'] = f; order.append(f'{d}{k}')
    json.dump({'pal': PAL, 'view_w': FW, 'order': order, 'views': views}, open(path, 'w'))

if __name__ == '__main__':
    main(sys.argv[1])
