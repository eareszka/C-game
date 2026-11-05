"""Each enemy's first view as the player sees it, with its name and tier."""
import os
from PIL import Image
import audit_core as ac

TIERS = [('STARTER', 'Starter'), ('LOW', 'Low'), ('MEDIUM', 'Medium'), ('UPPER', 'Upper'), ('HARD', 'Hard'), ('SEVERE', 'Severe'),
         ('ELITE', 'Elite'), ('BOSS1', 'Boss 1'), ('BOSS2', 'Boss 2'), ('BOSS3', 'Boss 3')]
SMALL = {'Of', 'The', 'At', 'A', 'That'}


def nice(name):
    t = name.title().replace("'G", "'g").replace("'N", "'n")
    parts = t.split(' ')
    parts = [p if i == 0 or p not in SMALL else p.lower() for i, p in enumerate(parts)]
    t = ' '.join(parts)
    return t.replace('-At-A-', '-at-a-').replace("Grand'goule", "Grand'Goule")


def composed(r):
    """The first view as the player sees it. 06's two lowest heads are parts, drawn over it at their homes."""
    v = r['view'].copy()
    if r['id'] == 6:
        parts = Image.open(os.path.join(ac.ROOT, r['sheet']['parts'])).convert('RGBA')
        CW, CH = 42, 53
        AX, AY = (76, 182), (73, 84)              # WakmangganchiAragondi::home: the top-left of a biting head's cell, in frame art px
        for h in (0, 1):
            cell = parts.crop((0, h * CH, CW, (h + 1) * CH))
            v.alpha_composite(cell, (AX[h], AY[h]))
    return v.crop(v.getbbox())


def load():
    rows = ac.load_all()
    for r in rows:
        r['sprite'] = composed(r)
        r['nice'] = nice(r['name'])
    return rows
