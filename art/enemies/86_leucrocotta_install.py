"""Install the approved 86 Leucrocotta sheets: the idle and the run.

Run after 86_leucrocotta_design.py. The drafts the user approved must still equal the design; the old
sheet is copied to art/_backup first. Art only: the ENEMY_SHEETS row and class Leucrocotta are edited by
hand to match what this prints.

    idle  assets/enemies/86_leucrocotta.png      the main sheet, 5 frames a direction
    run   assets/enemies/86_leucrocotta_run.png  its `flap`, 4 frames a direction, shown while it runs

Three views are drawn (front, side, back); the eight directions take them as enemy_sheet.cardinal lays
them out. The run is drawn from the side only (the user): its front and back cells hold the idle's first
four frames. The fight only ever runs it sideways, so those are not shown.

    python art/enemies/86_leucrocotta_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('86_leucrocotta_design')
ff, PAL, W, H = D.ff, D.PAL, D.W, D.H
FILES = {'idle': '86_leucrocotta', 'run': '86_leucrocotta_run'}


def main():
    sheets = D.build()                                             # also checks the three first-frame drafts
    pics = {name: {v: [ff.image(g, PAL, W, H) for g, thin in frames] for v, frames in sheets[name].items()} for name in sheets}
    for name in sheets:
        assert ff.same_as_draft(HERE / f'86_leucrocotta_{name}_draft.aseprite', [im for v in pics[name] for im in pics[name][v]]), \
            f'the {name} draft is not the design: it was edited, read it back before installing'
    n_run = D.SHEETS['run'][1]
    views = {'idle': pics['idle'], 'run': {'D': pics['idle']['D'][:n_run], 'R': pics['run']['R'], 'U': pics['idle']['U'][:n_run]}}
    backup = ROOT / 'art/_backup' / ('86_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    for name, (make, n, ms, drawn) in D.SHEETS.items():
        sheet = enemy_sheet.cardinal(views[name])
        tags = enemy_sheet.install(sheet, ROOT / 'assets/enemies' / (FILES[name] + '.png'), n, ms=ms, palette=list(PAL.values()), backup=backup)
        print(f'installed {FILES[name]}: {sheet.width}x{sheet.height}, frame {W}x{H}, {n} frames at {ms} ms, tags {tags}', flush=True)
    print('old sheet in', backup)
    # for the fight, in frame pixels (the frame's middle is 49, 32.5); a mirrored cell's column is 98 minus its view's
    print(f'  its mouth is open on idle frames {[f for f, c in enumerate(D.CALL) if c]}; the body sits {D.LIFT} rows up by frame')
    for v in 'DR':
        g = sheets['idle'][v][D.CALL_FRAME][0]
        red = [p for p, c in g.items() if c in 'mR']
        xs, ys = [x for x, y in red], [y for x, y in red]
        print(f'  open mouth {v}, frame {D.CALL_FRAME}: columns {min(xs)}-{max(xs)}, rows {min(ys)}-{max(ys)}')


if __name__ == '__main__':
    main()
