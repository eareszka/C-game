"""Paoxiao's eyeball spawners (phase 2): the sheet the spawner system draws.
Drawn here as NES pixel art in the game palette, so it passes the bible checker (tools/enemy_style.py):
a 17 px eye, squinting (an almond ~17x9; the user: "match the games bible checker as well as being slightly smaller") -- black outline,
white with a light-grey shade on its lower right, a few red veins, a mid-grey iris round a black pupil.
(The first cut was a 21 px PixelLab sprite, pixellab/eyeball.png: 31 colours off the palette.)
  0 emerge: squeezed to a slit          1 emerge: half open
  2-5 hover: the iris jerks 2 px left, right, up, back to the middle
  6 flash (firing): the ball swollen to 19 px, the pupil a pinprick, no iris
One row, 7 frames of 32x32 (the art centred), the same in every direction.
Run: python -B art/enemies/anim/11_paoxiao/build_spawner.py [--install]"""
import os, sys, math
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
S = 32
CLEAR = (0, 0, 0, 0)
BLACK, WHITE, SHADE, IRIS, RED = (0, 0, 0, 255), (252, 252, 252, 255), (198, 204, 218, 255), (132, 134, 148, 255), (182, 67, 61, 255)
CX = CY = 16.0
VEINS = [(-6, -2), (-5, 3), (6, 2), (5, -3), (-7, 0), (7, 1)]   # offsets from the middle, inside the rim

def ball(rx=8.6, ry=8.6, iris=(0, 0), pin=False):
    im = Image.new('RGBA', (S, S), CLEAR); px = im.load()
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - CX, y + 0.5 - CY
            e = (dx / rx) ** 2 + (dy / ry) ** 2
            if e > 1.0: continue
            if e > (1 - 1.0 / min(rx, ry)) ** 2 or ry < 2.5: px[x, y] = BLACK; continue    # the outline (a slit is all outline)
            ix, iy = dx - iris[0], dy - iris[1]; ri = math.hypot(ix, iy)
            if pin:
                px[x, y] = BLACK if abs(dx) < 1 and abs(dy) < 1 else (SHADE if dx + dy > rx * 0.62 else WHITE)
            elif ri <= (1.9 if ry > 6 else 1.3): px[x, y] = BLACK
            elif ri <= 3.4 * min(1.0, ry / rx * 1.4): px[x, y] = IRIS
            elif dx + dy > rx * 0.62: px[x, y] = SHADE
            else: px[x, y] = WHITE
    if ry >= 4 and not pin:
        for vx, vy in VEINS:
            x, y = int(CX + vx), int(CY + vy * ry / rx)
            if px[x, y] in (WHITE, SHADE): px[x, y] = RED
    return im

def frames():
    # squinting (the user: "the squinting shape instead of a full circle"): an almond, 17 x ~9
    return [ball(ry=1.6), ball(ry=3.2), ball(ry=SQ, iris=(-2, 0)), ball(ry=SQ, iris=(2, 0)), ball(ry=SQ, iris=(0, -1)),
            ball(ry=SQ), ball(rx=9.8, ry=6.2, pin=True)]
SQ = 4.9

if __name__ == '__main__':
    F = frames(); sheet = Image.new('RGBA', (S * len(F), S), CLEAR)
    for i, f in enumerate(F): sheet.paste(f, (i * S, 0), f)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    F[5].save(os.path.join(HERE, 'review', 'spawner_frame5.png'))
    board = Image.new('RGBA', sheet.size, (40, 40, 40, 255)); board.paste(sheet, (0, 0), sheet)
    board.resize((board.width * 6, board.height * 6), Image.NEAREST).save(os.path.join(HERE, 'review', 'spawner.png'))
    if '--install' in sys.argv: sheet.save(os.path.join(ROOT, 'assets/enemies/11_paoxiao_spawner.png')); print('installed', sheet.size)
