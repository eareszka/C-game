"""Draws enemies for judging by eye, which the audit needs before it can claim anything about a new install: eyes, design, reading on black.

  python -B tools/enemy_audit/look.py OUT.png 53 66 55:0,20,18,39

A bare id shows the first idle frame whole at 5x. id:x0,y0,x1,y1 zooms on that box of the frame at 12x, for eyes. Top row arena black, bottom row grey.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.abspath(os.path.join(HERE, '..', '..')))
sys.path.insert(0, 'tools')
import enemy_style as es

out_path, args = sys.argv[1], sys.argv[2:]
sheets, names, tiers = es.sheets(), es.names(), es.tiers()
font = ImageFont.truetype('arial.ttf', 15)
items = []
for a in args:
    i, _, box = a.partition(':')
    i = int(i)
    s = sheets[i]
    frame = es.first_frame(s['path'], s['frames'], s['rows'])[0]
    m, bad = es.check(frame, tiers[i])
    print(i, names[i], tiers[i], '%dx%d' % (m['w'], m['h']), '%d px' % m['drawn'], '%d tones' % m['tones'], '%.1f%% lines' % (100 * m['interior']), [t for _, t in bad])
    scale = 12 if box else 5
    if box:
        frame = frame.crop(tuple(int(n) for n in box.split(',')))
    items.append((a, frame.resize((frame.width * scale, frame.height * scale), Image.NEAREST)))
width = sum(big.width + 18 for _, big in items) + 18
height = max(big.height for _, big in items) + 30
sheet = Image.new('RGB', (width, height * 2), (0, 0, 0))
sheet.paste((132, 134, 148), (0, height, width, height * 2))
draw = ImageDraw.Draw(sheet)
x = 12
for a, big in items:
    for row in (0, 1):
        top = row * height
        sheet.paste(big, (x, top + height - 24 - big.height), big)
        draw.text((x, top + height - 20), a, fill=(240, 240, 240), font=font)
    x += big.width + 18
sheet.save(out_path)
print(out_path, sheet.size)
