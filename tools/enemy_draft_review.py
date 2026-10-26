"""Palette-clean a separate first-frame draft and report local checks.

    python tools/enemy_draft_review.py art/enemies/pixellab/66_ayotochtli
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'art/direction'))
import fcremap as fc


def main(folder, output=None, max_colors=9, align=False):
    inputs = json.loads((folder / 'inputs.json').read_text(encoding='utf-8-sig'))
    result = json.loads((folder / 'result.json').read_text(encoding='utf-8-sig'))
    paths = [Path(p) for p in result['files'] if p.lower().endswith('.png')]
    assert len(paths) == 1, 'Review multiple outputs individually before cleanup'
    raw = Image.open(paths[0]).convert('RGBA')
    assert list(raw.size) == inputs['size'], f'Unexpected dimensions: {raw.size}'
    pixels = list(raw.get_flattened_data() if hasattr(raw, 'get_flattened_data') else raw.getdata())
    assert all(p[3] in (0, 255) for p in pixels), 'Partial alpha requires review before cleanup'
    assert any(p[3] for p in pixels), 'Empty output'
    assert any(p[3] == 0 for p in pixels), 'No transparent background'
    mapping = {p[:3]: p[:3] if p[:3] in fc.PALETTE else fc.nearest(p[:3]) for p in pixels if p[3]}
    counts = Counter(mapping[p[:3]] for p in pixels if p[3])
    merges = []
    while len(counts) > max_colors:
        labs = {color: fc._lab(color) for color in counts}
        # Merge the least costly redundant shade; keep black outlines intact.
        _, source, target = min(
            (counts[a] * sum((x-y)**2 for x, y in zip(labs[a], labs[b])), a, b)
            for a in counts if a != (0, 0, 0) for b in counts if a != b)
        mapping = {original: target if mapped == source else mapped for original, mapped in mapping.items()}
        counts[target] += counts.pop(source)
        merges.append({'from': source, 'to': target})
    cleaned = Image.new('RGBA', raw.size)
    cleaned.putdata([(*mapping[p[:3]], 255) if p[3] else (0, 0, 0, 0) for p in pixels])
    offset = (0, 0)
    if align:
        old, new = inputs['bounds'], cleaned.getbbox()
        offset = (round((old[0] + old[2] - new[0] - new[2]) / 2), old[3] - new[3])
        assert new[0] + offset[0] >= 0 and new[2] + offset[0] <= raw.width
        assert new[1] + offset[1] >= 0 and new[3] + offset[1] <= raw.height
        aligned = Image.new('RGBA', raw.size)
        aligned.paste(cleaned, offset)
        cleaned = aligned
    destination = output or folder / 'frame0_clean.png'
    assert not destination.exists(), 'A cleaned draft already exists; preserve review edits'
    cleaned.save(destination)
    opaque = {mapping[p[:3]] for p in pixels if p[3]}
    originals_unchanged = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                              for name, digest in inputs['sha256'].items())
    report = {
        'raw': str(paths[0]), 'cleaned': str(destination), 'size': list(cleaned.size),
        'source_bounds': inputs['bounds'], 'draft_bounds': cleaned.getbbox(),
        'opaque_colors': len(opaque), 'color_budget_ok': len(opaque) <= 9,
        'raw_off_palette_pixels': sum(p[:3] not in fc.PALETTE for p in pixels if p[3]),
        'cleaned_off_palette_pixels': 0, 'partial_alpha_pixels': 0,
        'palette': ['%02x%02x%02x' % c for c in sorted(opaque)],
        'palette_merges': merges, 'alignment_offset': offset,
        'originals_unchanged': originals_unchanged,
        'approved': False, 'installed': False,
        'visual_review_required': ['anatomy and silhouette', 'pose and scale', 'outlines', 'shading'],
    }
    (folder / 'review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if originals_unchanged and len(opaque) <= 9 else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--output', type=Path, help='A new separate cleanup output')
    parser.add_argument('--max-colors', type=int, default=9, choices=range(2, 10))
    parser.add_argument('--align', action='store_true', help='Match source horizontal center and ground line without resampling')
    args = parser.parse_args()
    sys.exit(main(args.folder, args.output, args.max_colors, args.align))
