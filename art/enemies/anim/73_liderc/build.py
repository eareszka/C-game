"""Liderc's animation (front view only -- a floating phaser, always faces the player like the flyers).
PixelLab from its approved 33x41 NES sprite on a 48x48 canvas.
  idle (4 x 260 ms): flicker-01, flicker-02, flare-02, flicker-04 -- flames leaping and sinking; idle frame 2 is
        the flare-up (beak wide, flames tall) when its spit cone leaves (breath_frame 2)
  flap (the streak, phase 2's shooting-star dash): streak-03 held -- legs tucked, flames swept wide
Run: python -B art/enemies/anim/73_liderc/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W, H = 48, 48
def frames():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal))
    idle = [L('flicker-01.png'), L('flicker-02.png'), L('flare-02.png'), pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', 'flicker-04.png')), pal), strong=True)]   # strong: clears its clumps
    return idle, [L('streak-03.png')] * 4
if __name__ == '__main__':
    idle, streak = frames(); gap = 4
    board = Image.new('RGBA', (5 * (W + gap) + gap, H + 2 * gap), (40, 40, 40, 255))
    for i, fr in enumerate(idle + streak[:1]): board.paste(fr, (gap + i * (W + gap), gap), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 4, board.height * 4), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    if '--install' in sys.argv:
        P = {'down': {'idle': idle, 'flap': streak}}
        d = os.path.join(ROOT, 'assets/enemies')
        pt.sheet(P, 'idle', os.path.join(d, '73_liderc_anim.png'), W, H, front_only=True)
        pt.sheet(P, 'flap', os.path.join(d, '73_liderc_streak.png'), W, H, front_only=True)
        print(pt.check_frames(os.path.join(d, '73_liderc_anim.png'), 4, W, H, views=(('down', 0),))[0])
