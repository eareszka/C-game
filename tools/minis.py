"""Map minis: the small chasers drawn on the map, one per enemy, four views (D U L R).

Each is a map object under art/direction/OVERWORLD_STYLE.md: a 1-px black outline, three colours and black, one
ramp placed by form, at the player's scale (14x20 art px, drawn 2x). Made one enemy at a time from its battle
sheet (shrink() is the start, the enemy's art/enemies/minis/NN_name_mini.py the drawing), drawn through the pixel
plugin into art/enemies/minis/NN_name_mini.aseprite, then installed into assets/enemies/minis.png on the user's word.

    python tools/minis.py NN [rrggbb=X ...]  # print the shrink of enemy NN's battle views, letters per pixel
    python tools/minis.py --confirm NN  # the user confirmed NN: rebuild assets/enemies/minis.png with it
"""
from pathlib import Path
from collections import Counter
import json, math, os, re, subprocess, sys, tempfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

HERE = ROOT / 'art/enemies/minis'
W, H = 40, 28                       # a cell of minis.png; the feet on its bottom row, the middle at column 20
VIEWS = (('D', 0), ('U', 4), ('L', 6), ('R', 2))      # name, battle sheet row (sheet_dir in src/battle.cpp)
TIER_H = {'medium': 12, 'big': 16, 'giant': 24}       # a mini's height, outline included
GRASS = (0x4e, 0xdc, 0x4a, 255)
RUN = 240.0          # PLAYER_RUN_SPEED (include/entity.h), world px a second; an art px is 2 of them
PACE = 180.0         # CHASER_SPEED (src/main.cpp), 1.5x the player's walk: what chase_speed() is a share of
HOVER_UP = 6         # how far a flier's mini is drawn over its shadow, art px (HOVER_UP, src/main.cpp)
TOUCH = 22.0         # ACTOR_TOUCH (src/main.cpp): this near, the battle starts
OPEN = os.environ.get('MINIS_OPEN') == '1'   # open the review and GIFs on this PC (the user reviews on their phone now)
CONFIRMED = HERE / 'confirmed.json'                    # the ids the user confirmed, the only ones in the sheet
SHEET = ROOT / 'assets/enemies/minis.png'             # 5 enemies a row, 8 cells each: D1 D2 U1 U2 L1 L2 R1 R2 (src/main.cpp)


def sheet_row(nn):
    """ENEMY_SHEETS row nn: (path, frames, rows)."""
    src = (ROOT / 'src/battle.cpp').read_text(encoding='utf-8')
    rows = re.findall(r'\{ "(assets/enemies/(?:redraws/)?(\d\d)_\w+\.png)",\s*\{[^}]*\}(?:, (\d+))?(?:, (true|false))?', src)
    for path, n, frames, r in rows:
        if int(n) == nn: return path, int(frames or 3), r == 'true'
    raise KeyError(nn)


def battle_views(nn, f=0):
    """Frame f of each view, cut as battle.cpp cuts it."""
    path, frames, rows = sheet_row(nn)
    im = Image.open(ROOT / path).convert('RGBA')
    fw, fh = (im.width // frames, im.height // 8) if rows else (im.width // (8 * frames), im.height)
    return {v: im.crop((f * fw, d * fh, (f + 1) * fw, (d + 1) * fh) if rows else ((d * frames + f) * fw, 0, (d * frames + f + 1) * fw, fh))
            for v, d in VIEWS}


def tier(views):
    h = max(im.getbbox()[3] - im.getbbox()[1] for im in views.values())
    return 'medium' if h <= 44 else 'big' if h <= 70 else 'giant'


def shrink(im, height, letters, box=None):
    """The start of a mini: the view shrunk by blocks to `height` (outline included). letters: {'rrggbb': letter}
    for every colour but black; a block takes its most common colour, black lines left out, and is filled if
    40% of it is. Returns {(x, y): letter}, feet on the bottom row, centred, outline redrawn. box: crop to it
    rather than the view's own bounds -- the bounds of all a view's frames, so they line up."""
    im = im.crop(box or im.getbbox())
    s = (height - 2) / im.height
    w, h = max(1, round(im.width * s)), height - 2
    g = {}
    for y in range(h):
        for x in range(w):
            box = [im.getpixel((i, j)) for j in range(int(y / s), min(im.height, max(int(y / s) + 1, int((y + 1) / s))))
                   for i in range(int(x / s), min(im.width, max(int(x / s) + 1, int((x + 1) / s))))]
            solid = [p for p in box if p[3]]
            if len(solid) < 0.4 * len(box): continue
            cols = Counter('%02x%02x%02x' % p[:3] for p in solid if p[:3] != (0, 0, 0))
            if cols: g[x, y] = letters[cols.most_common(1)[0][0]]
    dx, dy = W // 2 - w // 2, H - 1 - h
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


def snap(im, pal):
    """A PixelLab drawing (art/enemies/pixellab/NN_name/mini) on the mini's palette: each opaque pixel the nearest
    of pal ({'K': '000000', ...}), so shrink() can read it; half-clear pixels clear."""
    cols = [tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in pal.values()]
    out = Image.new('RGBA', im.size)
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127: out.putpixel((x, y), min(cols, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p))) + (255,))
    return out


def recolour(im, tone, pal):
    """A PixelLab drawing on the mini's palette by what each colour is, not which is nearest (nearest takes a
    dark bamboo green to brown, a tan eye to green): tone(h, s, v) -> a letter of pal, h in degrees, s and v 0-1.
    Half-clear pixels clear."""
    import colorsys
    rgb = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in pal.items()}
    out = Image.new('RGBA', im.size)
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127:
                h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))
                out.putpixel((x, y), rgb[tone(h * 360, s, v)] + (255,))
    return out


def clean(g, passes=2):
    """Lone pixels of the shrink taken into the colour round them: a pixel whose four sides, all of it drawn,
    are mostly one other colour becomes that colour (never black: a thin horn or a tip stays)."""
    for _ in range(passes):
        out = dict(g)
        for (x, y), c in g.items():
            n = [g.get((x + dx, y + dy)) for dx, dy in ff.N4]
            if None in n: continue
            top, k = Counter(n).most_common(1)[0]
            if top != c and top != 'K' and k >= 3: out[x, y] = top
        g = out
    return g


def ascii(g):
    xs, ys = [x for x, y in g], [y for x, y in g]
    return '\n'.join(f'{y:2d} {min(xs):2d} ' + ''.join(g.get((x, y), '.') for x in range(min(xs), max(xs) + 1))
                     for y in range(min(ys), max(ys) + 1))


def hop(g):
    return {(x, y - 1): c for (x, y), c in g.items()}


def steps(views):
    """{view: [frame, ...]}: one frame a view (it hops as it moves), or two or three (it steps through them
    instead; three go in a strip of their own, mini_frames() in src/main.cpp)."""
    out = {v: g if isinstance(g, list) else [g] for v, g in views.items()}
    assert len({len(f) for f in out.values()}) == 1 and len(out['D']) in (1, 2, 3)
    return out


def make(nn, name, views, pal, ref=None, cap=None, cell=(W, H), colours=3):
    """Check the four views, draw them through the plugin (unless the user's draft is there), write the strip
    the overworld checker reads, the review picture and the hop GIF, and open both. A view is one frame, or a
    list of two: then the draft holds D1 D2 U1 U2 L1 L2 R1 R2, a tag a view. cell: a bigger canvas for a mini
    that will not fit the sheet's cells (sheet() gives it a strip of its own); colours: more than the bible's three,
    for a giant (as its battle sprite may)."""
    W, H = cell
    base = HERE / f'{nn:02d}_{name}_mini'
    cap = cap or TIER_H[tier(battle_views(nn))]
    views = steps(views)
    n = len(views['D'])
    for v, gs in views.items():
        for g in gs:
            print(v, '; '.join(l.strip() for l in ff.checks(g, pal, W, H, cap=cap, max_colours=colours) if 'hue' not in l))
    frames = [g for v, _ in VIEWS for g in views[v]]
    pics = [ff.image(g, pal, W, H) for g in frames]
    ase = base.with_suffix('.aseprite')
    if ase.exists():
        assert ff.same_as_draft(ase, pics), f'{ase.name} was edited: it is the drawing now, read it back'
        print(f'{ase.name}: already drawn, unchanged')
    else:
        ff.draw_frames(frames, pal, W, H, base, 150, {v: (i * n + 1, i * n + n) for i, (v, _) in enumerate(VIEWS)})
    strip = Image.new('RGBA', (W * len(pics), H))
    for i, p in enumerate(pics): strip.alpha_composite(p, (i * W, 0))
    strip.save(base.with_suffix('.png'))
    base.with_suffix('.json').write_text(json.dumps({'pal': pal}, indent=2) + '\n')
    r = subprocess.run([sys.executable, str(ROOT / 'tools/overworld_style.py'), f'mini {nn:02d}'],
                       capture_output=True, text=True, cwd=ROOT / 'tools')
    print(r.stdout.strip() or r.stderr.strip())
    # the review: on grass beside the player, the battle views above at their own size
    battle = ref or battle_views(nn)          # ref: other battle frames it is drawn from, by view
    bw, bh = max(b.width for b in battle.values()), max(b.height for b in battle.values())
    me = ff.player()
    step = max(W, bw) + 4
    rev = Image.new('RGBA', (26 + 4 * step, bh + H + 12), GRASS)
    rev.alpha_composite(me, (4, rev.height - 2 - me.height))
    for i, (v, _) in enumerate(VIEWS):
        rev.alpha_composite(pics[i * n], (22 + i * step + (step - W) // 2, rev.height - 2 - H))
        rev.alpha_composite(battle[v], (22 + i * step + (step - battle[v].width) // 2, 3))
    out = HERE / f'{nn:02d}_review.png'
    rev.resize((rev.width * 6, rev.height * 6), Image.Resampling.NEAREST).save(out)
    on = lambda g: ff.image(g, pal, W, H, bg=GRASS)
    walk = [on(g) for v in 'DLUR' for g in (views[v] if n > 1 else [views[v][0], hop(views[v][0])])]
    gif = HERE / f'{nn:02d}_hop.gif'
    big = [p.resize((W * 6, H * 6), Image.Resampling.NEAREST) for p in walk]
    big[0].save(gif, save_all=True, append_images=big[1:], duration=150, loop=0, disposal=1)
    if OPEN:
        for p in (out, gif): subprocess.Popen(['cmd', '/c', 'start', '', str(p)])
    print('review', out, '\ngif', gif)


def chase_speed(style, t):
    """As chase_speed() in src/main.cpp: its speed, a share of PACE, t seconds into the chase."""
    if style == 'dart': return 1.5 if t % 0.55 < 0.3 else 0.0      # a scurry, a freeze
    if style == 'swoop': return 1.3 if t % 0.9 < 0.5 else 0.4      # a glide, then wingbeats
    if style == 'bound': return 1.7 if t % 0.6 < 0.3 else 0.2      # a leap, a landing
    if style == 'dash': return 1.5 if t % 1.0 < 0.5 else 0.5       # a dash straight at you, then a breath
    if style == 'surge': return 1.6 if t % 0.6 < 0.4 else -0.3     # out like its breath, then drawn back
    if style == 'pounce': return 0.0 if t % 0.85 < 0.5 else 2.3    # a still wait, then a leap
    if style == 'jink': return 1.2                                 # a bat's darts, off one side then the other
    if style == 'prowl': return 1.1                                # circling in
    if style == 'flop': return 2.4 if t % 0.55 < 0.25 else 0.0     # a flop, then lying there
    if style == 'meander': return 1.0 + 0.5 * math.sin(t * 2 * math.pi / 0.9)   # its pace rising and falling
    if style == 'gust': return 2.0 if t % 0.8 < 0.35 else 0.6      # a gust, then a whirl
    if style == 'skirt': return 1.3 if t % 1.1 < 0.8 else 1.8      # circling you, then a dart in
    if style == 'flee': return 1.1                                 # running from you, a little slower than you run
    if style == 'surf': return 2.0 if t % 1.0 < 0.4 else 0.2       # a lunge through the water, then a glide
    if style == 'plod': return 0.8                                 # slow and steady
    if style == 'thrust': return 0.0 if t % 0.9 < 0.55 else 2.5    # coiled and still, then thrown straight at you
    if style == 'scuttle': return 1.0                              # an ant's scuttle, never stopping
    if style == 'spring': return 1.7 if t % 0.5 < 0.2 else 0.5     # sprung off its coils, then gathering
    if style == 'inch': return 1.5 if t % 0.6 < 0.35 else 0.2      # an inchworm: reaching out, then humped up gathering
    if style == 'buzz': return 1.15                                # an insect's buzz, weaving (chase_bend)
    if style == 'roll': return 1.7 - 1.5 * (t % 1.0)               # kicked off fast in its ball, rolling out, kicked off again
    if style == 'drift': return 0.7                                # a great fish that can barely move, swimming slow
    if style == 'streak': return 0.5 if t % 0.85 < 0.6 else 2.0   # a marsh light drifting, then a shooting star
    return 1.0                                                     # straight at the player


def chase_frame(style, t, n=2):
    """As chase_frame() in src/main.cpp: which of its n frames its chase shows t seconds in, or None to step
    through them every 150 ms."""
    if style == 'flop' and n == 3: return 1 if t % 0.55 < 0.1 else 2 if t % 0.55 < 0.25 else 0   # heaved up, flopping down, lying
    if style == 'bound': return 0 if t % 0.6 < 0.3 else 1       # stretched out in the leap, gathered on landing
    if style == 'pounce': return 0 if t % 0.85 < 0.5 else 1     # standing still, then in the air
    if style == 'flop': return 1 if t % 0.55 < 0.25 else 0      # in the air in the flop, lying between
    if style == 'spring': return 1 if t % 0.5 < 0.2 else 0      # up in the air in the spring
    if style == 'thrust': return 0 if t % 0.9 < 0.55 else 1     # coiled while it waits, uncoiled in the thrust
    if style == 'inch': return 1 if t % 0.6 < 0.35 else 0       # stretched out reaching, arched gathering
    return None


def chase_bend(style, t):
    """As chase_bend() in src/main.cpp: how far its heading turns off the line to the player, radians."""
    if style == 'zigzag': return 0.9 * math.sin(t * 2 * math.pi / 0.7)    # weaving side to side
    if style == 'wiggle': return 0.6 * math.sin(t * 2 * math.pi / 0.35)   # a quick slither
    if style == 'jink': return 0.8 if t % 0.5 < 0.25 else -0.8             # a dart off one side, then the other
    if style == 'prowl': return 0.6                                         # circling in on you
    if style == 'flop': return 0.7 if t % 1.1 < 0.55 else -0.7              # each flop veers the other way
    if style == 'meander': return 0.7 * math.sin(t * 2 * math.pi / 1.3)     # curving one way, then the other
    if style == 'gust': return 0.0 if t % 0.8 < 0.35 else 2 * math.pi * (t % 0.8 - 0.35) / 0.45   # straight, then one loop round
    if style == 'skirt': return 1.2 if t % 1.1 < 0.8 else 0.0               # circling wide, then straight in
    if style == 'flee': return math.pi                                      # straight away from you
    if style == 'scuttle': return 0.35 * math.sin(t * 2 * math.pi / 0.5)  # weaving a little on its long legs
    if style == 'buzz': return 0.8 * math.sin(t * 2 * math.pi / 0.45)     # weaving side to side as it buzzes in
    if style == 'drift': return 0.4 * math.sin(t * 2 * math.pi / 1.6)    # its slow swim weaving a little
    return 0.0


def shadow(frame, cx, gy, rx):
    """A flier's shadow on the ground, as draw_chaser() in src/main.cpp draws it: an ellipse rx art px across each
    way and 2 down, centred on (cx, gy), half its pixels black by the ordered dither (fc_bayer)."""
    M = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
    for y in range(-2, 3):
        for x in range(-rx, rx + 1):
            if x * x * 4 + y * y * rx * rx <= rx * rx * 4 and M[(y + 2) & 3][(x + rx) & 3] < 8:
                if 0 <= cx + x < frame.width and 0 <= gy + y < frame.height: frame.putpixel((cx + x, gy + y), (0, 0, 0, 255))


def chase_gif(nn, style, views, pal, spin=False, cell=(W, H), hover=0):
    """Its mini chasing a standing player across grass, 25 frames a second, by chase_speed() and chase_bend();
    returns how fast it closes on the player on average, a share of the player's running speed. One that flees
    (bend pi) is run down instead: the player starts near it and runs at it. hover: a flier's shadow's half width
    (mini_hover() in src/main.cpp): it is drawn HOVER_UP art px over its shadow, a pixel lower on its second frame."""
    dt, fw, fh = 0.04, 220, 130
    cw, ch = cell
    me, cells = ff.player(), {v: [ff.image(g, pal, cw, ch) for g in gs] for v, gs in steps(views).items()}
    P, x, y, t, frames, face = (400.0, 120.0), 40.0, 120.0, 0.0, [], 'R'      # world px; an art px is 2
    flees = math.cos(chase_bend(style, 0)) < 0
    if flees: P, x = (430.0, 120.0), 350.0
    start = math.hypot(P[0] - x, P[1] - y)
    while math.hypot(P[0] - x, P[1] - y) > TOUCH or not frames:
        ux, uy = P[0] - x, P[1] - y
        d = math.hypot(ux, uy); ux, uy = ux / d, uy / d
        a, v = chase_bend(style, t), chase_speed(style, t) * PACE
        mx, my = ux * math.cos(a) - uy * math.sin(a), ux * math.sin(a) + uy * math.cos(a)
        if v > 0: face = ('L' if ux < 0 else 'R') if abs(ux) > abs(uy) else ('U' if uy < 0 else 'D')   # it looks at you, however it runs
        if flees: face = ('L' if mx < 0 else 'R') if abs(mx) > abs(my) else ('U' if my < 0 else 'D')   # it looks where it flees
        if spin: face = 'DRUL'[int(t / 0.12) % 4]   # it spins whichever way it goes (draw_chaser in src/main.cpp)
        frame = Image.new('RGBA', (fw, fh), GRASS)
        frame.alpha_composite(me, (int(P[0] / 2) - 7, int(P[1] / 2) + 3 - me.height))
        n = len(cells[face])
        step = int(t / 0.15) % max(n, 2) if v > 0 or hover else 0   # moving (or hovering, its wings never still): its next frame, or a hop
        two = n > 1
        if two and chase_frame(style, t, n) is not None: step = chase_frame(style, t, n)
        lift = HOVER_UP - (step if two else 0) if hover else 0
        if hover: shadow(frame, int(x / 2), int(y / 2) + 4 - 2, hover)
        frame.alpha_composite(cells[face][step if two else 0], (int(x / 2) - cw // 2, int(y / 2) + 4 - ch - (step and not two) - lift))
        frames.append(frame)
        x, y, t = x + mx * v * dt, y + my * v * dt, t + dt
        if flees: P = (P[0] - ux * RUN * dt, P[1] - uy * RUN * dt)     # the player running it down
    frames += [frames[-1]] * 12
    big = [f.resize((fw * 4, fh * 4), Image.Resampling.NEAREST) for f in frames]
    out = HERE / f'{nn:02d}_chase.gif'
    big[0].save(out, save_all=True, append_images=big[1:], duration=int(dt * 1000), loop=0, disposal=1)
    if OPEN: subprocess.Popen(['cmd', '/c', 'start', '', str(out)])
    run = sum(chase_speed(style, i / 100) * math.cos(chase_bend(style, i / 100)) for i in range(1000)) / 1000
    print(f'chase {style}: ' + ('run down by the player in' if flees else 'reaches a standing player in') + f' {t:.2f} s; over 10 s it closes at {run:.2f} of the chase '
          f'pace on average; gif {out}')
    assert run <= 1.0001, 'faster than the player runs on average'
    return run


def drawn(ase):
    """The four views as the .aseprite was last saved, the user's edits included."""
    with tempfile.TemporaryDirectory() as d:
        png = Path(d) / 's.png'
        subprocess.run([ff.ASEPRITE, '-b', str(ase), '--sheet', str(png), '--sheet-type', 'horizontal'], check=True, stdout=subprocess.DEVNULL)
        strip = Image.open(png).convert('RGBA'); strip.load()
    assert strip.size in ((W * 4, H), (W * 8, H)) or strip.width % 8 == 0, strip.size
    return strip


def cell(nn, i):
    """Where cell i (view * 2 + frame) of enemy nn lies on the sheet: 5 enemies a row, 8 cells each."""
    return ((nn % 5) * 8 + i) * W, (nn // 5) * H


def sheet(confirm):
    done = sorted(set(json.loads(CONFIRMED.read_text()) if CONFIRMED.exists() else []) | {confirm})
    out = Image.new('RGBA', (W * 40, H * 20))
    for nn in done:
        ase, = HERE.glob(f'{nn:02d}_*_mini.aseprite')
        strip = drawn(ase)
        if strip.height != H or strip.width == W * 12:   # too big for a cell, or three frames a view: a strip of its own (src/main.cpp)
            strip.save(SHEET.parent / f'minis_{nn:02d}.png')
            continue
        k = strip.width // W                      # 4: one frame a view (cells 0 2 4 6, it hops); 8: two
        for f in range(k):
            out.paste(strip.crop((f * W, 0, (f + 1) * W, H)), cell(nn, f if k == 8 else 2 * f))
    out.save(SHEET)
    CONFIRMED.write_text(json.dumps(done) + '\n')
    back = Image.open(SHEET).convert('RGBA')
    for nn in done:
        ase, = HERE.glob(f'{nn:02d}_*_mini.aseprite')
        strip = drawn(ase)
        if strip.height != H or strip.width == W * 12:
            assert Image.open(SHEET.parent / f'minis_{nn:02d}.png').convert('RGBA').tobytes() == strip.tobytes()
            continue
        k = strip.width // W
        for f in range(k):
            x, y = cell(nn, f if k == 8 else 2 * f)
            assert back.crop((x, y, x + W, y + H)).tobytes() == strip.crop((f * W, 0, (f + 1) * W, H)).tobytes()
    print(f'{SHEET.name} {out.size}: {len(done)} confirmed {done}, each equal to its .aseprite')


if __name__ == '__main__':
    if sys.argv[1] == '--confirm':
        sheet(int(sys.argv[2])); sys.exit()
    nn = int(sys.argv[1])
    views = battle_views(nn)
    t = tier(views)
    cols = Counter('%02x%02x%02x' % p[:3] for im in views.values() for p in im.get_flattened_data() if p[3] and p[:3] != (0, 0, 0))
    print(f'{nn:02d}: tier {t} -> {TIER_H[t]} px tall; battle colours', ' '.join(f'{c} {n}' for c, n in cols.most_common()))
    letters = dict(a.split('=') for a in sys.argv[2:]) or {c: 'ABCDEFGHIJLMNOPQRSTUVWXYZ'[i] for i, (c, _) in enumerate(cols.most_common())}
    print('letters', letters)
    for v, _ in VIEWS:
        print(v); print(ascii(shrink(views[v], TIER_H[t], letters)))
