"""python grid.py OUT.png COLS img...: crops (18,30,80,65) at 6x in a labelled grid (review helper)."""
import sys, os
from PIL import Image, ImageDraw
out_p, cols, fs = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
z = int(os.environ.get("Z", 6)); box = tuple(map(int, os.environ.get("BOX", "18,30,80,65").split(","))); w, h = box[2] - box[0], box[3] - box[1]
rows = (len(fs) + cols - 1) // cols
out = Image.new('RGBA', (cols * (w * z + 6), rows * (h * z + 6)), (40, 40, 50, 255)); d = ImageDraw.Draw(out)
for k, p in enumerate(fs):
    im = Image.open(p).convert('RGBA').crop(box); bg = Image.new('RGBA', im.size, (40, 40, 50, 255)); bg.alpha_composite(im)
    x, y = (k % cols) * (w * z + 6), (k // cols) * (h * z + 6)
    out.paste(bg.resize((w * z, h * z), 0), (x, y)); d.text((x + 3, y + 3), os.path.basename(p), fill=(255, 255, 0, 255))
out.save(out_p)
