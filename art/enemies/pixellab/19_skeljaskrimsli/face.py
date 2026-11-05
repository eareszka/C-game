"""19 Skeljaskrimsli's head turned to look at the player (the user, 2026-10-29: "now have the head looking at the
player"), as the Dungavenhooter's: drawn by hand over the profile head of idle_frame0_profile.png (reference 4's
pose in reference 5's look), in front of the body. Its charcoal head seen from the front: two small pointed
ears, two glowing green eyes, a wide mouth of glowing green fangs round a dark throat, the shaggy mane under its
chin. paste(frame) puts the same face on an animated frame. By hand: one more PixelLab edit would pass the 60
generations it may spend.

    python art/enemies/pixellab/19_skeljaskrimsli/face.py   -> idle_frame0_clean.png
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
PAL = {'c': h('34343e'), 'd': h('1e1e24'), 'G': h('a8f0bc'), 'g': h('2c6c44'), 'K': (0, 0, 0)}
FACE = [
    '.c.........c.',
    '.cc.......cc.',
    '.ccccccccccc.',
    'ccccccccccccc',
    'ccGGcccccGGcc',
    'ccgGcccccGgcc',
    'ccccccccccccc',
    'cccKKKKKKKccc',
    'ccKGKGKGKGKcc',
    'ccKKKKKKKKKcc',
    'ccKgKgKgKgKcc',
    'dcccKKKKKccdd',
    'd.dcccccccd.d',
    '..d.d.d.d.d..',
]
AT = (4, 21)                     # its top left on the 86x43 canvas


def face():
    return {(AT[0] + x, AT[1] + y): PAL[ch] for y, r in enumerate(FACE) for x, ch in enumerate(r) if ch != '.'}


def paste(im):
    out = im.copy()
    g = face()
    for p, col in g.items():
        out.putpixel(p, col + (255,))
    for (x, y) in g:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in g and not out.getpixel(q)[3]:
                out.putpixel(q, (0, 0, 0, 255))
    return out


if __name__ == '__main__':
    im = Image.open(HERE / 'idle_frame0_profile.png').convert('RGBA')
    for y in range(20, 37):                         # the profile head off first (left of the neck)
        for x in range(0, 17):
            im.putpixel((x, y), (0, 0, 0, 0))
    out = paste(im)
    for y in range(20, 37):                         # the body's cut edge outlined again
        for x in range(0, 20):
            p = out.getpixel((x, y))
            if p[3] and p[:3] != (0, 0, 0):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if not out.getpixel(q)[3]:
                        out.putpixel(q, (0, 0, 0, 255))
    out.save(HERE / 'idle_frame0_clean.png')
    print('face on', out.getbbox(), len({q[:3] for q in out.get_flattened_data() if q[3]}) - 1, 'colours + black')
