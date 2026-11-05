"""Validate the first-frame draft and keep an editable Aseprite review source."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'art/direction'))
import first_frame as ff
import fcremap as fc

im = Image.open(HERE / 'idle_frame0_clean_v3.png').convert('RGBA')
pixels = list(im.getdata())
cols = sorted({p[:3] for p in pixels if p[3]})
pal = {('K' if c == (0, 0, 0) else f'c{i}'): '%02x%02x%02x' % c
       for i, c in enumerate(cols)}
inv = {tuple(bytes.fromhex(c)): k for k, c in pal.items()}
g = {(x, y): inv[im.getpixel((x, y))[:3]]
     for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]}
report = {
    'approved': False, 'stage': 'first-frame design review',
    'size': list(im.size), 'size_ok': im.size == (78, 59),
    'bounds': im.getbbox(), 'opaque_colors': len(cols),
    'off_palette_pixels': sum(p[:3] not in fc.PALETTE for p in pixels if p[3]),
    'partial_alpha_pixels': sum(p[3] not in (0, 255) for p in pixels),
    'transparent_pixels': sum(p[3] == 0 for p in pixels),
    'tile_violations': [],
    'external_bible_checker_available': False,
    'visual_review_required': ['identity and dugong', 'anatomy and silhouette',
                               'outline', 'flat form shading', 'pixel density'],
}
for y in range(0, im.height, 16):
    for x in range(0, im.width, 16):
        tile = im.crop((x, y, min(x + 16, im.width), min(y + 16, im.height)))
        count = len({p[:3] for p in tile.getdata() if p[3]})
        if count > 4:
            report['tile_violations'].append({'x': x, 'y': y, 'opaque_colors': count})
try:
    report['local_outline_checks'] = ff.checks(g, pal, *im.size, cap=59)
except AssertionError as e:
    report['local_outline_failure'] = str(e)
inputs = json.loads((HERE / 'inputs.json').read_text())
report['original_hashes_preserved'] = all(
    hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
    for p, h in inputs['sha256'].items())
ase = HERE / 'idle_frame0_review_v3.aseprite'
if ase.exists():
    assert ff.same_as_draft(ase, [im]), 'Aseprite review was edited; preserve user edits'
else:
    ff.aseprite_frames([g], pal, *im.size, ase, ms=400, tags={'D_design_review': (1, 1)})
report['aseprite_roundtrip_exact'] = ff.same_as_draft(ase, [im])
(HERE / 'frame0_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
