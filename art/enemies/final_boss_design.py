"""Design for boss 8, the final boss: the player's consciousness as a planet of
flesh -- every human emotion fused into one mass and crushed round by its own
gravity, hundreds of faces pressed into its surface (user, 2026-10-07; see the
ending notes). Not on the roster yet.

Writes rows of palette letters for one still view: a lit sphere of raw red
flesh, pale faces set into it on a Fibonacci lattice (foreshortened toward the
limb, each with its own expression), hands and loose eyes between them, and a
few arms reaching out past the rim. `--png out.png` previews it with PIL; the
source art is painted through the pixel plugin by tools/draw_views.py into
final_boss_views.aseprite (dump build() as its design json).
"""
import math, random, sys

W, H = 128, 124
CX, CY, R = 63.5, 61.5, 47.0
SEED = 8
LIGHT = (-0.55, -0.6, 0.58)          # upper left, toward the viewer

PAL = {
    'K': '000000',
    # raw flesh, dark to light
    '1': '280000', '2': '421618', '3': '5d1e1f', '4': '792727', '5': 'b6433d', '6': 'ec8476',
    # face skin, sallow to pale
    'a': '463422', 'b': '785830', 'c': 'b2966a', 'd': 'd7a175', 'e': 'f0b890',
    'W': 'e8e0c0',                    # eye whites, teeth
    'T': '5c94fc',                    # tears
    # the true world's greys: what the room turns to as it's hurt
    'v': '282828', 'w': '474751', 'x': '595965', 'y': '848694', 'z': 'a4aaba', 'Z': 'c6ccda',
}
def _lum(h): return 0.3 * int(h[0:2], 16) + 0.59 * int(h[2:4], 16) + 0.11 * int(h[4:6], 16)
GREY = {k: min('Kvwxyz' + 'Z', key=lambda q: abs(_lum(PAL[q]) - _lum(v))) for k, v in PAL.items()}
GREY['e'] = 'z'                   # keep pale skin a step under the eye whites, so stares still read
FLESH = '123456'
SKIN = 'abcde'               # sallow faces
SKIN_PINK = '34566e'          # pinker faces, paler than the raw flesh

def norm(v):
    l = math.sqrt(sum(c * c for c in v)); return tuple(c / l for c in v)
LIGHT = norm(LIGHT)

def lit(nx, ny, nz):
    return max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])

def ramp(ramp_chars, t):
    return ramp_chars[min(len(ramp_chars) - 1, max(0, int(t * len(ramp_chars))))]

# ── face templates: (u, v) in face space, v down, about 7x7 ──
EYES = ('dot', 'dot', 'dot', 'shut', 'wide', 'cry', 'angry')
MOUTHS = ('o', 'smile', 'frown', 'scream', 'flat', 'grin', 'o')

def face_pixel(u, v, eyes, mouth, look=(0, 0)):
    """The letter a face puts at (u, v), or None for plain skin. eyes 'stare'
    = wide open, pupils turned by look (-1..1 across, -1..0 up) -- at the player."""
    iu, iv = round(u), round(v)
    for ex in (-2, 2):
        if eyes == 'stare':
            if (iu, iv) == (ex + look[0], -1 + look[1]): return 'K'
            if ex - 1 <= iu <= ex + 1 and iv in (-2, -1): return 'W'
        elif eyes == 'wide':
            if (iu, iv) == (ex, -1): return 'K'
            if iv in (-2, -1) and iu == ex + (1 if ex < 0 else -1): return 'W'
        elif eyes == 'shut':
            if iv == -1 and iu in (ex, ex + (1 if ex < 0 else -1)): return '2'
        elif eyes == 'angry':
            if (iu, iv) == (ex, -1): return 'K'
            if (iu, iv) == (ex + (1 if ex < 0 else -1), -2): return '2'
        else:
            if (iu, iv) == (ex, -1): return 'K'
            if eyes == 'cry' and iu == ex and iv in (0, 1): return 'T'
    if mouth == 'o' and (iu, iv) in ((0, 2), (-1, 2)): return '1'
    if mouth == 'scream' and iu in (-1, 0) and 1 <= iv <= 3: return '1'
    if mouth == 'smile' and ((iv == 2 and -1 <= iu <= 0) or (iv == 1 and iu in (-2, 1))): return '1'
    if mouth == 'frown' and ((iv == 1 and -1 <= iu <= 0) or (iv == 2 and iu in (-2, 1))): return '1'
    if mouth == 'flat' and iv == 2 and -1 <= iu <= 0: return '3'
    if mouth == 'grin':
        if iv == 2 and -2 <= iu <= 1: return 'W'
        if iv in (1, 3) and -2 <= iu <= 1: return '1'
    return None

def stamp(g, kind, cx, cy, size, eyes, mouth, skin, L, radial=(0.0, 1.0), pz=1.0, look=None):
    """Draw one thing set into the flesh -- a face, a loose eye, or a hand
    pressed flat with its fingers along `radial` -- centred on (cx, cy) at
    light L (a number, or a function of the pixel), squashed along `radial` by the foreshortening pz (1 = seen
    straight on). Only over flesh already drawn (g[y][x] != '.')."""
    H, W = len(g), len(g[0])
    rx, ry = radial
    tx, ty = -ry, rx
    Lf = L if callable(L) else (lambda x, y, L=L: L)
    reach = int(7 * size) + 1
    for y in range(int(cy) - reach, int(cy) + reach + 1):
        for x in range(int(cx) - reach, int(cx) + reach + 1):
            if not (0 <= x < W and 0 <= y < H) or g[y][x] == '.': continue
            dx, dy = x - cx, y - cy
            # Undo the foreshortening (a squash along the radius) so each
            # thing is drawn upright in its own space, then scale it.
            ar = (dx * rx + dy * ry) / max(pz, 0.3)
            at = dx * tx + dy * ty
            ux, uy = (at * tx + ar * rx) / size, (at * ty + ar * ry) / size
            L = Lf(x, y)
            if kind == 'face':
                e = (ux / 3.6) ** 2 + (uy / 3.9) ** 2
                if e > 1.5: continue
                if e > 1.0:                                # pressed-in socket rim
                    g[y][x] = ramp(FLESH, L - 0.4 + 0.25 * (uy < 0)); continue
                c = face_pixel(ux, uy, 'stare' if look else eyes, mouth, look or (0, 0))
                g[y][x] = c if c else ramp(skin, L + 0.1 - 0.08 * uy / 3.9 - 0.05 * ux / 3.6)
            elif kind == 'eye':
                e = (ux / 2.6) ** 2 + (uy / 2.0) ** 2
                if e > 1.5: continue
                if e > 1.0: g[y][x] = ramp(FLESH, L - 0.35); continue
                lx, ly = (look[0] * 1.2, look[1] * 0.9) if look else (0.3, 0)
                g[y][x] = 'K' if abs(ux - lx) < 0.8 and abs(uy - ly) < 0.8 else 'W'
            else:
                ar2, at2 = ar / size, at / size
                palm = (at2 / 2.2) ** 2 + (ar2 / 1.8) ** 2 <= 1
                f = round(at2)
                finger = 1 <= ar2 <= (3.2 if f in (-2, 2) else 4.2) and f in (-2, -1, 1, 2)
                thumb = f == -3 and -1 <= ar2 <= 1
                if palm or finger or thumb:
                    g[y][x] = ramp(skin, L + 0.05)

FRAMES = 8          # giant tier: one idle cycle; it only ever faces the front
def wave(n, amp, lag=0.0): return amp * math.sin(2 * math.pi * n / FRAMES - lag)

GROW_MAX = 2.0      # the pull swells it to twice its size (user, ~30 s)

def canvas(grow=1.0):
    """Frame size for a planet grown by `grow` -- every size is drawn at the
    game's own pixel size, never stretched."""
    return 2 * math.ceil(W * grow / 2), 2 * math.ceil(H * grow / 2)

def build(n=0, grow=1.0):
    """Idle frame n of the planet at `grow` times its size: the mass heaves
    (radius breathes), a share of the faces change expression each frame, the
    arms grasp. Everything on it scales with it -- the faces swell too."""
    rnd = random.Random(SEED)
    W, H = canvas(grow)
    CX, CY = W / 2 - 0.5, H / 2 - 0.5
    Rn = R * grow + wave(n, 1.0)
    g = [['.'] * W for _ in range(H)]
    depth = [[-9.0] * W for _ in range(H)]

    # Lumpy rim: gravity keeps it round, the flesh still bulges.
    lumps = [(rnd.uniform(0, 2 * math.pi), rnd.randint(3, 9), rnd.uniform(0.4, 1.3)) for _ in range(5)]
    def rim(th): return Rn + grow * sum(a * math.sin(k * th + p) for p, k, a in lumps)

    # Flesh: lit sphere, with a mottle so it isn't a smooth ball.
    mott = [(rnd.uniform(0, 6.3), rnd.uniform(0.15, 0.35), rnd.uniform(0, 6.3)) for _ in range(6)]
    for y in range(H):
        for x in range(W):
            dx, dy = x - CX, y - CY
            r = math.hypot(dx, dy)
            if r > rim(math.atan2(dy, dx)): continue
            rr = min(r / Rn, 0.999)
            nz = math.sqrt(1 - rr * rr)
            nx, ny = dx / Rn, dy / Rn
            t = lit(nx, ny, nz) * 0.95 + 0.08
            t += 0.07 * sum(math.sin(x * f + p) * math.cos(y * f + q) for p, f, q in mott) / 3
            g[y][x] = ramp(FLESH, t)
            depth[y][x] = nz

    # Things set into the surface, on a Fibonacci lattice over the sphere --
    # sizes vary, and raw flesh shows between them.
    N = 330
    tilt = 0.35
    golden = math.pi * (3 - math.sqrt(5))
    items = []
    for i in range(N):
        yy = 1 - 2 * (i + 0.5) / N
        rad = math.sqrt(1 - yy * yy)
        th = golden * i
        px, py, pz = math.cos(th) * rad, yy, math.sin(th) * rad
        py, pz = py * math.cos(tilt) - pz * math.sin(tilt), py * math.sin(tilt) + pz * math.cos(tilt)
        k = rnd.random()
        kind = 'hand' if k < 0.07 else 'eye' if k < 0.15 else 'face'
        # each face cycles through its own expressions, changing on its own
        # frames, so the whole surface flickers but loops after FRAMES
        moods = [(rnd.choice(EYES), rnd.choice(MOUTHS)) for _ in range(2)]
        flip = rnd.randrange(FRAMES), rnd.randrange(FRAMES)
        size, skin = grow * rnd.uniform(0.65, 1.15), SKIN_PINK if rnd.random() < 0.6 else SKIN
        if pz < 0.12: continue
        eyes, mouth = moods[1] if min(flip) <= n < max(flip) else moods[0]
        items.append((pz, px, py, kind, eyes, mouth, size, skin))
    items.sort()                                       # far (near the limb) first

    for pz, px, py, kind, eyes, mouth, size, skin in items:
        rl = math.hypot(px, py) or 1.0
        stamp(g, kind, CX + px * Rn, CY + py * Rn, size, eyes, mouth, skin,
              lit(px, py, pz) * 0.95 + 0.08, (px / rl, py / rl), pz)

    # Arms reaching out past the rim -- everything in it still grasping.
    def blob(x, y, r, c):
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                if 0 <= xx < W and 0 <= yy < H and (xx - x) ** 2 + (yy - y) ** 2 <= r * r:
                    if g[yy][xx] == '.' or c != None: g[yy][xx] = c
    for k in range(6):
        th = 2 * math.pi * (k + rnd.uniform(0.2, 0.8)) / 6
        length = grow * (rnd.uniform(6, 10) + wave(n, 1.0, k * 1.3))
        skin = SKIN_PINK if k % 2 else SKIN
        r0 = rim(th) - 3 * grow
        ox, oy = math.cos(th), math.sin(th)
        nxx, nyy = -oy, ox
        s = 0.0
        while s <= length:
            bend = grow * (1.2 * math.sin(s * 0.35 / grow + k) + wave(n, 1.2, k) * s / length)
            t = lit(ox, oy, 0.3) + 0.15
            blob(CX + ox * (r0 + s) + nxx * bend, CY + oy * (r0 + s) + nyy * bend, grow * 1.6 - 0.04 * s, ramp(skin, t))
            s += 0.5
        hx = CX + ox * (r0 + length) + nxx * bend
        hy = CY + oy * (r0 + length) + nyy * bend
        blob(hx, hy, 2.0 * grow, ramp(skin, lit(ox, oy, 0.3) + 0.2))
        for f in (-2, -1, 0, 1):                         # fingers, from the palm's edge
            ang = th + f * 0.35 + 0.17
            fl = grow * (3.0 if f in (-1, 0) else 2.5)
            q = 1.5 * grow
            while q <= 1.5 * grow + fl:
                x, y = round(hx + math.cos(ang) * q), round(hy + math.sin(ang) * q)
                if 0 <= x < W and 0 <= y < H: g[y][x] = ramp(skin, lit(ox, oy, 0.3) + 0.15)
                q += 0.5

    # Black outline around the whole silhouette.
    out = [row[:] for row in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.': continue
            if any(0 <= x + ox < W and 0 <= y + oy < H and g[y + oy][x + ox] not in '.K'
                   for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'K'
    return out

# ── Phase 3: it bursts, and its faces cover the whole room ──
AW, AH = 320, 226          # the arena at the game's pixel size (640x452 drawn at 2x)
BURST = 32                 # frames from the swollen planet to the covered room (user: more, longer)
CRACK = 12                 # ... the first of them: it trembles and splits open, glowing, before it goes
FLASH = 2                  # ... then this many white flash frames

# The room is LAYERS, composited every frame rather than a loop of baked
# frames -- nothing in it repeats:
#   1 flesh     the raw flesh under everything (fixed detail)
#   2 light     a light/dark field that SCROLLS forever across flesh and faces
#               alike (drifts one way while its pattern slowly churns, at rates
#               that never line up, so it never comes round to the same frame)
#   3 faces     the faces, eyes and hands set into the flesh, each changing
#               expression on its own clock (random holds, never a cycle)
#   4 zone      the safe zone hole and the flesh drawn back around it
# (the player, their spinning shots and the burst's chunks go over these.)
LIGHT_DRIFT = (9.0, 4.0)       # art px/s the light field slides across the room
LOOK_ALL = 20.0                # seconds until every eye in the room is on the player

def _room_layout():
    """Layer 3's fixed part: where each thing sits and what it is."""
    rnd = random.Random(SEED + 1)
    things, STEP = [], 15
    for gy in range(-1, AH // STEP + 2):           # a jittered grid: fills the room without lining up
        for gx in range(-1, AW // STEP + 2):
            k = rnd.random()
            things.append(dict(
                x=gx * STEP + (gy % 2) * STEP / 2 + rnd.uniform(-4, 4), y=gy * STEP + rnd.uniform(-4, 4),
                kind='hand' if k < 0.07 else 'eye' if k < 0.17 else 'face',
                size=rnd.uniform(1.25, 1.9), skin=SKIN_PINK if rnd.random() < 0.6 else SKIN,
                ang=rnd.uniform(0, 2 * math.pi),
                hold=rnd.uniform(0.5, 2.5), off=rnd.uniform(0, 10),    # its expression clock
                stare=rnd.uniform(0, LOOK_ALL)))                       # when it turns to watch the player
    return things
ROOM_THINGS = _room_layout()
_mott_rnd = random.Random(SEED + 5)
ROOM_MOTT = [(_mott_rnd.uniform(0, 6.3), _mott_rnd.uniform(0.04, 0.12), _mott_rnd.uniform(0, 6.3),
              _mott_rnd.uniform(0.05, 0.31)) for _ in range(6)]   # phase, frequency, phase, churn rate

def room_light(x, y, sec):
    """Layer 2: light at (x, y) after `sec` seconds -- the field slides by
    LIGHT_DRIFT and each wave churns at its own (unrelated) rate."""
    x, y = x - LIGHT_DRIFT[0] * sec, y - LIGHT_DRIFT[1] * sec
    return 0.45 + 0.2 * sum(math.sin(x * f + p + c * sec) * math.cos(y * f + q - c * 0.7 * sec)
                            for p, f, q, c in ROOM_MOTT) / 3

def room_mood(i, sec):
    """The expression thing i wears at `sec`: held for its own random time,
    then a fresh random pick -- seeded by (thing, hold number), never a loop."""
    t = ROOM_THINGS[i]
    r = random.Random(i * 100003 + int((sec + t['off']) / t['hold']))
    return r.choice(EYES), r.choice(MOUTHS)

_gr = random.Random(SEED + 6)
_GREY_BLOBS = [(_gr.uniform(0, AW), _gr.uniform(0, AH), _gr.uniform(18, 55)) for _ in range(40)]
def _grey_noise(x, y):
    """Fixed blotchy field in 0..1: the order the room greys in -- low where
    a grey blotch starts, so patches open up and spread into each other."""
    d = min(math.hypot(x - bx, y - by) / br for bx, by, br in _GREY_BLOBS)
    return min(1.0, d * 0.5 + 0.08 * math.sin(x * 0.9 + y * 1.3))
_GREY_ORDER = sorted(_grey_noise(x, y) for y in range(0, AH, 3) for x in range(0, AW, 3))
def grey_threshold(damage):
    """Noise level under which the room is grey once `damage` (0..1) of its HP
    is gone -- by rank, so that share of the room is grey."""
    return _GREY_ORDER[min(len(_GREY_ORDER) - 1, int(damage * len(_GREY_ORDER)))] if damage < 1 else 9

def cut_holes(g, circles, grey=False, boxes=()):
    """Layer 4: cut holes out of the flesh -- round ones (x, y, r), the safe
    zone, and square ones (x0, y0, x1, y1), the blocks the player has mined -- each with a black edge and the
    flesh drawn back around it (in grey once the room is grey). Overlapping
    holes merge into one opening, and cutting new holes into a frame that
    already has some never closes them -- so a frozen room can be cut a hole
    at a time."""
    gap = {}
    for x0, y0, x1, y1 in boxes:                       # broken blocks: square holes
        for y in range(max(0, y0 - 6), min(AH, y1 + 6)):
            for x in range(max(0, x0 - 6), min(AW, x1 + 6)):
                ox = max(x0 - x, 0, x - (x1 - 1)); oy = max(y0 - y, 0, y - (y1 - 1))
                d = max(ox, oy) - 0.5 if (ox or oy) else -1    # square corners: tiles meet cleanly
                if d < gap.get((x, y), 9): gap[(x, y)] = d
    for cx, cy, r in circles:
        for y in range(max(0, int(cy - r - 6)), min(AH, int(cy + r + 7))):
            for x in range(max(0, int(cx - r - 6)), min(AW, int(cx + r + 7))):
                d = math.hypot(x - cx, y - cy) - r
                if d < gap.get((x, y), 9): gap[(x, y)] = d
    for (x, y), d in gap.items():
        if g[y][x] == '.': continue                      # ground already open stays open
        if d < 0: g[y][x] = '.'
        elif d < 1: g[y][x] = 'K'
        elif d < 3:                                      # a narrow rim, so a lone standing tile still reads whole
            c = ramp(FLESH, 0.17 + d / 12)               # from one step above the black edge
            g[y][x] = GREY[c] if grey else c

def room(sec=0.0, zone=None, player=None, damage=0.0, frozen_at=None, mined=()):
    """The room covered in flesh and faces, `sec` seconds into it -- the whole
    arena, faces seen straight on and bigger than on the planet. zone =
    (x, y, r): the safe zone (layer 4; the game cuts it at run time).
    player (x, y): one by one, on their own time, the eyes open wide and turn
    to it, until by LOOK_ALL every eye is on the player. damage 0..1: the share
    of its HP gone -- the room drains to the true world's grey in spreading
    patches, all grey at 1. frozen_at: once it's all grey, everything stops
    -- light and faces hold where they were at that time (pass the player's
    position from then, so the stares hold too). mined: the blocks (bx, by)
    the player has broken, cut out like the zone."""
    if frozen_at is not None: sec = min(sec, frozen_at)
    L = lambda x, y: room_light(x, y, sec)
    g = [[ramp(FLESH, L(x, y) + 0.04 * ((x * 7 + y * 13) % 3 == 0)) for x in range(AW)] for y in range(AH)]
    for i, t in enumerate(ROOM_THINGS):
        eyes, mouth = room_mood(i, sec)
        look = None
        if player and sec >= t['stare']:
            dx, dy = player[0] - t['x'], player[1] - t['y']
            d = math.hypot(dx, dy) or 1.0
            look = (round(dx / d), -1 if dy / d < -0.4 else 0)
        stamp(g, t['kind'], t['x'], t['y'], t['size'], eyes, mouth, t['skin'],
              lambda x, y: L(x, y) + 0.1,
              (math.cos(t['ang']), math.sin(t['ang'])) if t['kind'] == 'hand' else (0.0, 1.0), look=look)
    if damage > 0:
        thr = grey_threshold(damage)
        for y in range(AH):
            for x in range(AW):
                if _grey_noise(x, y) <= thr: g[y][x] = GREY[g[y][x]]
    cut_holes(g, [zone] if zone else [], grey=damage >= 1, boxes=[block_box(b) for b in mined])
    return g

# ── After it's all grey: the search through the blob for yourself ──
# The frozen grey blob is MINED like the overworld: it's cut into blocks the
# size of a map tile, the player strikes the block they face with whatever
# they hold, it shakes, and after BLOCK_HP blows it breaks and is open ground
# (the same rules as trees and rocks -- resource_node.cpp node_hit, and the
# shake from tilemap.cpp tilemap_shake_px). Only open ground can be walked.
BLOCK = 16                # art px: one map tile (TILE_SIZE 32 on screen, drawn at 2x)
BLOCK_HP = 2              # blows to break one (a tree takes 3, a rock 4)
SHAKE_T = 0.22            # seconds a struck block shakes (tilemap.cpp JITTER_DUR)
CLONE_AT = 0.9            # share of the room open at which the clone -- the player, eyes 1 wide 2 tall -- is found
BW, BH = AW // BLOCK, AH // BLOCK          # 20 x 14; the bottom row takes the arena's last few px

def shake_px(elapsed):
    """How far across (art px) a block struck `elapsed` seconds ago is drawn:
    tilemap_shake_px's wobble (4 screen px at 2x = 2 art px)."""
    return round(math.sin(elapsed * 80.0) * 2.0) if 0 <= elapsed < SHAKE_T else 0

def blocks_start(zone):
    """The blob as blocks, {(bx, by): hp}: every tile not already inside the
    stopped safe zone (by its middle)."""
    zx, zy, zr = zone
    return {(bx, by): BLOCK_HP for by in range(BH) for bx in range(BW)
            if math.hypot((bx + 0.5) * BLOCK - zx, (by + 0.5) * BLOCK - zy) >= zr}

SWEEP_REACH = 20          # art px: a swing's reach (resource_nodes_try_hit's 40 on screen)
SWEEP_HALF = math.radians(60)   # half the swing's arc (SLASH_SPAN 120 degrees)

def swing_hits(blocks, px, py, ang):
    """The blocks one swing from (px, py) facing `ang` strikes: every standing
    block whose middle is in its reach and arc -- like a sweep through trees,
    it can catch several."""
    out = []
    for b in blocks:
        x0, y0, x1, y1 = block_box(b)
        dx, dy = (x0 + x1) / 2 - px, (y0 + y1) / 2 - py
        if math.hypot(dx, dy) > SWEEP_REACH + BLOCK / 2: continue
        da = (math.atan2(dy, dx) - ang + math.pi) % (2 * math.pi) - math.pi
        if abs(da) <= SWEEP_HALF: out.append(b)
    return out

def frozen_room(zone, player, frozen_at):
    """The room at the freeze, ready to mine: all grey, everything held, and
    the stopped zone opened out to whole tiles (so the blocks around it are
    clean squares)."""
    g = room(frozen_at, zone, player, 1.0, frozen_at=frozen_at)
    standing = blocks_start(zone)
    cut_holes(g, [], grey=True, boxes=[block_box((bx, by)) for by in range(BH) for bx in range(BW)
                                       if (bx, by) not in standing])
    return g

def mine_hit(blocks, b):
    """One blow on block b. Returns True if it broke."""
    if b not in blocks: return False
    blocks[b] -= 1
    if blocks[b] <= 0: del blocks[b]; return True
    return False

def block_box(b):
    return (b[0] * BLOCK, b[1] * BLOCK, AW if b[0] == BW - 1 else (b[0] + 1) * BLOCK,
            AH if b[1] == BH - 1 else (b[1] + 1) * BLOCK)

def open_share(blocks):
    """Share of the room that's open ground (the stopped zone counts)."""
    return 1 - len(blocks) / (BW * BH)

def clone_spot(blocks):
    """Where the clone is found: in the biggest patch of blocks still standing
    -- the last place the player searches -- at the block nearest its middle.
    Returns (block, the patch's blocks), or None until CLONE_AT is open."""
    if open_share(blocks) < CLONE_AT or not blocks: return None
    left, best = set(blocks), []
    while left:                                        # flood fill each patch, keep the biggest
        stack, patch = [left.pop()], []
        while stack:
            x, y = stack.pop(); patch.append((x, y))
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in left: left.remove(n); stack.append(n)
        if len(patch) > len(best): best = patch
    mx, my = sum(p[0] for p in best) / len(best), sum(p[1] for p in best) / len(best)
    return min(best, key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2), best

def burst(k, n=0, sec=0.0):
    """Burst frame k (0..BURST-1), in arena coordinates: the swollen planet
    trembles harder and harder while glowing cracks run out across it from
    the middle (CRACK frames), a white flash, then it tears into chunks --
    each carrying its faces -- that fly out past the walls while the covered
    room splashes out from the middle behind them."""
    planet = build(n, GROW_MAX)
    ph, pw = len(planet), len(planet[0])
    ox, oy = AW / 2 - pw / 2, AH / 2 - ph / 2
    g = [['.'] * AW for _ in range(AH)]
    if k < CRACK:
        c = (k + 1) / CRACK
        rnd = random.Random(SEED + 4)
        shake = round(3 * c) * (1 if k % 2 else -1)       # trembles harder as it goes
        rows = [row[:] for row in planet]
        for _ in range(9):                                 # cracks: jagged lines out from the middle
            a = rnd.uniform(0, 2 * math.pi)
            x, y = pw / 2 + rnd.uniform(-6, 6), ph / 2 + rnd.uniform(-6, 6)
            for step in range(int(R * GROW_MAX * c)):
                a += rnd.uniform(-0.3, 0.3)
                x += math.cos(a); y += math.sin(a)
                X, Y = int(x), int(y)
                if 0 <= X < pw and 0 <= Y < ph and rows[Y][X] not in '.K':
                    rows[Y][X] = 'W' if step < R * GROW_MAX * c - 6 else '6'
                    if c > 0.5 and 0 <= X + 1 < pw and rows[Y][X + 1] not in '.K': rows[Y][X + 1] = '6'   # cracks widen
        for y in range(ph):
            for x in range(pw):
                X, Y = int(x + ox + shake), int(y + oy)
                if rows[y][x] != '.' and 0 <= X < AW and 0 <= Y < AH: g[Y][X] = rows[y][x]
        return g
    if k < CRACK + FLASH:                                  # the flash
        for y in range(ph):
            for x in range(pw):
                X, Y = int(x + ox), int(y + oy)
                if planet[y][x] != '.' and 0 <= X < AW and 0 <= Y < AH:
                    g[Y][X] = 'W' if planet[y][x] != 'K' else 'K'
        return g
    t = (k - CRACK - FLASH + 1) / (BURST - CRACK - FLASH)
    # the room, splashing out from the middle
    rm = room(sec)
    fly = (1 - (1 - t) ** 2) * 260                         # ease out, well past the walls
    reach = fly * 0.8 + 12                                 # the room fills in right behind the chunks
    for y in range(AH):
        for x in range(AW):
            if math.hypot(x - AW / 2, y - AH / 2) < reach: g[y][x] = rm[y][x]
    # the chunks: planet pixels grouped around random seeds, each flung outward
    rnd = random.Random(SEED + 2)
    seeds = []
    while len(seeds) < 36:
        a, r = rnd.uniform(0, 2 * math.pi), R * GROW_MAX * math.sqrt(rnd.random())
        seeds.append((pw / 2 + math.cos(a) * r, ph / 2 + math.sin(a) * r, rnd.uniform(0.8, 1.3)))
    for y in range(ph):
        for x in range(pw):
            c = planet[y][x]
            if c in '.K': continue
            sx, sy, sp = min(seeds, key=lambda q: (q[0] - x) ** 2 + (q[1] - y) ** 2)
            dx, dy = sx - pw / 2, sy - ph / 2
            dl = math.hypot(dx, dy) or 1.0
            if math.hypot(x - sx, y - sy) > 14 * (1 - t) + 4: continue   # chunks shrink as they tear apart
            X = int(x + ox + dx / dl * fly * sp)
            Y = int(y + oy + dy / dl * fly * sp)
            if 0 <= X < AW and 0 <= Y < AH: g[Y][X] = c
    return g

# Where every battle starts the player (battle.cpp: ARENA_W/2, ARENA_H-80 on
# screen, below the 28px HUD) in arena art pixels: the safe zone opens here.
ZONE_START = (320 / 2, (480 - 80 - 28) / 2)
ZONE_MAX = 26             # radius at its biggest: 52 px across (art pixels), what the user approved
ZONE_MIN = 13             # at its smallest: just bigger than the player (20 px tall)
ZONE_PULSE = 8.0          # seconds to shrink to ZONE_MIN and grow back out
ZONE_SPEED = 55.0         # art px/s at ZONE_MAX (~110 on screen, under the 160 walk); slower as it shrinks

def blast_push(k, player):
    """Where the burst carries the player on burst frame k, from wherever
    the pull had dragged them (player, arena px): nothing while it cracks,
    then the blast throws them -- fast, then easing -- to ZONE_START, so they
    land in the safe zone as it opens."""
    if k < CRACK + FLASH: return player
    t = (k - CRACK - FLASH + 1) / (BURST - CRACK - FLASH)
    e = 1 - (1 - t) ** 3
    return (player[0] + (ZONE_START[0] - player[0]) * e, player[1] + (ZONE_START[1] - player[1]) * e)

def zone_path(secs, dt, start=ZONE_START):
    """The safe zone through phase 3, one (x, y, r) per dt: it opens at the
    battle start position, where the burst threw the player (start), shrinks to just over the player's size
    and grows back, again and again, and wanders the room -- fast when it's
    big, slow when it's small (speed in proportion to its radius), turning
    gently and glancing off the walls."""
    rnd = random.Random(SEED + 3)
    x, y = start
    heading = rnd.uniform(0, 2 * math.pi)
    turn = 0.0
    out = []
    for i in range(int(secs / dt)):
        t = i * dt
        r = ZONE_MIN + (ZONE_MAX - ZONE_MIN) * (0.5 + 0.5 * math.cos(2 * math.pi * t / ZONE_PULSE))
        turn = 0.9 * turn + rnd.uniform(-0.6, 0.6) * dt * 10 * 0.1
        heading += turn
        v = ZONE_SPEED * r / ZONE_MAX
        x += math.cos(heading) * v * dt
        y += math.sin(heading) * v * dt
        if not r <= x <= AW - r: heading = math.pi - heading; x = min(max(x, r), AW - r)
        if not r <= y <= AH - r: heading = -heading;          y = min(max(y, r), AH - r)
        out.append((x, y, r))
    return out

def main():
    g = build()
    if len(sys.argv) > 2 and sys.argv[1] == '--png':
        from PIL import Image
        W, H = canvas()
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for y, row in enumerate(g):
            for x, c in enumerate(row):
                if c != '.':
                    h = PAL[c]; im.putpixel((x, y), (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255))
        im.resize((W * 4, H * 4), Image.NEAREST).save(sys.argv[2])
    else:
        print('\n'.join(''.join(r) for r in g))

if __name__ == '__main__':
    main()
