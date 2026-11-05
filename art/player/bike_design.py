"""The player on the bicycle: assets/player_bike.png, 40 frames of 24 x 24 --

    frame = facing * 5 + phase

    facing  down, up, left, right, down-left, down-right, up-left, up-right
            (the Facing enum's order, src/entity.cpp player_bike_frame)
    phase   0 coasting; 1-4 the wheel's turn, the spoke at top, right, bottom, left,
            the near foot up, level, down, level, the rider a pixel lower on 2 and 4

    python art/player/bike_design.py            # report: does the sheet match this?
    python art/player/bike_design.py --json F   # the 40 frames as a design for tools/draw_views.py
    python art/player/bike_design.py --write    # draw art/player/bike.png (+ .aseprite through
                                                # Aseprite's CLI), install assets/player_bike.png,
                                                # and a review strip in build_tmp/bike_review.png

The frame is drawn over the walk sprite's place (player_draw_bike,
src/overworld.cpp): a walk pixel (x, y) is bike pixel (x + 5, y + 4), so the
walk's ground line is row 23 and its middle column 12.

The art is PixelLab's, from the user's reference (a Yume Nikki FC-world bike, kept
at ~/OneDrive - UWM/Desktop/insp/images.png). bike_pixellab/build.py assembles it
into bike_pixellab/frames/ and this script packs and checks those: the walk's own
head at rows 7-14, fixed wheel outlines with one spoke turning inside, the shoes
going round, and on every other step the whole rider a pixel lower, the walk's bounce. bike_pixellab/bible_check.py runs the repo's bible checks on the sheet.

Colours: K line and pants, H hair, R shirt and shoes, S skin -- the walk
sheet's four -- and the bike in the stone ramp's greys (B base, L lit; TONES in
art/structures/gen_cave_entrances.py), its mass K. Down, up, right, down-right
and up-right are drawn; left, down-left and up-left are their mirrors.
"""
import os, sys, json, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WALK = os.path.join(ROOT, 'assets', 'player_small.png')
OUT = os.path.join(HERE, 'bike')                       # .png and .aseprite
INSTALL = os.path.join(ROOT, 'assets', 'player_bike.png')
REVIEW = os.path.join(ROOT, 'build_tmp', 'bike_review.png')
ASEPRITE = r'C:\Program Files\Aseprite\Aseprite.exe'

PAL = {'K': '000000', 'H': '633e1b', 'R': 'b6433d', 'S': 'f0b890',
       'B': '848694', 'L': 'bcbeca'}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) for k, v in PAL.items()}
W = H = 24
OX, OY = 5, 4                                          # the walk frame's place in this one
FACINGS = ['down', 'up', 'left', 'right', 'down_left', 'down_right', 'up_left', 'up_right']
IDLE = {'down': 0, 'up': 3, 'right': 8, 'down_right': 13, 'up_right': 19}   # the walk's idle frame
MIRROR = {'left': 'right', 'down_left': 'down_right', 'up_left': 'up_right'}
HEAD_TOP, BODY_TOP, PEDAL_TOP, GROUND = 7, 15, 18, 23
FRAMES = os.path.join(HERE, 'bike_pixellab', 'frames')
sys.path.insert(0, os.path.join(HERE, 'bike_pixellab'))
from build import WHEELS, WHEEL_STAMP, PHASES

_walk = {}


def walk_rows(frame, y0, y1):
    """Rows y0..y1 of a walk frame (14 wide) as strings of letters."""
    if frame not in _walk:
        from PIL import Image
        im = Image.open(WALK).convert('RGBA')
        let = {v: k for k, v in RGB.items()}
        _walk[frame] = [''.join(let[im.getpixel((frame * 14 + x, y))[:3]] if im.getpixel((frame * 14 + x, y))[3] else '.'
                                for x in range(14)) for y in range(20)]
    return _walk[frame][y0:y1 + 1]


def load_frame(facing, phase):
    """A frame PixelLab drew and bike_pixellab/build.py assembled, as rows of letters."""
    from PIL import Image
    im = Image.open(os.path.join(FRAMES, '%s_%d.png' % (facing, phase))).convert('RGBA')
    let = {v: k for k, v in RGB.items()}
    return [''.join(let[im.getpixel((x, y))[:3]] if im.getpixel((x, y))[3] else '.' for x in range(W)) for y in range(H)]


def frames():
    out = {f: [load_frame(f, p) for p in range(PHASES)] for f in IDLE}
    for left, right in MIRROR.items():
        out[left] = [[row[::-1] for row in f] for f in out[right]]
    seq = [out[f][p] for f in FACINGS for p in range(PHASES)]
    assert len(seq) == 40 and all(len(f) == H and all(len(r) == W for r in f) for f in seq)
    for i, f in enumerate(seq):
        facing, p = FACINGS[i // PHASES], i % PHASES
        drop = 1 if p in (2, 4) else 0                         # the bounce: every other step, the rider a pixel lower
        src = walk_rows(IDLE[MIRROR.get(facing, facing)], 5, 12)
        if facing in MIRROR: src = [r[::-1] for r in src]
        col0 = OX if facing not in MIRROR else W - OX - 14
        for y, r in enumerate(src):                            # the head is the walk's own
            for x, c in enumerate(r):
                if c != '.':
                    assert f[HEAD_TOP + drop + y][col0 + x] == c, (facing, p, 'head pixel', x, y)
        assert max(y for y, r in enumerate(f) if r.strip('.')) == GROUND, (facing, p, 'ground')
        for y in (BODY_TOP, BODY_TOP + 1):                     # the shirt moves rigidly: it stretched when it did not
            assert f[y + drop][9:15] == seq[i - p][y][9:15], (facing, p, 'shirt changed', y)
        # The tyres never change shape, below the row the rider's hips drop onto.
        src_facing = MIRROR.get(facing, facing)
        stamps = WHEEL_STAMP[src_facing]
        w = len(stamps[0][0])
        for x0, y0 in WHEELS[src_facing]:
            for dy in range(len(stamps[0])):
                y = y0 + dy
                if y < 19: continue
                for dx in range(w):
                    x = x0 + dx
                    if facing in MIRROR: x = W - 1 - x
                    a, b = stamps[0][dy][dx], stamps[1][dy][dx]
                    if a == b == 'K':                          # the tyre is always there
                        assert f[y][x] != '.', (facing, p, 'tyre missing', x, y)
                    elif a == b == '.':                        # and always the same shape
                        assert (f[y][x] == '.') == (seq[i - p][y][x] == '.'), (facing, p, 'tyre corner', x, y)
    # Each riding step must plainly differ from the next; coasting only has to be
    # visibly its own frame.
    for i in range(0, 40, PHASES):
        for a, b, least in ((1, 2, 12), (2, 3, 12), (3, 4, 12), (4, 1, 12), (0, 1, 4), (0, 2, 4), (0, 3, 4), (0, 4, 4)):
            diff = sum(1 for y in range(H) for x in range(W) if seq[i + a][y][x] != seq[i + b][y][x])
            assert diff >= least, (FACINGS[i // PHASES], a, b, 'frames alike', diff)
    return seq


def design():
    seq = frames()
    names = ['%s%d' % (f, p) for f in FACINGS for p in range(PHASES)]
    return {'pal': PAL, 'view_w': W, 'order': names, 'views': dict(zip(names, seq))}


def render(seq):
    from PIL import Image
    im = Image.new('RGBA', (W * len(seq), H))
    for i, f in enumerate(seq):
        for y, r in enumerate(f):
            for x, c in enumerate(r):
                if c != '.':
                    im.putpixel((i * W + x, y), RGB[c] + (255,))
    return im


def review(im):
    """The sheet at 5x on grass: a row a facing -- the walk's idle frame where
    the game draws it, then the three bike frames."""
    from PIL import Image
    Z, PAD = 5, 4
    walk = Image.open(WALK).convert('RGBA')
    cols = PHASES + 1
    sheet = Image.new('RGBA', ((W + PAD) * cols * Z + PAD * Z, (H + PAD) * 8 * Z + PAD * Z), (79, 166, 103, 255))
    for f, facing in enumerate(FACINGS):
        src = IDLE.get(facing, IDLE.get(MIRROR.get(facing)))
        cell = Image.new('RGBA', (W, H))
        wf = walk.crop((src * 14, 0, src * 14 + 14, 20))
        if facing in MIRROR: wf = wf.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        cell.alpha_composite(wf, (OX, OY))
        sheet.alpha_composite(cell.resize((W * Z, H * Z), Image.Resampling.NEAREST), (PAD * Z, (PAD + f * (H + PAD)) * Z))
        for p in range(PHASES):
            i = f * PHASES + p
            cell = im.crop((i * W, 0, i * W + W, H)).resize((W * Z, H * Z), Image.Resampling.NEAREST)
            sheet.alpha_composite(cell, ((PAD + (p + 1) * (W + PAD)) * Z, (PAD + f * (H + PAD)) * Z))
    os.makedirs(os.path.dirname(REVIEW), exist_ok=True)
    sheet.save(REVIEW)
    gif = []                                           # every facing riding, the strip's companion
    for p in range(1, PHASES):
        fr = Image.new('RGBA', ((W + PAD) * 4 * 4 + PAD * 4, (H + PAD) * 2 * 4 + PAD * 4), (79, 166, 103, 255))
        for f in range(8):
            i = f * PHASES + p
            cell = im.crop((i * W, 0, i * W + W, H)).resize((W * 4, H * 4), Image.Resampling.NEAREST)
            fr.alpha_composite(cell, ((PAD + (f % 4) * (W + PAD)) * 4, (PAD + (f // 4) * (H + PAD)) * 4))
        gif.append(fr.convert('RGB'))
    gif[0].save(REVIEW.replace('bike_review.png', 'bike_anim.gif'), save_all=True, append_images=gif[1:], duration=120, loop=0)


def main():
    if '--json' in sys.argv:
        json.dump(design(), open(sys.argv[sys.argv.index('--json') + 1], 'w'))
        return
    seq = frames()
    im = render(seq)
    if '--write' in sys.argv:
        im.save(OUT + '.png')
        if os.path.exists(ASEPRITE):
            subprocess.run([ASEPRITE, '-b', OUT + '.png', '--save-as', OUT + '.aseprite'], check=True)
        shutil.copyfile(OUT + '.png', INSTALL)
        review(im)
        print('wrote %s, %s and %s' % (OUT + '.png', INSTALL, REVIEW))
        return
    from PIL import Image
    try:
        have = Image.open(INSTALL).convert('RGBA')
    except FileNotFoundError:
        print('no sheet installed yet: run with --write'); return
    bad = sum(1 for x in range(im.width) for y in range(H)
              if have.size != im.size or have.getpixel((x, y)) != im.getpixel((x, y)))
    print('%s: %d pixels differ from this design' % (INSTALL, bad))


if __name__ == '__main__':
    main()
