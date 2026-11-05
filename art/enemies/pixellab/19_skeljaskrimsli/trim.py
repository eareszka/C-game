"""19 Skeljaskrimsli: lower plates and two eyes looking down (the user, 2026-10-29: "make the spikes not as tall on
the head and back. have both eyes looking 'down' at the player"). From idle_frame0_tallplates.png (the approved
pose): the top TRIM pixels off every column of its back and head, the new top edge outlined in black; a second
glowing eye beside the first, and in each a black pupil along its lower edge, so both look down at the player.
paste_eyes(frame) puts the same eyes on an animated frame.

    python art/enemies/pixellab/19_skeljaskrimsli/trim.py   -> idle_frame0_clean.png
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
TRIM = 3
HEAD = range(51, 70), 6        # the head's columns, trimmed lower still (its plate cap stood tallest)
GLOW, BLACK = (0xa8, 0xf0, 0xbc), (0, 0, 0)
# the eyes: (x, y) of each eye's top left, 2 wide and 3 tall -- glow above, the pupil along the bottom
EYES = ((55, 22), (58, 22))


def trim(im):
    out = im.copy()
    for x in range(im.width):
        ys = [y for y in range(im.height) if im.getpixel((x, y))[3]]
        if not ys:
            continue
        n = HEAD[1] if x in HEAD[0] else TRIM
        for y in ys[:n]:
            out.putpixel((x, y), (0, 0, 0, 0))
        top = ys[n] if len(ys) > n else None
        if top is not None:
            out.putpixel((x, top), BLACK + (255,))                 # the new top edge's outline
    return out


def paste_eyes(im):
    out = im.copy()
    for ex, ey in EYES:
        for dx in (0, 1):
            out.putpixel((ex + dx, ey), GLOW + (255,))
            out.putpixel((ex + dx, ey + 1), GLOW + (255,))
            out.putpixel((ex + dx, ey + 2), BLACK + (255,))           # the pupil, low: looking down
    return out


if __name__ == '__main__':
    out = paste_eyes(trim(Image.open(HERE / 'idle_frame0_tallplates.png').convert('RGBA')))
    out.save(HERE / 'idle_frame0_clean.png')
    print(out.getbbox(), len({q[:3] for q in out.get_flattened_data() if q[3]}) - 1, 'colours + black')
