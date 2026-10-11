"""62 Hugag: every other frame made from the user's frame 0.

    python art/enemies/62_hugag_follow.py FRAME0.png OUTDIR
        FRAME0: frame 0 of assets/enemies/62_hugag.aseprite, 98x65 (the user's drawing, 2026-10-10, after
                their reference: lumpy bare head on a long drooping face, shaggy green coat with a gold
                fringe, four stilt legs)
        writes OUTDIR/62_hugag.png (idle, 5 frames) and OUTDIR/62_hugag_stomp.png (stomp, 4 frames), each
        8 directions of the one view (left-facing ones mirrored), and review.png

Frame 0 is the drawing exactly; nothing in it is redrawn and nothing is drawn from shapes. The other frames
are that drawing with pixels moved:
  idle 1, 3   it sinks a pixel on its stilts (a row out of the legs, everything above it down one);
  idle 2      the bellow -- its head, from the neck out, lifted two pixels and its mouth open: two rows
              of dark across the drooping face (the frame its fight bellows on);
  idle 4      as frame 0;
  stomp 0     the near front leg swung out to the side, off the ground;
  stomp 1     SLAM: sunk a pixel, dust at that hoof;
  stomp 2     the other front leg lifted (the same leg, shorter: its hoof off the ground);
  stomp 3     SLAM: sunk a pixel, dust at that hoof.
The dust is the one thing drawn here, pixel by pixel (DUST)."""
import sys, os
from PIL import Image, ImageOps
W, H = 98, 65
K, T = (0, 0, 0, 255), (0, 0, 0, 0)
TAN, BROWN, RED = (0xd7, 0xa1, 0x75, 255), (0x78, 0x58, 0x30, 255), (0xb6, 0x43, 0x3d, 255)
# Where things are in the drawing (art px; 62_hugag_design.py's grid sits 17 across, 3 down):
NECK_X = 58                    # from this column right is the head (and the top of its neck): it lifts for the bellow
JAW = (62, 20, 74, 27)         # ...all but its jaw line and hanging beards [x0, y0, x1, y1): they stay, so the mouth opens
MOUTH = (63, 18, 72, 20)       # ...and this is the gap that opens: dark inside
LEG_ROW = 50                   # a row through all four legs where they are plain: the one that goes when it sinks
NEAR = (39, 48, 38, 64)        # the near front leg: its columns [x0, x1), the row it leaves the fringe at, its ground
OTHER = (48, 56, 38, 61)       # the far front leg (shorter: it stands further back)
DUST = ['...KK...KK..', '..KttKKKttK.', '.KttttKttttK', '.KtbbtttbbtK', '..KKKKKKKKK.']

def sunk(fr):
    out = Image.new('RGBA', (W, H), T)
    out.paste(fr.crop((0, 0, W, LEG_ROW)), (0, 1)); out.paste(fr.crop((0, LEG_ROW + 1, W, H)), (0, LEG_ROW + 1))
    return out

def bellow(fr):
    out = fr.copy(); px = out.load(); src = fr.load()
    stays = lambda x, y: JAW[0] <= x < JAW[2] and JAW[1] <= y < JAW[3]
    for y in range(H):
        for x in range(NECK_X, W):
            if stays(x, y): continue
            px[x, y] = src[x, y + 2] if y + 2 < H and not stays(x, y + 2) else T
    for y in range(MOUTH[1], MOUTH[3]):                                      # the open mouth, its corners black
        for x in range(MOUTH[0], MOUTH[2]): px[x, y] = RED
        px[MOUTH[0] - 1, y] = K; px[MOUTH[2], y] = K
    return out, ((MOUTH[0] + MOUTH[2]) // 2, MOUTH[1])

def without_leg(fr, leg):
    x0, x1, top, ground = leg
    out = fr.copy(); out.paste(T, (x0, top + 1, x1, H)); return out

def leg_rows(fr, leg):
    x0, x1, top, ground = leg
    return [fr.crop((x0, y, x1, y + 1)) for y in range(top + 1, H) if fr.crop((x0, y, x1, y + 1)).getbbox()]

def swung(fr, leg):
    """The leg out to the side: its own rows, every other one, each a pixel further right; its hoof at the end."""
    x0, x1, top, ground = leg
    rows = leg_rows(fr, leg); shaft, hoof = rows[:-4], rows[-4:]
    out = without_leg(fr, leg)
    for k, r in enumerate(shaft[::2][:11]): out.alpha_composite(r, (x0 + k, top + 1 + k))
    n = min(len(shaft[::2]), 11)
    for j, r in enumerate(hoof): out.alpha_composite(r, (x0 + n, top + 1 + n + j))
    return out

def lifted(fr, leg, up=9):
    """The leg lifted: the same leg with `up` rows gone from its shaft, so its hoof is off the ground."""
    x0, x1, top, ground = leg
    rows = leg_rows(fr, leg); keep = rows[:len(rows) - 3 - up] + rows[-3:]
    out = without_leg(fr, leg)
    for k, r in enumerate(keep): out.alpha_composite(r, (x0, top + 1 + k))
    return out

def dusted(fr, leg):
    x0, x1, top, ground = leg
    out = fr.copy(); px = out.load(); tone = {'K': K, 't': TAN, 'b': BROWN}
    cx = (x0 + x1) // 2 - 6
    for j, r in enumerate(DUST):
        for i, c in enumerate(r):
            if c != '.' and 0 <= cx + i < W: px[cx + i, ground - len(DUST) + 1 + j] = tone[c]
    return out

def sheet(frames):
    out = Image.new('RGBA', (W * len(frames) * 8, H), T)
    for d in range(8):
        for f, fr in enumerate(frames): out.paste(ImageOps.mirror(fr) if d in (5, 6, 7) else fr, ((d * len(frames) + f) * W, 0))
    return out

if __name__ == '__main__':
    f0 = Image.open(sys.argv[1]).convert('RGBA'); outdir = sys.argv[2]
    assert f0.size == (W, H), f0.size
    low = sunk(f0)
    open_, mouth = bellow(f0)
    idle = [f0, low, open_, low, f0]
    stomp = [swung(f0, NEAR), dusted(low, NEAR), lifted(f0, OTHER), dusted(low, OTHER)]
    sheet(idle).save(os.path.join(outdir, '62_hugag.png')); sheet(stomp).save(os.path.join(outdir, '62_hugag_stomp.png'))
    rv = Image.new('RGBA', (W * 5, H * 2), (0, 0, 0, 255))
    for i, f in enumerate(idle): rv.alpha_composite(f, (i * W, 0))
    for i, f in enumerate(stomp): rv.alpha_composite(f, (i * W, H))
    rv.resize((rv.width * 4, rv.height * 4), Image.NEAREST).save(os.path.join(outdir, 'review.png'))
    print('bellow mouth (art px):', mouth, '| slam feet x:', (NEAR[0] + NEAR[1]) // 2, (OTHER[0] + OTHER[1]) // 2)
