"""67 Lagopus breathing idle, front-only (the same 3 frames in all 8 views, as on 22, 28 and 63), 260 ms a frame.
The row's loop {0,1,0,2} plays them mid, in, mid, out:
    f0 half breath (rest)   f1 full breath in, chest up, wings drawn in (the class's "tips up")   f2 the still (out, wings spread)
f0 f1: one PixelLab animate of the still ("breathing idle"); f2: the still itself. All snapped to the still's colours.
The breath lifts the head 4 px, so the frame grows from 42x32 to 42x36 (feet on the same bottom row).
The fly sheet (flap, FLAP_FRAMES 4 = wings up, mid, down, mid; Lagopus::BEAT_T 4 x 110 ms), legs "still underneath
the sprite just tucked behind" (the user; the first try, paws up on the belly, was too far): the first wingbeat's spread
frame (mid_hang.png) PixelLab-edited ("feet pulled up shorter and folded back behind the belly, toes peek out below")
-> pixellab/under_key.png, then animate under_key --last under_key ("flapping ... short feet stay tucked just under and
behind its belly ... body and head still"); frames: up ufa-02, mid the key, down pixellab/down_key.png (a PixelLab
edit of the key: "the downstroke ... wings swept down low", seed c, checker clean; the animate's own down was malformed), mid ufa-07; snapped to the still's colours, cut to 52x43 (centred
on the body); front-only, all 8 views.
Run: python -B build.py [--install] [--install-fly]"""
import os, sys, glob, time
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, *['..'] * 4))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import enemy_sheet as es, enemy_style as st
GAME = os.path.join(ROOT, 'assets/enemies/redraws/67_lagopus.png')
STILL = Image.open(GAME).convert('RGBA').crop((0, 0, 42, 32))
PAD = (4, 6)                                   # where the still sits in pixellab/still_pad.png (50x40)
BOX = (4, 2, 46, 38)                           # the frame cut from the 50x40 PixelLab frames: 42x36
def G(pat):
    got = glob.glob(os.path.join(HERE, pat)); assert len(got) == 1, (pat, got); return got[0]
FRAMES = [G('pixellab/*breathing*/br-02.png'), G('pixellab/*breathing*/br-04.png'), None]   # None: the still
FLY = [G('pixellab/*under-key*/ufa-02.png'), G('pixellab/under_key.png'), G('pixellab/down_key.png'), G('pixellab/*under-key*/ufa-07.png')]   # up, mid, down, mid; feet tucked under, behind the belly
FLY_BOX = (10, 7, 62, 50)
GAME_FLY = os.path.join(ROOT, 'assets/enemies/redraws/67_lagopus_fly.png')
KEYS = sorted({c[:3] for c in STILL.getdata() if c[3]})

def snap(im):
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); p, o = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3] >= 128: o[x, y] = min(KEYS, key=lambda k: sum((a - b) ** 2 for a, b in zip(k, c[:3]))) + (255,)
    return out

def frame(path):
    if path is None:
        f = Image.new('RGBA', (50, 40), (0, 0, 0, 0)); f.paste(STILL, PAD)
    else:
        f = snap(Image.open(path).convert('RGBA'))
    assert f.getbbox()[0] >= BOX[0] and f.getbbox()[1] >= BOX[1] and f.getbbox()[2] <= BOX[2], (path, f.getbbox())
    return f.crop(BOX)

def gif(fr, path, z=2):
    big = []
    for f in fr:
        bg = Image.new('RGBA', f.size, (0, 0, 0, 255)); bg.alpha_composite(f); big.append(bg.convert('RGB').resize((f.width * z, f.height * z), 0))
    big[0].save(path, save_all=True, append_images=big[1:], duration=260, loop=0, disposal=1, optimize=False)
    g = Image.open(path); assert g.n_frames == len(fr), 'gif merged frames'
    for k in range(len(fr)):
        g.seek(k); g.load(); assert g.convert('RGB').tobytes() == big[k].tobytes(), f'gif frame {k} does not read back'

if __name__ == '__main__':
    fr = [frame(p) for p in FRAMES]
    for k, f in enumerate(fr):
        (_, bad), nes = st.check(f), st.check_nes(f)
        print('f%d' % k, 'top', f.getbbox()[1], 'check', bad or 'clean', 'nes', nes or 'clean')
    sheet = Image.new('RGBA', (42 * 3 * 8, 36), (0, 0, 0, 0))
    for d in range(8):
        for k, f in enumerate(fr): sheet.paste(f, ((d * 3 + k) * 42, 0))
    sheet.save(os.path.join(HERE, '67_lagopus_breath.png'))
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    gif([fr[i] for i in (0, 1, 0, 2)], os.path.join(rv, 'breath_loop_260.gif'))     # as the game plays it
    z = 4; still = Image.new('RGBA', (42, 36), (0, 0, 0, 0)); still.paste(STILL, (0, 4))
    row = [still] + fr; b = Image.new('RGBA', (len(row) * 42 * z + (len(row) - 1) * 8, 36 * z), (0, 0, 0, 255))
    for k, f in enumerate(row): b.alpha_composite(f.resize((42 * z, 36 * z), 0), (k * (42 * z + 8), 0))
    b.save(os.path.join(rv, 'breath_board.png'))
    print('wrote 67_lagopus_breath.png, review/breath_loop_260.gif, review/breath_board.png (the still, then f0 f1 f2)')
    fly = []
    for p in FLY:
        f = snap(Image.open(p).convert('RGBA')); b = f.getbbox()
        assert b[0] >= FLY_BOX[0] and b[1] >= FLY_BOX[1] and b[2] <= FLY_BOX[2] and b[3] <= FLY_BOX[3], (p, b)
        f = f.crop(FLY_BOX); fly.append(f)
        (_, bad), nes = st.check(f), st.check_nes(f)
        print('fly', os.path.basename(p), 'check', bad or 'clean', 'nes', nes or 'clean')
    fw, fh = fly[0].size
    fsheet = Image.new('RGBA', (fw * 4 * 8, fh), (0, 0, 0, 0))
    for d in range(8):
        for k, f in enumerate(fly): fsheet.paste(f, ((d * 4 + k) * fw, 0))
    fsheet.save(os.path.join(HERE, '67_lagopus_fly_new.png'))
    gif(fly, os.path.join(rv, 'fly_260.gif'))
    b = Image.new('RGBA', (4 * fw * z + 24, fh * z), (0, 0, 0, 255))
    for k, f in enumerate(fly): b.alpha_composite(f.resize((fw * z, fh * z), 0), (k * (fw * z + 8), 0))
    b.save(os.path.join(rv, 'fly_board.png'))
    print('wrote 67_lagopus_fly_new.png (%dx%d frames), review/fly_260.gif, review/fly_board.png' % (fw, fh))
    if '--install-fly' in sys.argv:
        bk = os.path.join(ROOT, 'art/_backup', '67_fly_' + time.strftime('%Y%m%d_%H%M%S'))
        print('installed fly', es.install(fsheet, GAME_FLY, 4, backup=bk), 'backup', bk)
    if '--install' in sys.argv:
        bk = os.path.join(ROOT, 'art/_backup', '67_idle_' + time.strftime('%Y%m%d_%H%M%S'))
        print('installed', es.install(sheet, GAME, 3, ms=260, backup=bk), 'backup', bk)
