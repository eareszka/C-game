"""Install the approved 39 Ajaju sheet: its idle (breath, tongues, tail).

Run after 39_ajaju_design.py. The drafts the user approved must still equal the design; the old sheet is
copied to art/_backup first. Art only: the ENEMY_SHEETS row and class Ajaju are edited by hand to match
what this prints.

    assets/enemies/39_ajaju.png   the main sheet, 10 frames a direction

Three views are drawn (front, side, back); the eight directions take them as enemy_sheet.cardinal lays them out.

    python art/enemies/39_ajaju_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('39_ajaju_design')
A, ff, PAL, W, H = D.A, D.ff, D.PAL, D.W, D.H
FIRST = {'D': '39_ajaju_frame0_draft', 'R': '39_ajaju_side_frame0_draft', 'U': '39_ajaju_back_frame0_draft'}


def main():
    sheet = D.build()
    pics = {v: [ff.image(g, PAL, W, H) for g, thin in sheet[v]] for v in D.VIEWS}
    assert ff.same_as_draft(HERE / '39_ajaju_idle_draft.aseprite', [im for v in D.VIEWS for im in pics[v]]), \
        'the idle draft is not the design: it was edited, read it back before installing'
    for v, name in FIRST.items():
        assert ff.same_as_draft(HERE / (name + '.aseprite'), [pics[v][0]]), f'{name} is not the design: it was edited, read it back'
    for v in 'DR':                                                 # the mouth is drawn where mouth() says, on every frame
        x, y = A.MOUTH if v == 'D' else A.S_MOUTH
        for f in range(D.N): assert sheet[v][f][0].get((x, y - D.LIFT[f])) == 'K', f'{v} frame {f}: the mouth moved'
    backup = ROOT / 'art/_backup' / ('39_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    out = enemy_sheet.cardinal(pics)
    tags = enemy_sheet.install(out, ROOT / 'assets/enemies/39_ajaju.png', D.N, ms=D.MS, palette=list(PAL.values()), backup=backup)
    print(f'installed 39_ajaju: {out.width}x{out.height}, frame {W}x{H}, {D.N} frames at {D.MS} ms, tags {tags}')
    print('old sheet in', backup)
    # for the fight, in frame pixels (the frame's middle is 31, 23.5); a mirrored cell's column is 62 minus its view's
    print('  rows the head sits above its first-frame drawing, by frame:', ' '.join(map(str, D.LIFT)))
    for v in D.VIEWS: print(f'  mouth {v}: {D.mouth(v, 0)} less that')
    print(f'  tongues widest on frame {D.FAN_FRAME} ({D.FAN_FRAME * D.MS} ms); the small flick on frame 8 ({8 * D.MS} ms)')


if __name__ == '__main__':
    main()
