"""Sannaja at half size (177x113): one model, the same pixels in every frame.

    python tools/sannaja_half.py body [--generate] [--try N]     # the master body: six attached legs, no neck or head
    python tools/sannaja_half.py head                            # the master head (void eyes, shut variant) from the stage-2 key
    python tools/sannaja_half.py sheet                           # the model sheet board

The user upscales the finished frames with another tool. Every frame reuses the master body's and
master head's exact pixels; PixelLab draws only what changes (the neck, the steps). Paid calls only
with --generate.
"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import pixellab_enemy as pe
import sannaja_redraw as sr

pe.ESTIMATE['inpaint'] = 30
D = os.path.join(ROOT, 'art/enemies/pixellab/52_sannaja/half')
W, H = 177, 113
K = (0, 0, 0)
LIGHT, MID, DARK = (0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x34, 0x34, 0x3e)
FLESH = {(0xb6, 0x43, 0x3d), (0x79, 0x27, 0x27), (0x53, 0x1b, 0x1c)}
FOOT_ROWS = range(98, 108)

BODY_PROMPT = """Redraw this as the body of enemy 52 Sannaja, a colossal living mountain, exactly 177x113 pixels, transparent background, in the same place and size as the guide, with NO neck and NO head. Huge slabs of grey rock with small snowy peaks along the back, bound together by seams of red flesh. Exactly SIX thick cracked stone-pillar legs standing on the ground: three near legs in light grey rock, evenly spaced, and three far legs in darker grey rock, each partly behind and between the near legs, all six feet on the same ground line. Every leg is attached: the top of each leg sits inside a wide band of red flesh that is fused to the underside of the rock body, no gap, no floating legs. The front of the body (left) is a closed, rounded rock shoulder with a round socket of red flesh high on it where a neck will grow. Side view facing left.
Pixel art like the reference: big simple flat-toned shapes, dark/mid/light ramps placed by form, a one-pixel black outline, thin black separation lines where parts overlap, no gradients, dithering, hatching or texture, only the reference's colours."""


def palette():
    return sorted({p[:3] for p in Image.open(os.path.join(D, 'lower_frame0_clean.png')).convert('RGBA').getdata() if p[3]})


def outline(img):
    px = img.load(); w, h = img.size
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and px[x, y][:3] != K and any(
                    not (0 <= x + dx < w and 0 <= y + dy < h) or not px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = K + (255,)
    return img


def tidy(img):
    """Lone pixels to their neighbours' colour, then the outline closed."""
    px = img.load(); w, h = img.size
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = px[x, y]
            if not c[3] or c[:3] == K:
                continue
            n = [px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if all(m[3] and m[:3] != c[:3] for m in n):
                px[x, y] = max(n, key=n.count)
    return outline(img)


def legs(img):
    """(near, far): column runs in the foot rows whose rock is mostly light/mid (near) or dark (far)."""
    px = img.load(); cols = []
    for x in range(W):
        c = [px[x, y][:3] for y in FOOT_ROWS if px[x, y][3] and px[x, y][:3] != K]
        if len(c) >= 4:
            cols.append((x, 'far' if sum(q == DARK for q in c) > len(c) / 2 else 'near'))
    runs = []
    for x, kind in cols:
        if runs and x <= runs[-1][1] + 1 and kind == runs[-1][2]:
            runs[-1][1] = x
        else:
            runs.append([x, x, kind])
    runs = [r for r in runs if r[1] - r[0] >= 2]            # a leg is at least 3 columns wide
    return sum(r[2] == 'near' for r in runs), sum(r[2] == 'far' for r in runs), runs


def pieces(img):
    """Sizes of the 4-connected opaque pieces, largest first."""
    px = img.load(); seen = set(); out = []
    for y in range(H):
        for x in range(W):
            if (x, y) in seen or not px[x, y][3]:
                continue
            st = [(x, y)]; seen.add((x, y)); n = 0
            while st:
                a, b = st.pop(); n += 1
                for q in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= q[0] < W and 0 <= q[1] < H and q not in seen and px[q][3]:
                        seen.add(q); st.append(q)
            out.append(n)
    return sorted(out, reverse=True)


def gates(img):
    near, far, runs = legs(img)
    p = pieces(img)
    n, off, ib, iso, o = sr.bible_numbers(img)
    checks = {'6 legs': near + far == 6, 'one piece': len(p) == 1 or sum(p[1:]) <= 3, 'colours<=9': n <= 9, 'on palette': off == 0,
              'outline': o > 0.999, 'interior 9.35-14.49': 9.35 <= ib <= 14.49, 'isolated<1%': iso < 1.0}
    return checks, {'near': near, 'far': far, 'legs': [tuple(r) for r in runs], 'pieces': p[:4], 'interior': round(ib, 2), 'isolated': round(iso, 2)}


def body_job():
    Image.new('RGBA', (W, H * 8)).save(os.path.join(D, 'cell.png'))
    Image.open(os.path.join(D, 'master_body.png')).save(os.path.join(D, 'source_body.png'))
    with open(os.path.join(D, 'prompt_body.txt'), 'w', encoding='utf-8') as fh:
        fh.write(BODY_PROMPT)
    cfg = json.load(open(os.path.join(D, 'job.json')))
    cfg['prompts']['body'] = 'prompt_body.txt'
    cfg['sheets']['body'] = cfg['sheets']['lower'] | {'from': 'lower'}       # style: the stage-2 key (the chosen face's frame)
    json.dump(cfg, open(os.path.join(D, 'job.json'), 'w'), indent=2)
    return pe.Job(os.path.join(D, 'job.json'))


def body(generate, first):
    j = body_job()
    pal = palette()
    for attempt in range(first, first + 3):
        pe.edit(j, 'body', generate, attempt)
        if not generate:
            return
        draft = Image.open(os.path.join(D, 'body_frame0_draft.png')).convert('RGBA')
        c = tidy(pe.despeckled(pe.to_palette(draft, pal), 6))
        c.save(os.path.join(D, f'body_try{attempt}_clean.png'))
        checks, nums = gates(c)
        ok = all(checks.values())
        print('body try', attempt, 'ok' if ok else 'FAIL', nums, [k for k, v in checks.items() if not v], flush=True)
        if ok:
            c.save(os.path.join(D, 'master_body_clean.png'))
            return c
    raise SystemExit('body: three tries failed -- stopping for review')



# -- key frames: the master body and head placed, only the neck drawn --------------------------------
SOCKET = (44, 50)                      # the flesh socket on the body's shoulder (master-body coords)
KEYS = {                               # body dx; head dx, dy; head-back point the neck reaches (frame coords)
    'stand': {'body': -11, 'head': (-11, -62), 'nape': (36, 8)},
    'lower': {'body': 8, 'head': (0, 0), 'nape': (40, 70)},
}
NECK_PROMPT = """A thick neck of red flesh with a ridge of grey stone vertebrae along its top, growing out of the red flesh socket on the rock shoulder and joining the back of the head, part of enemy 52 Sannaja, a colossal living mountain of grey rock bound by red flesh. Match the existing colours and style exactly: flat dark/mid/light ramps, one-pixel black outline, thin black separation lines, no gradients or dithering. No extra heads, faces, eyes or legs."""


def shifted(im, dx, dy=0):
    out = Image.new('RGBA', (W, H))
    out.alpha_composite(im.crop((max(0, -dx), max(0, -dy), W - max(0, dx), H - max(0, dy))), (max(0, dx), max(0, dy)))
    return out


def key(name, generate, head_file='master_head.png'):
    k = KEYS[name]
    body = shifted(Image.open(os.path.join(D, 'master_body_clean.png')).convert('RGBA'), k['body'])
    head = shifted(Image.open(os.path.join(D, head_file)).convert('RGBA'), *k['head'])
    base = body.copy(); base.alpha_composite(head)
    sock = (SOCKET[0] + k['body'], SOCKET[1])
    mask = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mask)
    d.line([sock, k['nape']], fill=255, width=16)
    d.ellipse((sock[0] - 9, sock[1] - 9, sock[0] + 9, sock[1] + 9), fill=255)
    hp, mp = head.load(), mask.load()
    for y in range(H):
        for x in range(W):
            if hp[x, y][3]:
                mp[x, y] = 0                                   # the head is kept exactly
    src = os.path.join(D, f'{name}_neck_src.png'); msk = os.path.join(D, f'{name}_neck_mask.png')
    base.save(src); mask.save(msk)
    j = pe.Job(os.path.join(D, 'job.json'))
    r = pe.call(j, f'{name}-neck', ['inpaint', src, '--mask', msk, '--prompt', NECK_PROMPT, '--transparent', '--keep-canvas',
                                     '--name', f'52-sannaja-half-{name}-neck'], generate)
    if not r:
        return None
    neck = pe.to_palette(Image.open(pe.pngs(r)[0]).convert('RGBA'), palette())
    out = base.copy(); out.paste(neck, (0, 0), mask)
    out.alpha_composite(head)                                  # the head over its neck
    out = tidy(out)
    out.save(os.path.join(D, f'key_{name}.png'))
    return out


# -- the neck, drawn from a curve (the user: no PixelLab drift), on the taller canvas ----------------
CH = H                                 # only what the battle shows is drawn (the user): the plain 177x113 canvas
BODY_Y = 0
VISIBLE_TOP = 25                       # the HUD covers the rows above (full-size row 51): nothing is drawn there
FL_LIGHT, FL_MID, FL_DARK = (182, 67, 61), (121, 39, 39), (32, 12, 14)
HEAD_BOX = (11, 62)                    # the head's top-left inside master_head.png
NAPE = (38, 72)                        # where the neck joins the back of the head (master_head.png coords)
POSES = {                              # body dx; head offset; the neck's bend (control point)
    'stand': {'body': -11, 'head': None, 'bend': (40, 18), 'nape': (52, -24)},   # the head off-screen above; nape absolute
    'lower': {'body': 8, 'head': (0, 0), 'bend': (34, 43), 'nape': (35, 80)},
}


def bezier(p0, p1, p2, n=200):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def neck(root, bend, nape, r0=12.0, r1=7.0, size=None):
    """A thick tube of flesh from the shoulder socket to the nape: the flesh ramp lit from the upper
    left, a fold line every few pixels, stone vertebrae along its top, a one-pixel outline."""
    import math
    pts = bezier(root, bend, nape)
    w, h = size or (W, CH)
    img = Image.new('RGBA', (w, h)); px = img.load()
    for y in range(h):
        for x in range(w):
            best = None
            for i, (cx, cy) in enumerate(pts):
                r = r0 + (r1 - r0) * i / (len(pts) - 1)
                d = math.hypot(x - cx, y - cy)
                if d <= r and (best is None or d / r < best[0]):
                    best = (d / r, i, (x - cx) / max(d, 1e-6), (y - cy) / max(d, 1e-6), d, r)
            if best is None:
                continue
            f, i, nx, ny, d, r = best
            lit = -0.7 * nx - 0.7 * ny if d > 1 else 0.5
            c = FL_LIGHT if lit > 0.35 else FL_DARK if lit < -0.8 else FL_MID
            if i % 22 in (0, 1) and 6 < i < len(pts) - 6 and f < 0.8:   # a fold across the tube (not at its ends)
                c = K
            px[x, y] = c + (255,)
    # vertebrae: grey knobs along the top side
    for i in range(18, len(pts) - 10, 24):
        (ax, ay), (bx, by) = pts[i - 1], pts[i + 1]
        tx, ty = bx - ax, by - ay; L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        if ny > 0: nx, ny = -nx, -ny                  # the upper side
        r = r0 + (r1 - r0) * i / (len(pts) - 1)
        cx, cy = pts[i][0] + nx * (r - 1), pts[i][1] + ny * (r - 1)
        for y in range(int(cy) - 3, int(cy) + 4):
            for x in range(int(cx) - 3, int(cx) + 4):
                e = ((x - cx) / 3.2) ** 2 + ((y - cy) / 2.6) ** 2
                if 0 <= x < w and 0 <= y < h and e <= 1:
                    px[x, y] = (LIGHT if e < 0.35 and y < cy else MID if e < 0.8 else DARK) + (255,)
    return outline_any(img)


def outline_any(img, top=0):
    """Outline every opaque edge pixel -- except along the cut at row `top`, where the creature runs on out of view."""
    px = img.load(); w, h = img.size
    edge = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] and any(
        y + dy >= top and (not (0 <= x + dx < w and 0 <= y + dy < h) or not px[x + dx, y + dy][3]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for q in edge:
        px[q] = K + (255,)
    return img


def tidy_any(img, top=0):
    px = img.load(); w, h = img.size
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = px[x, y]
            if not c[3] or c[:3] == K:
                continue
            n = [px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if all(m[3] and m[:3] != c[:3] for m in n):
                px[x, y] = max(n, key=n.count)
    return outline_any(img, top)


def cut(img):
    """Clear the rows the HUD hides."""
    px = img.load()
    for y in range(min(VISIBLE_TOP, img.height)):
        for x in range(img.width):
            px[x, y] = (0, 0, 0, 0)
    return img


def check(img):
    """The bible's numbers on the visible part only (the cut edge isn't an outline gap)."""
    import sannaja_redraw
    return sannaja_redraw.bible_numbers(img.crop((0, VISIBLE_TOP, img.width, img.height)))


def pose(body_dx, head_off, bend, nape_at=NAPE, eyes='open', shift=0):
    """One whole frame: master body, drawn neck, master head -- the same pixels in every frame."""
    body = Image.open(os.path.join(D, 'master_body_clean.png')).convert('RGBA')
    head = Image.open(os.path.join(D, 'master_head.png' if eyes == 'open' else 'master_head_shut.png')).convert('RGBA')
    root = (SOCKET[0] + body_dx + shift, SOCKET[1] + BODY_Y)
    nape = (nape_at[0] + shift, nape_at[1]) if head_off is None else (nape_at[0] + head_off[0] + shift, nape_at[1] + head_off[1])
    bp = body.load()
    for y in range(SOCKET[1] - 11, SOCKET[1] + 12):              # the socket's dark hollow filled with the neck's flesh
        for x in range(SOCKET[0] - 12, SOCKET[0] + 13):
            if ((x - SOCKET[0]) / 12) ** 2 + ((y - SOCKET[1]) / 11) ** 2 <= 1 and bp[x, y][3] and bp[x, y][:3] in (K, FL_DARK):
                bp[x, y] = FL_MID + (255,)
    f = Image.new('RGBA', (W, CH))
    f.alpha_composite(body, (body_dx + shift, BODY_Y)) if body_dx + shift >= 0 else f.alpha_composite(body.crop((-(body_dx + shift), 0, W, H)), (0, BODY_Y))
    f.alpha_composite(neck(root, (bend[0] + shift, bend[1]), nape))
    if head_off is not None:
        hx, hy = head_off[0] + shift, head_off[1]
        hb = head.crop(head.getbbox()); bx, by = head.getbbox()[:2]
        f.alpha_composite(hb, (bx + hx, by + hy))
    return tidy_any(cut(f), VISIBLE_TOP)


def keys():
    s = POSES['stand']; l = POSES['lower']
    out = {'stand': pose(s['body'], s['head'], s['bend'], s['nape']),
           'raised': pose(s['body'], s['head'], s['bend'], s['nape'], shift=l['body'] - s['body']),
           'lower': pose(l['body'], l['head'], l['bend'], l['nape'])}
    for n, im in out.items():
        im.save(os.path.join(D, f'key_{n}.png'))
        print(n, check(im))
    return out


# -- the close-up: only what the battle shows (the user's window), at 160x87, about 1.7x the model ----
CW, CHH = 160, 87                      # the battle's visible window at half size
ZOOM = 1.7
STRIP = (14, 66, 114, 113)             # master-body pixels the window ever sees (legs, flesh bands, underside)
CLOSE_BODY = """Redraw this close-up of enemy 52 Sannaja's legs, exactly 170x87 pixels, transparent background, keeping every shape exactly where and how the enlarged guide draws it: the grey rock underside of the colossal body along the top, cut off by the top edge; a wide band of red flesh wrapping the top of each leg; thick cracked grey stone-pillar legs standing on the ground, near legs light grey, far legs darker grey behind and between them; the legs at the left and right edges cut off by the frame. Change no shapes and add nothing: no heads, faces, eyes or extra legs. Only clean the blocky enlarged guide into crisp pixel art at this resolution, in the reference's style and colours: one-pixel black outlines, thin black crack lines, flat dark/mid/light ramps placed by form, no gradients, dithering, hatching or texture."""
CLOSE_HEAD = """Redraw these two close-ups of the head of enemy 52 Sannaja, exactly 128x88 pixels, transparent background, keeping each exactly where and how the enlarged guide draws it: a mouthless teardrop-shaped head of red flesh, hanging low, with dark red hair swept back like a flame. Left: eyes open, two round black-violet void eyes with lilac rims and a tiny white star glint. Right: the very same head, every pixel the same except the eyes, which are shut under heavy red lids. Change no shapes and add nothing. Only clean the blocky enlarged guide into crisp pixel art at this resolution, in the reference's style and colours: one-pixel black outlines, flat dark/mid/light ramps, no gradients, dithering, hatching or texture."""


def big(im):
    return im.resize((round(im.width * ZOOM), round(im.height * ZOOM)), Image.NEAREST)


def close_job():
    body = Image.open(os.path.join(D, 'master_body_clean.png')).convert('RGBA').crop(STRIP)
    g = Image.new('RGBA', (170, CHH)); g.alpha_composite(big(body).crop((0, 0, 170, 80)), (0, 0))
    g.save(os.path.join(D, 'source_cbody.png'))
    heads = Image.new('RGBA', (128, 88))
    for i, n in enumerate(('master_head.png', 'master_head_shut.png')):
        h = Image.open(os.path.join(D, n)).convert('RGBA'); h = big(h.crop(h.getbbox()))
        heads.alpha_composite(h, (i * 64 + (64 - h.width) // 2, 0))
    heads.save(os.path.join(D, 'source_chead.png'))
    Image.new('RGBA', (170, CHH * 8)).save(os.path.join(D, 'cell_cbody.png'))
    Image.new('RGBA', (128, 88 * 8)).save(os.path.join(D, 'cell_chead.png'))
    Image.open(os.path.join(D, 'key_lower.png')).save(os.path.join(D, 'cref_frame0_clean.png'))
    for k, t in (('cbody', CLOSE_BODY), ('chead', CLOSE_HEAD)):
        open(os.path.join(D, f'prompt_{k}.txt'), 'w', encoding='utf-8').write(t)
    sheet = lambda k: {'png': f'art/enemies/pixellab/52_sannaja/half/cell_{k}.png', 'frames': 1, 'rows': True, 'views': ['D'], 'make': 'none', 'from': 'cref'}
    cfg = {'id': 52, 'name': '52-sannaja-close', 'dir': 'art/enemies/pixellab/52_sannaja/half', 'description': '',
           'prompts': {'cbody': 'prompt_cbody.txt', 'chead': 'prompt_chead.txt'}, 'sheets': {'cbody': sheet('cbody'), 'chead': sheet('chead')}}
    json.dump(cfg, open(os.path.join(D, 'job_close.json'), 'w'), indent=2)
    return pe.Job(os.path.join(D, 'job_close.json'))


def outline_open(img):
    """The outline closed only where the creature meets empty space inside the frame: at the frame's
    edges it runs on out of view."""
    px = img.load(); w, h = img.size
    edge = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] and any(
        0 <= x + dx < w and 0 <= y + dy < h and not px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for q in edge:
        px[q] = K + (255,)
    return img


def tidy_open(img):
    px = img.load(); w, h = img.size
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = px[x, y]
            if not c[3] or c[:3] == K:
                continue
            n = [px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if all(m[3] and m[:3] != c[:3] for m in n):
                px[x, y] = max(n, key=n.count)
    return outline_open(img)


def close(generate, which, attempt):
    j = close_job(); pal = sorted({p[:3] for p in Image.open(os.path.join(D, 'key_lower.png')).convert('RGBA').getdata() if p[3]})   # the eyes' lilac too
    for k in which:
        pe.edit(j, k, generate, attempt)
        if not generate:
            continue
        draft = Image.open(os.path.join(D, f'{k}_frame0_draft.png')).convert('RGBA')
        c = tidy_open(pe.despeckled(pe.to_palette(draft, pal), 6))
        c.save(os.path.join(D, f'{k}_try{attempt}_clean.png'))
        print(k, 'try', attempt, sr.bible_numbers(c), flush=True)


# -- the close-up cycle: walk back, neck swung down (shut, then open), back up, walk forward ---------
CLEGS = [(8, 57), (61, 107), (118, 160), (161, 169)]   # each leg's columns in the close-up strip
CLEG_TOP = 8                                            # a leg's flesh band reaches up to here
BODY_LINE = 22                                          # the underside ends here: below it, all leg
CPAIRS = [(3, 1), (2, 0)]                               # diagonal pairs, the rightmost first (it backs away right)
CSTEPS = 4                                              # step cycles: every leg steps this many times
CWALK = 64                                              # how far it backs away
CLIFT = 3
SOCKET_C = (51, -27)                                    # the shoulder socket in strip coords (above the window)
NAPE_C = (44, 36)                                       # the back of the head in the close-up head (its bbox)
HEAD_REST = (48, -35)                                    # the head's top-left in the window when down
HEAD_FROM = (92, -92)                                   # ...and where it starts, up and right, just out of view
RED = FLESH | {FL_LIGHT, FL_MID, FL_DARK}             # the flesh colours, both sets


def band(px, x, y, w, h):
    """A leg's flesh band above the body line: the red, and black that borders the red."""
    c = px[x, y][:3]
    return c in RED or c == K and any(0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] in RED
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def close_parts():
    """strip -> (strip, body, [legs]): legs over body is the strip exactly. A leg takes its rock below the
    body line and its flesh band above it; the band's place in the body is refilled with the underside
    beside it, so a stepping leg uncovers rock, not a hole."""
    strip = Image.open(os.path.join(D, 'source_cbody_thin.png')).convert('RGBA')
    px = strip.load(); w, h = strip.size
    body = strip.copy(); bp = body.load(); legs = []
    for x0, x1 in CLEGS:
        x1 = min(x1, w - 1); lw = x1 - x0 + 1
        leg = Image.new('RGBA', strip.size); lp = leg.load()
        for y in range(CLEG_TOP, h):
            for x in range(x0, x1 + 1):
                if not px[x, y][3] or y < BODY_LINE and not band(px, x, y, w, h):
                    continue
                lp[x, y] = px[x, y]
                if y >= BODY_LINE:
                    bp[x, y] = (0, 0, 0, 0)
                    continue
                for sx in (x - lw, x + lw, x0 - 1, x1 + 1):      # the underside next door, its pattern carried over
                    if 0 <= sx < w and not x0 <= sx <= x1 and px[sx, y][3] and not band(px, sx, y, w, h):
                        bp[x, y] = px[sx, y]; break
                else:
                    bp[x, y] = MID + (255,)
        legs.append(leg)
    whole = body.copy()
    for l in legs:
        whole.alpha_composite(l)
    assert whole.tobytes() == strip.tobytes(), 'the leg split lost pixels'
    return strip, body, legs                           # outlines are closed on the whole frame


def put(canvas, layer, dx, dy=0):
    w, h = layer.size
    if -dx >= w or -dy >= h or dx >= canvas.width or dy >= canvas.height:
        return                                         # wholly out of view
    canvas.alpha_composite(layer.crop((max(0, -dx), max(0, -dy), w, h)), (max(0, dx), max(0, dy)))


def window(layer, sx):
    f = Image.new('RGBA', (CW, CHH)); put(f, layer, -sx); return f


def close_frame(body, legs, bx, ldx, ldy, sx=5):
    s = Image.new('RGBA', (170 + CWALK + 40, CHH))
    for i, l in enumerate(legs):                       # a lifted leg steps behind the body
        if ldy[i]:
            put(s, l, ldx[i], ldy[i])
    put(s, body, bx)
    for i, l in enumerate(legs):
        if not ldy[i]:
            put(s, l, ldx[i])
    return tidy_open(window(s, sx))


EYE_BOXES = [(14, 53, 23, 69), (27, 46, 38, 64)]          # each eye's lilac rim in the close-up head (its bbox)
VOID = (32, 12, 14)
WHITE = (252, 252, 252)


def eye_head(look):
    """The open close-up head with its eyes following the player: each void emptied of its drawn glint
    and catch-lights, then a 2x2 white glint set off the void's middle toward `look` (a direction)."""
    import math
    heads = Image.open(os.path.join(D, 'chead_try3_clean_thin.png')).convert('RGBA')
    h = heads.crop((0, 0, 64, 88)); h = h.crop(h.getbbox()); px = h.load()
    L = (182, 156, 238)
    lx, ly = look; n = math.hypot(lx, ly) or 1; lx, ly = lx / n, ly / n
    for x0, y0, x1, y1 in EYE_BOXES:
        out, st = set(), [(x0 - 1, y) for y in range(y0 - 1, y1 + 2)]    # outside: reachable from the box's edge without crossing the rim
        while st:
            q = st.pop()
            if q in out or not (x0 - 1 <= q[0] <= x1 + 1 and y0 - 1 <= q[1] <= y1 + 1):
                continue
            if x0 <= q[0] <= x1 and y0 <= q[1] <= y1 and px[q][3] and px[q][:3] == L and not small(px, q, L):
                continue
            out.add(q); st += [(q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)]
        inside = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if (x, y) not in out and not (px[x, y][:3] == L and not small(px, (x, y), L))]
        for q in inside:
            px[q] = VOID + (255,)
        cx = sum(q[0] for q in inside) / len(inside); cy = sum(q[1] for q in inside) / len(inside)
        rx = (max(q[0] for q in inside) - min(q[0] for q in inside)) / 2
        ry = (max(q[1] for q in inside) - min(q[1] for q in inside)) / 2
        inner = set(inside)
        for f in (1.0, 0.85, 0.7, 0.55, 0.4, 0.25, 0.0):          # as far toward the player as the void allows,
            gx, gy = round(cx + lx * rx * f - 0.5), round(cy + ly * ry * f - 0.5)
            ring = {(gx + dx, gy + dy) for dx in (-1, 0, 1, 2) for dy in (-1, 0, 1, 2)}
            if ring <= inner:                                      # the glint whole, with void all round it
                break
        for dx in (0, 1):
            for dy in (0, 1):
                px[gx + dx, gy + dy] = WHITE + (255,)
    return h


def small(px, q, L, most=8):
    """Whether the lilac piece at q is a small catch-light (not the rim)."""
    seen, st = {q}, [q]
    while st and len(seen) <= most:
        a, b = st.pop()
        for r in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1), (a + 1, b + 1), (a - 1, b - 1), (a + 1, b - 1), (a - 1, b + 1)):
            try:
                c = px[r]
            except IndexError:
                continue
            if r not in seen and c[3] and c[:3] == L:
                seen.add(r); st.append(r)
    return len(seen) <= most


def head_frame(base, t, eyes):
    """The head lowered at an angle: its nape travels in a straight diagonal from up-right above the
    window down to the left, and the heavy neck sags from the shoulder (above the window, upper right)
    down and forward to it. The head is the close-up head's exact pixels."""
    heads = Image.open(os.path.join(D, 'chead_try3_clean_thin.png')).convert('RGBA')
    h = heads.crop((0, 0, 64, 88) if eyes == 'open' else (64, 0, 128, 88)); h = h.crop(h.getbbox())
    if isinstance(eyes, tuple):
        h = eye_head(eyes)                               # open, looking toward the player
    root = (SOCKET_C[0] + CWALK - 5, SOCKET_C[1])
    s = (HEAD_FROM[0] + NAPE_C[0], HEAD_FROM[1] + NAPE_C[1]); e = (HEAD_REST[0] + NAPE_C[0], HEAD_REST[1] + NAPE_C[1])
    nape = (s[0] + (e[0] - s[0]) * t, s[1] + (e[1] - s[1]) * t)
    bend = (root[0] + 0.25 * (nape[0] - root[0]), max(root[1], nape[1]))   # down from the shoulder, then forward
    f = base.copy()
    f.alpha_composite(neck(root, bend, nape, r0=20, r1=12, size=(CW, CHH)))
    put(f, h, round(nape[0] - NAPE_C[0]), round(nape[1] - NAPE_C[1]))
    return tidy_open(f)


def cycle():
    strip, body, legs = close_parts()
    stride = CWALK / CSTEPS
    pos = [0.0] * 4; bx = 0.0; walk = []
    for s in range(CSTEPS):
        for pair in CPAIRS:
            walk.append(close_frame(body, legs, round(bx), [round(pos[i] + (stride / 2 if i in pair else 0)) for i in range(4)],
                                    [-CLIFT if i in pair else 0 for i in range(4)]))
            for i in pair: pos[i] += stride
            bx += stride / 2
            walk.append(close_frame(body, legs, round(bx), [round(p) for p in pos], [0] * 4))
    stand = close_frame(body, legs, 0, [0] * 4, [0] * 4)
    back = walk[-1]
    down = [head_frame(back, t, 'shut') for t in (0, .25, .45, .62, .77, .89, .97, 1)]
    looks = []                                           # the player walking left to right below it and back
    for k in range(16):
        u = k / 8 if k <= 8 else (16 - k) / 8
        ex, ey = HEAD_REST[0] + 30, HEAD_REST[1] + 60       # about the eyes, in the window
        looks.append(head_frame(back, 1, (-60 + 280 * u - ex, 150 - ey)))
    opened = looks[8]
    seq = [stand] * 6 + walk + down + [down[-1]] * 6 + looks + looks + down[::-1] + walk[::-1] + [stand] * 2
    for n, fs in {'stand': [stand], 'walk': walk, 'down': down, 'look': looks}.items():
        for k, f in enumerate(fs):
            print(n, k, [round(v, 2) for v in sr.bible_numbers(f)])
    frames = [stand] + walk + down + looks[:9]
    sheet = Image.new('RGBA', (CW * len(frames), CHH))
    for k, f in enumerate(frames):
        sheet.alpha_composite(f, (k * CW, 0))
    sheet.save(os.path.join(D, 'close_frames.png'))
    cols = 5; board = Image.new('RGBA', (cols * (CW * 2 + 6), -(-len(frames) // cols) * (CHH * 2 + 6)), (30, 30, 36, 255))
    S = 4; gif = []
    for k, f in enumerate(frames):
        bg = Image.new('RGBA', (CW, CHH), (70, 76, 90, 255)); bg.alpha_composite(f)
        board.alpha_composite(bg.resize((CW * 2, CHH * 2), Image.NEAREST), ((k % cols) * (CW * 2 + 6), (k // cols) * (CHH * 2 + 6)))
    board.save(os.path.join(ROOT, 'build_tmp/sannaja_gifs/close_frames_board.png'))
    for f in seq:
        bg = Image.new('RGBA', (CW, CHH), (70, 76, 90, 255)); bg.alpha_composite(f)
        gif.append(bg.convert('RGB').resize((CW * S, CHH * S), Image.NEAREST))
    out = os.path.join(ROOT, 'build_tmp/sannaja_gifs/half_full_cycle.gif')
    gif[0].save(out, save_all=True, append_images=gif[1:], duration=133, loop=0)
    return out

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'body':
        body('--generate' in a, int(a[a.index('--try') + 1]) if '--try' in a else 1)
    elif a[0] == 'key':
        for n in a[1].split(','):
            key(n, '--generate' in a)
    elif a[0] == 'keys':
        keys()
    elif a[0] == 'close':
        close('--generate' in a, a[1].split(','), int(a[a.index('--try') + 1]) if '--try' in a else 1)
    elif a[0] == 'cycle':
        print(cycle())
    elif a[0] == 'gates':
        print(gates(Image.open(a[1]).convert('RGBA')))
