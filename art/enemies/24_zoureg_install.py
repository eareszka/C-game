"""Install the approved 24 Zoureg sheets: idle, wind-up and dash.

Run after 24_zoureg_design.py. The drafts the user approved must still equal the design; the old sheets
are copied to art/_backup first. Art only: the ENEMY_SHEETS row and class Zoureg are edited by hand to
match what this prints.

    idle     assets/enemies/24_zoureg.png          the main sheet: resting in phase 1, all of phase 2
    wind-up  assets/enemies/24_zoureg_windup.png   its `alt`: the idle's layout, shown while it aims
    dash     assets/enemies/24_zoureg_dash.png     its `flap`: four frames a direction, shown while it thrusts

Three views are drawn (front, side, back). The eight directions take them the way a sheet with tags
D R U exports: the diagonals below it the front, the ones above it the side, the left the side mirrored.

    python art/enemies/24_zoureg_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('24_zoureg_design')
ff, PAL, W, H = D.ff, D.PAL, D.W, D.H
FILES = {'idle': '24_zoureg', 'windup': '24_zoureg_windup', 'dash': '24_zoureg_dash'}


def main():
    sheets = D.build()
    pics = {name: {v: [ff.image(g, PAL, W, H) for g, bare in sheets[name][v]] for v in D.DRAFT} for name in sheets}
    for name in sheets:
        assert ff.same_as_draft(HERE / f'24_zoureg_{name}_draft.aseprite', [im for v in D.DRAFT for im in pics[name][v]]), \
            f'the {name} draft is not the design: it was edited, read it back before installing'
    backup = ROOT / 'art/_backup' / ('24_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    for name, (make, ms) in D.SHEETS.items():
        n, sheet = len(pics[name]['D']), enemy_sheet.cardinal(pics[name])
        tags = enemy_sheet.install(sheet, ROOT / 'assets/enemies' / (FILES[name] + '.png'), n, ms=ms, palette=list(PAL.values()), backup=backup)
        print(f'installed {FILES[name]}: {sheet.width}x{sheet.height}, frame {W}x{H}, {n} frames at {ms} ms, tags {tags}', flush=True)
    print('old sheets in', backup)
    # for the fight: the blade's point on the idle sheet, front view, by frame (art pixels; the frame's middle is 22, 14.5)
    for f, (g, bare) in enumerate(sheets['idle']['D']):
        tip = sorted(p for p in bare if g[p] == 'W' or p[1] < 10)
        print(f'  idle frame {f}: point at columns {tip[0][0]}-{tip[-1][0]}, row {tip[0][1]}')


if __name__ == '__main__':
    main()
