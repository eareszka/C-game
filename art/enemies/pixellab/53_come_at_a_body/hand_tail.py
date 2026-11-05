"""53 Come-at-a-body: its bushy tail drawn back onto the rotated side views (PixelLab's rotate left it off; the
user, 2026-10-28: "add the bushy tail back to the side views"). A plume behind the rump, lit on top, dark
beneath, painted only where the view is empty so the body stays over it. The originals are kept as
idle_view_*_notail.png; the dash sheet's views are copies of these.

    python art/enemies/pixellab/53_come_at_a_body/hand_tail.py
"""
from pathlib import Path
import shutil
from PIL import Image

HERE = Path(__file__).resolve().parent
PAL = {'K': (0, 0, 0), 'D': (0x5c, 0x46, 0x16), 'M': (0x94, 0x70, 0x3d), 'L': (0xc1, 0x8a, 0x39)}
TAIL = [
    '..KKKK.',
    '.KLLLLK',
    'KLLMMMK',
    'KLMMMMK',
    'KMMMMDK',
    'KMMMDDK',
    '.KMDDK.',
    '..KKK..',
]
AT = {'DR': (8, 15), 'R': (7, 15), 'UR': (8, 17)}   # its right column on the rump's outline

for v, (x0, y0) in AT.items():
    src = HERE / f'idle_view_{v}.png'
    keep = HERE / f'idle_view_{v}_notail.png'
    if not keep.exists():
        shutil.copy(src, keep)
    im = Image.open(keep).convert('RGBA')
    for y, r in enumerate(TAIL):
        for x, c in enumerate(r):
            if c != '.' and not im.getpixel((x0 + x, y0 + y))[3]:
                im.putpixel((x0 + x, y0 + y), PAL[c] + (255,))
    im.save(src)
    shutil.copy(src, HERE / f'dash_view_{v}.png')
    print(v, im.getbbox())
