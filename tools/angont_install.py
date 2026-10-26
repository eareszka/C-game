"""Install 32 Angont's redraw: PixelLab front pose, gold-olive coils, shaded poison skulls.

    python tools/angont_install.py

One drawn D pose with breathing and the project's direction fallback, five frames in one row,
written to assets/enemies/redraws/ (the original sheet in assets/enemies/ is left alone).
Adds the installation.json entry and marks 32 done on the tracker. src/battle.cpp loads it.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import subprocess
import sys
from PIL import Image

import enemy_sheet
from install_enemy_redraws import breathe

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'art/direction'))
from fcremap import PALETTE

SOURCE = ROOT/'art/enemies/pixellab/32_angont/32_angont_frame0_gold.png'
ORIGINAL = ROOT/'assets/enemies/32_angont.png'
PNG = ROOT/'assets/enemies/redraws/32_angont.png'
FRAMES, ROWS, PIVOT = 5, False, 36     # coils stay put below the neck; head and upper coil breathe


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def install():
    assert not PNG.exists(), f'Refusing to replace {PNG}'
    protected = {p: sha(p) for p in (ORIGINAL, ORIGINAL.with_suffix('.aseprite'), SOURCE)}
    im = Image.open(SOURCE).convert('RGBA')
    old = Image.open(ORIGINAL).convert('RGBA')
    assert im.size == (old.width//(8*FRAMES), old.height), im.size
    assert all(c[:3] in PALETTE and c[3] in (0, 255) for c in im.getdata() if c[3])
    poses = breathe(im, PIVOT)
    sheet = enemy_sheet.sheet_of({'D': [poses[k] for k in (0, 1, 0, 2, 0)]}, ROWS)
    colors = Counter(c[:3] for c in im.getdata() if c[3])
    tags = enemy_sheet.install(sheet, PNG, FRAMES, ROWS, ms=260, palette=['%02x%02x%02x' % c for c in colors])
    got = Image.open(PNG).convert('RGBA')
    cells = enemy_sheet.cells_of(got, FRAMES, ROWS)
    assert got.size == old.size
    assert cells['D'][0].tobytes() == im.tobytes()
    assert len({f.tobytes() for f in cells['D']}) == 3
    assert all(sha(p) == h for p, h in protected.items()), 'An original changed'

    manifest_path = ROOT/'assets/enemies/redraws/installation.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['enemies'] = [e for e in manifest['enemies'] if e['id'] != 32] + [dict(
        id=32, source=SOURCE.relative_to(ROOT).as_posix(), png=PNG.relative_to(ROOT).as_posix(),
        aseprite=PNG.with_suffix('.aseprite').relative_to(ROOT).as_posix(), frame_size=list(im.size),
        frames=FRAMES, rows=ROWS, tags=tags, body_pivot=PIVOT, frame_zero_exact=True,
        png_sha256=sha(PNG), aseprite_sha256=sha(PNG.with_suffix('.aseprite')),
        pixellab_job='af594b04-ad01-4a45-a10f-afc15607e69f, 10 generations',
        recolor='tools/angont_recolor.py gold (hand palette mapping, shaded skulls)')]
    manifest_path.write_text(json.dumps(manifest, indent=2))
    subprocess.run([sys.executable, str(ROOT/'tools/enemy_redraw_sheet.py'), '--complete', '32'], cwd=ROOT, check=True)
    print(f'Installed 32: {PNG.name}, {FRAMES} frames, {im.width}x{im.height}')


if __name__ == '__main__':
    install()
