"""35 Lomie's walk sheet: its front view stepping sideways while it keeps facing you (the user, 2026-10-31:
"sprites in battle of lomie walking left or right while still facing down"). Played as the flap sheet
(battle.cpp) through Lomie::flap_phase while it runs the top of the arena in phase 2 (HUNTED). PixelLab had no
credits, so the frames are frame 0 of the installed D view (assets/enemies/redraws/35_lomie.png) with its legs
moved by hand:

    step_R   the screen-right pair of legs cut below the hip and sheared out to the right, angling from the hip
             (up to 6 px at the hooves), the pair lifted 2 px (two rows of the straight shin dropped); the
             screen-left pair planted; nothing else touched
    plant    frame 0 itself
    step_L   step_R mirrored whole (59 Tripodero's dance did the same, the user's call), re-centred on frame 0's
             bbox so the body doesn't jump between frames
    plant    frame 0 again

Sheet 35_lomie_walk.png: one row, 8 directions x 4 frames of 62x67 (D DR R UR U UL L DL). Only D carries the
walk; every other direction holds its own idle frame 0 four times (never drawn: Lomie::move_facing pins D
while it runs). Cleaned with the 45 pipeline's outline() (the line closed round any colour meeting clear, the
bottom row black, two speck sweeps). Also writes walk_review.png (the 4 D cells at 3x) and walk_D.gif.

    python art/enemies/claude/35_lomie/walk.py
"""
from collections import Counter
from pathlib import Path
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / 'assets/enemies/redraws/35_lomie.png'
W, H, IDLE_FRAMES, FRAMES, MS = 62, 67, 3, 4, 250
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
# the screen-right pair of legs in frame 0: cols 35-42, rows 47-66 (their outline included)
X0, X1, Y0, Y1 = 35, 42, 47, 66
LIFT_ROWS = (55, 56)      # straight shin rows dropped to lift the pair 2 px
SWING = 6                 # px the hooves swing out


def outline(im):
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    for x, y in [(x, y) for y in range(hh) for x in range(w) if not px[x, y][3]
                 and any(at(x + dx, y + dy)[3] and at(x + dx, y + dy)[:3] != K for dx, dy in N4)]:
        px[x, y] = K + (255,)
    for x in range(w):
        if px[x, hh - 1][3] and px[x, hh - 1][:3] != K: px[x, hh - 1] = K + (255,)
    for _ in range(2):
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if not c[3] or c[:3] == K: continue
                near = [at(x + dx, y + dy) for dx, dy in N8]
                if any(n[3] and n[:3] == c[:3] for n in near): continue
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
                px[x, y] = (pick[0][0] if pick else K) + (255,)
    return im


def step_right(f0):
    im = f0.copy()
    px = im.load()
    pts = {(x, y): px[x, y] for y in range(Y0, Y1 + 1) for x in range(X0, X1 + 1) if px[x, y][3]}
    for p in pts: px[p] = (0, 0, 0, 0)
    for (x, y), c in pts.items():
        if y in LIFT_ROWS: continue
        ny = y - sum(1 for r in LIFT_ROWS if r < y)
        dx = round(SWING * (ny - Y0) / (Y1 - 2 - Y0))
        px[x + dx, ny] = c
    return outline(im)


def recentre(im, ref):
    bx, rx = im.getbbox(), ref.getbbox()
    shift = ((rx[0] + rx[2]) - (bx[0] + bx[2])) // 2
    out = Image.new('RGBA', im.size)
    out.paste(im, (shift, 0))
    return out


if __name__ == '__main__':
    src = Image.open(SRC).convert('RGBA')
    idle0 = [src.crop((d * IDLE_FRAMES * W, 0, d * IDLE_FRAMES * W + W, H)) for d in range(8)]
    f0 = idle0[0]
    step_r = step_right(f0)
    step_l = recentre(ImageOps.mirror(step_r), f0)
    walk = [step_r, f0, step_l, f0]
    for name, im in zip(('step_R', 'plant', 'step_L'), (step_r, f0, step_l)):
        im.save(HERE / f'{name}.png')
    sheet = Image.new('RGBA', (W * 8 * FRAMES, H))
    for d in range(8):
        for f in range(FRAMES):
            sheet.paste(walk[f] if d == 0 else idle0[d], ((d * FRAMES + f) * W, 0))
    sheet.save(HERE / '35_lomie_walk.png')
    S = 3
    board = Image.new('RGBA', (FRAMES * (W * S + 4), H * S), (0, 0, 0, 255))
    for f, im in enumerate(walk):
        board.alpha_composite(im.resize((W * S, H * S), Image.NEAREST), (f * (W * S + 4), 0))
    board.save(HERE / 'walk_review.png')
    gif = [Image.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 255)), im).resize((W * S, H * S), Image.NEAREST) for im in walk]
    gif[0].save(HERE / 'walk_D.gif', save_all=True, append_images=gif[1:], duration=MS, loop=0)
    changed = [(x, y) for y in range(H) for x in range(W) if step_r.getpixel((x, y)) != f0.getpixel((x, y))]
    xs, ys = [p[0] for p in changed], [p[1] for p in changed]
    cols = {p[:3] for p in sheet.get_flattened_data() if p[3]}
    print('step_R: %d px changed in cols %d-%d rows %d-%d' % (len(changed), min(xs), max(xs), min(ys), max(ys)))
    print('sheet', sheet.size, len(cols) - 1, 'colours + black; new colours:', cols - {p[:3] for p in f0.get_flattened_data() if p[3]} or 'none')
