"""python view.py OUT.png img... : the images side by side at 4x on dark grey (review helper)."""
import sys
from PIL import Image
ims = [Image.open(p).convert('RGBA') for p in sys.argv[2:]]
w, h = max(i.width for i in ims), max(i.height for i in ims); z = 4
out = Image.new('RGBA', (len(ims) * (w * z + 8), h * z), (40, 40, 50, 255))
for k, im in enumerate(ims):
    bg = Image.new('RGBA', im.size, (40, 40, 50, 255)); bg.alpha_composite(im)
    out.paste(bg.resize((im.width * z, im.height * z), 0), (k * (w * z + 8), 0))
out.save(sys.argv[1])
