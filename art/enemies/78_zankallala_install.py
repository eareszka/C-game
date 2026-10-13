"""Install the approved 78 Zankallala sheets: the idle and the dash.

Run after 78_zankallala_design.py. The drafts the user approved must still equal the design; the old
sheets are copied to art/_backup first. Art only: the ENEMY_SHEETS row and class Zankallala are edited
by hand to match what this prints.

    idle  assets/enemies/78_zankallala.png      the main sheet, 10 frames
    dash  assets/enemies/78_zankallala_run.png  its `flap`, four frames a direction, shown while it runs

Three views are drawn (front, side, back); the eight directions take them as enemy_sheet.cardinal lays them out.

    python art/enemies/78_zankallala_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('78_zankallala_design')
ff, PAL, W, H = D.ff, D.PAL, D.W, D.H
FILES = {'idle': '78_zankallala', 'dash': '78_zankallala_run'}


def main():
    sheets = D.build()
    pics = {name: {v: [ff.image(g, PAL, W, H) for g, thin in sheets[name][v]] for v in D.DRAFT} for name in sheets}
    for name in sheets:
        assert ff.same_as_draft(HERE / f'78_zankallala_{name}_draft.aseprite', [im for v in D.DRAFT for im in pics[name][v]]), \
            f'the {name} draft is not the design: it was edited, read it back before installing'
    backup = ROOT / 'art/_backup' / ('78_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    for name, (make, n, ms) in D.SHEETS.items():
        sheet = enemy_sheet.cardinal(pics[name])
        tags = enemy_sheet.install(sheet, ROOT / 'assets/enemies' / (FILES[name] + '.png'), n, ms=ms, palette=list(PAL.values()), backup=backup)
        print(f'installed {FILES[name]}: {sheet.width}x{sheet.height}, frame {W}x{H}, {n} frames at {ms} ms, tags {tags}', flush=True)
    print('old sheets in', backup)
    # for the fight, in frame pixels (the frame's middle is 29, 26.5); a mirrored cell's column is 58 minus its view's
    for name in sheets:
        for v in D.DRAFT:
            print(f'  {name} {v}: staff tip by frame ' + ' '.join('(%.1f, %.1f)' % D.staff_tip(g) for g, thin in sheets[name][v]))
    for v in D.DRAFT:
        g = sheets['idle'][v][0][0]
        hat = [p for p, c in g.items() if c == 'G' and 12 <= p[1] <= 18 and any(g.get((p[0] + dx, p[1])) in ('G', 'D') for dx in (-1, 1))]
        xs, ys = [x for x, y in hat], [y for x, y in hat]
        print(f'  hat {v}: columns {min(xs) - 1}-{max(xs) + 1}, rows {min(ys) - 1}-{max(ys) + 1}, middle ({(min(xs) + max(xs) + 1) / 2:.1f}, {(min(ys) + max(ys) + 1) / 2:.1f})')


if __name__ == '__main__':
    main()
