"""Roperite on the user's approved FRONT still (2026-11-18: "have the original front sprite I approved" -- the 39x52
3/4 front view, exactly; one view for every direction, as 28 was done). 9 x 260 ms (2.34 s), on the still's own body:
  0 sprint: a bound, all of it 2 px off the ground, the left leg pumped up 5, the rattle shaken left   1 contact (the still)
  2 sprint: the bound again, the right leg pumped up 5, the rattle shaken right
  3 4 5 the rope GROWING (PixelLab animate still -> f-lasso: grow-01 02 03)   6 THE LASSO, fully out (f-lasso)
  7 8 the rope drawn back in (grow-02, grow-01) -> 0
  (the user: "the rope needs more frames between idle and fully expanded to see it actually grow. the legs
   should be more aggressive with running")
Dash (the flap sheet, 4): crouch-stride left kick, airborne, crouch-stride right kick, airborne (by hand).
Ghosts (phase 2's spawners): one row of 13 square cells -- 0-8 the idle, 9-12 the dash -- pale blue-white, baked alpha.
The side cycle the user passed on is build_side.py.
Run: python -B art/enemies/anim/61_roperite/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
PL = os.path.join(HERE, 'pixellab')
MS, LASSO = 260, 6
AT = ((64 - 39) // 2, 64 - 52 - 2)     # the still's place in the 64x64 base (pixellab/base.png)
LEGS_FROM, SPLIT = 36, 19              # still rows from 36 down are the legs; x < 19 the left leg, the rest the right
TIP = (0, 6, 8, 15)                    # the rattle's free part (still px): shaken sideways

def still(): return Image.open(os.path.join(HERE, 'original_sprite.png')).convert('RGBA')

def part(im, keep):
    out = Image.new('RGBA', im.size, pt.CLEAR); s, o = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            if keep(x, y): o[x, y] = s[x, y]
    return out

BROWN = {(129, 84, 35, 255), (88, 53, 24, 255)}

def still_rope():
    """The still's own rope (its loop over the head and the curl at its chest), as a set of still px."""
    s = still(); px = s.load(); W, H = s.size; out = set()
    for y in range(H):
        for x in range(W):
            p = px[x, y]
            if not p[3] or (x <= 8 and 6 <= y <= 18): continue
            if y <= 10 or (11 <= y <= 27 and x >= 32): out.add((x, y)); continue
            if 28 <= y <= 36 and x >= 20 and p not in BROWN:
                if p[:3] == (0, 0, 0) and all(px[x + dx, y + dy] in BROWN or not px[x + dx, y + dy][3]
                                              for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < W and 0 <= y + dy < H): continue
                out.add((x, y))
    return out

def pose(up=0, lift_left=0, lift_right=0, shake=0, rope=True):
    s = still(); W, H = s.size
    R = set() if rope else still_rope()
    top = part(s, lambda x, y: y < LEGS_FROM and not (TIP[0] <= x < TIP[2] and TIP[1] <= y < TIP[3]) and (x, y) not in R)
    tip = part(s, lambda x, y: TIP[0] <= x < TIP[2] and TIP[1] <= y < TIP[3])
    left = part(s, lambda x, y: y >= LEGS_FROM and x < SPLIT and (x, y) not in R); right = part(s, lambda x, y: y >= LEGS_FROM and x >= SPLIT and (x, y) not in R)
    out = Image.new('RGBA', (W, H), pt.CLEAR)
    out.alpha_composite(pt.jolt(left, 0, -lift_left)); out.alpha_composite(pt.jolt(right, 0, -lift_right))
    out.alpha_composite(top); out.alpha_composite(pt.jolt(tip, shake, 0))
    c = Image.new('RGBA', (64, 64), pt.CLEAR); c.alpha_composite(out, (AT[0], AT[1] - up)); return c   # up: the whole bound off the ground

def dash_pose(crouch=0, air=0, lift_left=0, lift_right=0, splay=0, dust=None, lean=0):
    """The dash (the flap sheet): harder than the idle's bound -- a crouch (the body pressed 2 px down over the legs)
    with one leg kicked back up 6 and a dust puff at the planted foot, or airborne 3 px with the legs splayed; the
    rattle tip swept back (up-left) 2 px."""
    s = still(); W, H = s.size
    top = part(s, lambda x, y: y < LEGS_FROM and not (TIP[0] <= x < TIP[2] and TIP[1] <= y < TIP[3]))
    tip = part(s, lambda x, y: TIP[0] <= x < TIP[2] and TIP[1] <= y < TIP[3])
    left = part(s, lambda x, y: y >= LEGS_FROM and x < SPLIT); right = part(s, lambda x, y: y >= LEGS_FROM and x >= SPLIT)
    out = Image.new('RGBA', (W + 8, H + 4), pt.CLEAR); o = (4, 2)
    out.alpha_composite(pt.jolt(left, -splay, -lift_left), o); out.alpha_composite(pt.jolt(right, splay, -lift_right), o)
    upper = Image.new('RGBA', (W, H), pt.CLEAR); upper.alpha_composite(top); upper.alpha_composite(pt.jolt(tip, -2, 0))
    if lean:                        # weaving: the upper body sheared toward the planted leg, lean px at its top
        sh = Image.new('RGBA', (W, H), pt.CLEAR)
        for y in range(H): sh.paste(upper.crop((0, y, W, y + 1)), (round(lean * (LEGS_FROM - y) / LEGS_FROM) if y < LEGS_FROM else 0, y))
        upper = sh
    out.alpha_composite(pt.jolt(upper, 0, crouch), o)
    if dust:                        # a puff kicked up beside the planted foot
        px = out.load(); dx, dy = dust[0] + o[0], H - 2 + o[1]
        PUFF = ['..##..', '.#LL##', '#LttL#', '#tLLt#']   # a dust cloud, outlined
        for y, row in enumerate(PUFF):
            for x, ch in enumerate(row):
                if ch == '.': continue
                X, Y = dx + x - 2, dy + y - 3
                if 0 <= X < out.width and 0 <= Y < out.height and not px[X, Y][3]:
                    px[X, Y] = {'#': (0, 0, 0, 255), 'L': (206, 190, 130, 255), 't': (178, 158, 92, 255)}[ch]
        for x, y, c in ():
            if 0 <= dx + x < out.width and 0 <= dy + y < out.height and not px[dx + x, dy + y][3]:
                px[dx + x, dy + y] = (206, 190, 130, 255) if c else (178, 158, 92, 255)
    c = Image.new('RGBA', (64, 64), pt.CLEAR); c.alpha_composite(out, (AT[0] - o[0], AT[1] - o[1] - air)); return c

DASH = [dict(crouch=2, lift_left=6, dust=(34, 0), lean=2), dict(air=3, lift_left=2, lift_right=2, splay=1),
        dict(crouch=2, lift_right=6, dust=(-2, 0), lean=-2), dict(air=3, lift_left=2, lift_right=2, splay=1)]

def dash_frames(box):
    return [dash_pose(**k).crop(box) for k in DASH]

def rope_of(n):
    """A PixelLab rope frame's rope alone: everything it drew off the still's body (the body = the still minus its
    rope and rattle), plus the tan rope where it crosses the still's brown belly and legs."""
    fr = pl(n); px = fr.load(); s = still(); sp = s.load(); R = still_rope()
    out = Image.new('RGBA', fr.size, pt.CLEAR); o = out.load()
    for y in range(64):
        for x in range(64):
            p = px[x, y]
            if not p[3]: continue
            sx, sy = x - AT[0], y - AT[1]
            inside = 0 <= sx < s.width and 0 <= sy < s.height and sp[sx, sy][3]
            if inside and (sx, sy) in R: o[x, y] = p; continue                     # where its own rope was
            if inside and sx <= 8 and 6 <= sy <= 18: continue                      # the rattle
            if not inside: o[x, y] = p; continue
            if sy >= 28 and sp[sx, sy] in BROWN and p not in BROWN: o[x, y] = p   # the rope across the belly / legs
    # PixelLab's own (moved) rattle is not rope: its red/gold and the black round it go, then any crumbs left
    hp = {(x, y) for y in range(64) for x in range(64) if px[x, y] in ((240, 188, 60, 255), (183, 0, 0, 255))}   # the rattle's gold and red
    for x, y in hp: o[x, y] = pt.CLEAR
    for y in range(64):
        for x in range(64):
            if o[x, y][:3] == (0, 0, 0) and o[x, y][3] and any((x + dx, y + dy) in hp for dx in (-1, 0, 1) for dy in (-1, 0, 1)): o[x, y] = pt.CLEAR
    return drop_crumbs(out, 8)

def drop_crumbs(im, n):
    px = im.load(); seen = set()
    for y in range(im.height):
        for x in range(im.width):
            if not px[x, y][3] or (x, y) in seen: continue
            comp, st = [], [(x, y)]; seen.add((x, y))
            while st:
                c = st.pop(); comp.append(c)
                for q in ((c[0] + dx, c[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    if 0 <= q[0] < im.width and 0 <= q[1] < im.height and q not in seen and px[q][3]: seen.add(q); st.append(q)
            if len(comp) < n:
                for c in comp: px[c] = pt.CLEAR
    return im

WALK = [dict(up=2, lift_left=5, shake=-2), dict(), dict(up=2, lift_right=5, shake=2)]   # f0 f1 f2: bound, contact, bound

def walking_rope(k, n):
    body = pose(rope=False, **WALK[k]); r = rope_of(n); up = WALK[k].get('up', 0)
    out = body.copy(); out.alpha_composite(pt.jolt(r, 0, -up)); return out

def pl(n):
    return pt.tidy(pt.snap(Image.open(os.path.join(PL, n + '.png')), pt.palette_of(os.path.join(HERE, 'original_sprite.png'))))

def frames():
    fs = [pose(**WALK[0]), pose(**WALK[1]), pose(**WALK[2]),            # the user: "always walking or dashing" --
          walking_rope(0, 'grow-01'), walking_rope(1, 'grow-02'), walking_rope(2, 'grow-03'),   # the walk goes on
          walking_rope(0, 'f-lasso'), walking_rope(1, 'grow-02'), walking_rope(2, 'grow-01')]   # under the rope
    bs = [f.getbbox() for f in fs]; box = (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    W, H = box[2] - box[0], box[3] - box[1]; W += W % 2; H += H % 2
    box = (box[0], box[3] - H, box[0] + W, box[3])
    return [f.crop(box) for f in fs], box

def hot(p): return p[3] and p[0] > 170 and p[2] < 110 and abs(p[0] - p[1]) > 60

def ghost(fr):
    out = Image.new('RGBA', fr.size, pt.CLEAR); s, o = fr.load(), out.load()
    for y in range(fr.height):
        for x in range(fr.width):
            p = s[x, y]
            if not p[3]: continue
            if p[:3] == (0, 0, 0): o[x, y] = (70, 90, 140, 190); continue
            l = (p[0] * 3 + p[1] * 6 + p[2]) / 10
            o[x, y] = (int(150 + l * 0.35), int(175 + l * 0.3), 255, 150)
    return out

def ghost_sheet(fs, path):
    W, H = fs[0].size; S = max(W, H)
    sheet = Image.new('RGBA', (S * len(fs), S), pt.CLEAR)
    for i, f in enumerate(fs): sheet.alpha_composite(ghost(f), (i * S + (S - W) // 2, (S - H) // 2))
    sheet.save(path); return S

def gif(fs, ms, path, S=4):
    W, H = fs[0].size
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).convert('RGB').resize((W * S, H * S), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, disposal=2)

if __name__ == '__main__':
    fs, box = frames(); W, H = fs[0].size; gap = 4
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    b = Image.new('RGBA', (len(fs) * (W + gap) + gap, 2 * (H + gap) + gap), (24, 24, 32, 255))
    for i, f in enumerate(fs):
        b.alpha_composite(f, (gap + i * (W + gap), gap)); b.alpha_composite(ghost(f), (gap + i * (W + gap), 2 * gap + H))
    b.resize((b.width * 4, b.height * 4), Image.NEAREST).save(os.path.join(rv, 'front_board.png'))
    gif(fs, MS, os.path.join(rv, 'front_260.gif'))
    ds = dash_frames(box); gif(ds, MS, os.path.join(rv, 'dash_260.gif'))
    db = Image.new('RGBA', (4 * (W + gap) + gap, 2 * (H + gap) + gap), (24, 24, 32, 255))
    for i, f in enumerate(ds): db.alpha_composite(f, (gap + i * (W + gap), gap)); db.alpha_composite(ghost(f), (gap + i * (W + gap), 2 * gap + H))
    db.resize((db.width * 4, db.height * 4), Image.NEAREST).save(os.path.join(rv, 'dash_board.png'))
    off = lambda p: '(%+.0f,%+.0f)' % ((p[0] + .5 - W / 2) * 2, (p[1] + .5 - H / 2) * 2)
    print('frame %dx%d' % (W, H))
    for i, f in enumerate(fs):
        px = f.load(); pts = [(x, y) for y in range(H) for x in range(W) if px[x, y][3]]
        rt = min((p for p in pts if hot(px[p])), key=lambda p: p[1])
        print('f%d rattle tip %s  right-most px %s' % (i, off(rt), off(max(pts, key=lambda p: p[0]))))
    t = os.path.join(rv, 'check.png'); pt.sheet({v: {'i': fs} for v in ('down', 'right', 'up')}, 'i', t, W, H, front_only=True)
    print(*pt.check_frames(t, len(fs), W, H, views=(('D', 0),)), sep=chr(10)); os.remove(t)
    if '--install' in sys.argv:
        pt.sheet({v: {'i': fs} for v in ('down', 'right', 'up')}, 'i', os.path.join(ROOT, 'assets/enemies/redraws/61_roperite.png'), W, H, front_only=True)
        pt.sheet({v: {'i': ds} for v in ('down', 'right', 'up')}, 'i', os.path.join(ROOT, 'assets/enemies/redraws/61_roperite_dash.png'), W, H, front_only=True)
        print('ghost cell', ghost_sheet(fs + ds, os.path.join(ROOT, 'assets/enemies/61_roperite_ghosts.png')), '(0-8 the idle, 9-12 the dash)')
