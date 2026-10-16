"""Install the approved 98 Boiuna sheet: its idle.

Run after 98_boiuna_design.py. The draft the user approved must still equal the design; the old sheet is
copied to art/_backup first. Art only: the ENEMY_SHEETS row and the Boiuna's class are edited by hand to
match what this prints.

    assets/enemies/98_boiuna.png   12 frames a direction, one row a direction (giant), all eight the front view

    python art/enemies/98_boiuna_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('98_boiuna_design')
ff, A, PAL, W, H = D.ff, D.A, D.PAL, D.W, D.H


def main():
    pics = [ff.image(g, PAL, W, H) for g in D.build()]              # also checks the first-frame draft
    assert ff.same_as_draft(HERE / '98_boiuna_idle_draft.aseprite', pics), \
        'the idle draft is not the design: it was edited, read it back before installing'
    backup = ROOT / 'art/_backup' / ('98_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    out = enemy_sheet.sheet_of({'D': pics}, True)
    tags = enemy_sheet.install(out, ROOT / 'assets/enemies/98_boiuna.png', D.N, rows=True, ms=D.MS, palette=list(PAL.values()), backup=backup)
    print(f'installed 98_boiuna: {out.width}x{out.height}, frame {W}x{H}, {D.N} frames at {D.MS} ms, tags {tags}')
    print('old sheet in', backup)
    ys = [y for g in D.build() for x, y in g]
    print(f'  for the fight, in frame pixels (the frame\'s middle is {W / 2:g}, {H / 2:g}): the middle of its open mouth {A.MOUTH}; '
          f'the head is a row up on frames {[f for f in range(D.N) if D.LIFT[f]]}; drawn rows {min(ys)}-{max(ys)}')


if __name__ == '__main__':
    main()
