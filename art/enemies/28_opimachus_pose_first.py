"""Enemy 28 Opimachus, first-frame draft: the user's reference without wings, in the old sprite's sand and gold.

A crouched, sitting cat-griffin, body turned a little as in the reference: curled
crest, dark face, hooked beak tipped to our left, a gold hood over the
shoulders, front legs together, the haunch to our right, tail round to our left. Literal pixel rows, drawn through the Aseprite pixel
plugin. Writes only a draft and a review; the game's assets are not touched.

    python art/enemies/28_opimachus_pose_first.py          # draw, check, write the draft
    python art/enemies/28_opimachus_pose_first.py look DIR  # PIL render only, for looking at
"""
from pathlib import Path
import colorsys, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff
W, H = 50, 39                 # the old sheet's frame
PAL = {'K': '000000',
       'd': '94703d', 's': 'b2966a', 'l': 'f4ce80',   # sand fur: dark, mid, light
       'g': 'd89830', 'y': 'f0bc3c',                  # gold: hood, beak, claws
       'b': '633e1b',                                 # face mask, tail bands
       'r': 'b6433d'}                                 # crest, chest
RGB, N4 = ff.rgb(PAL), ff.N4

# row: (first column, letters), ...   One letter a pixel, '.' nothing.
ROWS = {
    3:  [(23, 'rr...rr')],                                          # crest: four plumes of different heights, each tip curled over to our left
    4:  [(22, 'r..r.r..r')],
    5:  [(19, 'rr....r....r..rr')],
    6:  [(18, 'r..r..rr...rr.r..r')],
    7:  [(21, 'rr.rr..rr...rr')],
    8:  [(21, 'rr.rr.rr..rrr')],
    9:  [(21, 'rrrrrrrrrrr')],
    10: [(22, 'rrrrrrrr')],
    11: [(21, 'KKKKKKKK')],                                         # head
    12: [(20, 'KbbbbbbbbK')],
    13: [(19, 'KbbbbbbbbbbK')],
    14: [(19, 'KbybbbbbbybK')],                                     # eyes: two gold pixels each, slanted in
    15: [(19, 'KbbybllbybbK')],
    16: [(19, 'KbbblllsbbbK')],                                     # beak, pale, hooking to our left
    17: [(17, 'KKKbbbllssbbbKKKK')],                                # shoulders start either side of the head
    18: [(16, 'KyygKbKllsKbbKgyyyK')],
    19: [(15, 'KyggggKKlsKKKKggggyyK')],
    20: [(15, 'KgggggdKlKddddggggggK')],                            # hood, the chin's shadow on it
    21: [(15, 'KggggggdKddddgggggggK')],
    22: [(15, 'KlggggggggggggggglllK')],
    23: [(16, 'KlggggggggggggllKKKK')],                             # the haunch comes out under the hood
    24: [(9, 'K'), (17, 'KllggggggggllKKsllK')],                    # tail tip
    25: [(7, 'KKbK'), (17, 'KKKlgggggllKKsslllsK')],
    26: [(6, 'KbbK'), (16, 'KsssKllgllKKssKsllsssK')],              # front legs leave the hood
    27: [(5, 'KbbK'), (16, 'KsllsKKlKKsllsKsslsssK')],
    28: [(4, 'KssK'), (16, 'KsllsKrKrKslssKssssssK')],              # chest
    29: [(4, 'KssK'), (16, 'KslssKrrrKslssKsssssssK')],
    30: [(4, 'KbbK'), (14, 'KKK'), (17, 'KlsdKrrrKdssKdsssssssK')], # tail comes round from behind the leg
    31: [(4, 'KssK'), (12, 'KKbbs'), (17, 'KssdKrrrKdssKddssssssK')],
    32: [(4, 'KsssKKKKssbbs'), (17, 'KssdKdddKdssKddssssssK')],
    33: [(5, 'Ksssbbsssbbs'), (17, 'KssdKdddKdssKddddssssK')],
    34: [(6, 'KddbbdddKKK'), (17, 'KsssKdddKsssKdddddssK')],
    35: [(7, 'KKKKKKK'), (17, 'KsssKdddKsssKKKKKKKKK')],
    36: [(16, 'KllsssKKKllsssKsssssssK')],                          # paws
    37: [(16, 'KsssssKKKsssssKsssssssK')],
    38: [(17, 'gKgKgKKKgKgKgKKgKgKgK')],                            # claws on the baseline
}


def pose():
    return ff.grid(ROWS, PAL)


def checks(g):
    """The numbers shown with the frame: the shared checks, then this palette's own hue families."""
    out = ff.checks(g, PAL, W, H, old='front 20 x 36 (rows 3-38), 3/4 34 x 36',
                    open_ok=lambda p, c: (c == 'r' and p[1] <= 10) or (c == 'g' and p[1] == H - 1))   # crest plumes, claws
    hv = {c: colorsys.rgb_to_hsv(*(v / 255 for v in RGB[c])) for c in PAL if c != 'K'}
    warm = [round(hv[c][0] * 360) for c in 'dslgyb']
    assert max(warm) - min(warm) <= 15, warm
    vals = [round(hv[c][2] * 100) for c in 'dsl']
    assert all(b - a >= 12 for a, b in zip(vals, vals[1:])), vals
    return out + [f'warm tones within hue {min(warm)}-{max(warm)}; sand ramp value steps {vals}']


def image(g, bg=(0, 0, 0, 0)):
    return ff.image(g, PAL, W, H, bg)


def review(im, out):
    old = Image.open(ROOT / 'assets/enemies/28_opimachus.png').convert('RGBA').crop((0, 0, W, H))
    ff.review([('DRAFT', im), ('IN GAME', old), ('PLAYER', ff.player()), ('SILHOUETTE', ff.silhouette(im))], out)


if __name__ == '__main__':
    g = pose()
    for line in checks(g): print(line, flush=True)
    if sys.argv[1:2] == ['look']:
        d = Path(sys.argv[2]); d.mkdir(parents=True, exist_ok=True)
        review(image(g), d / '28_look.png')
        image(g, (0, 0, 0, 255)).resize((W * 10, H * 10), Image.Resampling.NEAREST).save(d / '28_big.png')
    else:
        im = ff.draw_plugin(g, PAL, W, H, HERE / '28_opimachus_frame0_draft')
        ff.style_check(im, sys.argv[1] if sys.argv[1:] else HERE, '28_opimachus')
        review(im, HERE / '28_review.png')
