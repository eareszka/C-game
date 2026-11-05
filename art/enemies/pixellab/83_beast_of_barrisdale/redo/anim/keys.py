"""83 redo: the three approved key frames, last touches, ready to animate (100x68: 2 rows padding on top).
  idle   frame0_tilt.png as approved.
  fly    poses/fly.png with its feet pink, as frame 0's.
  block  poses/cocoon/block_s1.png with its broken ribs joined and the near foot pink.

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/anim/keys.py   # writes key_idle/fly/block.png (100x65), input_*.png (100x68)
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
RED, SALMON, MID = (0xb6, 0x43, 0x3d, 255), (0xec, 0x84, 0x76, 255), (0x59, 0x59, 0x65, 255)
idle = Image.open(HERE.parent / 'frame0_tilt.png').convert('RGBA')
fly = Image.open(HERE.parent / 'poses/fly.png').convert('RGBA')
block = Image.open(HERE.parent / 'poses/cocoon/block_s1.png').convert('RGBA')
for x in range(36, 76):
    for y in range(49, 57):
        if fly.getpixel((x, y)) == RED: fly.putpixel((x, y), SALMON)
for x in range(35, 51):
    for y in range(51, 56):
        if block.getpixel((x, y)) == RED: block.putpixel((x, y), SALMON)
for p in [(36, y) for y in range(28, 31)] + [(37, y) for y in range(28, 31)] + [(30, y) for y in range(28, 35)]:
    block.putpixel(p, MID)                                  # the left ribs, whole
for n, im in (('idle', idle), ('fly', fly), ('block', block)):
    im.save(HERE / f'key_{n}.png')
    pad = Image.new('RGBA', (100, 68)); pad.paste(im, (0, 2)); pad.save(HERE / f'input_{n}.png')
