"""The boy asleep, for the intro's opening: assets/story/boy_sleep.png, in the
residents' sleep-sheet layout (include/npc_sleep.h): 56x20, four 14x20 cels,
two per head side, the second of each pair breathing in. npc_sleep_draw
turns a cel 90 degrees into the bed, so the cels are his own side frames
from assets/player_small.png: facing left for the head at the right (the
face then looks up), facing right for the head at the left. Breathing in,
his chest (rows 13-15) comes a pixel forward.

    python art/story/intro/boy_sleep.py
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
FACE_LEFT, FACE_RIGHT, W, H = 6, 8, 14, 20
CHEST = range(13, 16)


def frame(sheet, f):
    return sheet.crop((f * W, 0, f * W + W, H))


def breathe(cel, forward):
    """The chest rows shifted a pixel the way he faces."""
    out = cel.copy()
    for y in CHEST:
        row = [cel.getpixel((x, y)) for x in range(W)]
        for x in range(W):
            src = x + forward if 0 <= x + forward < W else None
            out.putpixel((x, y), row[src] if src is not None else (0, 0, 0, 0))
    return out


if __name__ == '__main__':
    sheet = Image.open(os.path.join(ROOT, 'assets', 'player_small.png')).convert('RGBA')
    left, right = frame(sheet, FACE_LEFT), frame(sheet, FACE_RIGHT)
    out = Image.new('RGBA', (4 * W, H))
    for i, cel in enumerate([left, breathe(left, 1), right, breathe(right, -1)]):
        out.alpha_composite(cel, (i * W, 0))
    out.save(os.path.join(ROOT, 'assets', 'story', 'boy_sleep.png'))
    print('boy_sleep.png written')
