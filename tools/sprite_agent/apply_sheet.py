"""Puts each sprite.png into the game as a still: the same picture in every frame and direction slot of its main sheet.

    python -B tools/sprite_agent/apply_sheet.py          # say what would change
    python -B tools/sprite_agent/apply_sheet.py --write  # change the sheets and the ENEMY_SHEETS table

The frame size becomes the sprite's size and the frame count stays, so the game's animation indexes stay valid. An applied
enemy's flap and alt sheets are turned off in src/battle.cpp, because they show the old design at the old size. Its log and
marks stay. Run edit_sheet.py update first, so saved edits are included. Real animation is a later job.
"""
import glob
import os
import sys

from PIL import Image, ImageChops

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
os.chdir(ROOT)
sys.path.insert(0, 'tools')
import enemy_style as es


def trimmed(im):
    return im.crop(im.getbbox())


def changed_ids(sheets):
    out = []
    for i, s in enumerate(sheets):
        found = glob.glob('art/enemies/nes/%02d_*/sprite.png' % i)
        if not found:
            continue
        new = trimmed(Image.open(found[0]).convert('RGBA'))
        now = es.first_frame(s['path'], s['frames'], s['rows'])[0].convert('RGBA')
        if new.size != now.size or ImageChops.difference(new, now).getbbox():
            out.append((i, new))
    return out


def still_sheet(sprite, frames, rows):
    w, h = sprite.size
    columns, lines = (frames, 8) if rows else (8 * frames, 1)
    sheet = Image.new('RGBA', (w * columns, h * lines), (0, 0, 0, 0))
    for y in range(lines):
        for x in range(columns):
            sheet.paste(sprite, (x * w, y * h))
    return sheet


def turn_off_extras(source, sheets, ids):
    """flap and alt become nullptr on the applied enemies' rows of ENEMY_SHEETS."""
    start = source.index('ENEMY_SHEETS[] = {')
    end = source.index('\n};', start)
    lines = source[start:end].split('\n')
    rows = [n for n, line in enumerate(lines) if line.strip().startswith('{')]
    assert len(rows) == len(sheets), (len(rows), len(sheets))
    off = []
    for i in ids:
        s = sheets[i]
        n = rows[i]
        assert '"%s"' % s['path'] in lines[n], (i, lines[n][:80])
        stop = rows[i + 1] if i + 1 < len(rows) else len(lines)      # an entry can span two lines
        for key in ('flap', 'alt'):
            if not s[key]:
                continue
            for m in range(n, stop):
                code, bar, comment = lines[m].partition('//')
                if '"%s"' % s[key] in code:
                    lines[m] = code.replace('"%s"' % s[key], 'nullptr', 1) + bar + comment
                    off.append((i, key))
                    break
            else:
                raise SystemExit('%d: no %s in its table entry' % (i, key))
    return source[:start] + '\n'.join(lines) + source[end:], off


def main():
    write = '--write' in sys.argv
    sheets = es.sheets()
    todo = changed_ids(sheets)
    print('%d sprites differ from the game: %s' % (len(todo), ' '.join(str(i) for i, _ in todo)))
    path = os.path.join('src', 'battle.cpp')
    with open(path, encoding='utf-8', newline='') as f:
        source = f.read()
    updated, off = turn_off_extras(source, sheets, [i for i, _ in todo])
    print('extra sheets turned off: %s' % ' '.join('%d:%s' % o for o in off))
    if not write:
        return
    for i, sprite in todo:
        s = sheets[i]
        still_sheet(sprite, s['frames'], s['rows']).save(s['path'])
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(updated)
    left = changed_ids(es.sheets())
    print('after: %d still differ: %s' % (len(left), [i for i, _ in left]))


if __name__ == '__main__':
    main()
