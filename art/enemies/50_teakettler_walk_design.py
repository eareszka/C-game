"""Design for the Teakettler's backward walk (assets/enemies/50_teakettler_walk.aseprite).

    python art/enemies/50_teakettler_walk_design.py <out.json>
    python tools/draw_views.py <out.json> assets/enemies/50_teakettler_walk   # through the pixel plugin

In its second phase the Teakettler walks backwards away from the player -- by
choice, the lore says -- still facing them. Laid out like the idle sheet: one
row, 32x29 frames, directions D DR R UR U UL L DL, four frames each (a trot,
diagonal pairs of legs together), played in a loop while it backs off
(the battle's flap path, FLAP_FRAMES). Every frame starts from idle frame 0
of its direction (assets/enemies/50_teakettler.png), so the hand-polished
head, body and tail stay pixel for pixel; only the pixels the legs change are
redrawn. Which ones: the dog's skeleton (the Cu Sith's build, its outline the
Teakettler's) is drawn twice, legs at rest and legs mid-step, and the frame
takes the step's pixels wherever the two differ. Backwards: the lifted pair
swings toward the tail, and the planted pair slides toward the head.
L, DL, UL mirror R, DR, UR, as the build does.
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from enemy_shapes import blank, skeleton, YAW, edges

IDLE = os.path.join(HERE, '..', '..', 'assets', 'enemies', '50_teakettler.png')
PAL = {'K': '000000', 'F': '8d6b4f', 'f': '583518', 'L': 'b2966a', 'k': '22140c',
       'P': 'ec8476', 'R': 'b6433d', 'W': 'fcfcfc', 'w': 'c6ccda'}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
FW, FH, N_IDLE = 32, 29, 3
W, H, GROUND, CX, S = 30, 28, 26, 13, 0.6       # the sketch's canvas: frame minus the build's margins

def coat(cells):
    tops = {}
    for (x, y) in cells: tops[x] = min(tops.get(x, 99), y)
    return {(x, y): 'L' if y == tops[x] else 'F' for (x, y) in cells}

def paw(cells):
    at = edges(cells)
    return {(x, y): 'f' if at(x, y) == -1 else 'F' for (x, y) in cells}

# Each frame: per leg (side, front?) how far the foot sits toward the head, in
# body units, and how high it is lifted. A trot: diagonal pairs move together.
# Walking backwards, a planted pair slides toward the head as the body backs
# off, and the lifted pair swings toward the tail -- forward, lifted, back.
A = ((1, True), (-1, False))
B = ((-1, True), (1, False))
def legs(pair_a, pair_b):
    return {**{leg: pair_a for leg in A}, **{leg: pair_b for leg in B}}
STEPS = [
    legs((1.5, 0), (-1.5, 0)),     # A forward, B back
    legs((0, 1.6), (0, 0)),        # A lifted, swinging back; B planted, sliding forward
    legs((-1.5, 0), (1.5, 0)),     # A back, B forward
    legs((0, 0), (0, 1.6)),        # A planted, sliding forward; B lifted, swinging back
]

def pose(walk):
    """The Cu Sith's legs and body (the Teakettler's outline) with the legs
    placed by walk: {(side, front): (dz, lift)}."""
    P = []
    for s in (1, -1):
        for z in (6, -6):
            dz, up = walk.get((s, z > 0), (0, 0))
            k = 1 if z > 0 else 0
            P.append(('tube', [(s * 4.5, 13, z), (s * (5 + k), 7 + up * 0.5, z + 0.5 + dz * 0.5),
                               (s * 4.5, 2.2 + up, z + 0.5 + dz)], (1.5, 1.2), coat))
            P.append(('ball', [(s * 4.5, 1.6 + up, z + 1 + dz)], (1.6, 1.1), paw))
    P.append(('tube', [(0, 15, -7), (0, 15.5, 5)], (5, 8), coat))
    return P

def render(view, walk):
    g = blank(W, H)
    cx = W / 2 if view in ('D', 'U') else CX
    skeleton(g, pose(walk), YAW[view], cx, GROUND, S)
    return g

def idle_frame0(d):
    im = Image.open(IDLE).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    x0 = ORDER.index(d) * N_IDLE * FW
    return [[('.' if im.getpixel((x0 + x, y))[3] == 0 else letter[im.getpixel((x0 + x, y))[:3]])
             for x in range(FW)] for y in range(FH)]

def walk_frame(view, walk):
    g = idle_frame0(view)
    rest, moved = render(view, {}), render(view, walk)
    for y in range(H):
        for x in range(W):
            if rest[y][x] != moved[y][x]:
                g[y + 1][x + 1] = moved[y][x]          # the build's margins: a column each side, a row on top
    return [''.join(r) for r in g]

def main(out):
    F = {v: [walk_frame(v, w) for w in STEPS] for v in ('D', 'DR', 'R', 'UR', 'U')}
    for r, l in (('R', 'L'), ('DR', 'DL'), ('UR', 'UL')):
        F[l] = [[row[::-1] for row in f] for f in F[r]]
    views, order = {}, []
    for d in ORDER:
        for i, f in enumerate(F[d]):
            views[f'{d}{i}'] = f
            order.append(f'{d}{i}')
    json.dump({'pal': PAL, 'view_w': FW, 'order': order, 'views': views}, open(out, 'w'))

if __name__ == '__main__':
    main(sys.argv[1])
