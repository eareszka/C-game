"""Install the user-approved Roperite running sheet, preserving original assets."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

import enemy_sheet

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/enemies/pixellab/61_roperite/running'
DEST = ROOT / 'assets/enemies/redraws'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    review = json.loads((ART / 'review.json').read_text())
    for name, expected in review['sha256'].items():
        if not name.endswith('.aseprite'):
            assert sha(ROOT / name) == expected, f'Reviewed artifact changed: {name}'
    source_png = ART / '61_roperite_running.png'
    source_ase = source_png.with_suffix('.aseprite')
    image = Image.open(source_png).convert('RGBA')
    # Preserve the saved review file. Its extra front frame is accepted only
    # when it is an adjacent duplicate and all remaining artwork matches the
    # approved runtime-layout PNG exactly.
    with tempfile.TemporaryDirectory() as tmp:
        strip, data = Path(tmp) / 'strip.png', Path(tmp) / 'frames.json'
        subprocess.run([enemy_sheet.ASEPRITE, '-b', '--list-tags', str(source_ase), '--sheet', str(strip),
                        '--sheet-type', 'horizontal', '--format', 'json-array', '--data', str(data)], check=True)
        meta = json.loads(data.read_text())
        sheet = Image.open(strip).convert('RGBA')
        frames = []
        for frame in meta['frames']:
            rect = frame['frame']
            frames.append(sheet.crop((rect['x'], rect['y'], rect['x'] + rect['w'], rect['y'] + rect['h'])))
        tags = {tag['name']: frames[tag['from']:tag['to'] + 1] for tag in meta['meta']['frameTags']}
    removed_duplicates = {}
    for tag, poses in tags.items():
        removed_duplicates[tag] = 0
        while len(poses) > 5:
            duplicate = next((i for i in range(1, len(poses)) if poses[i].tobytes() == poses[i-1].tobytes()), None)
            assert duplicate is not None, f'{tag}: extra distinct pose requires review'
            del poses[duplicate]
            removed_duplicates[tag] += 1
    assert image.size == (3920, 65)
    assert enemy_sheet.sheet_of(tags, False).tobytes() == image.tobytes()
    assert set(tags) == {'D', 'DR', 'R', 'UR', 'U'}
    assert all(len(frames) == 5 for frames in tags.values())
    original_paths = [ROOT / f'assets/enemies/61_roperite.{ext}' for ext in ('png', 'aseprite')]
    originals = {str(p.relative_to(ROOT)): sha(p) for p in original_paths}
    target_png = DEST / '61_roperite.png'
    target_ase = target_png.with_suffix('.aseprite')
    assert not target_ase.exists() and not target_png.exists(), 'Already installed; verify existing assets instead'
    enemy_sheet.pack(image, str(target_ase), 5, False)
    subprocess.run([enemy_sheet.ASEPRITE, '-b', '--script-param', f'source={target_ase.as_posix()}',
                    '--script-param', 'ms=260', '--script-param', 'pal=' + ','.join(review['palette']),
                    '--script', str(ROOT / 'tools/sheet_meta.lua')], check=True)
    assert enemy_sheet.sheet_of(enemy_sheet.read(str(target_ase)), False).tobytes() == image.tobytes()
    shutil.copyfile(source_png, target_png)
    # Copy PNG last so the game does not need to export on first load.
    assert all(sha(ROOT / name) == digest for name, digest in originals.items())
    record = {
        'id': 61, 'source': str(source_ase.relative_to(ROOT)).replace('\\', '/'),
        'png': 'assets/enemies/redraws/61_roperite.png',
        'aseprite': 'assets/enemies/redraws/61_roperite.aseprite',
        'frame_size': [98, 65], 'frames': 5, 'rows': False,
        'directions': enemy_sheet.ORDER, 'tags': list(tags), 'frame_ms': 260,
        'attack_frame': 2, 'approved': True, 'approval_date': '2026-10-18',
        'review_source_sha256': sha(source_ase), 'duplicate_review_frames_removed': removed_duplicates,
        'png_sha256': sha(target_png), 'aseprite_sha256': sha(target_ase),
        'preserved_original_sha256': originals,
    }
    manifest_path = DEST / 'installation.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['enemies'] = [e for e in manifest['enemies'] if e['id'] != 61] + [record]
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    review.update(approved=True, approval_date='2026-10-18', installed=True,
                  installed_png=record['png'], installed_aseprite=record['aseprite'])
    (ART / 'review.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
