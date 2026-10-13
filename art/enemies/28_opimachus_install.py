"""Install the approved 28 Opimachus idle as the game's sheet.

Run after 28_opimachus_design.py. The draft the user approved must still equal the design; the old
sheet, its .aseprite and built.json are copied to art/_backup first. Art only: the ENEMY_SHEETS row
and class Opimachus are edited by hand to match what this prints.

    python art/enemies/28_opimachus_install.py
"""
from pathlib import Path
from datetime import datetime
import importlib, shutil, sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import enemy_sheet
D = importlib.import_module('28_opimachus_design')
W, H, N = D.W, D.H, len(D.TAIL)
NAME = '28_opimachus'
PLUMES = {'left': ((19, 5), (20, 5)), 'right': ((33, 5), (34, 5))}   # the outer plumes' tops in frame 0: where the crest rings leave


def plume_tips(fr):
    """Per frame, the middle of each outer plume's top, in frame pixels."""
    g0 = fr[0]
    out = []
    for f in range(N):
        tips = {}
        for side, px in PLUMES.items():
            assert all(g0.get(p) == 'r' for p in px), f'the {side} plume is not where it was drawn'
            moved = D.breathe(D.sway({p: 'r' for p in px}, D.GUST[f]), D.BREATH[f])
            assert all(fr[f].get(p) == 'r' for p in moved)
            tips[side] = (sum(x for x, y in moved) / len(moved) + 0.5, sum(y for x, y in moved) / len(moved) + 0.5)
        out.append(tips)
    return out


def main():
    fr = D.frames()
    assert D.P.ff.same_as_draft(HERE / (NAME + '_idle_draft.aseprite'), [D.P.image(g) for g in fr]), \
        'the draft is not the design: it was edited, read it back before installing'
    backup = ROOT / 'art/_backup' / (NAME[:2] + '_before_install_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(ROOT / 'assets/enemies/built.json', backup)
    # one row, 8 directions x N frames, every direction the drawing as drawn (nothing mirrored)
    sheet = Image.new('RGBA', (8 * N * W, H), (0, 0, 0, 0))
    for d in range(8):
        for f, g in enumerate(fr): sheet.paste(D.P.image(g), ((d * N + f) * W, 0))
    tags = enemy_sheet.install(sheet, ROOT / 'assets/enemies' / (NAME + '.png'), N, ms=D.STEP_MS, palette=list(D.PAL.values()), backup=backup)
    print(f'installed {NAME}: {sheet.width}x{sheet.height}, frame {W}x{H}, {N} frames at {D.STEP_MS} ms, tags {tags}')
    print('old sheet in', backup)
    for f, t in enumerate(plume_tips(fr)):
        print(f'  frame {f}: plume tops left ({t["left"][0]:.1f}, {t["left"][1]:.1f})  right ({t["right"][0]:.1f}, {t["right"][1]:.1f})'
              f'   gust {D.GUST[f]:+d} breath {D.BREATH[f]:+d} tail {D.TAIL[f]}')


if __name__ == '__main__':
    main()
