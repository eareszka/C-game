"""Two fishing cels drawn, saved and exported through the earlier pixel plugin."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'art/direction'))
from first_frame import draw_frames
from mcpc import Pixel

source = ROOT / 'assets/npcs/fisher.png'
before = hashlib.sha256(source.read_bytes()).hexdigest()
base = Image.open(source).convert('RGBA').crop((0, 60, 14, 80))
palette = {'K': '000000', 'B': '2850a0', 'G': '9797aa', 'S': 'd7a175'}
inverse = {tuple(bytes.fromhex(color)): key for key, color in palette.items()}
frames = []

def line(g, a, b, color):
    x0, y0 = a
    x1, y1 = b
    steps = max(abs(x1-x0), abs(y1-y0))
    for i in range(steps+1):
        t = i / max(1, steps)
        g[round(x0+(x1-x0)*t), round(y0+(y1-y0)*t)] = color

for phase in range(2):
    g = {(x, y+8): inverse[base.getpixel((x,y))[:3]]
         for y in range(20) for x in range(14) if base.getpixel((x,y))[3]}
    # Hold the rod with a small hand adjustment; head, body and feet stay fixed.
    for x in range(10,15):
        g[x,20+phase] = 'K'
        g[x,21+phase] = 'S'
        g[x,22+phase] = 'K'
    line(g, (14,22+phase), (27,5+phase), 'K')
    line(g, (15,21+phase), (26,6+phase), 'S')
    line(g, (27,5+phase), (35,24-phase), 'G')
    # A tiny float rises one pixel on the second cel.
    for dx,dy,c in [(0,0,'K'),(-1,1,'K'),(0,1,'G'),(1,1,'K'),(0,2,'B'),(0,3,'K')]:
        g[35+dx,24-phase+dy] = c
    frames.append(g)

out = ROOT / 'art/npcs/fisher_fishing'
if not out.with_suffix('.aseprite').exists():
    draw_frames(frames, palette, 40, 28, out, 600, {'fishing_east': (1,2)})
# A partial export may have already saved the source. Reopen and verify it;
# never overwrite an existing editable file on a retry.
px = Pixel()
try:
    exported = px.call('export_spritesheet', sprite_path=out.with_suffix('.aseprite').as_posix(),
        output_path=(ROOT/'assets/npcs/fisher_fishing.png').as_posix(),
        layout='horizontal', padding=0, include_json=True)
finally:
    px.p.terminate()
sheet = Image.open(ROOT/'assets/npcs/fisher_fishing.png').convert('RGBA')
assert sheet.size == (80,28)
for index,g in enumerate(frames):
    for y in range(28):
        for x in range(40):
            p=sheet.getpixel((index*40+x,y))
            assert (inverse[p[:3]] if p[3] else None)==g.get((x,y))
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(ROOT/'assets/npcs/fisher_fishing.json').write_text(json.dumps({
    'frame_width':40,'frame_height':28,'frames':2,'duration_ms':600,
    'sprite_offset':{'x':0,'y':-8},'facing':'east','palette':palette,
    'source':'art/npcs/fisher_fishing.aseprite','plugin_pixel_verified':True},indent=2)+'\n')
sheet.resize((640,224),Image.Resampling.NEAREST).save(ROOT/'build_tmp/npc_review/fisher_fishing_preview.png')
print('Two fishing cels exported through pixel-plugin; every pixel verified; walking art unchanged.')
