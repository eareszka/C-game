"""Preserve approved side sprites; edit faces and breathe through the pixel plugin."""
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

names = ('girl', 'fisher', 'sailor', 'woodcutter')
review = Image.new('RGBA', (14 * 4, 20 * 4))
for row, name in enumerate(names):
    source = ROOT / f'assets/npcs/{name}.png'
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    reference = Image.open(source).convert('RGBA').crop((0, 40, 14, 60))
    colors = sorted(set(reference.getdata()) - {(0, 0, 0, 0)})
    palette = {str(i): bytes(c[:3]).hex() for i, c in enumerate(colors)}
    inverse = {c: str(i) for i, c in enumerate(colors)}
    original = {(x, y): inverse[reference.getpixel((x, y))]
                for y in range(20) for x in range(14) if reference.getpixel((x, y))[3]}
    skin = original[4, 9]
    black = inverse[(0, 0, 0, 255)]
    closed = dict(original)
    # The open vertical eye becomes a two-pixel horizontal eyelid.
    closed[5, 10] = skin
    closed[4, 11] = black
    # Fill the dark mouth notch without altering the face's transparency.
    closed[4, 12] = skin
    assert set(closed) == set(original)
    assert {p for p in original if closed[p] != original[p]} == {(5, 10), (4, 11), (4, 12)}
    frames = [closed]
    for chest_rows in ((14,), (14, 15)):
        breathing = dict(closed)
        for y in chest_rows:
            breathing[3, y] = black
            breathing[4, y] = closed[5, y]
        frames.append(breathing)
    base = ROOT / f'art/npcs/{name}_sleep_exact'
    if not base.with_suffix('.aseprite').exists():
        draw_frames(frames, palette, 14, 20, base, 700, {'sleep_side': (1, 3)})
    px = Pixel()
    try:
        px.call('export_spritesheet', sprite_path=base.with_suffix('.aseprite').as_posix(),
                output_path=(ROOT / f'assets/npcs/{name}_sleep.png').as_posix(),
                layout='horizontal', padding=0, include_json=True)
    finally:
        px.p.terminate()
    sheet = Image.open(ROOT / f'assets/npcs/{name}_sleep.png').convert('RGBA')
    assert sheet.size == (42, 20)
    for i, frame in enumerate(frames):
        actual = {(x, y): inverse[sheet.getpixel((i * 14 + x, y))]
                  for y in range(20) for x in range(14) if sheet.getpixel((i * 14 + x, y))[3]}
        assert actual == frame, f'{name}: export does not match frame {i}'
        review.paste(sheet.crop((i * 14, 0, (i + 1) * 14, 20)), ((i + 1) * 14, row * 20))
    review.paste(reference, (0, row * 20))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
    (ROOT / f'assets/npcs/{name}_sleep.json').write_text(json.dumps({
        'frame_width': 14, 'frame_height': 20, 'frames': 3,
        'duration_ms': 700, 'playback': [0, 1, 2, 1],
        'source': base.with_suffix('.aseprite').relative_to(ROOT).as_posix(),
        'reference': source.relative_to(ROOT).as_posix(), 'reference_row': 2,
        'reference_sha256': original_hash, 'palette': palette,
        'face_edits': [[5, 10], [4, 11], [4, 12]],
        'plugin_pixel_verified': True}, indent=2) + '\n')
    print(f'{name}: 3 exact 14x20 frames verified; walking source unchanged', flush=True)
review.resize((448, 640), Image.Resampling.NEAREST).save(ROOT / 'art/npcs/sleep_exact_review.png')
