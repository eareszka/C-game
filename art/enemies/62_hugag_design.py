"""62 Hugag, big tier, to art/direction/SPRITE_STYLE.md: its first frame, drawn pixel by pixel after the
user's reference (A Book of Creatures' hugag, seen from the side).

    python art/enemies/62_hugag_design.py      # writes art/enemies/62_hugag_frame.png (98x65) and draft.png

The user (2026-10-10): "face and make the body look more like a bush and match the reference"; before that,
"try not to use shapes" and "not too bloby". So every pixel below is placed by hand, a letter a colour, in
rows of (row, first column, pixels) -- no ellipses, no polygons:
- the body is a shaggy mound, a bush: lit along the top of its hump, green down its sides, dark under its
  overhang, with a few long blades drawn down it and a ragged gold fringe along its hem;
- a bare pink neck comes out of its front and carries the head up and out, clear of the body -- the
  reference's silhouette;
- the head has a face: four big lobes on its crown, an eye, a nostril, a mouth corner, the great lip hanging
  down in front, and a ragged beard under the jaw;
- four jointless legs that narrow toward big clawed feet, the far pair shorter and in shade.
Eight colours and black. The other frames are made from this one by 62_hugag_follow.py."""
import os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
PAL = {'K': '000000', 'L': '4fa667', 'G': '2c6c44', 'D': '235436', 'Y': 'c18a39', 'b': '785830', 't': 'd7a175', 'P': 'ec8476', 'R': 'b6433d'}
W, H, X0, Y0, GW = 98, 65, 17, 3, 64               # the frame; the drawing is GW wide and sits X0, Y0 in

LEGS = (
    [(y, 5, 'KtttK') for y in range(34, 46)] + [(y, 6, 'KttK') for y in range(46, 58)] +          # near hind leg
    [(58, 5, 'KttttK'), (59, 4, 'KtttttttK'), (60, 4, 'KttKttKtK'), (61, 4, 'KKKKKKKKK')] +
    [(y, 13, 'KttbK') for y in range(34, 46)] + [(y, 14, 'KtbK') for y in range(46, 56)] +        # far hind leg: shorter, shaded
    [(56, 13, 'KttbbK'), (57, 13, 'KttKtbK'), (58, 13, 'KKKKKKK')] +
    [(y, 23, 'KtttK') for y in range(34, 46)] + [(y, 24, 'KttK') for y in range(46, 58)] +        # near front leg
    [(58, 23, 'KttttK'), (59, 22, 'KtttttttK'), (60, 22, 'KttKttKtK'), (61, 22, 'KKKKKKKKK')] +
    [(y, 31, 'KttbK') for y in range(34, 46)] + [(y, 32, 'KtbK') for y in range(46, 56)] +        # far front leg
    [(56, 31, 'KttbbK'), (57, 31, 'KttKtbK'), (58, 31, 'KKKKKKK')]
)
COAT = [
    (14, 18, 'KKKKKKKK'),
    (15, 15, 'KKKLLLLLLLLKKK'),
    (16, 12, 'KKKLLLLLLLLLLLLLLKKK'),
    (17, 10, 'KKLLLLLLLLLLLLLLLLLLGGKK'),
    (18, 8, 'KKLLLLLLLLLLLLLLGGGGGGGGGGK'),
    (19, 6, 'KKLLLLLLLLLLGGGGGGGGGGGGGGGGGK'),
    (20, 5, 'KLLLLLLLGGGGGGGGGGGGGGGGGGGGGGGK'),
    (21, 4, 'KLLLLLGGGGGGGGGGGGGGGGGGGGGGGGGGK'),
    (22, 3, 'KLLLGGGGGGGGKGGGGGGGGGGGGKGGGGGGGK'),
    (23, 3, 'KLGGGGGGGGGGKGGGGGGKGGGGGKGGGGGGK'),
    (24, 2, 'KGGGGGGKGGGGGKGGGGGGKGGGGGKGGGGGGK'),
    (25, 2, 'KGDDDDDKGDDDDKGGGDDDKGGDDDKGGGGGG'),
    (26, 2, 'KDDDDDDKDDDDDKDDDDDDKDDDDDKDDDDD'),
    (27, 2, 'KDDDDDDKDDDDDKDDDDDDKDDDDDKDDDDDK'),
    (28, 2, 'KDYDDDDKDYYDDKDDDYDDKDDYDDKDDYDDK'),
    (29, 2, 'KYYYDDYKYYYYDKDYYYYDKDYYYDKDYYYDK'),
    (30, 2, 'KYYYYYYKYYYYYKYYYYYYKYYYYYKYYYYYK'),
    (31, 1, 'KKYYYbYYKYYYYbKYYYYYbKYYYYbKYYYYbK'),
    (32, 0, 'KKYYbbYYKYYYbbKYYYYbbKYYYbbKYYYbbK'),
    (33, 0, 'KYYbbKYbKYbbbKKYYbbbKKYbbbKKYbbbK'),
    (34, 1, 'KbbKKbbKKbbKK.KbbbKK.KbbKK.KbbKK'),
    (35, 2, 'KK..KK..KK....KKK....KK....KK'),
]
NECK = [
    (13, 42, 'KPP'), (14, 41, 'KPPP'), (15, 40, 'KPPPRK'), (16, 40, 'KPPRRK'), (17, 39, 'KPPPRK'), (18, 39, 'KPPRRK'),
    (19, 38, 'KPPPRK'), (20, 38, 'KPPRRK'), (21, 37, 'KPPPRK'), (22, 37, 'KPPRRK'), (23, 36, 'KPPPRK'), (24, 36, 'KPPRRK'),
    (25, 35, 'KPPPRK'), (26, 34, 'KPPRRK'), (27, 35, 'PPRRK'), (28, 35, 'PRRK'), (29, 35, 'RRK'), (30, 35, 'K'),
]
HEAD = [
    (2, 47, 'KK'), (2, 52, 'KKK'),
    (3, 46, 'KPPK'), (3, 51, 'KPPPK'), (3, 57, 'KK'),
    (4, 45, 'KPPPPKKPPPPPKPPK'),
    (5, 44, 'KPPRPPPPRPPPPPRPPK'),
    (6, 44, 'KPRPPPPRPPPPPRPPPK'),
    (7, 43, 'KPPPPPPPPPPPPPPPPPPK'),
    (8, 43, 'KRPPPPPPPPPPPPPPPPPK'),
    (9, 43, 'KRPPPPPPPPKtPPPPPPPK'),
    (10, 44, 'KRPPPPPPPPPPPPPPPPK'),
    (11, 44, 'KRRPPPPPPPPPPPPPPPK'),
    (12, 44, 'KKRRPPPPPPPPPPPPPPK'),
    (13, 45, 'KRRPPPPPKPPPPPPPPK'),
    (14, 45, 'KKRRPPPKKPPPPPPPPK'),
    (15, 47, 'KRRPPKK.KRPPPPPK'),
    (16, 48, 'KRRRK...KRPPPPPK'),
    (17, 48, 'KRKRK...KRPPPPPK'),
    (18, 48, 'KRKRK....KRPPPPK'),
    (19, 48, 'KK.KK....KRRPPPK'),
    (20, 49, 'K..K.....KRRPPK'),
    (21, 58, 'KRRPPK'), (22, 59, 'KRRPK'), (23, 59, 'KRRK'), (24, 60, 'KK'),
]

def drawing():
    g = {}
    for part in (LEGS, COAT, NECK, HEAD):                                  # later parts lie over earlier ones
        for y, x0, s in part:
            for i, c in enumerate(s):
                if c != '.':
                    assert 0 <= x0 + i < GW, (y, x0, s)
                    g[(x0 + i, y)] = c
    return g

if __name__ == '__main__':
    g = drawing()
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (x, y), c in g.items(): im.putpixel((X0 + x, Y0 + y), tuple(int(PAL[c][k:k + 2], 16) for k in (0, 2, 4)) + (255,))
    im.save(os.path.join(HERE, '62_hugag_frame.png'))
    bg = Image.new('RGBA', (W * 2, H), (0, 0, 0, 255)); bg.alpha_composite(im, (0, 0))
    sil = Image.new('RGBA', (W, H), (255, 170, 200, 255)); sil.paste((0, 0, 0, 255), (0, 0), im.getchannel('A')); bg.paste(sil, (W, 0))
    bg.resize((bg.width * 6, bg.height * 6), Image.NEAREST).save('draft.png')
    ys = [y for x, y in g]; xs = [x for x, y in g]
    print('drawn', max(xs) - min(xs) + 1, 'x', max(ys) - min(ys) + 1, 'colours', len(set(g.values())))
