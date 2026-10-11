"""54 Billdad, medium tier (19 px; the user: "smaller", then "thinner and smaller"),
to art/direction/SPRITE_STYLE.md: one view a phase.

    python art/enemies/54_billdad_design.py     # writes 54_billdad/_jump/_slap .json and .txt, draft.png

The user, 2026-10-10: "front sprite only jumping and slapping tail", "only back
sprite for 2nd phase of it coming down looking behind it and slapping tail".
Three sheets, each a single view:
  54_billdad       front: stand / spring (tail flung up: the flick) / stance
  54_billdad_jump  front: in the air / tail raised over its head / tail slammed down
  54_billdad_slap  back, head turned to look behind it: in the air / tail raised /
                   tail slammed down / standing

After the user's reference picture (A Book of Creatures' billdad; "its entire
body should be fleshy"): bare and flesh-coloured all over -- bill, feet and tail
too -- a small head with a hooked bill on a long neck, little arms held at the
chest, a thin body on kangaroo haunches and long feet, a flat tail a tone darker
than the skin.

At this size the body is drawn by hand (the grids below, a letter a colour);
the poses are cut from them and the tail laid on as a shape. Then drawn into the
.aseprite through the pixel plugin by tools/draw_views.py."""
import json, io
from PIL import Image, ImageDraw
PAL = {'K': '000000', 't': '583518', 'D': '8d6b4f', 'M': 'd7a175', 'L': 'f0b890'}
W, H = 28, 27
GROUND = H - 3                                            # the feet's outline sits on this row

FRONT_HALF = """
.....KKK
...KKMMM
..KMMMMM
.KKMMKMM
KMMKMMMM
.KKKMMKK
...KMKLL
....KKLL
.....KKL
.....KMK
.....KMM
....KMMM
...KMMLL
...KDMLL
.KKKMMLL
KMMMKMLL
KMMMKMMM
KMMMKDDD
.KMMMKKK
KMMMMK..
.KKKK...
""".split()
FRONT = [r + r[::-1] for r in FRONT_HALF]                 # the front is symmetric
FRONT_AIR = FRONT[:14] + [r + r[::-1] for r in """
..KMKMLL
..KMKMLL
..KMKMMM
..KMKDDD
..KMKKKK
..KMK...
..KK....
""".split()]                                              # legs hanging, toes down

BACK = """
......KKKKK.......
.....KMMMMMK......
....KMMMMMMMKKK...
..KKMMMMMKMLLLLK..
.KMMMMMMMMMLLLLK..
..KKKMMMMMKKKLLK..
.....KMMMMK.KLK...
......KMMK...K....
.......KMMK.......
.......KMMK.......
......KMMMMK......
.....KMLLLLMK.....
.....KMMLLMMK.....
...KKKMMMMMMKKK...
..KMMMKMMMMKMMMK..
..KMMMKMMMMKMMMK..
..KMMMKDDDDKMMMK..
...KMMMKKKKMMMK...
..KMMMMK..KMMMMK..
...KKKK....KKKK...
""".split()
BACK_AIR = BACK[:13] + """
....KMKMMMMKMK....
....KMKMMMMKMK....
....KMKDDDDKMK....
....KMKKKKKKMK....
....KMK....KMK....
....KK......KK....
""".split()

def mask(draw_fn):
    im = Image.new('1', (W, H), 0); draw_fn(ImageDraw.Draw(im)); px = im.load()
    return {(x, y) for y in range(H) for x in range(W) if px[x, y]}
def ell(box): return mask(lambda d: d.ellipse(box, fill=1))
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
def rim(shape): return {(x + dx, y + dy) for (x, y) in shape for dx, dy in N4} - shape

def tail(g, box):
    """The flat tail: bare like the rest of it, a tone darker, darkest where it turns under."""
    t = ell(box)
    for p in t: g[p] = 'D'
    for (x, y) in t:
        if (x, y + 1) not in t: g[(x, y)] = 't'
    for p in rim(t): g[p] = 'K'

def squat(grid, cut):
    """Crouched: two rows shorter (one out of the neck, one out of the belly)."""
    return [r for i, r in enumerate(grid) if i not in cut]
SQF, SQB = squat(FRONT, (10, 13)), squat(BACK, (9, 12))

def stretch(grid):
    """Sprung: legs straight, a row taller."""
    return grid[:17] + [grid[16]] + grid[17:]

def pose(grid, lift=0, behind=None, over=None):
    """A body grid standing on the ground (lifted `lift` px), with the tail behind it or over it."""
    g = {}
    if behind: tail(g, behind)
    x0, y0 = (W - len(grid[0])) // 2, GROUND - len(grid) + 1 - lift
    for y, r in enumerate(grid):
        for x, c in enumerate(r):
            if c != '.': g[(x0 + x, y0 + y)] = c
    if over: tail(g, over)
    return g

IDLE = [pose(FRONT, behind=(19, 17, 26, 23)), pose(stretch(FRONT), behind=(19, 6, 24, 17)), pose(SQF, behind=(19, 18, 26, 23))]
JUMP = [pose(FRONT_AIR, lift=1, behind=(18, 12, 23, 21)), pose(SQF, behind=(8, 1, 19, 10)), pose(SQF, over=(7, 19, 20, 23))]
SLAP = [pose(BACK_AIR, lift=1, over=(11, 16, 16, 23)), pose(SQB, over=(9, 10, 18, 21)), pose(SQB, over=(6, 19, 21, 23)), pose(BACK, over=(10, 17, 17, 23))]
SHEETS = {'54_billdad': IDLE, '54_billdad_jump': JUMP, '54_billdad_slap': SLAP}
rows = lambda g: [''.join(g.get((x, y), '.') for x in range(W)) for y in range(H)]

if __name__ == '__main__':
    for name, fr in SHEETS.items():
        json.dump({'pal': PAL, 'view_w': W, 'views': {str(i): rows(g) for i, g in enumerate(fr)}, 'order': [str(i) for i in range(len(fr))]}, open(name + '.json', 'w'))
        t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + ['#BODY', '14', '#POSE', 'frames', '#DIRS', 'down']
        for i, g in enumerate(fr): t += ['#D' + (f'@{i}' if i else '')] + rows(g)[:-1]
        io.open(name + '.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    im = Image.new('RGBA', (W * 8, H * 3), (0, 0, 0, 255)); im.paste((255, 170, 200, 255), (W * 4, 0, W * 8, H * 3))
    for r, fr in enumerate(SHEETS.values()):
        for i, g in enumerate(fr):
            for (x, y), c in g.items():
                for b in (0, 1): im.putpixel((b * 4 * W + i * W + x, r * H + y), tuple(int(PAL[c][k:k + 2], 16) for k in (0, 2, 4)) + (255,))
    im.resize((im.width * 7, im.height * 7), Image.NEAREST).save('draft.png')
    allg = [g for fr in SHEETS.values() for g in fr]
    out = {(x, y) for g in allg for x, y in g if not (0 <= x < W and 0 <= y < H - 1)}
    assert not out, f'drawn outside the frame: {sorted(out)[:8]}'
