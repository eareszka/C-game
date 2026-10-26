"""Sannaja's turn (its flap sheet) and its head-down idle, built from the approved PixelLab parts.

    python tools/sannaja_turn.py            # writes art/enemies/pixellab/52_sannaja/turn_sheet.png, body_sheet.png, board

The turn: it walks backwards to the right in steps -- legs lift and plant in diagonal pairs, the
body following on each plant, so no foot slides -- then lowers its head into view from above the
battle's visible top edge (canvas row about 51: the frame is drawn 2x about (320,150) and the HUD
covers the top 28 screen rows). Its head-down idle is the legs' own approved idle shifted by the
walk, with the still head over it, so the two sheets join without a pop. Nothing is redrawn: every
pixel is from the PixelLab frames, moved; the outline is closed after.
"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import enemy_sheet

D = os.path.join(ROOT, 'art/enemies/pixellab/52_sannaja')
W, H = 354, 225
BAND = 80                                   # rows above: the body (underside, between-leg dark); below: legs
LEGS = [(6, 90), (121, 198), (213, 272), (287, 353)]   # each leg's columns below the body
LEG_TOP = 12                                # a leg's sprite reaches up to here inside its widened columns (its flesh band)
WIDEN = 8
WALK = 194                                  # how far it backs away (where phase 2's legs stand)
PAIRS = [(3, 1), (2, 0)]                    # diagonal pairs, the rightmost first (walking backwards, right)
LIFT = 6
HEAD_DY = [-150, -110, -70, -38, -14, 0]    # the head layer's offset in its 6 lowering frames (ease out)
VISIBLE_TOP = 51
GREY = {(0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x34, 0x34, 0x3e)}
UNDER = (0x34, 0x34, 0x3e, 255)


def load(name):
    return Image.open(os.path.join(D, name)).convert('RGBA')


def split(frame):
    """frame -> (body, [leg sprites]) -- each a full-canvas image; their union is the frame."""
    px = frame.load()
    body = frame.copy(); bp = body.load()
    legs = []
    for x0, x1 in LEGS:
        leg = Image.new('RGBA', (W, H)); lp = leg.load()
        for y in range(LEG_TOP, H):
            lo, hi = (x0, x1) if y >= BAND else (x0 - WIDEN, x1 + WIDEN)
            for x in range(max(lo, 0), min(hi, W - 1) + 1):
                if px[x, y][3] and (y >= BAND or y >= LEG_TOP):
                    if y >= BAND or _flesh_band(px, x, y):
                        lp[x, y] = px[x, y]
                        bp[x, y] = UNDER if y < BAND else (0, 0, 0, 0)   # behind a band: the body's dark underside
        legs.append(leg)
    return body, legs


def _flesh_band(px, x, y):
    """Above the body line only the leg's red flesh band (and its outline) travels with the leg."""
    c = px[x, y][:3]
    red = c in ((0xb6, 0x43, 0x3d), (0x79, 0x27, 0x27), (0x53, 0x1b, 0x1c))
    return red or (c == (0, 0, 0) and any(0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] and
                                          px[x + dx, y + dy][:3] in ((0xb6, 0x43, 0x3d), (0x79, 0x27, 0x27), (0x53, 0x1b, 0x1c))
                                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))


def place(canvas, layer, dx, dy=0):
    canvas.alpha_composite(layer.crop((max(0, -dx), max(0, -dy), W, H)), (max(0, dx), max(0, dy)))


def front(body):
    """The body's front end, where the walk has carried it in from the left: a rounded, outlined edge."""
    px = body.load()
    box = body.getbbox()
    if not box or box[0] == 0:
        return body
    x0 = box[0]
    for y in range(H):
        cut = x0 + max(0, (y - 40) // 3) if y >= 40 else x0          # the underside curves back under the body
        for x in range(x0, min(cut, W)):
            px[x, y] = (0, 0, 0, 0)
        for x in range(W):
            if px[x, y][3]:
                px[x, y] = (0, 0, 0, 255); break
    return body


def outline(img):
    px = img.load()
    for y in range(H):
        for x in range(W):
            if px[x, y][3] and px[x, y][:3] != (0, 0, 0) and any(
                    0 <= x + dx < W and 0 <= y + dy < H and not px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = (0, 0, 0, 255)
    return img


ROCK = {(0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x34, 0x34, 0x3e)}
FLESH = {(0xb6, 0x43, 0x3d), (0x79, 0x27, 0x27), (0x53, 0x1b, 0x1c)}
CREASES = [((0xb6, 0x43, 0x3d), (0x53, 0x1b, 0x1c)), ((0x84, 0x86, 0x94), (0x34, 0x34, 0x3e))]


def interior_black(img):
    px = img.load()
    op = [(x, y) for y in range(H) for x in range(W) if px[x, y][3]]
    edge = {(x, y) for x, y in op if any(0 <= x + dx < W and 0 <= y + dy < H and not px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    return 100.0 * sum(1 for q in op if q not in edge and px[q][:3] == (0, 0, 0)) / len(op)


def bible(img):
    """The sprite bible's lines: separation lines where rock meets flesh, crease lines in the deepest
    folds until the interior black is in its band (9.35-14.49 %), lone stray pixels merged away."""
    px = img.load()
    def mark(pairs, one_side):
        marks = []
        for y in range(H):
            for x in range(W):
                if not px[x, y][3]:
                    continue
                for dx, dy in ((1, 0), (0, 1)):
                    q = (x + dx, y + dy)
                    if q[0] < W and q[1] < H and px[q][3] and pairs(px[x, y][:3], px[q][:3]):
                        marks.append((x, y) if one_side else q); break
        for q in marks:
            px[q] = (0, 0, 0, 255)
    mark(lambda a, b: (a in ROCK and b in FLESH) or (a in FLESH and b in ROCK), True)
    for light, dark in CREASES:
        if interior_black(img) >= 9.4:
            break
        mark(lambda a, b, l=light, d=dark: (a == l and b == d) or (a == d and b == l), False)
    for y in range(1, H - 1):                                                   # lone pixels: to their neighbours' colour
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] == (0, 0, 0):
                continue
            n = [px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if all(m[3] and m[:3] != c[:3] for m in n):
                px[x, y] = max(n, key=n.count)
    return img


def compose(body, legs, body_dx, leg_dx, leg_dy, head=None, head_dy=0):
    f = Image.new('RGBA', (W, H))
    for i in range(len(legs)):                                        # a lifted leg steps behind: under the body
        if leg_dy[i]:
            place(f, legs[i], leg_dx[i], leg_dy[i])
    b = Image.new('RGBA', (W, H)); place(b, body, body_dx); b = front(b) if body_dx else b
    f.alpha_composite(b)
    for i in range(len(legs)):                                        # a planted leg over it, its flesh band showing
        if not leg_dy[i]:
            place(f, legs[i], leg_dx[i], leg_dy[i])
    if head is not None:
        place(f, head, 0, head_dy)
    return outline(bible(outline(f)))


def head_layer(frame, legs_shifted):
    """The head and neck alone from a head-down frame: what isn't the legs, grey only as the neck's vertebrae."""
    px = frame.load(); lp = legs_shifted.load()
    out = Image.new('RGBA', (W, H)); op = out.load()
    for y in range(H):
        for x in range(232):
            if not px[x, y][3] or lp[x, y][3] and x >= WALK:
                continue
            if px[x, y][:3] in GREY and not (x < 215 and y < 115):
                continue
            op[x, y] = px[x, y]
    # the largest connected piece
    seen, best = set(), set()
    for y in range(H):
        for x in range(W):
            if (x, y) in seen or not op[x, y][3]:
                continue
            st, comp = [(x, y)], set(); seen.add((x, y))
            while st:
                a, b = st.pop(); comp.add((a, b))
                for q in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= q[0] < W and 0 <= q[1] < H and q not in seen and op[q][3]:
                        seen.add(q); st.append(q)
            if len(comp) > len(best):
                best = comp
    clean = Image.new('RGBA', (W, H))
    for q in best:
        clean.putpixel(q, op[q])
    return clean


def main():
    idle = enemy_sheet.cells_of(Image.open(os.path.join(ROOT, 'assets/enemies/redraws/52_sannaja.png')).convert('RGBA'), 8, True)['D']
    body0, legs0 = split(idle[0])
    union = Image.new('RGBA', (W, H)); union.alpha_composite(body0)
    for l in legs0: union.alpha_composite(l)
    assert union.tobytes() == idle[0].tobytes(), 'the split lost pixels'   # legs over body = the frame exactly

    # the walk: per frame, body offset and each leg's (dx, dy)
    stride = WALK / 3
    frames = []
    pos = [0.0] * 4; body_x = 0.0
    for s in range(3):
        for pair in PAIRS:
            lifted = [i for i in pair]
            # lifted, halfway
            dx = [round(pos[i] + (stride / 2 if i in lifted else 0)) for i in range(4)]
            dy = [-LIFT if i in lifted else 0 for i in range(4)]
            frames.append((round(body_x), dx, dy))
            # planted, the body following half a stride
            for i in lifted: pos[i] += stride
            body_x += stride / 2
            frames.append((round(body_x), [round(p) for p in pos], [0] * 4))
    frames[-1] = (WALK, [WALK] * 4, [0] * 4)
    walk = [compose(body0, legs0, bx, dx, dy) for bx, dx, dy in frames]

    # the head: shut-eyed while it lowers, open in the idle
    legs_final = compose(body0, legs0, WALK, [WALK] * 4, [0] * 4)
    shut = head_layer(load('lids_frame0_clean.png'), legs_final)
    body_now = enemy_sheet.cells_of(Image.open(os.path.join(ROOT, 'assets/enemies/redraws/52_sannaja_body.png')).convert('RGBA'), 8, True)['D'][0]
    opened = head_layer(body_now, legs_final)
    lower = [compose(body0, legs0, WALK, [WALK] * 4, [0] * 4, shut, dy) for dy in HEAD_DY]
    turn = walk + lower
    hidden = [f for f, dy in zip(lower, HEAD_DY) if shut.getbbox()[3] + dy <= VISIBLE_TOP]
    print('turn frames', len(turn), '| head still hidden in', len(hidden), 'lowering frame(s)')

    # head-down idle: the legs' idle shifted by the walk, the still head over it
    body_frames = []
    for f in idle:
        b, ls = split(f)
        body_frames.append(compose(b, ls, WALK, [WALK] * 4, [0] * 4, opened, 0))

    enemy_sheet.sheet_of({'D': turn}, True).save(os.path.join(D, 'turn_sheet.png'))
    enemy_sheet.sheet_of({'D': body_frames}, True).save(os.path.join(D, 'body_sheet.png'))
    shut.save(os.path.join(D, 'turn_head_layer.png')); opened.save(os.path.join(D, 'open_head_layer.png'))
    board = Image.new('RGBA', (6 * (W + 4), 4 * (H + 4)), (0, 0, 0, 255))
    for k, f in enumerate(turn + body_frames[:6]):
        board.alpha_composite(f, ((k % 6) * (W + 4), (k // 6) * (H + 4)))
    board.save(os.path.join(D, 'turn_board.png'))
    return turn, body_frames


if __name__ == '__main__':
    main()
