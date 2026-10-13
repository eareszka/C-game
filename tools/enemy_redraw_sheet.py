"""The redraw chart: every enemy by tier -- what is redrawn to the sprite bible, and what is left.

    python tools/enemy_redraw_sheet.py [out.png]        (default: enemy_rating.png)

The tier sheet (tools/enemy_tier_sheet.py) with three marks a cell:
    top right     DONE (redrawn and installed), REF (one of the bible's four), OK (the user: fine as it is),
                  or, for one still to do, how close its sprite was to the bible when rated (8 closest)
    bottom left   PASS, or FAIL and the rules it breaks: the bible's checker on the sheets the game loads today
    faded         nothing left to do
What is done is data, art/enemies/redraw_status.json. The checker and sprite_style.json live on the
sprites branch (SPRITES below); it is pointed at this tree's ENEMY_SHEETS and assets.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPRITES = os.environ.get('SPRITES_WORKTREE', 'C:/Users/emery/.herdr/worktrees/C-game/sprites')
sys.path.insert(0, HERE)
import enemy_tier_sheet as ets              # this tree's: style_check's own import of the name gets it too
sys.path.append(os.path.join(SPRITES, 'tools'))
import style_check as sc
sc.ROOT = ROOT

RATED = {8: (120, 220, 60), 7: (160, 220, 60), 6: (200, 220, 60), 5: (232, 220, 60),
         4: (236, 180, 50), 3: (236, 140, 50), 2: (232, 100, 50)}


def main(out):
    st = json.load(open(os.path.join(ROOT, 'art', 'enemies', 'redraw_status.json'), encoding='utf-8'))
    settled = {**{i: 'REF' for i in st['reference']}, **{i: 'OK' for i in st['fine']['ids']}, **{i: 'DONE' for i in st['done']}}
    rating = {int(k): v for k, v in st['rating'].items() if k != '_'}
    count = len(ets.table('include/enemy.h', 'ENEMY_TIERS[] = {').split('T_')) - 1
    drawn = {i for i in range(count) if sc.enemy_sheets(i)}
    assert set(settled) <= drawn, sorted(set(settled) - drawn)
    left = sorted(drawn - set(settled))

    def tags(i):
        bad = [k for p, f, r, kind in sc.enemy_sheets(i)
               for k, (ok, _) in sc.check_sheet(p, f, r, sc.direction_class(i), sc.tier_of(i)).items() if ok is False]
        bad = list(dict.fromkeys(bad))
        mark = ('tr', settled[i], (60, 170, 90)) if i in settled else ('tr', str(rating[i]), RATED[rating[i]]) if i in rating else None
        return ([mark] if mark else []) + [('bl', 'FAIL ' + ' '.join(bad), (190, 40, 40)) if bad else ('bl', 'PASS', (40, 150, 70))]

    def row_note(ids):
        n = len([i for i in ids if i in left])
        return '%d left of %d' % (n, len(ids)) if n else 'all %d done' % len(ids)

    ets.main(out, tags=tags, dim=set(settled), row_note=row_note,
             title='Enemy redraw to the sprite bible: %d left of %d drawn, %d done.   Faded = done.   '
                   'Number = closeness to the bible when rated (8 closest).   PASS / FAIL = the bible checker today.'
                   % (len(left), len(drawn), len(drawn) - len(left)))
    print('%d left: %s' % (len(left), ' '.join('%02d' % i for i in left)))
    print('no sprite: %s' % (' '.join('%02d' % i for i in range(count) if i not in drawn) or 'none'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'enemy_rating.png'))
