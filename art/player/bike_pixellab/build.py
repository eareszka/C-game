"""Assemble the bike sheet's frames from PixelLab's output.

    python art/player/bike_pixellab/build.py views    # raw rotations -> views/<facing>.png, 17 rows on the ground
    python art/player/bike_pixellab/build.py frames   # views + animations -> frames/<facing>_<phase>.png

Every view is the same size: the walk sprite's own head at rows 7-14, then nine rows
chosen from what PixelLab drew (BODY_ROWS). Frames keep that pose: each wheel is one
fixed stamp whose outline never changes, one spoke turns inside it in four steps, the
shoes go round on the pedals, and on every other step the whole rider drops a pixel in
one piece, the walk's bounce.
PixelLab's direction names are wrong, so RAW names the views by looking at them.
"""
import glob, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
from snap import snap
from unroll import unroll

OUT = os.path.join(ROOT, 'pixellab-out', 'bike', 'bike')
VIEWS = os.path.join(HERE, 'views')
FRAMES = os.path.join(HERE, 'frames')
# Front, back and the diagonals are their own generations, not the rotation's: its
# front was a bearded face, its back stretched, its diagonal wheels black lumps.
RAW = {'right': 'rotations/v1/rot-101-south-00.png', 'up': 'sprites/*/back-16.png', 'down': 'sprites/*/front-16.png',
       'down_right': 'sprites/*/diagdown-16.png', 'up_right': 'sprites/*/diagup-16.png'}
# Short black bar ends past the body, (row, columns): the end-on views draw none.
BAR_ENDS = {'down': (17, (6, 7, 17, 18)), 'up': (16, (6, 18))}
IDLE = {'down': 0, 'up': 3, 'right': 8, 'down_right': 13, 'up_right': 19}   # the walk's idle frame
# The raw rows kept below the head, by looking at each view.
BODY_ROWS = {'right': list(range(15, 24)), 'down': list(range(15, 24)),
             'up': [13, 14, 15, 17, 18, 19, 20, 21, 23], 'down_right': [14, 15, 17, 18, 19, 20, 21, 22, 23],
             'up_right': [14, 15, 16, 17, 18, 19, 21, 22, 23]}
# One fixed wheel an angle, spokes in two patterns of the same brightness: the outline
# never changes. PixelLab's animations redrew the wheels every frame, so they are unused.
# The wheel the user picked (PixelLab edit 81, from their chosen preview): a thick black
# tyre, a small grey ring, a black hub. Coasting is that ring; riding, one black spoke turns
# clockwise from the hub in four steps, the same grey at each. Left-facing frames are
# mirrors, so theirs turn the other way, as they should. The diagonals narrow it; end on,
# a thin tyre with a dash of tread rolling down it and out of sight.
def _wheel(top, bottom, rows):
    return [top[0], top[1]] + rows + [bottom[0], bottom[1]]
_ST, _SB = ['..KKK..', '.KKKKK.'], ['.KKKKK.', '..KKK..']
_TT, _TB = ['.KKK.', 'KKKKK'], ['KKKKK', '.KKK.']
_SIDE = [_wheel(_ST, _SB, r) for r in (
    ['KKLLLKK', 'KKLKLKK', 'KKLLLKK'], ['KKLKLKK', 'KKLKLKK', 'KKLLLKK'], ['KKLLLKK', 'KKLKKKK', 'KKLLLKK'],
    ['KKLLLKK', 'KKLKLKK', 'KKLKLKK'], ['KKLLLKK', 'KKKKLKK', 'KKLLLKK'])]
_TURNED = [_wheel(_TT, _TB, r) for r in (
    ['KLLLK', 'KLKLK', 'KLLLK'], ['KLKLK', 'KLKLK', 'KLLLK'], ['KLLLK', 'KLKKK', 'KLLLK'],
    ['KLLLK', 'KLKLK', 'KLKLK'], ['KLLLK', 'KKKLK', 'KLLLK'])]
_END = [['.K.', 'KLK', 'KLK', 'KKK', 'KKK', '.K.'], ['.K.', 'KLK', 'KLK', 'KKK', 'KKK', '.K.'],
        ['.K.', 'KKK', 'KLK', 'KLK', 'KKK', '.K.'], ['.K.', 'KKK', 'KKK', 'KLK', 'KLK', '.K.'],
        ['.K.', 'KKK', 'KKK', 'KKK', 'KKK', '.K.']]
WHEEL_STAMP = {'right': _SIDE, 'down_right': _TURNED, 'up_right': _TURNED, 'down': _END, 'up': _END}
PHASES = 5                                                     # coasting, then the wheel's four steps
# (col, row) of each stamp, rear (left) then front.
WHEELS = {'right': ((4, 17), (14, 17)), 'down_right': ((5, 14), (15, 17)), 'up_right': ((6, 17), (16, 14)),
          'down': ((11, 18),), 'up': ((11, 18),)}
FAR_WHEEL = {'down_right': 0, 'up_right': 1}                   # this one is behind the rider
SHOES = {'right': (12, 20, 11), 'down_right': (11, 19, 13), 'up_right': (13, 20, 12), 'down': (9, 20, 14), 'up': (9, 20, 14)}   # near col, coasting row, far col
RIDER_BOTTOM = 17
RED, GREY = (0xb6, 0x43, 0x3d, 255), (0xbc, 0xbe, 0xca, 255)
HEAD_TOP, BODY_TOP, PEDAL_TOP = 7, 15, 18
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
BLACK = (0, 0, 0, 255)


def no_hair(im, facing):
    """PixelLab colours the end-on wheel's tread and some shirt pixels hair brown:
    grey on the end-on views, shirt red on the others."""
    to = (0x84, 0x86, 0x94, 255) if facing in ('down', 'up') else (0xb6, 0x43, 0x3d, 255)
    px = im.load()
    for y in range(BODY_TOP, 24):
        for x in range(24):
            if px[x, y][:3] == (0x63, 0x3e, 0x1b) and px[x, y][3]: px[x, y] = to


def walk_head(facing):
    w = Image.open(os.path.join(ROOT, 'assets', 'player_small.png')).convert('RGBA')
    f = IDLE[facing]
    return w.crop((f * 14, 5, f * 14 + 14, 13))


def tidy(im, top=None):
    """What the bible asks: every colour pixel inside a black line, no lone specks."""
    px = im.load()
    for x in range(24):                                # the ground row has no room for a line under it: it is the line
        if px[x, 23][3]: px[x, 23] = BLACK
    top = BODY_TOP if top is None else top
    for y in range(top, 24):                           # the head is the walk's own: its single pixels are drawn
        for x in range(24):
            c = px[x, y]
            if c[3] and c != BLACK and not any(
                    0 <= x + dx < 24 and 0 <= y + dy < 24 and px[x + dx, y + dy] == c for dx, dy in N8):
                px[x, y] = BLACK                       # a speck joins the line
    add = [(x + dx, y + dy) for y in range(BODY_TOP, 24) for x in range(24) if px[x, y][3] and px[x, y] != BLACK
           for dx, dy in N4 if 0 <= x + dx < 24 and 0 <= y + dy < 24 and not px[x + dx, y + dy][3]]
    for p in add: px[p] = BLACK
    return im


def views():
    os.makedirs(VIEWS, exist_ok=True)
    for facing, name in RAW.items():
        raw = snap(unroll(Image.open(glob.glob(os.path.join(OUT, name))[0]).convert('RGBA')))
        x0, y0, x1, y1 = raw.getbbox()
        head = raw.crop((0, y0, 24, y0 + 8)).getbbox()         # the view's own head, to centre it on column 12
        shift = 12 - (head[0] + head[2] - 1 + 1) // 2 if facing in ('down_right', 'up_right') else 0
        out = Image.new('RGBA', (24, 24))
        for i, row in enumerate(BODY_ROWS[facing]):
            out.paste(raw.crop((0, row, 24, row + 1)), (shift, BODY_TOP + i))
        no_hair(out, facing)
        if facing in BAR_ENDS:
            row, cols = BAR_ENDS[facing]
            for x in cols: out.putpixel((x, row), BLACK)
        out.alpha_composite(walk_head(facing), (5, HEAD_TOP))
        out = tidy(out)
        out.save(os.path.join(VIEWS, facing + '.png'))
        print(facing, 'shift', shift, 'box', out.getbbox())


def stamp(im, rows, x0, y0):
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in '.o': continue
            im.putpixel((x0 + x, y0 + y), GREY if c == 'L' else BLACK)


def shoe(im, x, y):
    im.putpixel((x, y), RED); im.putpixel((x + 1, y), RED)


def frame(facing, phase):
    """The PixelLab pose with its wheels stamped, the shoes on the pedals, and on
    stroke B the whole rider a pixel lower, in one piece: the walk's bounce."""
    base = Image.open(os.path.join(VIEWS, facing + '.png')).convert('RGBA')
    spokes = phase                                             # a wheel a phase
    bike = base.copy()
    bike.paste((0, 0, 0, 0), (0, 0, 24, RIDER_BOTTOM + 1))     # the rider goes on last
    for y in range(RIDER_BOTTOM + 1, 24):                      # the drawn shoes off: they go back on the pedals
        for x in range(24):
            if bike.getpixel((x, y))[:3] == RED[:3] and bike.getpixel((x, y))[3]: bike.putpixel((x, y), BLACK)
    rider = base.crop((0, 0, 24, RIDER_BOTTOM + 1))
    rows = WHEEL_STAMP[facing][spokes]
    w = len(rows[0])
    end_on = facing in ('down', 'up')
    for n, (x0, y0) in enumerate(WHEELS[facing]):
        behind = FAR_WHEEL.get(facing) == n
        for dy, r in enumerate(rows):
            for dx, c in enumerate(r):
                x, y = x0 + dx, y0 + dy
                if c == 'o':                                   # between the spokes: the ground
                    bike.putpixel((x, y), (0, 0, 0, 0))
                    if y <= RIDER_BOTTOM and not behind: rider.putpixel((x, y), (0, 0, 0, 0))
                elif c == '.':
                    outer = not end_on and ((dx < w // 2) if n == 0 else (dx > w // 2))
                    if dy == len(rows) - 1 or outer:           # clear round the tyre, or the corner squares it off
                        bike.putpixel((x, y), (0, 0, 0, 0))
                        if y <= RIDER_BOTTOM and not behind: rider.putpixel((x, y), (0, 0, 0, 0))
                    elif bike.getpixel((x, y))[3]:             # the corner against the frame: no stray spoke
                        bike.putpixel((x, y), BLACK)
                elif y <= RIDER_BOTTOM and not behind:
                    rider.putpixel((x, y), (0, 0, 0, 0))       # the near wheel stays when the rider drops
        stamp(bike, rows, x0, y0)
        if behind:                                             # PixelLab's own far wheel off the rider: only the body's outline stays
            body = lambda x, y: 0 <= x < 24 and 0 <= y <= RIDER_BOTTOM and rider.getpixel((x, y))[3] and rider.getpixel((x, y)) not in (BLACK, GREY)
            gone = [(x, y) for y in range(max(y0, BODY_TOP), min(y0 + len(rows), RIDER_BOTTOM + 1)) for x in range(x0, x0 + w)
                    if rider.getpixel((x, y))[3] and (rider.getpixel((x, y)) == GREY or (rider.getpixel((x, y)) == BLACK and not any(body(x + dx, y + dy) for dx, dy in N8)))]
            for q in gone: rider.putpixel(q, (0, 0, 0, 0))
    near_col, near_row, far_col = SHOES[facing]
    lift = {0: 0, 1: -1, 2: 0, 3: 1, 4: 0}[phase]              # the pedals follow the wheel round
    shoe(bike, near_col, near_row + lift)
    if facing in ('down', 'up') or (lift and facing != 'right'):   # side on, the bike hides the far foot
        shoe(bike, far_col, near_row - lift)
    drop = 1 if phase in (2, 4) else 0                         # the walk's bounce, every other step
    out = bike.copy()
    out.alpha_composite(rider, (0, drop))
    return tidy(out, RIDER_BOTTOM + 1 + drop)


def frames():
    os.makedirs(FRAMES, exist_ok=True)
    for facing in RAW:
        for phase in range(PHASES):
            frame(facing, phase).save(os.path.join(FRAMES, f'{facing}_{phase}.png'))
        print(facing, 'frames written')


if __name__ == '__main__':
    {'views': views, 'frames': frames}[sys.argv[1]]()
