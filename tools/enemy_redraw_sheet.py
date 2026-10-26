"""The redraw chart: every enemy by tier -- what is redrawn to the sprite bible, and what is left.

    python tools/enemy_redraw_sheet.py [out.png]        (default: enemy_rating.png)
    python tools/enemy_redraw_sheet.py --complete ID   (approved, installed art only)

The tier sheet (tools/enemy_tier_sheet.py) with three marks a cell:
    top right     DONE (redrawn and installed), REF (one of the bible's four), OK (the user: fine as it is),
                  or, for one still to do, how close its sprite was to the bible when rated (8 closest)
    bottom left   PASS, or FAIL and the rules it breaks: the bible's checker on the sheets the game loads today
    faded         nothing left to do
What is done is data, art/enemies/redraw_status.json. The checker and sprite_style.json live on the
sprites branch (SPRITES below); it is pointed at this tree's ENEMY_SHEETS and assets.
Without that optional checker, LOCAL labels check primary-sheet palette,
binary alpha and layout only; they do not certify the full sprite bible.
"""
import argparse, json, os, re, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPRITES = os.environ.get('SPRITES_WORKTREE', 'C:/Users/emery/.herdr/worktrees/C-game/sprites')
sys.path.insert(0, HERE)
import enemy_tier_sheet as ets              # this tree's: style_check's own import of the name gets it too
sys.path.append(os.path.join(SPRITES, 'tools'))
try:
    import style_check as sc
except ModuleNotFoundError as error:
    if error.name != 'style_check':
        raise
    sc = None
if sc is not None:
    sc.ROOT = ROOT
else:
    sys.path.insert(0, os.path.join(ROOT, 'art', 'direction'))
    import fcremap


def primary_sheets():
    return [(m.group(1), int(m.group(2) or 3), m.group(3) == 'true') for m in re.finditer(
        r'\{\s*(?:"([^"]+)"|nullptr)\s*(?:,\s*\{[^}]*\}\s*(?:,\s*(\d+))?\s*(?:,\s*(true|false))?)?',
        ets.table('src/battle.cpp', 'ENEMY_SHEETS[] = {'))]


def local_checks(sheet):
    path, frames, rows = sheet
    im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
    pixels = list(im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata())
    bad = []
    if (im.width % frames or im.height % 8) if rows else im.width % (8 * frames):
        bad.append('LAYOUT')
    if any(p[3] not in (0, 255) for p in pixels):
        bad.append('ALPHA')
    if any(p[:3] not in fcremap.PALETTE for p in pixels if p[3]):
        bad.append('PAL')
    return bad

RATED = {8: (120, 220, 60), 7: (160, 220, 60), 6: (200, 220, 60), 5: (232, 220, 60),
         4: (236, 180, 50), 3: (236, 140, 50), 2: (232, 100, 50)}


def main(out, complete=None):
    st = json.load(open(os.path.join(ROOT, 'art', 'enemies', 'redraw_status.json'), encoding='utf-8'))
    sheets = primary_sheets()
    if complete is not None:
        assert 0 <= complete < len(sheets) and sheets[complete][0], 'Cannot complete an enemy without an installed sprite'
        st['done'] = sorted(set(st['done']) | {complete})
    settled = {**{i: 'REF' for i in st['reference']}, **{i: 'OK' for i in st['fine']['ids']}, **{i: 'DONE' for i in st['done']}}
    rating = {int(k): v for k, v in st['rating'].items() if k != '_'}
    count = len(ets.table('include/enemy.h', 'ENEMY_TIERS[] = {').split('T_')) - 1
    drawn = {i for i in range(count) if sc.enemy_sheets(i)} if sc else {i for i, sheet in enumerate(sheets) if sheet[0]}
    assert set(settled) <= drawn, sorted(set(settled) - drawn)
    left = sorted(drawn - set(settled))

    def tags(i):
        bad = ([k for p, f, r, kind in sc.enemy_sheets(i)
                for k, (ok, _) in sc.check_sheet(p, f, r, sc.direction_class(i), sc.tier_of(i)).items() if ok is False]
               if sc else local_checks(sheets[i]))
        bad = list(dict.fromkeys(bad))
        mark = ('tr', settled[i], (60, 170, 90)) if i in settled else ('tr', str(rating[i]), RATED[rating[i]]) if i in rating else None
        prefix = '' if sc else 'LOCAL '
        return ([mark] if mark else []) + [('bl', prefix + 'FAIL ' + ' '.join(bad), (190, 40, 40)) if bad else ('bl', 'PASS' if sc else 'LOCAL OK', (40, 150, 70))]

    def row_note(ids):
        n = len([i for i in ids if i in left])
        return '%d left of %d' % (n, len(ids)) if n else 'all %d done' % len(ids)

    check_note = ('PASS/FAIL = bible checker.' if sc else
                  'LOCAL = primary palette/alpha/layout only; style needs review.')
    title = ('Enemy redraws: %d left of %d drawn, %d settled. Faded = done. '
             'Number = old bible rating. %s') % (len(left), len(drawn), len(drawn) - len(left), check_note)
    ets.main(out, tags=tags, dim=set(settled), row_note=row_note, title=title)
    if complete is not None:
        status_path = os.path.join(ROOT, 'art', 'enemies', 'redraw_status.json')
        with open(status_path, encoding='utf-8') as f:
            text = f.read()
        text = re.sub(r'"done":\s*\[[^\]]*\]', '"done": ' + json.dumps(st['done']), text)
        with open(status_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    print('%d left: %s' % (len(left), ' '.join('%02d' % i for i in left)))
    print('no sprite: %s' % (' '.join('%02d' % i for i in range(count) if i not in drawn) or 'none'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', nargs='?', default=os.path.join(ROOT, 'enemy_rating.png'))
    parser.add_argument('--complete', type=int, help='Mark a user-approved, installed sprite DONE and refresh the visible chart')
    args = parser.parse_args()
    main(args.output, args.complete)
