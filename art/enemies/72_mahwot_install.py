"""Install the approved 72 Mahwot sheets: swimming, and firing.

Run after 72_mahwot_design.py. The drafts the user approved must still equal the design; the old sheets
are copied to art/_backup first. Art only: the ENEMY_SHEETS row and class Mahwot are edited by hand to
match what this prints.

    swim  assets/enemies/72_mahwot.png       the main sheet, 6 frames a direction
    fire  assets/enemies/72_mahwot_roar.png  its `alt`, shown while it breathes its beam

One view is drawn, the side (the user: left and right only); the left is its mirror. The game's sheets
hold eight directions, so the front and back slots take the side view too (enemy_sheet.cardinal); the
fight only ever shows left and right.

    python art/enemies/72_mahwot_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('72_mahwot_design')
A, ff, PAL, W, H = D.A, D.ff, D.PAL, D.W, D.H
FILES = {'swim': '72_mahwot', 'fire': '72_mahwot_roar'}


def main():
    sheets = D.build()                                             # also checks the two first-frame drafts
    pics = {name: [ff.image(g, PAL, W, H) for g in frames] for name, frames in sheets.items()}
    for name in sheets:
        assert ff.same_as_draft(HERE / f'72_mahwot_{name}_draft.aseprite', pics[name]), \
            f'the {name} draft is not the design: it was edited, read it back before installing'
    backup = ROOT / 'art/_backup' / ('72_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    for name, (make, n, ms) in D.SHEETS.items():
        sheet = enemy_sheet.cardinal({v: pics[name] for v in 'DRU'})
        tags = enemy_sheet.install(sheet, ROOT / 'assets/enemies' / (FILES[name] + '.png'), n, ms=ms, palette=list(PAL.values()), backup=backup)
        print(f'installed {FILES[name]}: {sheet.width}x{sheet.height}, frame {W}x{H}, {n} frames at {ms} ms, tags {tags}', flush=True)
    print('old sheets in', backup)
    # for the fight, in frame pixels (the frame's middle is 49, 32.5); a mirrored cell's column is 98 minus its view's
    x, y = A.F_MOUTH
    print(f'  firing: the glow in its throat is the 2 x 2 at {A.F_MOUTH}, its middle ({x + 1.0}, {y + 1.0}); mirrored, column {W - x - 1.0}')
    print(f'  firing: from these columns on it is a row up, by frame: {D.BREATH} (the head is past all of them)')


if __name__ == '__main__':
    main()
