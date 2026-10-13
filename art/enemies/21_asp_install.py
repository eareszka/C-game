"""Install the approved 21 Asp sheet: its idle.

Run after 21_asp_design.py. The drafts the user approved must still equal the design; the old sheet is
copied to art/_backup first. Art only: the ENEMY_SHEETS row and class Asp are edited by hand to match
what this prints.

    assets/enemies/21_asp.png   the main sheet, 10 frames a direction

Three views are drawn (front, side, back); the eight directions take them as enemy_sheet.cardinal lays them out.

    python art/enemies/21_asp_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('21_asp_design')
ff, PAL, W, H = D.ff, D.PAL, D.W, D.H


def main():
    sheet = D.build()                                              # also checks the three first-frame drafts
    pics = {v: [ff.image(g, PAL, W, H) for g, thin in sheet[v]] for v in D.DRAFT}
    assert ff.same_as_draft(HERE / '21_asp_idle_draft.aseprite', [im for v in D.DRAFT for im in pics[v]]), \
        'the idle draft is not the design: it was edited, read it back before installing'
    backup = ROOT / 'art/_backup' / ('21_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    out = enemy_sheet.cardinal(pics)
    tags = enemy_sheet.install(out, ROOT / 'assets/enemies/21_asp.png', D.N, ms=D.MS, palette=list(PAL.values()), backup=backup)
    print(f'installed 21_asp: {out.width}x{out.height}, frame {W}x{H}, {D.N} frames at {D.MS} ms, tags {tags}')
    print('old sheet in', backup)
    # for the fight, in frame pixels (the frame's middle is 21, 17.5); a mirrored cell's column is 42 minus its view's
    print(f'  its tongue is out from frame {D.HISS_FRAME} ({D.HISS_FRAME * D.MS} ms); on that frame it neither sways nor dips: {D.SWAY[D.HISS_FRAME]}, {D.DIP[D.HISS_FRAME]}')
    for v in D.DRAFT: print(f'  tongue tip {v}: {D.tip(v, D.HISS_FRAME)}')
    top = min(y for (x, y), c in sheet['U'][D.HISS_FRAME][0].items() if c == 'L')
    print(f'  from behind, the top of its head: its first lit row is {top}')


if __name__ == '__main__':
    main()
