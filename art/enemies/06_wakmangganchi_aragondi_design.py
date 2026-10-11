"""06 Wakmangganchi Aragondi, giant tier (the Dajna's size; the user, 2026-10-10),
to art/direction/SPRITE_STYLE.md: one view, 8 frames.

    python art/enemies/06_wakmangganchi_aragondi_design.py [FRAME.png [HEADS.png]]
        FRAME: art/enemies/06_wakmangganchi_aragondi_frame.png, the finished first frame
        HEADS: art/enemies/06_wakmangganchi_aragondi_heads.png, which of its pixels are which head
    writes design.json, 06_wakmangganchi_aragondi.txt, draft.png

The mountain-sized boar of Garo legend: seven one-eyed, tusked heads, bamboo
growing on its back, rivers running down it. Its pose is the user's own (set in
Aseprite after their third reference: charging at us, body trailing to the left,
a foreleg raised, the heads crowded round the middle one), its colours the first
reference's (A Book of Creatures). One fixed view, the same for every direction.

The first frame is a drawing in a PNG -- the user's pose with the heads
06_wakmangganchi_aragondi_heads.py set on it, or whatever they make of it next --
and is the whole design: nothing in it is changed here. This script only makes
the other seven frames follow it:
- breathing: everything above the belly sinks a pixel and comes back; the legs
  stand still;
- the heads bob, each on its own beat, two pixels down and back up;
- the bamboo on its back sways, and its tail swings, one sway a loop, their tips
  the most.
Frame 0 is the drawing exactly. Its colours are read from the drawing, so a
colour the user adds needs no change here (the build checks them against the game
palette; a giant may carry up to 24 plus black). HEADS only says which pixels move
together: head i (0 = furthest back) is every pixel whose red is 30 + 30 i.

Then drawn into the .aseprite through the pixel plugin by tools/draw_views.py."""
import json, io, os, sys, math
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = '06_wakmangganchi_aragondi'
W, H, FRAMES = 302, 166, 8                                # the built frame; its top row is empty, so the drawing is rows 1..165
PIVOT = 122                                               # the belly line: above it the body breathes
BODY_DIP = (0, 0, 1, 1, 1, 1, 0, 0)
HEAD_BOB = (0, 1, 2, 2, 1, 0, 0, 0)                       # px a head is down, by frame, before its own lag
LAG = (1, 3, 2, 1, 3, 2, 0)                               # frames each head is behind (0-3, so every head is home on frame 0)
SWAY = 4                                                  # px the tallest bamboo's tips move each way
TAIL_TOP, TAIL_LOW, TAIL_RIGHT, SWING = 100, 140, 50, 5   # the tail hangs free between these rows, left of this column (below it is a hind leg); px its tip swings each way
LETTERS = 'KabcdefghijklmnopqrstuvwxyzABCDEFGHIJ'
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]

def drawing(path):
    """The frame as {pixel: letter}, and the palette {letter: 'rrggbb'} (black is K)."""
    im = Image.open(path).convert('RGBA'); px = im.load()
    assert im.size == (W, H), im.size
    cols = sorted({px[x, y][:3] for y in range(H) for x in range(W) if px[x, y][3]}, key=lambda c: (c != (0, 0, 0), c))
    letter = {c: LETTERS[i] for i, c in enumerate(cols)}
    return ({(x, y): letter[px[x, y][:3]] for y in range(H) for x in range(W) if px[x, y][3]},
            {l: '%02x%02x%02x' % c for c, l in letter.items()})

def heads_of(path, g):
    """[{pixel: letter}] a head, back to front."""
    px = Image.open(path).convert('RGBA').load()
    out = {}
    for (x, y), c in g.items():
        if px[x, y][3]: out.setdefault((px[x, y][0] - 30) // 30, {})[(x, y)] = c
    return [out[i] for i in sorted(out)]

def without(g, heads):
    """The body with the heads lifted off. Behind a head the body carries on (in its commonest colour)
    wherever body lies either side of the gap; where a head stood clear of it there is nothing."""
    gone = {p for h in heads for p in h}
    body = {p: c for p, c in g.items() if p not in gone}
    counts = {}
    for c in body.values():
        if c != 'K': counts[c] = counts.get(c, 0) + 1
    fur = max(counts, key=counts.get)
    def reach(p, dx, dy):
        x, y = p
        while True:
            x, y = x + dx, y + dy
            if not (0 <= x < W and 0 <= y < H): return False
            if (x, y) in gone: continue
            return (x, y) in body
    for p in gone:
        if (reach(p, -1, 0) and reach(p, 1, 0)) or (reach(p, 0, -1) and reach(p, 0, 1)): body[p] = fur
    return body

def crest_of(g, pal):
    """The plants standing free above its back: {pixel: height above the back there}. A plant pixel is a
    green one, or a black one touching green."""
    rgb = {l: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for l, h in pal.items()}
    green = {p for p, c in g.items() if rgb[c][1] > rgb[c][0] + 20 and rgb[c][1] > rgb[c][2]}
    plant = green | {p for p, c in g.items() if c == 'K' and any((p[0] + dx, p[1] + dy) in green for dx, dy in N8)}
    back = {}
    for x in {p[0] for p in plant}:                       # the back: the first pixel under the plants that is not one
        ys = [y for (qx, y) in g if qx == x and (qx, y) not in plant and y > min(py for (px, py) in plant if px == x)]
        back[x] = min(ys) if ys else H
    xs = sorted(back)
    level = {x: sorted(back[q] for q in xs if abs(q - x) <= 8)[len([q for q in xs if abs(q - x) <= 8]) // 2] for x in xs}   # evened out
    return {p: level[p[0]] - p[1] for p in plant if p[1] < level[p[0]]}

def tail_of(g):
    """The free-hanging tail: in each row from TAIL_TOP to TAIL_LOW, the runs of pixels that end left of TAIL_RIGHT."""
    out = set()
    for y in range(TAIL_TOP, TAIL_LOW):
        x = 0
        while x < TAIL_RIGHT + 1:
            if (x, y) in g:
                s = x
                while (x, y) in g: x += 1
                if x - 1 < TAIL_RIGHT: out |= {(q, y) for q in range(s, x)}
            else: x += 1
    return out

def frame(body, heads, crest, tail, f):
    sway = math.sin(math.tau * f / FRAMES)
    tall = max(crest.values()) if crest else 1
    low = max(y for x, y in tail) if tail else TAIL_TOP + 1
    lean = lambda p: (round(SWAY * sway * crest[p] / tall) if p in crest else
                      round(SWING * sway * ((p[1] - TAIL_TOP) / (low - TAIL_TOP)) ** 1.4) if p in tail else 0)
    moved = {p: c for p, c in body.items() if not lean(p)}
    for p in sorted(body):                                # bamboo and tail lean from their roots: nothing there, the most at the tips
        if lean(p): moved.setdefault((p[0] + lean(p), p[1]), body[p])
    d = BODY_DIP[f]; out = {}
    for (x, y), c in moved.items():
        if y < PIVOT - d: out[(x, y + d)] = c
        elif y >= PIVOT: out[(x, y)] = c                  # the row at the pivot is swallowed as it sinks
    for i, head in enumerate(heads):                      # the heads over it, the far ones first, each on its own beat
        dy = HEAD_BOB[(f - LAG[i % len(LAG)]) % FRAMES]
        for (x, y), c in head.items(): out[(x, y + dy)] = c
    return out

rows = lambda g: [''.join(g.get((x, y + 1), '.') for x in range(W)) for y in range(H - 1)] + ['.' * W]   # rows 1..165: build_enemy always leaves the top row empty

if __name__ == '__main__':
    g, PAL = drawing(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, NAME + '_frame.png'))
    heads = heads_of(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, NAME + '_heads.png'), g)
    assert not any(y == 0 for x, y in g), 'the top row must stay empty'
    body = without(g, heads)
    crest, tail = crest_of(body, PAL), tail_of(body)
    gs = [frame(body, heads, crest, tail, f) for f in range(FRAMES)]
    assert gs[0] == g, 'frame 0 must be the drawing exactly'
    json.dump({'pal': PAL, 'view_w': W, 'views': {str(i): rows(q) for i, q in enumerate(gs)}, 'order': [str(i) for i in range(FRAMES)]}, open('design.json', 'w'))
    head = ['#BODY', '90', '#POSE', 'frames', '#DIRS', 'down', '#ROWS']
    t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + head
    for i, q in enumerate(gs): t += ['#D' + (f'@{i}' if i else '')] + rows(q)[:-1]
    io.open(NAME + '.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    im = Image.new('RGBA', (W * 4, H * 2), (0, 0, 0, 255))
    for i, q in enumerate(gs):
        for (x, y), c in q.items():
            if 0 <= x < W and 0 <= y < H: im.putpixel(((i % 4) * W + x, (i // 4) * H + y), tuple(int(PAL[c][j:j + 2], 16) for j in (0, 2, 4)) + (255,))
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save('draft.png')
    out = {p for q in gs for p in q if not (0 <= p[0] < W and 1 <= p[1] < H)}
    assert not out, f'drawn outside the frame: {sorted(out)[:8]}'
    print('heads', len(heads), '| plant pixels that sway', len(crest), '| tail pixels', len(tail), '| colours', len(PAL) - 1, '+ K')
