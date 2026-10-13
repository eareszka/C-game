"""Install the approved 07 Alber sheet: its one animation, flying.

Run after 07_alber_design.py. The draft the user approved must still equal the design; the old sheet is
copied to art/_backup first. Art only: the ENEMY_SHEETS row and class Alber are edited by hand to match
what this prints.

    assets/enemies/07_alber.png   the main sheet, 6 frames a direction

Three views are drawn (front, side, back); the eight directions take them as enemy_sheet.cardinal lays them out.

    python art/enemies/07_alber_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('07_alber_design')
ff, PAL, W, H = D.ff, D.PAL, D.W, D.H
# Where its fire leaves, on each view's first-frame drawing, frame pixels: the middle of the mouth from the
# front, the front of the mouth from the side, the top of its head from behind (the mouth is past it).
MOUTH = {'D': (36.0, 20.5), 'R': (63.0, 18.5), 'U': (36.0, 8.0)}


def main():
    sheet = D.build()
    pics = {v: [ff.image(g, PAL, W, H) for g, thin in sheet[v]] for v in D.VIEWS}
    assert ff.same_as_draft(HERE / '07_alber_fly_draft.aseprite', [im for v in D.VIEWS for im in pics[v]]), \
        'the flying draft is not the design: it was edited, read it back before installing'
    g = sheet['D'][0][0]
    assert all(g.get((x, 20 + D.RISE[0])) == 'K' for x in (34, 35, 36, 37)), 'the front mouth is not where MOUTH says'
    g = sheet['R'][0][0]
    assert g.get((63, 18 + D.RISE[0])) == 'K' and (64, 18 + D.RISE[0]) not in g, 'the side mouth is not where MOUTH says'
    backup = ROOT / 'art/_backup' / ('07_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    out = enemy_sheet.cardinal(pics)
    tags = enemy_sheet.install(out, ROOT / 'assets/enemies/07_alber.png', D.N, ms=D.MS, palette=list(PAL.values()), backup=backup)
    print(f'installed 07_alber: {out.width}x{out.height}, frame {W}x{H}, {D.N} frames at {D.MS} ms, tags {tags}')
    print('old sheet in', backup)
    # for the fight, in frame pixels (the frame's middle is 36, 32); a mirrored cell's column is 72 minus its view's
    print('  rows the body sits below its first-frame drawing, by frame:', ' '.join(map(str, D.RISE)))
    for v, (mx, my) in MOUTH.items(): print(f'  mouth {v}: ({mx}, {my}) plus that')


if __name__ == '__main__':
    main()
