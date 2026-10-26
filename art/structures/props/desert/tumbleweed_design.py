"""The tumbleweed, desert scenery: a ball of dry twigs, and the roll it blows along in.

    python art/structures/props/desert/tumbleweed_design.py

One 16x16 cell, eight frames side by side (128x16), after a PixelLab draft
(pixellab-out/desert-tumbleweed/sprites/v1): a ball of dry twigs in wood's tones (bark reads as a dark burr on the sand)
with twigs standing out all round it and a few bold twigs curling across it.
Frame 0 is the tumbleweed lying still; the eight together are one turn rolling
to the right, 45 degrees a frame, hopping a pixel off the sand on the way.

The ball is defined, not drawn: twigs by their angle round the middle, so each
frame is the same ball laid down again turned, never a picture rotated and
smeared. The light does not turn with it -- lit at the upper left, the lower
right in shade, in every frame. Three tones and black, the objects' rule.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import save

CELL, FRAMES = 16, 8
R = 4.7                                      # the ball
SPIKES = [(0.3, 6.2), (1.2, 5.6), (2.0, 6.3), (2.9, 5.5), (3.7, 6.2), (4.6, 5.8), (5.5, 6.3)]   # angle, reach
CURLS = [(1.0, 2.4, 3.0), (3.7, 2.5, 3.0), (5.6, 1.4, 1.8)]   # an arc of a circle: its centre's angle, distance, radius
HOP = [0, 0, 1, 1, 0, 0, 1, 1]


def frame(k):
    turn = -k * math.pi / 4                  # rolling right turns it clockwise (y is down)
    cx, cy = 7.5, CELL - 2 - R - HOP[k] - 0.5
    g = [['.'] * CELL for _ in range(CELL)]
    body = set()
    for y in range(CELL):
        for x in range(CELL):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if r <= R:
                body.add((x, y))
                # a twig curling across it, turned with the ball
                curl = False
                for a, dist, rad in CURLS:
                    ox, oy = cx + dist * math.cos(a + turn), cy + dist * math.sin(a + turn)
                    if abs(math.hypot(x + 0.5 - ox, y + 0.5 - oy) - rad) < 0.5:
                        curl = True
                lit = (dx + dy) / R
                if curl:
                    c = 'd' if lit > -0.2 else 'm'
                elif lit > 0.45 and r > R - 1.4:
                    c = 'd'                  # the rim turned from the light
                elif lit < -0.55 and r > R - 1.6:
                    c = 'l'                  # the rim toward it
                else:
                    c = 'm'
                g[y][x] = c
    for a, reach in SPIKES:                  # the twigs standing out, turned with the ball
        ang = a + turn
        t = R - 0.5
        while t <= reach:
            x, y = int(cx + t * math.cos(ang)), int(cy + t * math.sin(ang))
            if 1 <= x < CELL - 1 and 1 <= y < CELL - 1 and (x, y) not in body and 2 <= x <= CELL - 3 and 2 <= y <= CELL - 3:
                body.add((x, y))
                g[y][x] = 'd' if math.cos(ang) + math.sin(ang) > 0.9 else 'm'
            t += 0.4
    for x, y in list(body):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body and 0 <= q[0] < CELL and 0 <= q[1] < CELL:
                g[q[1]][q[0]] = 'K'
    assert all(c == '.' for c in g[0] + g[CELL - 1] + [r[0] for r in g] + [r[CELL - 1] for r in g]), f'frame {k}: at the edge'
    return g


if __name__ == '__main__':
    rows = [[] for _ in range(CELL)]
    for k in range(FRAMES):
        f = frame(k)
        save(f, os.path.join(HERE, 'tumbleweed_frames', f'tumbleweed_{k}.png'), 'wood')
        for y in range(CELL):
            rows[y] += f[y]
    save(rows, os.path.join(HERE, 'tumbleweed.png'), 'wood')
