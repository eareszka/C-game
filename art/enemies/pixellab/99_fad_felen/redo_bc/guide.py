"""99 Fad Felen: the guide for PixelLab, its idle art nearest-enlarged 1.25x (44 px tall, Elite wants 50+), and blank bases of the new cell sizes.

    python art/enemies/pixellab/99_fad_felen/redo_bc/guide.py
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
G = 1.25
def art(path, w, h):
    im = Image.open(ROOT / path).convert('RGBA').crop((0, 0, w, h))
    a = im.crop(im.getbbox())
    return a.resize((round(a.width * G), round(a.height * G)), 0)
idle = art('assets/enemies/redraws/99_fad_felen.png', 76, 52)
W, H = idle.width + 8, idle.height + 8
sheet = Image.new('RGBA', (W * 10, H * 8))
sheet.paste(idle, ((W - idle.width) // 2, H - idle.height - 4))
sheet.save(HERE / 'base/99_fad_felen.png')
stand = art('assets/enemies/redraws/99_fad_felen_standing.png', 76, 75)
SW, SH = stand.width + 8, stand.height + 8
Image.new('RGBA', (SW * 10, SH * 8)).save(HERE / 'base/99_fad_felen_standing.png')
print('idle cell', W, H, 'art', idle.size, 'standing cell', SW, SH, 'art', stand.size)
