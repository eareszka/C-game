"""Tripodero's animation (phase 1 stands and sights; phase 2 dances on its telescopic legs). PixelLab, 44x56.
views: down = its approved NES sprite; right = rotate's east-02, up = north-04; left mirrored.
  idle (5 x 260 ms = 1.3 s, the old loop): IDLE order of pixellab/idle-VIEW-NN -- frame 1 legs tall, nose
        sighted (the SLUG, Tripodero::breathe), frame 3 the pouch SPIT (on_idle_frame)
  flap (the dance, 4; Tripodero::update's map: 0 step out LEFT, 1 planted, 2 step out RIGHT, 3 planted; 260 ms a
        pose). The user: "the dance needs to be very dramatic leg movement, a good reference is the dance from 2
        redesigns ago" -- the first hand-made dance (reference_dance_ee91b1ff.png, commit ee91b1ff): stilts in a
        wide A-frame, one leg flung far out and up, alternating. So:
          front/back: the step = a PixelLab EDIT, one stilt swung out to the side, foot about knee height
                      (pixellab/step-VIEW.png; the high kicks, kick-VIEW.png, were "too dramatic, tone it back"),
                      mirrored for the step the other way; the plants = PixelLab's wide A stances
                      (dance2-VIEW-02/03), jolted a pixel down so they land hard
          side:       PixelLab's big kicks dance2-right-03 / -04 with plants -00 / -01
        (The first cut, pixellab/dance-VIEW-NN, was too subtle.)
Run: python -B art/enemies/anim/59_tripodero/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W, H = 44, 56
VIEWS = ('down', 'right', 'up')
IDLE = [0, 3, 2, 1, 4]
def poses():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal))
    return {v: {'idle': [L('idle-%s-%02d.png' % (v, i)) for i in IDLE],
                'flap': dance(v, L)} for v in VIEWS}

def dance(v, L):
    if v == 'right':
        return [L('dance2-right-03.png'), pt.jolt(L('dance2-right-00.png'), 0, 1), L('dance2-right-04.png'), pt.jolt(L('dance2-right-01.png'), 0, 1)]
    kick = L('step-%s.png' % v)                     # its step goes out to the screen's right
    return [pt.mirror(kick), pt.jolt(L('dance2-%s-02.png' % v), 0, 1), kick, pt.jolt(L('dance2-%s-03.png' % v), 0, 1)]
if __name__ == '__main__':
    P = poses(); gap = 4
    board = Image.new('RGBA', (9 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for r, v in enumerate(VIEWS):
        for c, fr in enumerate(P[v]['idle'] + P[v]['flap']): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies/redraws')
        pt.sheet(P, 'idle', os.path.join(d, '59_tripodero.png'), W, H)
        pt.sheet(P, 'flap', os.path.join(d, '59_tripodero_dance.png'), W, H)
        for name, n in (('59_tripodero.png', 5), ('59_tripodero_dance.png', 4)):
            print(name); print('\n'.join('  ' + l for l in pt.check_frames(os.path.join(d, name), n, W, H)))
