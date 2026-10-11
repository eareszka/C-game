"""06 Wakmangganchi Aragondi: make frames 1-7 of the draft follow the user's frame 0.

    python art/enemies/06_wakmangganchi_aragondi_follow.py [FRAME.png]
        FRAME: frame 0 exported from the draft (default 06_wakmangganchi_aragondi_frame.png)
        writes strip.png (8 frames side by side), review.png, zoom.png, loop.gif in the current directory;
        the strip goes into the draft with tools/pack_frames.lua (tags=D:8)

06_wakmangganchi_aragondi_design.py's rules (the body breathes, each head bobs on its own beat, the
bamboo sways, the tail swings), and three the user asked for on 2026-10-10:
- the mouths open and close: a head's jaw comes up, rows of the open mouth closing from the top,
  until its upper and lower teeth meet -- a snap, then open again, each head in its own time;
- the water flows: the light pixels the user set in the rivers run down them, 2 px a frame;
- the bamboo sways further (SWAY px at the tallest tips);
- drool hangs from some mouths (DROOL: the top-left head's, and three others'): a strand from the lower
  lip that lengthens, lets a drop fall and starts again; it rides the jaw and the head.
The two lowest heads (BITERS) bite in the fight (the user, 2026-10-10), so the game draws them as their own
pieces over the body: body_strip.png and 06_sheet.png are the frames without them, 06_bite.png their cells
-- a row a head: its 8 idle frames (bob, snap and drool baked in, so cell f at the head's home is today's
frame f), then mouth wide open, mouth shut, and a length of neck (stretched by the game). strip.png is still the whole creature,
for the draft. The homes and the cell size printed at the end are WakmangganchiAragondi's constants.
Frame 0 is the drawing exactly, plus its drool. The drool is not in FRAME: it is added here, in its own
colour (DROOL_RGB, used for nothing else), so a frame 0 exported from the draft must have those pixels put
back from the FRAME before it is used as the next FRAME."""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image
sp = importlib.util.spec_from_file_location('d', os.path.join(HERE, '06_wakmangganchi_aragondi_design.py')); d = importlib.util.module_from_spec(sp); sp.loader.exec_module(d)
d.SWAY = 6
W, H, FRAMES = d.W, d.H, d.FRAMES
SNAP = (0, 0, 0, 0.5, 1, 0.5, 0, 0)            # how far shut a mouth is, by frame, before its head's own lag
SNAP_LAG = (0, 1, 2, 1, 0, 2, 1)               # 0-2 only: every mouth is open on frame 0
DROOL_RGB = 'c6ccda'                           # pale spit, from the game palette
STRAND = (5, 6, 7, 8, 9, 5, 4, 4)              # px a strand hangs, by frame; at 9 it lets go a drop, which falls for three frames
DROP = {5: 2, 6: 6, 7: 11}                     # ...that far below where the strand ended
DROOL = {0: ((0.15, 0, 0), (0.7, 4, -2)),      # head: (where along the lower lip, frames behind, px shorter) a strand -- the top-left head has two
         3: ((0.25, 2, 0),), 4: ((0.75, 5, -1),), 6: ((0.2, 3, 0), (0.8, 7, -2))}
BITERS = (4, 5)                                # the lower-left and lower-right heads
FLOW, RUN = 2, 16                              # px the water runs a frame; a light that has run RUN px starts again that far up

g, PAL = d.drawing(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '06_wakmangganchi_aragondi_frame.png'))
rgb = {l: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for l, h in PAL.items()}
MOUTH = {l for l, c in rgb.items() if c in ((0x42, 0x16, 0x18), (0xb6, 0x43, 0x3d))}      # inside the mouth, the tongue
BLUE = {l for l, c in rgb.items() if c[2] > c[0] + 60}
PAL['Z'] = DROOL_RGB; rgb['Z'] = tuple(int(DROOL_RGB[i:i + 2], 16) for i in (0, 2, 4))
heads = d.heads_of(os.path.join(HERE, '06_wakmangganchi_aragondi_heads.png'), g)

def jaw_of(head):
    """A head's mouth: the rows that can close (its open rows between the upper teeth and the lower), and the jaw's columns."""
    rows_ = sorted({y for (x, y), c in head.items() if c in MOUTH})
    shut = rows_[2:-1]                                                 # the top two rows hold the upper teeth, the last the lower
    xs = [x for (x, y), c in head.items() if c in MOUTH and y in shut]
    return shut, min(xs) - 3, max(xs) + 3                              # ...out to the jaw's own outline

def snapped(head, k):
    """The head with its mouth k rows shut: those rows gone from the jaw, the jaw below them come up."""
    if not k: return head
    shut, x0, x1 = jaw_of(head)
    gone = set(shut[:k])
    out = {}
    for (x, y), c in head.items():
        if x0 <= x <= x1 and y >= shut[0]:
            if y in gone: continue
            out[(x, y - sum(1 for r in gone if r < y))] = c
        else: out.setdefault((x, y), c)
    seen, best = set(), set()                                          # a scrap the jaw left behind beside it goes with it
    for p in out:
        if p in seen: continue
        comp, todo = {p}, [p]
        while todo:
            x, y = todo.pop()
            for q in ((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                if q in out and q not in comp: comp.add(q); todo.append(q)
        seen |= comp
        if len(comp) > len(best): best = comp
    return {p: out[p] for p in best}

def drooling(head, shut_head, k, strands, f):
    """shut_head (the head with its mouth k rows shut) with its drool for frame f: each strand from the lower lip down."""
    rows_ = sorted({y for (x, y), c in head.items() if c in MOUTH})
    xs = sorted(x for (x, y), c in head.items() if c in MOUTH and y == rows_[-1])
    lip = rows_[-1] + 1 - k                                            # the jaw has come up k rows
    out = dict(shut_head)
    for along, lag, less in strands:
        x = xs[0] + round(along * (xs[-1] - xs[0])); ph = (f - lag) % FRAMES
        n = max(STRAND[ph] + less, 2)
        for y in range(lip, lip + n): out[(x, y)] = 'Z'
        out[(x + 1, lip + n - 1)] = 'Z'; out[(x + 1, lip + n - 2)] = 'Z'             # the bead at its end
        if ph in DROP:
            y0 = lip + 9 + less + DROP[ph]
            for q in ((x, y0), (x, y0 + 1), (x + 1, y0 + 1)): out[q] = 'Z'
    return out

def flowing(body, f):
    """The body with its rivers run on f frames: each river pixel takes the colour that was FLOW * f px up its stream."""
    if not f: return body
    river = {p: c for p, c in body.items() if c in BLUE}
    runs = {}
    for (x, y) in sorted(river, key=lambda p: (p[1], p[0])):
        r = runs.setdefault(y, [])
        if r and r[-1][-1] == x - 1: r[-1].append(x)
        else: r.append([x])
    def run_at(x, y):
        best = min(runs.get(y, []), key=lambda r: abs((r[0] + r[-1]) / 2 - x), default=None)
        return best if best and abs((best[0] + best[-1]) / 2 - x) <= 8 else None
    out = dict(body)
    for (x, y) in river:
        mine = run_at(x, y)
        src = run_at(x, y - FLOW * f) or run_at(x, y - FLOW * f + RUN)
        if src: out[(x, y)] = river[(src[min(x - mine[0], len(src) - 1)], (y - FLOW * f) if run_at(x, y - FLOW * f) else (y - FLOW * f + RUN))]
    return out

body = d.without(g, heads)
for i in BITERS:                                                       # a biter leaves its place: no stray threads of fill where it stood clear of the body
    for _ in range(4):
        thin = [p for p in heads[i] if p in body and sum((p[0] + dx, p[1] + dy) in body for dx, dy in d.N8) < 5]
        for p in thin: del body[p]
crest, tail = d.crest_of(body, PAL), d.tail_of(body)
gs, bodies, cells = [], [], {i: [] for i in BITERS}
for f in range(FRAMES):
    ks = [round(SNAP[(f - SNAP_LAG[i]) % FRAMES] * len(jaw_of(h)[0])) for i, h in enumerate(heads)]
    hs = [drooling(h, snapped(h, k), k, DROOL.get(i, ()), f) for i, (h, k) in enumerate(zip(heads, ks))]
    gs.append(d.frame(flowing(body, f), hs, crest, tail, f))
    bodies.append(d.frame(flowing(body, f), [{} if i in BITERS else h for i, h in enumerate(hs)], crest, tail, f))
    for i in BITERS:
        dy = d.HEAD_BOB[(f - d.LAG[i % len(d.LAG)]) % FRAMES]
        cells[i].append({(x, y + dy): c for (x, y), c in hs[i].items()})
for f in range(FRAMES):                                               # the body with its biters set back on it is the frame, to the pixel
    whole = dict(bodies[f])
    for i in BITERS: whole.update(cells[i][f])
    assert whole == gs[f], f'frame {f}: the body plus its two heads is not the frame'
for i in BITERS: cells[i] += [dict(heads[i]), snapped(heads[i], len(jaw_of(heads[i])[0]))]   # mouth wide open; shut
box = {i: (min(x for q in cells[i] for x, y in q), min(y for q in cells[i] for x, y in q),
           max(x for q in cells[i] for x, y in q), max(y for q in cells[i] for x, y in q)) for i in BITERS}
CW = max(b[2] - b[0] + 1 for b in box.values()); CH = max(b[3] - b[1] + 1 for b in box.values())
bite = Image.new('RGBA', (CW * 11, CH * len(BITERS)), (0, 0, 0, 0))
furs = {}                                                             # (a head's fur, not the body's: that is all but black, and the arena is black)
for c in heads[BITERS[0]].values():
    if c != 'K' and c not in BLUE: furs[c] = furs.get(c, 0) + 1
fur = rgb[max(furs, key=furs.get)]
for r, i in enumerate(BITERS):
    for k, q in enumerate(cells[i]):
        for (x, y), c in q.items(): bite.putpixel((k * CW + x - box[i][0], r * CH + y - box[i][1]), rgb[c] + (255,))
    # The neck (the user: "a neck with the same colour and shading as the rest of the body ... less like a
    # shape"): the body's own three tones -- lit along the top like its back, its fur, shade underneath --
    # thick where it leaves the body (the cell's left) and narrowing to the head, both edges shaggy, each tuft
    # its own size. Its first third has no outline, so it runs into the body with no line across the join.
    # The game stretches the cell from the body out to the head.
    TUFT_TOP = (0, 1, 2, 1, 0, 0, 2, 3, 1, 0, 1, 2, 0, 1, 3, 2, 0, 1, 0, 2, 1)
    TUFT_BOT = (1, 0, 2, 3, 1, 0, 0, 1, 2, 0, 3, 1, 0, 2, 1, 0, 1, 3, 2, 0, 1)
    LIGHT, FUR, SHADE = (0x58, 0x35, 0x18), (0x34, 0x1e, 0x10), (0x22, 0x14, 0x0c)
    for x in range(CW):
        half = 17 - 7 * x / (CW - 1)                                  # 34 rows thick at the body, 20 at the head
        top = round(-half) + TUFT_TOP[(x // 2) % len(TUFT_TOP)]; bot = round(half) - TUFT_BOT[(x // 2) % len(TUFT_BOT)]
        for y in range(top, bot + 1):
            rim = x >= CW // 3 and y in (top, bot)
            tone = (0, 0, 0) if rim else LIGHT if y <= top + 3 else SHADE if y >= bot - (bot - top) // 3 else FUR
            bite.putpixel((10 * CW + x, r * CH + CH // 2 + y), tone + (255,))
# Under the cells, the two necks as the game draws them: NECK_W x CH each, body end on the left, the left
# head's first. The user's own (06_wakmangganchi_aragondi_necks.png, drawn in 06_bite_pose.aseprite and
# taken out by 06_bite_pose.py) if they have drawn them; else the neck cell above stretched to length.
NECK_W = (82, 88)
grid = bite; bite = Image.new('RGBA', (grid.width, CH * (len(BITERS) + 2)), (0, 0, 0, 0)); bite.paste(grid, (0, 0))
own = os.path.join(HERE, '06_wakmangganchi_aragondi_necks.png')
if os.path.exists(own): bite.paste(Image.open(own).convert('RGBA'), (0, len(BITERS) * CH))
else:
    for r in range(len(BITERS)):
        bite.paste(grid.crop((10 * CW, r * CH, 11 * CW, (r + 1) * CH)).resize((NECK_W[r], CH), Image.NEAREST), (0, (len(BITERS) + r) * CH))
bite.save('06_bite.png')
assert {p: c for p, c in gs[0].items() if c != 'Z'}.items() <= g.items(), 'frame 0 must be the drawing, plus its drool'
strip = Image.new('RGBA', (W * 8, H), (0, 0, 0, 0)); lost = 0
for i, q in enumerate(gs):
    for (x, y), c in q.items():
        if 0 <= x < W and 0 <= y < H: strip.putpixel((i * W + x, y), rgb[c] + (255,))
        else: lost += 1
strip.save('strip.png')
sheet = Image.new('RGBA', (W * 8, H * 8), (0, 0, 0, 0))               # the game's sheet: the body, one row a direction (left rows mirrored)
for i, q in enumerate(bodies):
    cell = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (x, y), c in q.items():
        if 0 <= x < W and 0 <= y < H: cell.putpixel((x, y), rgb[c] + (255,))
    for dr in range(8): sheet.paste(cell.transpose(Image.FLIP_LEFT_RIGHT) if dr in (5, 6, 7) else cell, (i * W, dr * H))
sheet.save('06_sheet.png')
rv = Image.new('RGBA', (W * 4, H * 2), (0, 0, 0, 255))
for i in range(8): rv.alpha_composite(strip.crop((i * W, 0, (i + 1) * W, H)), ((i % 4) * W, (i // 4) * H))
rv.resize((rv.width * 2, rv.height * 2), Image.NEAREST).save('review.png')
fr = [strip.crop((i * W, 0, (i + 1) * W, H)) for i in range(8)]
x0, y0, x1, y1 = 60, 20, 180, 125
zm = Image.new('RGBA', ((x1 - x0) * 4, (y1 - y0) * 2), (0, 0, 0, 255))
for i, k in enumerate((0, 3, 4, 5)): zm.alpha_composite(fr[k].crop((x0, y0, x1, y1)), (i * (x1 - x0), 0))
for i, k in enumerate((1, 2, 6, 7)): zm.alpha_composite(fr[k].crop((x0, y0, x1, y1)), (i * (x1 - x0), y1 - y0))
zm.resize((zm.width * 4, zm.height * 4), Image.NEAREST).save('zoom.png')
gif = [Image.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 255)), x).resize((W * 3, H * 3), Image.NEAREST).convert('RGB') for x in fr]
gif[0].save('loop.gif', save_all=True, append_images=gif[1:], duration=250, loop=0)
print('mouth rows that close, by head:', [len(jaw_of(h)[0]) for h in heads], '| river px', sum(1 for c in body.values() if c in BLUE),
      '| pushed off the frame', lost, '| drool px in frame 0:', sum(1 for c in gs[0].values() if c == 'Z'))
print('bite cells', CW, 'x', CH, '| homes (cell top-left, art px):', {i: box[i][:2] for i in BITERS},
      '| a head stands in its cell at', {i: (min(x for x, y in heads[i]) - box[i][0], min(y for x, y in heads[i]) - box[i][1]) for i in BITERS},
      '| its mouth', {i: (sum(x for (x, y), c in heads[i].items() if c in MOUTH) // sum(1 for c in heads[i].values() if c in MOUTH) - box[i][0],
                        sum(y for (x, y), c in heads[i].items() if c in MOUTH) // sum(1 for c in heads[i].values() if c in MOUTH) - box[i][1]) for i in BITERS})
