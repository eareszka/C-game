"""Local, read-only draft checks; optional palette cleanup writes a separate copy."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'art/direction'))
import fcremap as fc

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('image', type=Path)
parser.add_argument('--clean-to', type=Path, help='Write a separate palette-mapped PNG; never overwrite input')
parser.add_argument('--size', default='98x65', help='Expected WxH (97 RO: 130x81)')
args = parser.parse_args()
SIZE = tuple(int(n) for n in args.size.split('x'))
image = Image.open(args.image).convert('RGBA')
def pixels_of(im):
    return list(im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata())

if args.clean_to:
    if args.clean_to.resolve() == args.image.resolve() or args.clean_to.exists():
        parser.error('cleanup output must be a new, separate file')
    if image.size != SIZE:
        parser.error('review unexpected dimensions before cleanup')
    if any(p[3] not in (0, 255) for p in pixels_of(image)):
        parser.error('review partial alpha before cleanup; no automatic threshold')
    # Use exact palette entries, including colors fcremap.lookup exempts as keys.
    pixels = [((*p[:3], p[3]) if p[:3] in fc.PALETTE else (*fc.nearest(p[:3]), p[3]))
              if p[3] else (0, 0, 0, 0) for p in pixels_of(image)]
    image.putdata(pixels)
    args.clean_to.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.clean_to)
pixels = pixels_of(image)
opaque = [p[:3] for p in pixels if p[3]]
colors = set(opaque)
report = {
    'input': str(args.image), 'reviewed': str(args.clean_to or args.image),
    'size': list(image.size), 'size_ok': image.size == SIZE,
    'occupied_bounds': image.getbbox(), 'opaque_colors': len(colors),
    'off_palette_pixels': sum(c not in fc.PALETTE for c in opaque),
    'partial_alpha_pixels': sum(p[3] not in (0, 255) for p in pixels),
    'transparent_pixels': sum(p[3] == 0 for p in pixels),
    'black_pixels': opaque.count((0, 0, 0)), 'color_budget_ok': len(colors) <= 9,
    'human_review_required': ['rope-snout lasso', 'rattle tail', 'pose and scale',
                              'single-pixel outlines', 'flat material ramps', 'shading placement'],
    'approved': False,
}
manifest = ROOT / 'art/enemies/pixellab/61_roperite/inputs.json'
if manifest.exists():
    recorded = json.loads(manifest.read_text(encoding='utf-8-sig'))
    report['originals_unchanged'] = all(
        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
        for name, digest in recorded['sha256'].items())
print(json.dumps(report, indent=2))
sys.exit(0 if (report['size_ok'] and not report['off_palette_pixels']
               and not report['partial_alpha_pixels'] and report['transparent_pixels']
               and report['color_budget_ok'] and report.get('originals_unchanged', True)) else 1)
