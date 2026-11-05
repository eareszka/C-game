"""93 Chipique's battle poses (the user, 2026-11-03: back to the approved sprite, no rotations): the approved frame's neck-and-head sway, the
existing L poses, one view for all 8 directions. Pose 0 is the approved frame itself; poses 1 and 2 had a red eye, so the approved solid black
2 x 2 eye goes back on, a row higher each as the head lifts.

    python art/enemies/pixellab/93_chipique/redo3/anim/single.py   # writes single_N.png, single.gif; single.lua makes single_review.aseprite
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
K, SLATE = (0, 0, 0, 255), (0x84, 0x86, 0x94, 255)
EYE_TOP = {1: 13, 2: 12}
for i in range(3):
    im = Image.open(HERE / f'L_{i}.png').convert('RGBA')
    if i in EYE_TOP:
        t = EYE_TOP[i]
        for y in (t, t + 1):
            im.putpixel((19, y), SLATE)
            im.putpixel((20, y), K)
            im.putpixel((21, y), K)
    im.save(HERE / f'single_{i}.png')
fr = [Image.open(HERE / f'single_{i}.png').convert('RGBA') for i in (0, 1, 0, 2)]
big = []
for f in fr:
    bg = Image.new('RGBA', f.size, (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(f); big.append(bg.resize((f.width * 4, f.height * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / 'single.gif', save_all=True, append_images=big[1:], duration=[400, 250, 400, 250], loop=0)
S = 4
b = Image.new('RGBA', (98 * S * 3, 65 * S), (0x6f, 0x9e, 0x5c, 255))
for i in range(3): b.alpha_composite(Image.open(HERE / f'single_{i}.png').convert('RGBA').resize((98 * S, 65 * S), 0), (i * 98 * S, 0))
b.save(HERE / 'single_review.png')
