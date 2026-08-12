"""Reference above, a strip of the game below, both at one pixel per art pixel.

The game draws its 16px cells at 32px, so the render is halved first —
otherwise the two are being compared at different magnifications and the
generated rock always looks coarser than it is.
"""
import sys
from PIL import Image

ref = Image.open(sys.argv[1]).convert('RGB')
shot = Image.open(sys.argv[2]).convert('RGB')
box = [int(v) for v in sys.argv[4:8]] if len(sys.argv) > 7 else [0, 0, 448, 384]

half = shot.resize((shot.width // 2, shot.height // 2), Image.Resampling.NEAREST)
b = half.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
a = ref.crop((0, 0, min(ref.width, box[2]), ref.height))

Z = 3
gap = 8
w = max(a.width, b.width) * Z
canvas = Image.new('RGB', (w, (a.height + b.height + gap) * Z), (40, 40, 40))
canvas.paste(a.resize((a.width * Z, a.height * Z), Image.Resampling.NEAREST), (0, 0))
canvas.paste(b.resize((b.width * Z, b.height * Z), Image.Resampling.NEAREST),
             (0, (a.height + gap) * Z))
canvas.save(sys.argv[3])
print('wrote', sys.argv[3], '(top: reference, bottom: game at 1:1)')
