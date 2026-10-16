"""Install the approved 23 Olgoi-Khorkhoi sheets: its idle, and the spinning head for its enraged phase.

Run after 23_olgoi_khorkhoi_design.py. The drafts the user approved must still equal the design; the old sheet is
copied to art/_backup first. Art only: the ENEMY_SHEETS row and the class are edited by hand to match what this
prints.

    assets/enemies/23_olgoi_khorkhoi.png        12 frames a direction, one row a direction (giant), all eight the front view
    assets/enemies/23_olgoi_khorkhoi_spin.png   the same, the head and blades spinning, the body pumping (the row's `alt`)

    python art/enemies/23_olgoi_khorkhoi_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('23_olgoi_khorkhoi_design')
ff, A, PAL, W, H = D.ff, D.A, D.PAL, D.W, D.H


def main():
    sheets = {'23_olgoi_khorkhoi': (D.build(), D.DRAFT), '23_olgoi_khorkhoi_spin': (D.build(spin=True), D.SPIN_DRAFT)}
    pics = {name: [ff.image(g, PAL, W, H) for g in frames] for name, (frames, draft) in sheets.items()}
    for name, (frames, draft) in sheets.items():
        assert ff.same_as_draft(draft.with_suffix('.aseprite'), pics[name]), f'{draft.name} is not the design: it was edited, read it back before installing'
    backup = ROOT / 'art/_backup' / ('23_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    for name in sheets:
        out = enemy_sheet.sheet_of({'D': pics[name]}, True)
        tags = enemy_sheet.install(out, ROOT / f'assets/enemies/{name}.png', D.N, rows=True, ms=D.MS, palette=list(PAL.values()), backup=backup)
        print(f'installed {name}: {out.width}x{out.height}, frame {W}x{H}, {D.N} frames at {D.MS} ms, tags {tags}')
    print('old sheet in', backup)
    mx, my = A.MOUTH[0] + D.OX, A.MOUTH[1] + D.OY
    print(f'  for the fight, in frame pixels (the frame\'s middle is {W / 2:g}, {H / 2:g}): the middle of its mouth ({mx}, {my}), '
          f'{D.BOB[4]} rows lower on the idle\'s frames 4-5; the sand line is row {D.SAND_ROW + D.OY}, the arch\'s top row {D.TOP + D.OY}; '
          f'the blades sweep {D.BLADE_TIP:g} px round the mouth on the spin sheet')


if __name__ == '__main__':
    main()
