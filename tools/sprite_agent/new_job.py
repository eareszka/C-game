"""Sets up one sprite job folder, so each new agent gets the same rule and prompt and only this enemy's brief. run.py calls this.

    python -B tools/sprite_agent/new_job.py 42           # makes art/enemies/nes/42_nykur/
    python -B tools/sprite_agent/new_job.py --board      # rebuilds the fixed style board

An earlier attempt moves to art/enemies/nes/_old/, where the next agent can't see it.
"""
import hashlib
import json
import os
import re
import shutil
import sys
import time

from PIL import Image

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
os.chdir(ROOT)
sys.path.insert(0, 'tools')
import enemy_style as es

JOBS = os.path.join('art', 'enemies', 'nes')
RULE = os.path.join('art', 'direction', 'SPRITE_STYLE.md')
PROMPT = os.path.join('tools', 'sprite_agent', 'PROMPT.md')
BOARD = os.path.join('art', 'direction', 'nes_style_board.png')
CELLS = (40, 44, 48, 80)


def mini_front(i):
    import glob
    paths = glob.glob(os.path.join('art', 'enemies', 'minis', '%02d_*_mini.png' % i))
    if not paths:
        return None
    im = Image.open(paths[0]).convert('RGBA')
    for n in (2, 1, 3):
        w = im.width / (4 * n)
        if w == int(w) and int(w) in CELLS:
            cell = im.crop((0, 0, int(w), im.height))
            return cell.crop(cell.getbbox())
    return None


def board():
    """The 26 picks at 3x on black, smallest tiers first: what the style looks like. Fixed, the same for every job."""
    sheets, tiers = es.sheets(), es.tiers()
    order = list(es.NES_SIDE)
    items = sorted(es.NES_ANCHORS, key=lambda i: (order.index(tiers[i]), i))
    ims = [es.first_frame(sheets[i]['path'], sheets[i]['frames'], sheets[i]['rows'])[0] for i in items]
    scale, width, gap = 3, 1280, 18
    x = y = gap
    shelf = 0
    place = []
    for im in ims:
        w, h = im.width * scale, im.height * scale
        if x + w + gap > width:
            x, y, shelf = gap, y + shelf + gap, 0
        place.append((im, x, y))
        x += w + gap
        shelf = max(shelf, h)
    out = Image.new('RGB', (width, y + shelf + gap), (0, 0, 0))
    for im, px, py in place:
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        out.paste(big, (px, py), big)
    out.save(BOARD)
    print(BOARD, out.size)


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()[:12]


def make(i):
    names, tiers, sheets = es.names(), es.tiers(), es.sheets()
    with open(os.path.join(HERE, 'briefs.json'), encoding='utf-8') as f:
        briefs = json.load(f)
    entry = briefs.get(str(i))
    if not entry or not entry.get('look'):
        raise SystemExit('Enemy %d has no brief yet. Add its look to tools/sprite_agent/briefs.json first.' % i)

    slug = re.sub(r'[^a-z0-9]+', '_', names[i].lower()).strip('_')
    folder = os.path.join(JOBS, '%02d_%s' % (i, slug))
    if os.path.isdir(folder):
        old = os.path.join(JOBS, '_old', '%02d_%s_%s' % (i, slug, time.strftime('%Y%m%d_%H%M%S')))
        os.makedirs(os.path.dirname(old), exist_ok=True)
        shutil.move(folder, old)
    os.makedirs(folder)

    side = es.nes_target(i)[0]
    colours = entry.get('colours', es.NES2_COLOURS)     # a brief can ask for up to 8 when the design needs it
    tier_name = es.TIER_NAMES[tiers[i]]
    lines = ['# Job: %d %s' % (i, names[i].title()), '',
             '- **Tier:** %s' % tier_name,
             '- **Size:** %d px on its longer side. Within %d px either way is fine.' % (side, es.nes_tolerance(side)),
             '- **Colours:** at most %d plus black.' % colours,
             '- **Look:** %s' % entry['look'],
             '- **Draw:** %s' % entry.get('draw', 'its first idle pose, facing the player, as in the reference.')]
    if entry.get('note'):
        lines.append('- **Note:** %s' % entry['note'])
    for fix in entry.get('fixes', []):
        lines.append('- **Must have:** %s' % fix)
    with open(os.path.join(folder, 'BRIEF.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')

    shutil.copyfile(RULE, os.path.join(folder, 'RULE.md'))
    shutil.copyfile(os.path.join(HERE, 'pix.py'), os.path.join(folder, 'pix.py'))
    if not os.path.exists(BOARD):
        board()
    shutil.copyfile(BOARD, os.path.join(folder, 'style.png'))

    # reference: what this creature looks like now, battle sprite then map mini, at 4x (2x if it's big) on black
    if entry.get('reference'):  # a redesign: the picture the user gave replaces the current sprite
        shutil.copyfile(entry['reference'], os.path.join(folder, 'reference.png'))
    else:
        s = sheets[i]
        battle = es.first_frame(s['path'], s['frames'], s['rows'])[0]
        if i == 6:                  # its two lowest heads are separate parts in the game: show the whole creature
            sys.path.insert(0, os.path.join('tools', 'enemy_audit'))
            import audit_core as ac
            import audit_rows as ar
            battle = ar.composed(next(r for r in ac.load_all() if r['id'] == 6))
        mini = mini_front(i)
        k = 4 if max(battle.size) <= 110 else 2
        parts = [battle.resize((battle.width * k, battle.height * k), Image.NEAREST)]
        if mini is not None:
            parts.append(mini.resize((mini.width * 4, mini.height * 4), Image.NEAREST))
        ref = Image.new('RGB', (sum(p.width for p in parts) + 24 * (len(parts) + 1), max(p.height for p in parts) + 32), (0, 0, 0))
        x = 24
        for p in parts:
            ref.paste(p, (x, ref.height - 16 - p.height), p)
            x += p.width + 24
        ref.save(os.path.join(folder, 'reference.png'))

    # palette, as a plain list, because draw.py needs exact colours
    with open(os.path.join(folder, 'palette.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join('%02x%02x%02x' % tuple(c) for c in es.fcremap.PALETTE if tuple(c) != (0, 0, 0)) + '\n')

    with open(os.path.join(folder, 'job.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(id=i, side=side, tolerance=es.nes_tolerance(side), colours=colours, rule_version=3, rule=sha(RULE), prompt=sha(PROMPT) if os.path.exists(PROMPT) else None,
                       made=time.strftime('%Y-%m-%d %H:%M')), f, indent=0)
    return folder


if __name__ == '__main__':
    if sys.argv[1:] == ['--board']:
        board()
    else:
        print(make(int(sys.argv[1])))
