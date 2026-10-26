"""Every enemy's front sprite, grouped by tier, easiest row first.

    python tools/enemy_tier_sheet.py <out.png>

Reads the tiers from ENEMY_TIERS in include/enemy.h, the sheet layouts from
ENEMY_SHEETS in src/battle.cpp and the names from ENEMY_NAMES in src/main.cpp,
so it always shows what the game uses. An enemy whose sprite isn't drawn yet
gets a NO SPRITE cell. The DONE tags are READY_ENEMIES in include/ready.h, the
list the game itself spawns from. Rerun after any tier change.
"""
import re, sys, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ORDER = [('STARTER', 'Starter', (200, 200, 200)), ('LOW', 'Low', (78, 220, 74)),
         ('MEDIUM', 'Medium', (132, 167, 233)), ('UPPER', 'Upper', (92, 148, 252)),
         ('HARD', 'Hard', (240, 188, 60)), ('SEVERE', 'Severe', (252, 152, 56)),
         ('ELITE', 'Elite', (236, 132, 118)), ('BOSS1', 'Boss tier 1', (183, 0, 0)),
         ('BOSS2', 'Boss tier 2', (124, 10, 27)),
         ('BOSS3', 'Boss tier 3', (80, 0, 40)), ('UNSET', 'Unset', (90, 90, 100))]

def table(path, start):
    s = open(os.path.join(ROOT, path), encoding='utf-8').read()
    i = s.index(start)
    return s[i:s.index('};', i)]

def ready_ids():
    # READY_ENEMIES in include/ready.h: the enemies a player can meet
    return {int(v) for v in re.findall(r'\d+', table('include/ready.h', 'READY_ENEMIES[] = {').split('{', 1)[1])}

def main(out, done=(), tags=None, dim=(), title=None, row_note=None):
    # done: ids whose bullet patterns are finished -- drawn with a green DONE mark
    # For charts built on this one (tools/enemy_redraw_sheet.py):
    #   tags(i) -> [(corner, text, fill)]: 'tr' a large mark top right, 'bl' / 'br' a small one at the bottom
    #   dim: ids drawn faded;  title: a line across the top;  row_note(ids) -> the text under a row's name
    sheets = [(m.group(1), int(m.group(2) or 3), m.group(3) == 'true') for m in re.finditer(
        # a row is { "path", {loop}, frames, rows, ... } -- or { nullptr } for an
        # enemy with no sprite yet, which still takes its slot
        r'\{\s*(?:"([^"]+)"|nullptr)\s*(?:,\s*\{[^}]*\}\s*(?:,\s*(\d+))?\s*(?:,\s*(true|false))?)?',
        table('src/battle.cpp', 'ENEMY_SHEETS[] = {'))]
    tiers = re.findall(r'T_([A-Z0-9]+)', table('include/enemy.h', 'ENEMY_TIERS[] = {'))
    names = re.findall(r'"([^"]+)"', table('src/main.cpp', 'ENEMY_NAMES[] = {'))
    assert len(names) == len(tiers) >= len(sheets), (len(names), len(tiers), len(sheets))
    CELL, LAB, LEFT = 96, 26, 130
    COLS = max(sum(1 for t in tiers if t == k) for k, _, _ in ORDER)
    rows = [(n, c, [i for i, t in enumerate(tiers) if t == k]) for k, n, c in ORDER]
    rows = [r for r in rows if r[2]]
    HEAD = 24 if title else 0
    img = Image.new('RGB', (LEFT + COLS * (CELL + 6) + 8, HEAD + len(rows) * (CELL + LAB + 14) + 8), (24, 24, 30))
    d = ImageDraw.Draw(img)
    try:
        font, big, small = (ImageFont.truetype('arial.ttf', 11), ImageFont.truetype('arialbd.ttf', 15),
                            ImageFont.truetype('arial.ttf', 10))
    except OSError:
        font = big = small = ImageFont.load_default()
    if title: d.text((10, 8), title, fill=(235, 235, 235), font=font)
    def tag(x0, y, corner, text, fill):
        f, h = (big, 20) if corner == 'tr' else (small, 14)
        w = int(d.textlength(text, font=f)) + 8
        x, yy = (x0 + CELL - w if corner in ('tr', 'br') else x0), (y if corner == 'tr' else y + CELL - h)
        d.rectangle([x, yy, x + w, yy + h], fill=fill)
        d.text((x + 4, yy + 1), text, fill=(0, 0, 0) if corner == 'tr' else (255, 255, 255), font=f)
    y = 8 + HEAD
    for name, col, ids in rows:
        d.rectangle([8, y, LEFT - 12, y + CELL + LAB], fill=(36, 36, 44))
        d.rectangle([8, y, 13, y + CELL + LAB], fill=col)
        d.text((20, y + CELL // 2 - 4), name, fill=(240, 240, 240), font=big)
        d.text((20, y + CELL // 2 + 16), row_note(ids) if row_note else '%d enemies' % len(ids), fill=(150, 150, 160), font=small)
        for j, i in enumerate(ids):
            x0 = LEFT + j * (CELL + 6)
            nm = names[i] if len(names[i]) <= 15 else names[i][:14] + '.'
            if i >= len(sheets) or sheets[i][0] is None:   # not drawn yet
                d.rectangle([x0, y, x0 + CELL, y + CELL], fill=(40, 40, 48))
                d.rectangle([x0, y, x0 + CELL, y + 2], fill=col)
                d.text((x0 + 18, y + CELL // 2 - 6), 'NO SPRITE', fill=(120, 120, 130), font=font)
                d.text((x0 + 2, y + CELL + 5), '%02d %s' % (i, nm), fill=(235, 235, 235), font=font)
                continue
            path, frames, byrow = sheets[i]
            im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
            W, H = im.size
            fw, fh = (W // frames, H // 8) if byrow else (W // (8 * frames), H)
            fr = im.crop((0, 0, fw, fh))           # front view, idle frame 0
            fr = fr.crop(fr.getbbox() or (0, 0, fw, fh))
            d.rectangle([x0, y, x0 + CELL, y + CELL], fill=(40, 40, 48))
            d.rectangle([x0, y, x0 + CELL, y + 2], fill=col)
            s = min(CELL / fr.width, CELL / fr.height)
            s = int(s) if s >= 1 else s
            nw, nh = max(1, int(fr.width * s)), max(1, int(fr.height * s))
            sp = fr.resize((nw, nh), Image.NEAREST)
            if i in dim: sp.putalpha(sp.getchannel('A').point(lambda a: a * 3 // 10))
            img.paste(sp, (x0 + (CELL - nw) // 2, y + (CELL - nh) // 2), sp)
            d.text((x0 + 2, y + CELL + 5), '%02d %s' % (i, nm), fill=(235, 235, 235), font=font)
            if i in done: tag(x0, y, 'br', 'DONE', (40, 160, 70))   # patterns finished: a green tag in the corner
            for corner, text, fill in (tags(i) if tags else ()): tag(x0, y, corner, text, fill)
        y += CELL + LAB + 14
    img.save(out)

if __name__ == '__main__':
    # optional 2nd arg: comma-separated ids to tag DONE instead of the ready list
    main(sys.argv[1], {int(v) for v in sys.argv[2].split(',')} if len(sys.argv) > 2 else ready_ids())
