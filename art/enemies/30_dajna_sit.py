"""Dajna's sit: the way down and the seated idle.

    python art/enemies/30_dajna_sit.py assets/enemies/30_dajna.png art/enemies/30_dajna_sat_user_frame.png OUTDIR
        the standing sheet; the seated frame the user finished; where to write
    writes 30_dajna_sit.png  the way down: 4 frames a direction, one row a direction (the flap layout)
           30_dajna_sat.png  seated: 8 idle frames a direction (the alt layout)
    both at the idle's 302x166 frame. Run again whenever either source changes.

The seated frame is the user's (2026-10-10): 30_dajna_seat_first.py set the standing body on the
ground with its near legs folded, and the user redrew the fore leg in Aseprite. It is the pose;
nothing in it is changed here.

The way down (the user: "make 3 sprites transitioning to that pose that makes sense"; asked how,
they chose front first, like a camel, and the seated pose as the 4th frame):
  1  the fore legs give and the chest dips; the rump stays up
  2  kneeling: the chest is down on the folded fore leg, the rump still high, the body tilted
  3  the hind legs give and the rump comes down onto its feet
  4  seated: the user's frame
Frames 1-3 are the standing frame with each column of the body lowered by its own amount -- along
a line from rump to chest, the neck and head by theirs -- so the body tilts without being
redrawn. A leg still standing shortens from its top, going up under the body, and its foot slides
toward where the body is; once the chest is down, everything from the shoulder forward is the
seated frame's own. Nothing goes into the ground: the hair under the belly gives up rows, the
plain ones first, column by column as the belly meets the ground, and the tail lays what would be
below the ground along it (checked: no pixel of the body goes below the frame).

The seated idle (the user: "make idle for the sitting") follows the standing one's: everything
above the folded legs sinks a pixel and comes back as it breathes, the neck and head a frame
behind; the tail, hanging to the ground, sways and draws its end along the ground with it; the
throat fringe sways in the same wind. Frame 0 is the user's frame exactly.

FOR THE FIGHT CODE: seated, the body (pyramid, doorway) is 32 px lower and the head 22; on the way
down the body is lower by WAY's rump..chest amounts along its length, the head by its third number."""
import sys, math
from PIL import Image
W, H, FRAMES = 302, 166, 8
FEET_TOP, LEG_TOP = 154, 134   # standing: the feet are rows FEET_TOP..165; below LEG_TOP a leg hangs free of the body
DROP, NECK_DROP = 32, 22       # px the body, and the neck and head, are down, seated
RUMP, CHEST = 62, 199          # the body tilts between these columns
NECK = (212, 229)              # the neck bends between these columns
WAY = ((0, 14, 10), (2, 32, 22), (20, 32, 22))   # frames 1-3: px down at the rump, at the chest, at the head
BREATH = (0, 0, 1, 1, 1, 1, 0, 0)                 # px the body is down in each idle frame (30_dajna_design.py)
K = (0, 0, 0, 255)

# The four legs of the standing frame, far ones first: (first column, last column) from LEG_TOP
# down, foot included -- where an edge is not one column all the way, the rows that differ -- and
# the px its foot slides along the ground by the time the body is all the way down (+ toward the head).
LEGS = (
    (lambda y: 50, lambda y: 77, 16),                                                                # far hind
    (lambda y: {134: 178, 135: 176, 136: 173, 137: 172}.get(y, 171 if y < 150 else 164),
     lambda y: {134: 184, 135: 185, 136: 186, 137: 188, 138: 189}.get(y, 196), 0),                   # far fore
    (lambda y: 76 if y == 153 else 78, lambda y: 101 if y in (134, 135, 137) or y >= FEET_TOP else 99, 14),   # near hind
    (lambda y: {134: 185, 135: 186, 136: 187, 137: 189, 138: 190}.get(y, 190 if y < 153 else 197), lambda y: 228, -25),   # near fore
)
MIDDLE = (80, 178, 80, 205)                               # the column each leg takes its drop from
HIND, FORE = (0, 2), (1, 3)
HAIR = (100, 177)                                         # the columns of the hair under the belly
HAIR_LOW = 154                                            # its lowest row
HAIR_GIVES = (137, 136, 138, 135, 139, 134, 140) + tuple(range(141, 155))   # the rows it gives up, in order: the plain ones, then its strands from their tops
TAIL = (56, 111)                                          # standing: the tail hangs free left of this column, from this row down
FRONT = (165, 146)                                        # seated: from this column right and this row down is the folded fore leg and the chest on it
# seated idle
PIVOT = 146                                               # above this row the body breathes; the folded legs lie still
NECK_X = 232                                              # from here right is neck and head: it breathes a frame late
TAIL_TOP, TAIL_LAID, TAIL_SWAY = 143, 157, 3              # seated: the tail hangs free from this row; from this row its end lies on the ground; px it sways each way at the ground
FRINGE = ((226, 256), 155, 165, 3)                        # the throat fringe: columns, root row, lowest row, px its tips sway each way

def leg_of(x, y):
    """Which leg a pixel of the standing frame belongs to, or None (the body)."""
    if y < LEG_TOP: return None
    for i in (2, 3, 0, 1):                                # the near legs' edges win where two meet
        if LEGS[i][0](y) <= x <= LEGS[i][1](y): return i
    return None

def drop_at(x, rump, chest, head):
    """How far column x of the body is down."""
    if x >= NECK[1]: return head
    if x > NECK[0]: return chest - round((chest - head) * (x - NECK[0]) / (NECK[1] - NECK[0]))
    return round(rump + (chest - rump) * min(1.0, max(0.0, (x - RUMP) / (CHEST - RUMP))))

def way_down(stand, seat, rump, chest, head):
    """A frame of the way down."""
    src, end = stand.load(), seat.load()
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = out.load()
    drop = lambda x: drop_at(x, rump, chest, head)
    legs = [[] for _ in LEGS]; body = []; tail = {}
    for y in range(H):
        for x in range(W):
            if src[x, y][3]:
                i = leg_of(x, y)
                if i is not None: legs[i].append((x, y))
                elif x <= TAIL[0] and y >= TAIL[1]: tail.setdefault(y, []).append(x)
                else: body.append((x, y))
    down = chest >= DROP                                  # the chest is on the ground: the fore legs are folded
    def leg(i):
        if i in FORE and down: return
        d = drop(MIDDLE[i]); dx = round(LEGS[i][2] * d / DROP)
        for (x, y) in legs[i]:
            if y >= min(LEG_TOP + d, FEET_TOP): px[x + dx, y] = src[x, y]   # its rows from LEG_TOP have gone up under the body; its foot is always there
    for i in (0, 1): leg(i)                               # the far legs behind the body
    for (x, y) in body:
        d = drop(x); up = 0
        if HAIR[0] <= x <= HAIR[1]:
            gave = HAIR_GIVES[:max(0, HAIR_LOW + d - (H - 1))]
            if y in gave: continue                        # a row of hair given up
            up = sum(1 for r in gave if r < y)
        assert y + d - up < H, f'part of the body would go into the ground: {(x, y)}'
        px[x, y + d - up] = src[x, y]
    turn = H - rump                                       # the tail's first row that would be below the ground: from here it lies along it
    for y, xs in tail.items():
        for x in xs:
            if y < turn: px[x, y + rump] = src[x, y]
            else: px[min(tail[turn - 1]) - 1 - (y - turn), (H - 1) - (max(xs) - x)] = src[x, y]
    for i in (2, 3): leg(i)                               # the near legs in front of it
    if down:                                              # from the shoulder forward it is already seated
        for y in range(H):
            for x in range(CHEST + 1, W): px[x, y] = end[x, y]
            if y >= FRONT[1]:
                for x in range(FRONT[0], CHEST + 1): px[x, y] = end[x, y]
    bare = [(x, y) for y in range(LEG_TOP, H) for x in range(W) if px[x, y][3] and px[x, y] != K   # close the outline where colour is left bare, and along the ground
            and (y == H - 1 or any(0 <= x + ax < W and not px[x + ax, y + ay][3] for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))))]
    for p in bare: px[p] = K
    return out

def idle(seat, f):
    """Frame f of the seated idle."""
    g = {(x, y): c for y in range(H) for x in range(W) for c in [seat.getpixel((x, y))] if c[3]}
    sway = math.sin(math.tau * f / FRAMES)
    moved = dict(g)
    tail = [p for p in g if p[0] <= TAIL[0] and p[1] >= TAIL_TOP]
    laid_from = min(x for x, y in tail if y == TAIL_LAID - 1)          # left of the hanging part, the end that lies on the ground
    for p in tail: del moved[p]
    for (x, y) in sorted(tail):                           # the hanging part leans from its root; its end is drawn along the ground with it
        dx = round(TAIL_SWAY * sway * (1.0 if y >= TAIL_LAID and x < laid_from else ((y - TAIL_TOP) / (H - 1 - TAIL_TOP)) ** 1.4))
        moved.setdefault((x + dx, y), g[(x, y)]) if dx else moved.__setitem__((x, y), g[(x, y)])
    (xa, xb), root, low, amp = FRINGE                     # the fringe: each row slides sideways, further the lower it hangs
    hair = {p: moved[p] for p in moved if xa <= p[0] <= xb and root < p[1] <= low}
    shift = {y: round(amp * sway * (y - root) / (low - root)) for y in range(root, low + 1)}
    for p in hair:
        if shift[p[1]]: del moved[p]
    for (x, y), c in hair.items():
        if shift[y]: moved.setdefault((x + shift[y], y), c)
    body, neck = BREATH[f], BREATH[f - 1]
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (x, y), c in moved.items():
        d = neck if x >= NECK_X else body
        if y < PIVOT - d: out.putpixel((x, y + d), c)
        elif y >= PIVOT: out.putpixel((x, y), c)          # the row at the pivot is swallowed as it sinks
    return out

if __name__ == '__main__':
    sheet = Image.open(sys.argv[1]).convert('RGBA'); seat = Image.open(sys.argv[2]).convert('RGBA'); out = sys.argv[3]
    assert seat.size == (W, H), seat.size
    stand = sheet.crop((0, 0, W, H))
    assert way_down(stand, seat, 0, 0, 0).tobytes() == stand.tobytes(), 'standing must come back exactly'
    cols = lambda im: {c for n, c in im.getcolors(1 << 20) if c[3]}
    down = [way_down(stand, seat, *w) for w in WAY] + [seat]
    sat_fr = [idle(seat, f) for f in range(FRAMES)]
    assert sat_fr[0].tobytes() == seat.tobytes(), 'seated frame 0 must be the user\'s frame exactly'
    for im in down + sat_fr: assert cols(im) <= cols(sheet) | cols(seat), 'a colour neither source has'
    sit = Image.new('RGBA', (W * len(down), H * 8), (0, 0, 0, 0)); sat = Image.new('RGBA', (W * FRAMES, H * 8), (0, 0, 0, 0))
    for d in range(8):
        for i, im in enumerate(down): sit.paste(im, (i * W, d * H))
        for f, im in enumerate(sat_fr): sat.paste(im, (f * W, d * H))
    sit.save(out + '/30_dajna_sit.png'); sat.save(out + '/30_dajna_sat.png')
    print('frames down', len(down), '| seated idle', len(sat_fr), '| frames that differ in the idle', len({im.tobytes() for im in sat_fr}))
