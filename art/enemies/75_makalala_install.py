"""Install the approved 75 Makalala sheets: the idle and the flying.

Run after 75_makalala_design.py. The drafts the user approved must still equal the design; the old sheets
are copied to art/_backup first. Art only: the ENEMY_SHEETS row and class Makalala are edited by hand to
match what this prints.

    idle  assets/enemies/75_makalala.png      the main sheet, 5 frames a direction: the front (the user)
    fly   assets/enemies/75_makalala_fly.png  its `flap`, 4 frames a direction: the side, left its mirror

One view is drawn for each. The game's sheets hold eight directions, so every slot takes that view
(enemy_sheet.cardinal); the fight shows the idle from the front only and the flying left and right only.

    python art/enemies/75_makalala_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('75_makalala_design')
A, ff, PAL, W, H = D.A, D.ff, D.PAL, D.W, D.H
FILES = {'idle': '75_makalala', 'fly': '75_makalala_fly'}


def main():
    sheets = D.build()                                             # also checks the two first-frame drafts
    pics = {name: [ff.image(g, PAL, W, H) for g, thin in frames] for name, frames in sheets.items()}
    for name in sheets:
        assert ff.same_as_draft(HERE / f'75_makalala_{name}_draft.aseprite', pics[name]), \
            f'the {name} draft is not the design: it was edited, read it back before installing'
    backup = ROOT / 'art/_backup' / ('75_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    for name, (make, n, ms) in D.SHEETS.items():
        sheet = enemy_sheet.cardinal({v: pics[name] for v in 'DRU'})
        tags = enemy_sheet.install(sheet, ROOT / 'assets/enemies' / (FILES[name] + '.png'), n, ms=ms, palette=list(PAL.values()), backup=backup)
        print(f'installed {FILES[name]}: {sheet.width}x{sheet.height}, frame {W}x{H}, {n} frames at {ms} ms, tags {tags}', flush=True)
    print('old sheets in', backup)
    # for the fight, in frame pixels (the frame's middle is 49, 32.5)
    print(f'  idle: the closed beak\'s tip is pixel {A.BEAK}, its middle ({A.BEAK[0] + 0.5}, {A.BEAK[1] + 0.5}); the body is {D.LIFT} rows up by frame')
    print(f'  idle: on the scream, frame {D.SCREAM}, the gape\'s middle is ({D.GAPE[0] + 0.5}, {D.GAPE[1] + 0.5 - D.LIFT[D.SCREAM]})')
    print(f'  fly: the club\'s middle pixel is {A.CLUB} on every frame; mirrored, column {W - 1 - A.CLUB[0]}')


if __name__ == '__main__':
    main()
