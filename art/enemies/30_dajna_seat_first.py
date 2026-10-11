"""Dajna seated, the first drawing of it: how the frame the user then finished was made.

    python art/enemies/30_dajna_seat_first.py assets/enemies/30_dajna.png OUTDIR
        writes OUTDIR/30_dajna_sat.png, whose first frame is that drawing

Kept as the record of the pose's construction; it is not part of the build. The user opened its
first frame in Aseprite and redrew the fore leg (art/enemies/30_dajna_sat_user_frame.png), and
art/enemies/30_dajna_sit.py makes the game's two sheets from that frame.

The seated pose (the user, 2026-10-10: "make dajna look like its actually sitting with its legs
folded and make sure no parts get cut off", a picture of a seated camel, and of the draft that
set its standing feet under it: "legs look like blocks"):
- the body comes all the way down, DROP px: the row its legs leave it at lands on the ground, so
  it lies flat from rump to chest. Its neck and head come down less (NECK_DROP), the neck bending
  up from its base, so the throat fringe hangs clear;
- nothing that would go into the ground is cut off. The hair under the belly gives up rows as the
  belly meets the ground, the plain ones first and then its strands from their tops, till only its
  top band lies along the ground. The tail turns where it meets the ground and the rest of it lies
  along the ground behind, its tip whole. (Checked: no pixel of the body goes below the frame.)
- the far legs are out of sight under it. The two near legs are folded on its side, each
  pixelled by hand as one whole limb in the standing sheet's colours (FOLD: row -> runs of one
  colour, first and last column):
    hind: under the thigh the body already has, the lower leg lies along the ground -- a round
          hock out behind the rump, tapering forward to a foot lying flat before the thigh;
    fore: the forearm from the elbow forward to a round knee on the ground before the chest, the
          lower leg folded back beneath it in shade, its foot tucked under the elbow;
  the light tone on top, the shade on the undersides, toenails and one wrinkle as the user draws
  them;
- where the neck's bend left its edges ragged they are drawn clean (NECK_TOP, with the body's
  breathing; the throat's underside is in FOLD);
- an outline is closed wherever colour is left bare, and along the ground.

FOR THE FIGHT CODE: seated, the body (pyramid, doorway) is DROP px lower and the head NECK_DROP."""
import sys
from PIL import Image
W, H, FRAMES = 302, 166, 8
LEG_TOP = 134                  # below this row a leg hangs free of the body
DROP = 32                      # px the body is down, seated: row LEG_TOP - 1 on the ground
NECK_DROP = 22                 # px the neck and head are down, seated
NECK = (212, 229)              # the neck bends between these columns: left of them the body, right the neck
BREATH = (0, 0, 1, 1, 1, 1, 0, 0)   # px the body is down in each idle frame as it breathes (30_dajna_design.py)
K = (0, 0, 0, 255)
hexrgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
INK = {'K': K, 'D': hexrgb('605028'), 'M': hexrgb('b2966a'), 'L': hexrgb('cebe82'), '.': (0, 0, 0, 0)}

# The four legs of the standing frame: what lies between these columns from LEG_TOP down, foot
# included; where an edge is not one column all the way, the rows that differ.
LEGS = (
    (lambda y: 50, lambda y: 77),                                                                    # far hind
    (lambda y: {134: 178, 135: 176, 136: 173, 137: 172}.get(y, 171 if y < 150 else 164),
     lambda y: {134: 184, 135: 185, 136: 186, 137: 188, 138: 189}.get(y, 196)),                      # far fore
    (lambda y: 76 if y == 153 else 78, lambda y: 101 if y in (134, 135, 137) or y >= 154 else 99),   # near hind
    (lambda y: {134: 185, 135: 186, 136: 187, 137: 189, 138: 190}.get(y, 190 if y < 153 else 197), lambda y: 228),   # near fore
)
HAIR = (100, 177)                                         # the columns of the hair under the belly
HAIR_LOW = 154                                            # its lowest row
HAIR_GIVES = (137, 136, 138, 135, 139, 134, 140) + tuple(range(141, 155))   # the rows it gives up, in order: the plain ones, then its strands from their tops
TAIL = (57, 111)                                          # the tail: left of this column, from this row down

# The near legs folded, seated.
FOLD = {
    147: ((201, 208, 'M'),),
    148: ((186, 208, 'K'),),
    149: ((182, 185, 'K'), (186, 208, 'M'), (209, 213, 'K')),
    150: ((180, 181, 'K'), (182, 213, 'M'), (214, 217, 'K'), (218, 229, 'M')),
    151: ((62, 66, 'K'),
          (179, 179, 'K'), (180, 217, 'M'), (218, 218, 'K'), (219, 229, 'D')),
    152: ((60, 61, 'K'), (62, 66, 'M'), (67, 71, 'K'),
          (178, 178, 'K'), (179, 218, 'M'), (219, 219, 'K'), (220, 229, 'D')),
    153: ((59, 59, 'K'), (60, 71, 'M'), (72, 76, 'K'),
          (178, 178, 'K'), (179, 219, 'M'), (220, 220, 'K'), (221, 229, 'D')),
    154: ((58, 58, 'K'), (59, 76, 'M'), (77, 80, 'K'),
          (177, 177, 'K'), (178, 220, 'M'), (221, 221, 'K'), (222, 229, 'K')),
    155: ((58, 58, 'K'), (59, 80, 'M'), (81, 84, 'K'),
          (176, 176, 'K'), (177, 220, 'M'), (221, 221, 'K'), (222, 228, '.')),
    156: ((58, 58, 'K'), (59, 84, 'M'), (85, 87, 'K'), (94, 106, 'K'),
          (175, 175, 'K'), (176, 221, 'M'), (222, 222, 'K')),
    157: ((58, 58, 'K'), (59, 87, 'M'), (88, 93, 'K'), (94, 106, 'M'), (107, 108, 'K'),
          (174, 214, 'K'), (215, 221, 'M'), (222, 222, 'K')),
    158: ((58, 58, 'K'), (59, 108, 'M'), (109, 110, 'K'),
          (173, 173, 'K'), (174, 214, 'D'), (215, 221, 'M'), (222, 222, 'K')),
    159: ((58, 58, 'K'), (59, 110, 'M'), (111, 111, 'K'),
          (172, 172, 'K'), (173, 214, 'D'), (215, 215, 'M'), (216, 220, 'K'), (221, 221, 'M'), (222, 222, 'K')),
    160: ((58, 58, 'K'), (59, 62, 'M'), (63, 67, 'K'), (68, 111, 'M'), (112, 112, 'K'),
          (172, 172, 'K'), (173, 214, 'D'), (215, 221, 'M'), (222, 222, 'K')),
    161: ((58, 58, 'K'), (59, 95, 'M'), (96, 100, 'D'), (101, 103, 'K'), (104, 104, 'D'), (105, 107, 'K'), (108, 108, 'D'), (109, 110, 'K'), (111, 111, 'D'), (112, 112, 'K'),
          (172, 172, 'K'), (173, 173, 'D'), (174, 176, 'K'), (177, 177, 'D'), (178, 180, 'K'), (181, 181, 'D'), (182, 184, 'K'), (185, 214, 'D'), (215, 220, 'M'), (221, 221, 'K')),
    162: ((59, 59, 'K'), (60, 93, 'M'), (94, 99, 'D'), (100, 100, 'K'), (101, 103, 'D'), (104, 104, 'K'), (105, 107, 'D'), (108, 108, 'K'), (109, 111, 'D'), (112, 112, 'K'),
          (172, 172, 'K'), (173, 176, 'D'), (177, 177, 'K'), (178, 180, 'D'), (181, 181, 'K'), (182, 184, 'D'), (185, 185, 'K'), (186, 214, 'D'), (215, 220, 'M'), (221, 221, 'K')),
    163: ((59, 59, 'K'), (60, 99, 'D'), (100, 100, 'K'), (101, 103, 'D'), (104, 104, 'K'), (105, 107, 'D'), (108, 108, 'K'), (109, 111, 'D'), (112, 112, 'K'),
          (172, 172, 'K'), (173, 176, 'D'), (177, 177, 'K'), (178, 180, 'D'), (181, 181, 'K'), (182, 184, 'D'), (185, 185, 'K'), (186, 219, 'D'), (220, 220, 'K')),
    164: ((60, 60, 'K'), (61, 99, 'D'), (100, 100, 'K'), (101, 103, 'D'), (104, 104, 'K'), (105, 107, 'D'), (108, 108, 'K'), (109, 110, 'D'), (111, 111, 'K'),
          (173, 173, 'K'), (174, 176, 'D'), (177, 177, 'K'), (178, 180, 'D'), (181, 181, 'K'), (182, 184, 'D'), (185, 185, 'K'), (186, 218, 'D'), (219, 219, 'K')),
    165: ((60, 111, 'K'), (173, 218, 'K')),
}
# The top of the neck where it bends, drawn clean; it rides the body's breathing.
NECK_TOP = {
    124: ((214, 221, 'K'), (222, 230, '.')),
    125: ((211, 221, 'L'), (222, 228, 'K'), (229, 232, '.')),
    126: ((212, 228, 'L'), (229, 232, 'K'), (233, 233, '.')),
}

def leg_of(x, y):
    """Which leg a pixel of the standing frame belongs to, or None (the body)."""
    if y < LEG_TOP: return None
    for i in (2, 3, 0, 1):                                # the near legs' edges win where two meet
        if LEGS[i][0](y) <= x <= LEGS[i][1](y): return i
    return None

def drop_at(x):
    """How far column x of the body is down, seated."""
    if x <= NECK[0]: return DROP
    if x >= NECK[1]: return NECK_DROP
    return DROP - round((DROP - NECK_DROP) * (x - NECK[0]) / (NECK[1] - NECK[0]))

def paint(px, runs_by_row, dy=0):
    for y, runs in runs_by_row.items():
        for x0, x1, c in runs:
            for x in range(x0, x1 + 1): px[x, y + dy] = INK[c]

def seated(fr, breath=0):
    """The standing frame, seated."""
    src = fr.load()
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = out.load()
    body = []; tail = {}
    for y in range(H):
        for x in range(W):
            if src[x, y][3] and leg_of(x, y) is None:    # the legs are not carried over: they are drawn folded
                if x <= TAIL[0] and y >= TAIL[1]: tail.setdefault(y, []).append(x)
                else: body.append((x, y))
    gave = sorted(HAIR_GIVES[:max(0, HAIR_LOW + DROP - (H - 1))])
    for (x, y) in body:
        up = 0
        if HAIR[0] <= x <= HAIR[1]:
            if y in gave: continue                        # a row of hair given up
            up = sum(1 for r in gave if r < y)
        ny = y + drop_at(x) - up
        assert ny < H, f'part of the body would go into the ground: {(x, y)}'
        px[x, ny] = src[x, y]
    turn = H - DROP                                       # the tail's first row that would be below the ground: from here it lies along it
    foot = min(tail[turn - 1])
    for y, xs in tail.items():
        for x in xs:
            if y < turn: px[x, y + DROP] = src[x, y]
            else:                                         # laid over: its right edge on the ground, running left from the foot of the hanging part
                nx, ny = foot - 1 - (y - turn), (H - 1) - (max(xs) - x)
                assert 0 <= nx, 'the tail would leave the frame'
                px[nx, ny] = src[x, y]
    for ny in range(H - 1 - (max(tail[turn]) - min(tail[turn])) + 1, H - 1):   # no outline across the tail where it turns
        if px[foot - 1, ny][3] and px[foot - 1, ny] != K: px[foot, ny] = px[foot - 1, ny]
    paint(px, NECK_TOP, breath)
    paint(px, FOLD)
    bare = [(x, y) for y in range(LEG_TOP, H) for x in range(W) if px[x, y][3] and px[x, y] != K   # close the outline where colour is left bare, and along the ground
            and (y == H - 1 or any(0 <= x + ax < W and not px[x + ax, y + ay][3] for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))))]
    for p in bare: px[p] = K
    return out

if __name__ == '__main__':
    sheet = Image.open(sys.argv[1]).convert('RGBA'); out = sys.argv[2]
    idle = [sheet.crop((f * W, 0, (f + 1) * W, H)) for f in range(FRAMES)]
    cols = lambda im: {c for n, c in im.getcolors(1 << 20) if c[3]}
    sat_fr = [seated(f, BREATH[i]) for i, f in enumerate(idle)]
    sat = Image.new('RGBA', (W * FRAMES, H * 8), (0, 0, 0, 0))
    for d in range(8):
        for f, im in enumerate(sat_fr): sat.paste(im, (f * W, d * H))
    for f, im in enumerate(sat_fr):                       # the body is the standing one, DROP lower: check it above the legs, left of the neck
        a, b = idle[f].crop((60, 0, 205, 100)), im.crop((60, DROP, 205, 100 + DROP))
        assert a.tobytes() == b.tobytes(), f'frame {f}: the body changed above the legs'
        assert cols(im) <= cols(sheet), f'frame {f}: a colour the standing sheet does not have'
    sat.save(out + '/30_dajna_sat.png')
    print('seated bbox', sat_fr[0].getchannel('A').getbbox(), 'standing', idle[0].getchannel('A').getbbox())
