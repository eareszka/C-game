"""Rebuild the enemy style audit from the sprites as they stand now: the same set as the newest edit sheet. Numbers in the copy are measured here.

  python -B tools/enemy_audit/build_audit.py [OUT_DIR]

Writes enemy_style_audit.html to OUT_DIR (default: a temp folder), and records what it was built from in last_build.json.
Publish the page with the Artifact tool to https://claude.ai/artifact/EVMbnRYyQaVXmJuyjp8whu. A session that hasn't published it yet passes that as `url`, after reading it.
The by-eye ratings live in diagnosis.json, each tied to the sprite it was made from, so a changed sprite shows as needing a new look. The page before the refresh of 2026-11-05 is in old/."""
import base64, glob, io, json, os, re, statistics as st, subprocess, sys, tempfile, time
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), 'enemy_audit')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE)
import audit_core as ac
import audit_rows as ar
import audit_watch as aw
os.chdir(ac.ROOT)

# Edits saved on an edit sheet go into each sprite.png first, so the audit always shows them. A failure here doesn't stop the build.
_took = subprocess.run([sys.executable, '-B', os.path.join('tools', 'sprite_agent', 'edit_sheet.py'), 'update'], capture_output=True, text=True, encoding='utf-8', errors='replace')
for _line in (_took.stdout.strip().splitlines() or ['printed nothing']) + (['failed: ' + _took.stderr.strip()[-400:]] if _took.returncode else []):
    print('edit sheets: ' + _line)

sys.path.insert(0, 'tools')
sys.path.insert(0, os.path.join('tools', 'sprite_agent'))
import enemy_style as es
import edit_sheet as ed
sys.path.insert(0, os.path.join(ac.ROOT, 'art', 'direction'))
import fcremap

BUILT_FROM = aw.snapshot()      # before reading any sprite, so a sheet that changes mid-build still shows as new
DIAG = {int(k): v for k, v in json.load(open(os.path.join(HERE, 'diagnosis.json'), encoding='utf-8')).items() if k != '_'}
tiers, game = es.tiers(), es.sheets()
TIERS = ar.TIERS
RATED = [('standard', 'The standard', 'Your picks and approvals: what the rest is judged against.'),
         ('match', 'Matches', 'Would sit beside the standard without standing out.'),
         ('close', 'Close', 'Fits, with one thing off.'),
         ('no', "Doesn't match", 'Stands out as a different kind of drawing.')]
RULES = {0: 'Your original', 1: 'First rule', 2: 'Tightened rule', 3: 'Closed-parts rule'}
PICKS = [i for i in es.NES_ANCHORS if i not in es.NES_RESIZE]


def b64(im):
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def join_and(items):
    items = [str(i) for i in items]
    return items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' and ' + items[-1]


def med(values):
    return st.median(values) if values else 0


R = {}
for i in range(101):
    folder, job, loops = None, {}, None
    if i in PICKS:
        s = game[i]
        im = es.first_frame(s['path'], s['frames'], s['rows'])[0].convert('RGBA')
    else:
        folder = glob.glob(os.path.join('art', 'enemies', 'nes', '%02d_*' % i))[0]
        im = Image.open(os.path.join(folder, 'sprite.png')).convert('RGBA')
        job = json.load(open(os.path.join(folder, 'job.json'), encoding='utf-8'))
    im = im.crop(im.getbbox())
    m = es.measure(im)
    px = im.load()
    by = {}
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3] and px[x, y][:3] != (0, 0, 0):
                by.setdefault(px[x, y][:3], []).append((x, y))
    if folder and os.path.exists(os.path.join(folder, 'draw.py')):
        loops = len(re.findall(r'^\s*(?:for|while)\s', open(os.path.join(folder, 'draw.py'), encoding='utf-8').read(), re.M))
    reply = os.path.join(folder, 'agent_reply.txt') if folder else None
    hand = bool(reply and os.path.exists(reply) and os.path.getmtime(os.path.join(folder, 'sprite.png')) > os.path.getmtime(reply) + 1)
    d = DIAG[i]
    R[i] = dict(id=i, im=im, nice=ar.nice(es.names()[i]), tier=tiers[i], longer=max(im.size), target=es.nes_target(i)[0], colours=len(by), tones=m['tones'], interior=m['interior'] * 100,
                detail=100 * sum(len(es.blobs(v)) for v in by.values()) / max(1, sum(map(len, by.values()))), repeat=es.repeats(im), off=len(m['off']), partial=m['partial'],
                rule=job.get('rule_version', 1 if folder else 0), loops=loops, hand=hand, codex=job.get('agent') == 'codex', rating=d['rating'], why=d['why'], stale=d['hash'] != ed.pixel_hash(im))

ids = {k: [i for i in R if R[i]['rating'] == k] for k, _, _ in RATED}
n = {k: len(v) for k, v in ids.items()}
stale = [i for i in R if R[i]['stale']]
bench, drawn = ids['standard'], [i for i in R if i not in PICKS]
bosses = [i for i in R if tiers[i].startswith('BOSS')]
boss_ok = [i for i in bosses if R[i]['rating'] in ('standard', 'match')]
print(n, 'stale', stale, 'bosses that fit', boss_ok)

# ---------- the tier bars and table
top = max(sum(1 for i in R if tiers[i] == k) for k, _ in TIERS)
bars, size_rows, trend_rows = [], [], []
for k, name in TIERS:
    t = [i for i in R if tiers[i] == k]
    segs = ''.join('<span class="seg-%s" style="width:%.2f%%">%d</span>' % (key, 100 * c / top, c) for key, c in ((key, sum(1 for i in t if R[i]['rating'] == key)) for key, _, _ in RATED) if c)
    said = ', '.join('%d %s' % (sum(1 for i in t if R[i]['rating'] == key), label.lower()) for key, label, _ in RATED)
    bars.append('<div class="bar-row"><span class="bar-name">%s</span><span class="bar" role="img" aria-label="%s: %s">%s</span></div>' % (name, name, said, segs))
    lo, hi = es.NES_SIDE[k]
    out = sorted((i for i in t if not lo <= R[i]['longer'] <= hi), key=lambda i: R[i]['longer'])
    size_rows.append('<tr><th scope="row">%s</th><td class="num">%s</td><td class="num">%s</td><td>%s</td></tr>' % (
        name, '%d px' % lo if lo == hi else '%d to %d px' % (lo, hi), '%d to %d px' % (min(R[i]['longer'] for i in t), max(R[i]['longer'] for i in t)) if len(t) > 1 else '%d px' % R[t[0]]['longer'],
        ', '.join('%d (%d px)' % (i, R[i]['longer']) for i in out) or 'None'))
    trend_rows.append('<tr><th scope="row">%s</th><td class="num">%d</td><td class="num">%.0f px</td><td class="num">%.1f</td><td class="num">%.2f</td><td class="num">%.1f%%</td></tr>' % (
        name, len(t), med([R[i]['longer'] for i in t]), med([R[i]['detail'] for i in t]), med([R[i]['repeat'] for i in t]), med([R[i]['interior'] for i in t])))
    print(name, 'detail %.1f repeat %.2f interior %.1f tones3+ %d/%d' % (med([R[i]['detail'] for i in t]), med([R[i]['repeat'] for i in t]), med([R[i]['interior'] for i in t]), sum(1 for i in t if R[i]['tones'] > 2), len(t)))

# ---------- facts the copy states
big_bench = sorted((i for i in bench if R[i]['longer'] > 66), key=lambda i: R[i]['longer'])
over_bench = [i for i in R if R[i]['longer'] > max(R[j]['longer'] for j in bench)]
first_rule = [i for i in R if R[i]['rule'] == 1]
with_loops = [i for i in drawn if R[i]['loops']]
over_tones = [i for i in bench if R[i]['tones'] > 2]
over_colours = [i for i in bench if R[i]['colours'] > 5]
cast_over = [i for i in R if R[i]['tones'] > 2 or R[i]['colours'] > 5]
codex = [i for i in R if R[i]['codex']]
hand = [i for i in R if R[i]['hand']]
severe = [R[i]['detail'] for i in R if tiers[i] == 'SEVERE' and i not in (90, 93)]
assert not any(R[i]['off'] or R[i]['partial'] for i in R)
assert all(R[i]['colours'] <= es.NES_COLOURS for i in R)
fact = dict(
    VERDICT=('<strong>No, not all of them.</strong> %d sprites set the standard, %d sit well beside them, %d are close and %d don\'t match. Small enemies hold together. '
             'The match breaks down as sprites grow, and of the %d bosses only %s fit.' % (n['standard'], n['match'], n['close'], n['no'], len(bosses), join_and('%d %s' % (i, R[i]['nice']) for i in boss_ok) if boss_ok else 'none')),
    N_STD=n['standard'], N_MATCH=n['match'], N_CLOSE=n['close'], N_NO=n['no'],
    DRAWN_N=len(drawn), PICKS_N=len(PICKS),
    FIRST_RULE=len(first_rule), LOOPS=len(with_loops),
    BIG_BENCH=join_and('%d %s at %d px' % (i, R[i]['nice'], R[i]['longer']) for i in big_bench), BIG_BENCH_N=len(big_bench), BENCH_MAX=max(R[j]['longer'] for j in bench), OVER_BENCH=len(over_bench),
    D90='%.1f' % R[90]['detail'], D93='%.1f' % R[93]['detail'], SEV_MED='%.1f' % med(severe), I90='%.0f' % R[90]['interior'], I93='%.0f' % R[93]['interior'],
    TONES_OVER=len(over_tones), COLOURS_OVER=len(over_colours), BENCH_N=len(bench), CAST_OVER=len(cast_over),
    B23=R[23]['longer'], B30=R[30]['longer'], B34=R[34]['longer'], B44=R[44]['longer'],
    CODEX=join_and(codex), HAND=join_and(hand), HAND_N=len(hand), WHEN=time.strftime('%B %#d, %Y'),
    STALE=('<p class="warn"><strong>%s changed after it was rated</strong>, so its rating needs a new look.</p>' % join_and(stale)) if stale else '',
    BARS=''.join(bars), SIZE_ROWS=''.join(size_rows), TREND_ROWS=''.join(trend_rows),
    NO_IDS=','.join(map(str, sorted(ids['no'], key=lambda i: R[i]['longer']))), CLOSE_IDS=','.join(map(str, sorted(ids['close'], key=lambda i: R[i]['longer']))),
)

# ---------- the sheet's data
sprites = {}
for i, r in R.items():
    label = next(l for k, l, _ in RATED if k == r['rating'])
    stats = [['Rating', label], ['Tier', es.TIER_NAMES[r['tier']]], ['Size', '%dx%d px' % r['im'].size]]
    if i not in PICKS:
        stats.append(['Target longer side', '%d px' % r['target']])
    stats += [['Colours plus black', str(r['colours'])], ['Most shades of a hue', str(r['tones'])], ['Black inside outline', '%.0f%%' % r['interior']], ['Colour patches per 100 px', '%.1f' % r['detail']],
              ['Repeat score', '%.2f' % r['repeat']], ['Drawn under', RULES[r['rule']]]]
    notes = [r['why']] if r['why'] else []
    if r['hand']:
        notes.append('You edited this one by hand.')
    if r['codex']:
        notes.append('Codex drew this one, not Claude.')
    if r['stale']:
        notes.append('This sprite changed after it was rated.')
    sprites[i] = dict(n=r['nice'], r=r['rating'], label=label, why=r['why'], w=r['im'].width, h=r['im'].height, src=b64(r['im']), stats=stats, notes=notes)
groups = dict(tier=[dict(name=name, ids=[i for i in R if tiers[i] == k]) for k, name in TIERS],
              rating=[dict(name=label, desc=desc, ids=ids[k]) for k, label, desc in RATED],
              id=[dict(name='', ids=list(range(101)))])

html = open(os.path.join(HERE, 'audit_template.html'), encoding='utf-8').read()
for k, v in fact.items():
    html = html.replace('{{%s}}' % k, str(v))
assert '{{' not in html, re.findall(r'\{\{[A-Z0-9_]+\}\}', html)
used = set(re.findall(r'--[a-z]+:(#[0-9a-f]{6})', html))
assert used <= {'#%02x%02x%02x' % c for c in fcremap.PALETTE}, used
font = base64.b64encode(open(os.path.join(ac.ROOT, 'art', 'fonts', 'Pixuf.ttf'), 'rb').read()).decode()
html = html.replace('/*PIXUF*/', font).replace('/*DATA*/', json.dumps(dict(sprites={str(k): v for k, v in sprites.items()}, groups=groups), separators=(',', ':')))
path = os.path.join(OUT, 'enemy_style_audit.html')
open(path, 'w', encoding='utf-8', newline='\n').write(html)
print(path, os.path.getsize(path) // 1024, 'KB')
aw.write_stamp(BUILT_FROM)
