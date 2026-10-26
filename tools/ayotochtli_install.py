"""Install approved Ayotochtli battle sheets and refresh the visible tracker."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image

import enemy_sheet

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/enemies/pixellab/66_ayotochtli/battle'
DEST = ROOT / 'assets/enemies/redraws'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(check=False):
    review = json.loads((ART / 'review.json').read_text())
    originals = {f'assets/enemies/{name}.{ext}': sha(ROOT / f'assets/enemies/{name}.{ext}')
                 for name in ('66_ayotochtli', '66_ayotochtli_roll') for ext in ('png', 'aseprite')}
    copies = []
    for kind, count, filename in [('idle', 3, '66_ayotochtli'), ('roll', 4, '66_ayotochtli_roll')]:
        record = review['sheets'][kind]
        for name, expected in record['sha256'].items():
            assert sha(ROOT / name) == expected, f'Review artifact changed: {name}'
        png, ase = ROOT / record['png'], ROOT / record['aseprite']
        image = Image.open(png).convert('RGBA')
        tags = enemy_sheet.read(str(ase))
        assert set(tags) == {'D', 'DR', 'R', 'UR', 'U'}
        assert all(len(frames) == count for frames in tags.values())
        assert image.size == (48 * 8 * count, 35)
        assert image.tobytes() == enemy_sheet.sheet_of(tags, False).tobytes()
        for source, target in [(ase, DEST / f'{filename}.aseprite'), (png, DEST / f'{filename}.png')]:
            assert not target.exists() or sha(target) == sha(source), f'Existing different asset: {target}'
            copies.append((source, target))
        print(f'{kind}: reviewed source unchanged; {count} frames per direction; pixel-exact export')
    if check:
        return
    for source, target in copies:
        shutil.copyfile(source, target)  # PNG last for each pair avoids a first-load export.
    assert all(sha(ROOT / name) == digest for name, digest in originals.items())
    record = {
        'id': 66, 'source': 'art/enemies/pixellab/66_ayotochtli/battle/66_ayotochtli_idle.aseprite',
        'roll_source': 'art/enemies/pixellab/66_ayotochtli/battle/66_ayotochtli_roll.aseprite',
        'png': 'assets/enemies/redraws/66_ayotochtli.png',
        'aseprite': 'assets/enemies/redraws/66_ayotochtli.aseprite',
        'roll_png': 'assets/enemies/redraws/66_ayotochtli_roll.png',
        'roll_aseprite': 'assets/enemies/redraws/66_ayotochtli_roll.aseprite',
        'frame_size': [48, 35], 'frames': 3, 'roll_frames': 4, 'rows': False,
        'directions': enemy_sheet.ORDER, 'tags': ['D', 'DR', 'R', 'UR', 'U'],
        'standing_loop': [0, 1, 0, 2], 'standing_ms': [400, 250, 400, 250],
        'roll_frame_ms': 70, 'attack_frame': 1, 'approved': True,
        'approval_date': '2026-10-18', 'preserved_original_sha256': originals,
        'installed_sha256': {str(target.relative_to(ROOT)): sha(target) for _, target in copies},
    }
    manifest_path = DEST / 'installation.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['enemies'] = [entry for entry in manifest['enemies'] if entry['id'] != 66] + [record]
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    review.update(approved=True, installed=True, approval_date='2026-10-18',
                  installed_idle=record['png'], installed_roll=record['roll_png'])
    (ART / 'review.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    from enemy_redraw_sheet import main as refresh_tracker
    refresh_tracker(str(ROOT / 'enemy_rating.png'), complete=66)
    print('Installed both battle sheets; original assets preserved; visible tracker updated for 66')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    main(parser.parse_args().check)
