"""Bes Chem's animation (Two-mode, redone 2026-11-06 by the user: phase 1 perched, bursting and flapping;
phase 2 bursts, then flies to a new spot after each burst). Front view only (its NES sprite is drawn straight on).
PixelLab (pixellab/beschem-0N.png, from its 33x29 sprite on a 45x39 canvas): the chest mouth squeezing shut
and bursting open, wings shrugging. Colours snapped to the sprite's own palette.
  idle: SHUT (02), WIDE OPEN (04, frame 1: the e... e... e... rings leave on it), opening ring (03),
        rest (00), clenched (01)   5 x 260 ms = 1.3 s, the old loop
  idle sheet (phase 1): that mouth cycle with the wings beating over it (pixellab/beschem-flap-0N.png, PixelLab):
        wings out (02), UP (03, on the burst), out (04), down (00), lifting (01)
  alt sheet (perched in phase 2): the mouth cycle alone, wings still
  flap sheet (flying): the wingbeat down (00), out (02), up (03), out (04), legs TUCKED (the user: shaking or
        tucked, whichever reads as flying better -- tucked): the legs cleared, two curled feet up under the belly
The mouth's middle is the frame's middle, so the rings leave from the enemy's (x, y).
Run: python -B art/enemies/anim/69_bes_chem/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 45, 39
ORDER = [2, 4, 3, 0, 1]

def palette():
    s = Image.open(os.path.join(HERE, 'original_sprite.png')).convert('RGBA')
    return sorted({p for p in s.getdata() if p[3] == 255})

def snap(im, pal):
    out = im.convert('RGBA').copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            px[x, y] = min(pal, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2)
    return out

WINGS_ON_IDLE = [2, 3, 4, 0, 1]
BEAT = [0, 2, 3, 4]
MOUTH_R = 8.5            # the chest mouth: a disc this wide about the frame's middle

LEG = (215, 161, 117, 255)
OUTLINE = (0, 0, 0, 255)

def tuck(fr):
    """Legs up, evenly: everything from the legs' first row down cleared, then a curled foot (2 px of leg
    colour, outlined) under the belly for each leg -- the left leg's place mirrored for the right, same row."""
    out = fr.copy(); px = out.load()
    legs = [(x, y) for y in range(H) for x in range(W) if px[x, y] == LEG]
    if not legs: return out
    top = min(y for _, y in legs)
    left = [x for x, y in legs if x < W // 2]
    lx = round(sum(left) / len(left)) if left else W // 2 - 4    # the left leg's middle column
    for y in range(top, H):
        for x in range(W): px[x, y] = (0, 0, 0, 0)
    for x0 in (lx - 1, W - 1 - lx - 2):                            # left foot, and its mirror
        for i, c in enumerate((OUTLINE, LEG, LEG, OUTLINE)): px[x0 + i, top] = c
        for i in range(4): px[x0 + i, top + 1] = OUTLINE
    return out

def with_mouth(wing_frame, mouth_frame):
    """The wing pose, with the chest mouth (a disc about the middle) from the mouth pose."""
    out = wing_frame.copy(); po = out.load(); pm = mouth_frame.load()
    for y in range(H):
        for x in range(W):
            if (x + 0.5 - W / 2) ** 2 + (y + 0.5 - H / 2) ** 2 <= MOUTH_R ** 2: po[x, y] = pm[x, y]
    return out

def sheets():
    pal = palette()
    mouth = [snap(Image.open(os.path.join(HERE, 'pixellab', 'beschem-%02d.png' % i)), pal) for i in ORDER]
    flap = {i: snap(Image.open(os.path.join(HERE, 'pixellab', 'beschem-flap-%02d.png' % i)), pal) for i in range(5)}
    return {'idle': [with_mouth(flap[w], m) for w, m in zip(WINGS_ON_IDLE, mouth)],
            'perch': mouth, 'fly': [tuck(flap[i]) for i in BEAT]}

def frames(): return sheets()['idle']

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    S = sheets(); F = S['idle'] + S['perch'] + S['fly']
    board = Image.new('RGBA', (len(F) * (W + 4) + 4, H + 8), (40, 40, 40, 255))
    for i, fr in enumerate(F): board.paste(fr, (4 + i * (W + 4), 4), fr)
    board.resize((board.width * 5, board.height * 5), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    S = sheets()
    for k, name in (('idle', '69_bes_chem.png'), ('perch', '69_bes_chem_perch.png'), ('fly', '69_bes_chem_fly.png')):
        F = S[k]; im = Image.new('RGBA', (W * 8 * len(F), H))
        for d in range(8):
            for i, fr in enumerate(F): im.paste(fr, ((d * len(F) + i) * W, 0))
        im.save(os.path.join(ROOT, 'assets/enemies', name))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
