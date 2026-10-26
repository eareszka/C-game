"""Prepare and pack PixelLab Roperite runs without changing runtime assets.

prepare: palette-clean the five unique direction inputs after rotation.
pack: collect eight-frame runs, fit the existing five-frame battle layout,
      mirror left directions, and write a verified review .aseprite and PNG.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

import enemy_sheet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'art/direction'))
import fcremap as fc

ART = ROOT / 'art/enemies/pixellab/61_roperite'
OUT = ART / 'running'
WORK = ROOT / 'pixellab-out/61-roperite-animation'
APPROVED = Image.open(ART / '61_roperite_frame0_clean.png').convert('RGBA')
COLORS = sorted({p[:3] for p in APPROVED.get_flattened_data() if p[3]})
LAB = {c: fc._lab(c) for c in COLORS}
SIZE = (98, 65)
VIEWS = {'D': 'south', 'DR': 'south-east', 'R': 'east', 'UR': 'north-east', 'U': 'north'}


def clean(path):
    im = Image.open(path).convert('RGBA')
    if im.size != SIZE:
        raise ValueError(f'{path}: unexpected size {im.size}')
    data = list(im.get_flattened_data())
    if any(p[3] not in (0, 255) for p in data):
        raise ValueError(f'{path}: partial transparency needs review')
    mapping = {}
    for p in data:
        c = p[:3]
        if p[3] and c not in mapping:
            lab = fc._lab(c)
            mapping[c] = min(COLORS, key=lambda v: sum((a-b)**2 for a, b in zip(lab, LAB[v])))
    im.putdata([(*mapping[p[:3]], 255) if p[3] else (0, 0, 0, 0) for p in data])
    return im


def prepare():
    dest = OUT / 'inputs'
    dest.mkdir(parents=True, exist_ok=True)
    files = list(WORK.glob('61-roperite/rotations/v1/*.png'))
    for tag, name in VIEWS.items():
        if tag == 'D':
            im = APPROVED.copy()  # The approved view is the canonical first frame.
        else:
            matches = [p for p in files if p.stem.rsplit('-', 1)[0] == 'roperite-views-' + name]
            if len(matches) != 1:
                raise ValueError(f'Expected one {name} rotation, found {matches}')
            im = clean(matches[0])
            # Match the approved ground line without resampling any pixels.
            bounds = im.getbbox()
            aligned = Image.new('RGBA', SIZE)
            aligned.paste(im, (0, APPROVED.getbbox()[3] - bounds[3]))
            im = aligned
        im.save(dest / f'{tag}.png')
        print(tag, 'bounds', im.getbbox())


def pack():
    # Eight evenly timed generation frames sampled to the existing five slots.
    # Index 4 (the described midpoint flick) becomes attack-hook frame 2.
    views, records = {}, {}
    for tag in VIEWS:
        result = json.loads((OUT / f'{tag}-result.json').read_text(encoding='utf-8-sig'))
        paths = [Path(p) for p in result['files'] if p.lower().endswith('.png')]
        # Some responses include the conditioning frame before eight generated
        # frames; retain and sample that nine-frame sequence evenly.
        if len(paths) not in (8, 9):
            raise ValueError(f'{tag}: expected eight frames or source plus eight, got {paths}')
        sample = [0, 2, 4, 6, 8] if len(paths) == 9 else [0, 2, 4, 5, 7]
        all_frames = [clean(p) for p in paths]
        # Preserve the direction input exactly as the first contact pose.
        all_frames[0] = Image.open(OUT / 'inputs' / f'{tag}.png').convert('RGBA')
        views[tag] = [all_frames[i] for i in sample]
        if len({im.tobytes() for im in views[tag]}) < 3:
            raise ValueError(f'{tag}: insufficient distinct running poses')
        records[tag] = {'raw_frames': [str(p.relative_to(ROOT)) for p in paths], 'sampled_indices': sample,
                        'bounds': [im.getbbox() for im in views[tag]]}
    for tag, source in {'UL': 'UR', 'L': 'R', 'DL': 'DR'}.items():
        views[tag] = [ImageOps.mirror(im) for im in views[source]]
    sheet = enemy_sheet.sheet_of(views, False)
    png = OUT / '61_roperite_running.png'
    ase = png.with_suffix('.aseprite')
    sheet.save(png)
    enemy_sheet.pack(sheet, str(ase), 5, False)
    import subprocess
    subprocess.run([enemy_sheet.ASEPRITE, '-b', '--script-param', f'source={ase.as_posix()}',
                    '--script-param', 'ms=260', '--script-param',
                    'pal=' + ','.join('%02x%02x%02x' % c for c in COLORS),
                    '--script', str(ROOT / 'tools/sheet_meta.lua')], check=True)
    got = enemy_sheet.read(str(ase))
    assert enemy_sheet.sheet_of(got, False).tobytes() == sheet.tobytes()
    assert views['D'][0].tobytes() == APPROVED.tobytes()
    assert sheet.size == (3920, 65)
    assert all(p[:3] in COLORS for p in sheet.get_flattened_data() if p[3])
    for tag in enemy_sheet.ORDER:
        frames = views[tag]
        frames[0].save(OUT / f'{tag}-run.gif', save_all=True, append_images=frames[1:],
                       duration=260, loop=0, disposal=2)
    board = Image.new('RGB', (40 + 98 * 5, 65 * 8), (151, 151, 170))
    draw = ImageDraw.Draw(board)
    for row, tag in enumerate(enemy_sheet.ORDER):
        draw.text((4, row * 65 + 26), tag, fill=(0, 0, 0))
        for column, im in enumerate(views[tag]):
            board.paste(im, (40 + column * 98, row * 65), im)
    board.save(OUT / 'all-directions-review.png')
    report = {'frames_per_direction': 5, 'directions': enemy_sheet.ORDER, 'frame_ms': 260,
              'sheet_size': sheet.size, 'palette': ['%02x%02x%02x' % c for c in COLORS],
              'approved_front_preserved': True, 'aseprite_round_trip': True,
              'attack_frame': 2, 'views': records,
              'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (png, ase)}, 'installed': False}
    (OUT / 'review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'pack'])
    args = parser.parse_args()
    (prepare if args.action == 'prepare' else pack)()
