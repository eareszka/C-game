"""Design for the Questing Beast's gallop (assets/enemies/09_questing_beast_walk.aseprite).

    python art/enemies/09_questing_beast_walk_design.py <out.json>
    python tools/draw_views.py <out.json> assets/enemies/09_questing_beast_walk   # through the pixel plugin

Laid out like the idle sheet: one row, 36x31 frames, directions D DR R UR U UL
L DL, four frames each, played in a loop while it gallops side to side in its
first phase. Every frame starts from idle frame 0 of its direction (read from
assets/enemies/09_questing_beast.png), so head, body and tail stay put; only
the four legs are redrawn, swinging from the hip. It only ever gallops left or
right, so R (and L, its mirror) carry the cycle; the other views are idle
frame 0 four times, there to keep the layout the one the battle reads.
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IDLE = os.path.join(HERE, '..', '..', 'assets', 'enemies', '09_questing_beast.png')
PAL = {'K': '000000', 'Y': 'd89830', 'L': 'f4ce80', 'y': '967448', 'D': '3c2412', 'T': 'c18a39',
       't': '876a1f', 'h': '463422', 'G': '29633e', 'g': '4fa667', 'H': '14301f', 'R': 'b70000'}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
FW, FH, N_IDLE = 36, 31, 3

# The legs in the R view: hip column at row HIP_Y, near legs filled T, far t.
HIP_Y, FOOT_Y = 22, 28          # leg rows; the hoof is row 29, its sole row 30
LEGS = {'BN': (7, 'T'), 'BF': (11, 't'), 'FF': (19, 't'), 'FN': (22, 'T')}
# Each frame: how far each foot lands from its hip (+ toward the head).
GALLOP = [
    {'FN':  2, 'FF':  2, 'BN': -2, 'BF': -2},   # stretched: fronts reach, hinds push
    {'FN':  1, 'FF':  0, 'BN': -1, 'BF':  0},   # coming under
    {'FN': -2, 'FF': -2, 'BN':  2, 'BF':  2},   # gathered: fronts under, hinds forward
    {'FN': -1, 'FF':  0, 'BN':  1, 'BF':  0},   # reaching again
]
# Each pair swings together, a gallop's footfall: the front legs stand only
# three apart, so they must never cross.

def idle_frame0(d):
    im = Image.open(IDLE).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    x0 = ORDER.index(d) * N_IDLE * FW
    return [[('.' if im.getpixel((x0 + x, y))[3] == 0 else letter[im.getpixel((x0 + x, y))[:3]])
             for x in range(FW)] for y in range(FH)]

def gallop_frame(pose):
    g = idle_frame0('R')
    # Clear the legs: rows HIP_Y down, from the hind leg to past the front one
    # (the tail, left of x 5, stays; so does the belly tuft at 16, HIP_Y).
    for y in range(HIP_Y, FH):
        for x in range(5, 27):
            if not (y == HIP_Y and x == 16):
                g[y][x] = '.'
    # Far legs first, near over them.
    for name in ('BF', 'FF', 'BN', 'FN'):
        hip, fill = LEGS[name]
        dx = pose[name]
        for y in range(HIP_Y, FOOT_Y + 1):
            x = hip + round(dx * (y - HIP_Y) / (FOOT_Y - HIP_Y))
            g[y][x], g[y][x + 1] = 'K', fill
        x = hip + dx
        g[FOOT_Y + 1][x], g[FOOT_Y + 1][x + 1] = 'K', 'h'
        g[FOOT_Y + 2][x], g[FOOT_Y + 2][x + 1] = 'K', 'K'
    return [''.join(r) for r in g]

def mirror(rows):
    return [r[::-1] for r in rows]

def main(out):
    views, order = {}, []
    side = [gallop_frame(p) for p in GALLOP]
    for d in ORDER:
        for f in range(4):
            key = f'{d}{f}'
            if d == 'R':   rows = side[f]
            elif d == 'L': rows = mirror(side[f])
            else:          rows = [''.join(r) for r in idle_frame0(d)]
            views[key] = rows
            order.append(key)
    json.dump({'pal': PAL, 'view_w': FW, 'order': order, 'views': views}, open(out, 'w'))

if __name__ == '__main__':
    main(sys.argv[1])
