"""Enemy 28 Opimachus, idle: the approved frame, moved. Tail curling and stretching, breathing, crest in the wind.

The body and crest of every frame are frame 0's own pixels moved (the frame is read from the draft
.aseprite, so an edit there carries into all of them); the tail is redrawn:
    tail    curls up over itself, then stretches out away from the body: five typed shapes (TAILS),
            frame 0's own in the middle
    breath  everything above the legs' middle rises a pixel, rests, sinks a pixel
    crest   the plumes lean with the wind, most at the tips

Ten frames of 130 ms = 1.3 s, the fight's own loop (battle.cpp LOOP_MS 400+250+400+250):
the crest's gust peaks on frame 3 (390 ms; the crest rings leave at 400) and the
out-breath starts on frame 8 (1040 ms; the peck's rings leave at 1050).

    python art/enemies/28_opimachus_design.py look DIR   # PIL only: strip + GIF into DIR
    python art/enemies/28_opimachus_design.py            # draw through the plugin, write the draft and the review
"""
from pathlib import Path
import importlib, math, subprocess, sys, tempfile
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
P = importlib.import_module('28_opimachus_pose_first')   # palette, frame size, image()
W, H, PAL, RGB, N4 = P.W, P.H, P.PAL, P.RGB, P.N4
ASEPRITE = r'C:\Program Files\Aseprite\Aseprite.exe'
MASTER = HERE / '28_opimachus_frame0_draft.aseprite'
STEP_MS = 130
# The tail's shapes between curled and stretched out, typed as its colour pixels: (row, first column, letters).
# 'N' is frame 0's own tail. Every shape leaves the leg on the same three rows; its black edge is put round it after.
TAILS = {
    'C1': [(25, 7, 'bbb'),                                  # the tip comes over the top
           (26, 6, 'bb..b'),
           (27, 5, 'ss...b'),
           (28, 5, 'ss'),
           (29, 5, 'bb'),
           (30, 5, 'ss'),
           (31, 5, 'ss'), (31, 14, 'bbs'),
           (32, 5, 'sss'), (32, 12, 'ssbbs'),
           (33, 6, 'sssbbsssbbs'),
           (34, 7, 'ddbbddd')],
    'C2': [(24, 9, 'sbb'),                                  # curled right up: pulled in, the tip turned back under
           (25, 8, 'ss.bb'),
           (26, 7, 'ss...b'),
           (27, 7, 'bb...b'),
           (28, 7, 'ss..b'),
           (29, 7, 'ss'),
           (30, 7, 'ss'),
           (31, 7, 'bb'), (31, 14, 'bbs'),
           (32, 7, 'sss'), (32, 12, 'ssbbs'),
           (33, 8, 'ssssssbbs'),
           (34, 9, 'ddddd')],
    'E1': [(26, 3, 'b'),                                    # opening: the end leans away from the body
           (27, 3, 'bb'),
           (28, 3, 'bb'),
           (29, 4, 'ss'),
           (30, 4, 'bb'),
           (31, 5, 'ss'), (31, 14, 'bbs'),
           (32, 5, 'sss'), (32, 12, 'ssbbs'),
           (33, 6, 'sssbbsssbbs'),
           (34, 7, 'ddbbddd')],
    'E2': [(29, 2, 'b'),                                    # stretched out low, the tip a little raised
           (30, 2, 'bbs'),
           (31, 3, 'bssb'), (31, 14, 'bbs'),
           (32, 5, 'sbbssbbssbbs'),
           (33, 7, 'bssbbssbbs'),
           (34, 9, 'dbbdd')],
}
#          frame    0     1     2     3     4     5    6     7     8     9
TAIL   = (         'N', 'C1', 'C2', 'C2', 'C1', 'N', 'E1', 'E2', 'E2', 'E1')   # curls up, then stretches out
#          frame   0   1   2   3   4   5   6   7   8   9
BREATH = (         0,  0,  1,  1,  1,  0,  0,  0, -1, -1)   # px the upper body is raised
GUST   = (         0,  1,  2,  3,  2,  1,  0, -1, -1,  0)   # px the crest's tips are blown to our right
HINGE = 30          # breath: rows to here move; the row is doubled to rise, the next one dropped to sink
CREST_ROOT = 10     # crest: its bottom row, which stays on the head
rnd = lambda v: int(math.floor(v + 0.5))


def master():
    """Frame 0 as the user last saved it: {(x, y): letter}."""
    with tempfile.TemporaryDirectory() as d:
        png = Path(d) / 'f0.png'
        subprocess.run([ASEPRITE, '-b', str(MASTER), '--save-as', str(png)], check=True)
        im = Image.open(png).convert('RGBA')
    assert im.size == (W, H), im.size
    inv = {v: k for k, v in RGB.items()}
    g = {}
    for y in range(H):
        for x in range(W):
            p = im.getpixel((x, y))
            if p[3]:
                assert p[:3] in inv, f'colour {p[:3]} at ({x},{y}) is not one of the sprite\'s'
                g[x, y] = inv[p[:3]]
    return g


def split(g):
    """tail, crest, body. The tail is everything left of the near front leg from its tip down."""
    tail = {p: c for p, c in g.items() if 24 <= p[1] <= 35 and (p[0] <= 15 or (p[0] == 16 and 30 <= p[1] <= 34))}
    crest = {p: c for p, c in g.items() if c == 'r' and p[1] <= CREST_ROOT}
    body = {p: c for p, c in g.items() if p not in tail and p not in crest}
    assert tail and crest and len(tail) + len(crest) + len(body) == len(g)
    return tail, crest, body


def tail_shape(name, drawn):
    """The tail in one of its shapes, colour only ('N': as drawn in frame 0, edge and all)."""
    if name == 'N': return dict(drawn)
    out = {(x0 + i, y): c for y, x0, text in TAILS[name] for i, c in enumerate(text) if c != '.'}
    assert pieces(out) == 1, f'tail {name} is in pieces'
    root = lambda px: {p: c for p, c in px.items() if p[0] == 16 and c != 'K'}
    assert root(out) == root(drawn), f'tail {name} does not leave the leg where the drawn one does'
    return out


def sway(crest, gust):
    return {(x + rnd(gust * (CREST_ROOT - y) / 7), y): c for (x, y), c in crest.items()}


def breathe(px, level):
    """Rows down to HINGE moved up `level` px; rising doubles the hinge row, sinking drops the row under it."""
    out = {}
    for (x, y), c in px.items():
        if y <= HINGE: out[x, y - level] = c
        elif not (level < 0 and y == HINGE + 1): out[x, y] = c
    if level > 0:
        out.update({(x, y): c for (x, y), c in px.items() if y == HINGE})
    return out


def pieces(px):
    """How many separate pieces a set of pixels is in, diagonals joined."""
    todo, n = set(px), 0
    while todo:
        n += 1; stack = [todo.pop()]
        while stack:
            x, y = stack.pop()
            for q in ((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                if q in todo: todo.remove(q); stack.append(q)
    return n


def frames():
    g0 = master()
    tail, crest, body = split(g0)
    out = []
    for f in range(len(TAIL)):
        top = breathe({**body, **sway(crest, GUST[f])}, BREATH[f])
        g = {**tail_shape(TAIL[f], tail), **top}                 # the body stands in front of the tail
        red = {p for p, c in g.items() if c == 'r' and p[1] <= CREST_ROOT - BREATH[f]}
        for p, c in list(g.items()):                             # the black edge round a typed tail
            if c != 'K' and p not in red and p[1] < H - 1 and p[0] <= 16:
                for dx, dy in N4:
                    g.setdefault((p[0] + dx, p[1] + dy), 'K')
        assert all(1 <= x < W - 1 and 1 <= y < H for x, y in g), f'frame {f} leaves the canvas'
        open_px = [p for p, c in g.items() if c != 'K' and p not in red and p[1] < H - 1
                   and any((p[0] + dx, p[1] + dy) not in g for dx, dy in N4)]
        assert not open_px, f'frame {f}: outline open at {sorted(open_px)}'
        assert pieces(red) == pieces(crest), f'frame {f}: the wind tore a plume ({pieces(red)} pieces, {pieces(crest)} drawn)'
        assert set(g.values()) <= set(g0.values())
        out.append(g)
    assert out[0] == g0, 'frame 0 is not the drawn frame'
    assert all(a != b for a, b in zip(out, out[1:] + out[:1])), 'two frames in a row are the same'
    return out


def strip(fr, scale=6):
    im = Image.new('RGBA', (W * len(fr), H), (0, 0, 0, 255))
    for i, g in enumerate(fr): im.alpha_composite(P.image(g), (i * W, 0))
    return im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)


def gif(fr, path, scale=8):
    """The loop at the game's speed, on black. Colours checked: only the sheet's."""
    ims = []
    for g in fr:
        im = Image.new('RGB', (W, H), (0, 0, 0)); im.paste(P.image(g), (0, 0), P.image(g))
        ims.append(im.resize((W * scale, H * scale), Image.Resampling.NEAREST))
    pal = Image.new('P', (1, 1)); pal.putpalette(sum((list(v) for v in RGB.values()), []) + [0] * (768 - 3 * len(RGB)))
    ims = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=STEP_MS, loop=0, disposal=1, optimize=False)
    back = Image.open(path); seen = set()
    for i in range(back.n_frames):
        back.seek(i); seen |= {c for n, c in back.convert('RGB').getcolors(1 << 20)}
    assert seen <= set(RGB.values()), f'the GIF holds colours the sheet does not: {seen - set(RGB.values())}'
    assert back.n_frames == len(fr)


def draw_plugin(fr):
    """A 10-frame .aseprite, 130 ms a frame, drawn through the pixel plugin; each frame read back and compared."""
    sys.path.insert(0, str(HERE.parents[1] / 'art/direction'))
    from mcpc import Pixel
    base = HERE / '28_opimachus_idle_draft'
    ase = str(base.with_suffix('.aseprite')).replace('\\', '/')
    px = Pixel()
    try:
        src = px.call('create_canvas', width=W, height=H, color_mode='rgb')['file_path']
        px.call('set_palette', sprite_path=src, colors=['#' + h for h in PAL.values()])
        px.call('set_frame_duration', sprite_path=src, frame_number=1, duration_ms=STEP_MS)
        for _ in fr[1:]: px.call('add_frame', sprite_path=src, duration_ms=STEP_MS)
        for i, g in enumerate(fr, 1):
            pixels = [{'x': x, 'y': y, 'color': '#' + PAL[c]} for (x, y), c in sorted(g.items())]
            for at in range(0, len(pixels), 800):
                px.call('draw_pixels', sprite_path=src, layer_name='Layer 1', frame_number=i, pixels=pixels[at:at + 800])
        px.call('create_tag', sprite_path=src, tag_name='idle', from_frame=1, to_frame=len(fr), direction='forward')
        px.call('save_as', sprite_path=src, output_path=ase)
        inv = {v: k for k, v in RGB.items()}
        with tempfile.TemporaryDirectory() as d:
            for i, g in enumerate(fr, 1):
                png = (Path(d) / f'{i}.png').as_posix()
                px.call('export_sprite', sprite_path=ase, output_path=png, format='png', frame_number=i)
                im = Image.open(png).convert('RGBA')
                got = {(x, y): inv[im.getpixel((x, y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]}
                assert got == g, f'frame {i}: the plugin export differs from the design'
    finally:
        px.p.terminate()
    print(f'{base.name}.aseprite: {len(fr)} frames, {STEP_MS} ms each, 0 export mismatches', flush=True)


if __name__ == '__main__':
    fr = frames()
    hs = [max(y for x, y in g) - min(y for x, y in g) + 1 for g in fr]
    ws = [max(x for x, y in g) - min(x for x, y in g) + 1 for g in fr]
    print(f'{len(fr)} frames x {STEP_MS} ms = {len(fr) * STEP_MS} ms loop; drawn {min(ws)}-{max(ws)} wide, {min(hs)}-{max(hs)} tall', flush=True)
    if sys.argv[1:2] == ['look']:
        d = Path(sys.argv[2]); d.mkdir(parents=True, exist_ok=True)
        strip(fr).save(d / '28_idle_strip.png'); gif(fr, d / '28_idle.gif')
    else:
        draw_plugin(fr)
        strip(fr).save(HERE / '28_idle_review.png'); gif(fr, HERE / '28_idle_review.gif')
