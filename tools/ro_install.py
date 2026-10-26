"""Install 97 RO's house-rules redraw: black outline, charcoal hide, red accents only.

    python tools/ro_install.py

Replaces the demonic red-outline sheet in assets/enemies/redraws/ the way
install_enemy_redraws.py installed it: one drawn D pose, breathing, the project's
direction fallback, 8 frames in rows. The replaced PNG/.aseprite are backed up;
the originals in assets/enemies/ and the demonic draft are left alone.
"""
from pathlib import Path
from datetime import datetime
from collections import Counter
import hashlib
import json
import shutil
import subprocess
import sys
from PIL import Image

import enemy_sheet
from install_enemy_redraws import breathe

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'art/direction'))
from fcremap import PALETTE

SOURCE = ROOT/'art/enemies/pixellab/97_ro/97_ro_frame0_clean.png'
PNG = ROOT/'assets/enemies/redraws/97_ro.png'
FRAMES, ROWS, PIVOT = 8, True, 56


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def install():
    protected = {p.relative_to(ROOT).as_posix(): sha(p) for p in [
        ROOT/'assets/enemies/97_ro.png', ROOT/'assets/enemies/97_ro.aseprite',
        ROOT/'art/enemies/97_ro_demonic_frame0_draft.png', ROOT/'art/enemies/97_ro_demonic_frame0_draft.aseprite', SOURCE]}
    backup = ROOT/'art/_backup'/('ro_redraw_install_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    for p in (PNG, PNG.with_suffix('.aseprite')):
        shutil.copy2(p, backup/p.name)
    im = Image.open(SOURCE).convert('RGBA')
    old = Image.open(PNG).convert('RGBA')
    assert im.size == (old.width//FRAMES, old.height//8), im.size
    assert all(c[:3] in PALETTE and c[3] in (0, 255) for c in im.getdata() if c[3])
    poses = breathe(im, PIVOT)
    sheet = enemy_sheet.sheet_of({'D': [poses[k] for k in (0, 0, 1, 1, 0, 0, 2, 2)]}, ROWS)
    colors = Counter(c[:3] for c in im.getdata() if c[3])
    tags = enemy_sheet.install(sheet, PNG, FRAMES, ROWS, ms=260, palette=['%02x%02x%02x' % c for c in colors])
    got = Image.open(PNG).convert('RGBA')
    cells = enemy_sheet.cells_of(got, FRAMES, ROWS)
    assert got.size == old.size
    assert cells['D'][0].tobytes() == im.tobytes()
    assert len({f.tobytes() for f in cells['D']}) == 3
    for rel, h in protected.items():
        assert sha(ROOT/rel) == h, f'Protected source changed: {rel}'

    manifest_path = ROOT/'assets/enemies/redraws/installation.json'
    manifest = json.loads(manifest_path.read_text())
    entry = next(e for e in manifest['enemies'] if e['id'] == 97)
    entry.update(source=SOURCE.relative_to(ROOT).as_posix(), tags=tags, frame_zero_exact=True,
                 png_sha256=sha(PNG), aseprite_sha256=sha(PNG.with_suffix('.aseprite')),
                 replaced='97_ro_demonic_frame0_draft (red outline); backup '+backup.relative_to(ROOT).as_posix(),
                 pixellab_job='cb625e56-dbf6-4127-9799-3b15b7747c68, 10 generations')
    manifest_path.write_text(json.dumps(manifest, indent=2))
    subprocess.run([sys.executable, str(ROOT/'tools/enemy_redraw_sheet.py')], cwd=ROOT, check=True)
    print(f'Installed 97: {PNG.name}, {FRAMES} frames, {im.width}x{im.height}; backup {backup.relative_to(ROOT)}')


if __name__ == '__main__':
    install()
