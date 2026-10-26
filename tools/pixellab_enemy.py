"""Redraw an installed enemy through PixelLab, every frame, from one job.json.

    python tools/pixellab_enemy.py JOB.json source  SHEET            # frame 0 of the loaded sheet -> source_<SHEET>.png
    python tools/pixellab_enemy.py JOB.json edit    SHEET [try=N] [--generate]   # frame 0 restyled to the Bible (~10 gens)
    python tools/pixellab_enemy.py JOB.json clean   SHEET [OLD=NEW ...]  # draft -> palette; hand map wins over nearest
    python tools/pixellab_enemy.py JOB.json rotate  SHEET [--generate]   # approved frame 0 -> other drawn views (~1)
    python tools/pixellab_enemy.py JOB.json animate SHEET [--generate]   # one call per drawn view (~1 each)
    python tools/pixellab_enemy.py JOB.json frames  SHEET [--generate]   # big sheets: edit every distinct frame (~10 each)
    python tools/pixellab_enemy.py JOB.json pack    SHEET            # review sheet, board and GIF; nothing installed
    python tools/pixellab_enemy.py JOB.json install                  # every packed sheet into assets/enemies/redraws/

Paid stages are dry runs unless --generate, which the user authorizes; each call keeps its own
workspace and ledger under pixellab-out/<name>/, and a saved result is reused, never resubmitted
(tools/ayotochtli_battle.py's rules). Approval stops: after `clean` (frame 0) and after `pack`.

job.json: {"id", "name", "dir", "prompts": {SHEET: file}, "sheets": {SHEET: {
    "png": the sheet the game loads now, "frames", "rows", "ms",
    "views": drawn directions (D DR R UR U), others fall back,
    "make": "animate" | "frames" | "breathe",
    "action": animate text, "count": frames to request (even, 4-16),
    "map": {view or "*": [animation index per game frame]}  -- 0 is the approved pose,
    "pivot": breathing pivot row, "breathe": [pose per game frame] (make = breathe),
    "action" may be {name: text} for several animations, mapped as "name:i";
    "anchor": {"at": [x, y], "colors"} keeps a coded art point (an eye) fixed in every frame;
    "ground": true puts every frame's lowest pixel on the approved frame's ground line;
    "despeckle": N drops loose islands of N pixels or fewer from animated frames;
    "flash": {"png", "colors", "radius", "to"} derives an alternate sheet (the eye gone white),
    "from": another SHEET whose approved frame 0 is this one's palette and reference}}}
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

import enemy_sheet
from install_enemy_redraws import breathe

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'art/direction'))
import fcremap as fc

BOARD = 'art/direction/approved_enemy_study/approved_42_fronts_native_512.png'
VIEWS = {'D': 'south', 'DR': 'south-east', 'R': 'east', 'UR': 'north-east', 'U': 'north',
         'UL': 'north-west', 'L': 'west', 'DL': 'south-west'}   # left views: only where drawn, not mirrored (16)
MAX_SIDE = 256          # rotate / animate input limit
ESTIMATE = {'edit': 30, 'rotate': 3, 'animate': 1}


class Job:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.cfg = json.loads(self.path.read_text(encoding='utf-8'))
        self.dir = ROOT / self.cfg['dir']
        self.work = ROOT / 'pixellab-out' / self.cfg['name']

    def sheet(self, key):
        return self.cfg['sheets'][key]

    def cell(self, key):
        s = self.sheet(key)
        im = Image.open(ROOT / s['png'])
        return (im.width // s['frames'], im.height // 8) if s['rows'] else (im.width // (8 * s['frames']), im.height)

    def f(self, name):
        return self.dir / name

    def approved(self, key):
        return Image.open(self.f(f'{key}_frame0_clean.png')).convert('RGBA')

    def palette(self, key):
        key = self.sheet(key).get('from', key)
        return sorted({p[:3] for p in self.approved(key).getdata() if p[3]})


def pngs(result):
    return [Path(p) for p in result['files'] if p.lower().endswith('.png')]


def call(job, name, request, generate):
    """One PixelLab request: dry run, estimate check, then (only with --generate) the paid call."""
    result_path = job.f(f'{name}-result.json')
    if generate and result_path.exists():
        print(f'{name}: reuse saved result')
        return json.loads(result_path.read_text(encoding='utf-8-sig'))
    if request[0] == 'edit':
        prompt = request[request.index('--prompt') + 1]
        assert len(prompt) <= 2000, f'{name}: prompt is {len(prompt)} characters; the API takes 2000'
    workspace = job.work / name
    ledger = workspace / 'ledger.jsonl'
    if generate and ledger.exists() and ledger.read_text().strip():
        raise SystemExit(f'{name}: a ledger exists without a saved result; collect the job (pixellab-cli job show) before retrying')
    common = ['pixellab-cli', '--json', '--workspace', str(workspace), '--subject', name]
    env = dict(os.environ, PIXELLAB_ASSUME_YES='0')
    dry = subprocess.run(common + ['--dry-run'] + request, capture_output=True, text=True, env=env, cwd=ROOT)
    assert dry.returncode == 0, f'{name} dry run failed: {dry.stderr}'
    data = json.loads(dry.stdout)
    est = data['estimated_cost']['generations']
    assert data['dry_run'] and est <= ESTIMATE[request[0]], f'{name}: unexpected estimate {est}'
    print(f"{name}: dry run {data['route']}, estimated {est} generations")
    if not generate:
        return None
    paid = subprocess.run(common + ['--yes'] + request, capture_output=True, text=True, env=env, cwd=ROOT)
    job.f(f'{name}-stderr.txt').write_text(paid.stderr, encoding='utf-8')
    assert paid.returncode == 0, f'{name} failed; inspect {name}-stderr.txt and the ledger before retrying'
    result_path.write_text(paid.stdout, encoding='utf-8')
    result = json.loads(paid.stdout)
    print(f"{name}: done, reported {result['cost']['generations']} generations")
    return result


# -- palette ----------------------------------------------------------------------
def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def to_palette(im, palette, hand=None):
    """Opaque pixels to `palette` (nearest in Lab), with `hand` {draft rgb: rgb} first; alpha made binary."""
    lab = {c: fc._lab(c) for c in palette}
    near = {}
    out = Image.new('RGBA', im.size)
    for i, p in enumerate(im.convert('RGBA').getdata()):
        if p[3] < 128:
            continue
        c = p[:3]
        if hand and c in hand:
            new = hand[c]
        else:
            if c not in near:
                l = fc._lab(c)
                near[c] = min(palette, key=lambda q: sum((a - b) ** 2 for a, b in zip(l, lab[q])))
            new = near[c]
        out.putpixel((i % im.width, i // im.width), new + (255,))
    return out


def roomy(im, path):
    """Save `im` for rotate/animate as its subject plus a margin on every side, so the subject fills
    about 80% of the frame (the CLI refuses one with no room to move, or one lost in empty canvas).
    Returns the crop's top-left on the native canvas; fit() pastes results back there."""
    box = im.getbbox()
    m = max(4, round(0.12 * max(box[2] - box[0], box[3] - box[1])))
    m = min(m, (MAX_SIDE - max(box[2] - box[0], box[3] - box[1])) // 2)   # never past the 256 px limit
    origin = (box[0] - m, box[1] - m)
    im.crop((origin[0], origin[1], box[2] + m, box[3] + m)).save(path)
    return origin


def fit(im, size, origin, ground=None):
    """A generated frame back onto the native canvas at the crop's origin, never resampled; with
    `ground`, moved up or down so its lowest pixel sits on that line (a rotated view). A pose that
    leaves the canvas is an error, not clipped."""
    out = Image.new('RGBA', (size[0] + 2 * im.width, size[1] + 2 * im.height))
    out.paste(im, (origin[0] + im.width, origin[1] + im.height))
    box = out.getbbox()
    dy = 0 if ground is None else ground - (box[3] - im.height)
    inner = (im.width, im.height - dy, im.width + size[0], im.height - dy + size[1])
    assert box[0] >= inner[0] and box[2] <= inner[2] and box[1] >= inner[1] and box[3] <= inner[3],         f'pose leaves the {size} canvas'
    return out.crop(inner)


# -- stages -------------------------------------------------------------------------
def source(job, key):
    s = job.sheet(key)
    w, h = job.cell(key)
    im = Image.open(ROOT / s['png']).convert('RGBA').crop((0, 0, w, h))
    job.dir.mkdir(parents=True, exist_ok=True)
    im.save(job.f(f'source_{key}.png'))
    print(job.f(f'source_{key}.png'), im.size, im.getbbox())


def edit(job, key, generate, attempt=1):
    """attempt > 1: a retry with a revised prompt; earlier drafts and ledgers are kept."""
    w, h = job.cell(key)
    tag = '' if attempt == 1 else f'-try{attempt}'
    prompt = job.f(job.cfg['prompts'][key]).read_text(encoding='utf-8').strip()
    ref = job.sheet(key).get('from')
    match = str(job.f(f'{ref}_frame0_clean.png')) if ref else str(ROOT / job.cfg.get('match', BOARD))   # "match": a style image (the bosses: Boiuna)
    # The edit route fails on a subject sitting low or high in an empty canvas (Namungumi, 3 failed
    # jobs): send it centred vertically, and move the draft back by the same rows.
    src = Image.open(job.f(f'source_{key}.png')).convert('RGBA')
    box = src.getbbox()
    dy = (h - (box[3] - box[1])) // 2 - box[1]
    sent = Image.new('RGBA', src.size)
    sent.paste(src, (0, dy))
    sent.save(job.f(f'source_{key}_sent.png'))
    result = call(job, f'{key}-edit{tag}', ['edit', str(job.f(f'source_{key}_sent.png')), '--prompt', prompt, '--size', f'{w}x{h}',
                                            '--match', match, '--transparent', '--name', f'{job.cfg["name"]}-{key}-frame0{tag}'], generate)
    if result:
        draft = job.f(f'{key}_frame0_draft.png')
        if attempt > 1 and draft.exists():
            draft.replace(job.f(f'{key}_frame0_draft_try{attempt - 1}.png'))
        back = Image.new('RGBA', (w, h))
        back.paste(Image.open(pngs(result)[0]).convert('RGBA'), (0, -dy))
        back.save(draft)


def clean(job, key, pairs):
    draft = Image.open(job.f(f'{key}_frame0_draft.png')).convert('RGBA')
    hand = {rgb(a): rgb(b) for a, b in (p.split('=') for p in pairs)}
    out = to_palette(draft, fc.PALETTE, hand)
    out.save(job.f(f'{key}_frame0_clean.png'))
    colors = {p[:3] for p in out.getdata() if p[3]}
    print(job.f(f'{key}_frame0_clean.png'), out.size, out.getbbox(), len(colors), 'colours')
    review([out], job.f(f'{key}_frame0_review.png'))


def rotate(job, key, generate):
    s = job.sheet(key)
    others = [v for v in s['views'] if v != 'D']
    if not others:
        return print(f'{key}: front only, nothing to rotate')
    src = job.f(f'{key}_rotate_input.png')
    origin = roomy(job.approved(key), src)
    result = call(job, f'{key}-rotate', ['rotate', str(src),
                                        '--description', job.cfg['description'], '--transparent',
                                        '--name', f'{job.cfg["name"]}-{key}-views'], generate)
    if not result:
        return
    approved = job.approved(key)
    ground = approved.getbbox()[3]
    files = pngs(result)
    for v in others:
        f = next(p for p in files if p.stem.rsplit('-', 1)[0].split('-views-')[-1] == VIEWS[v])   # <name>-views-<view>-NN
        shifted = to_palette(fit(Image.open(f), approved.size, origin, ground), job.palette(key))
        shifted.save(job.f(f'{key}_view_{v}.png'))
    print(f'{key}: views', ', '.join(others))


def view_image(job, key, v):
    return job.approved(key) if v == 'D' else Image.open(job.f(f'{key}_view_{v}.png')).convert('RGBA')


def actions(s):
    """{name: action text}; a plain string is the one unnamed animation."""
    return s['action'] if isinstance(s['action'], dict) else {'': s['action']}


def animate_crops(job, key, generate, attempt=1):
    """Sheets too big to animate whole: each "crops" box {"box": [x0, y0, x1, y1], "action"} animated on
    its own from frame 0 (under the 256 px limit); poses() lays each returned frame back into its box."""
    s = job.sheet(key)
    tag = '' if attempt == 1 else f'-try{attempt}'
    for i, c in enumerate(s['crops']):
        x0, y0, x1, y1 = c['box']
        part = job.approved(key).crop((x0, y0, x1, y1))
        src = job.f(f'{key}_crop{i}_input.png')
        origin = roomy(part, src)
        result = call(job, f'{key}-animate-crop{i}{tag}', ['animate', str(src), '--action', c['action'], '--frames', str(s['count']),
                                                         '--transparent', '--name', f'{job.cfg["name"]}-{key}-crop{i}{tag}'], generate)
        if result:
            for n, p in enumerate(pngs(result)[-s['count']:], 1):
                to_palette(fit(Image.open(p), part.size, origin), job.palette(key)).save(job.f(f'{key}_crop{i}_{n}.png'))


def animate(job, key, generate, attempt=1, only=None):
    """attempt > 1: a re-run with revised action text (earlier results kept); only: those views."""
    s = job.sheet(key)
    if s.get('crops'):
        return animate_crops(job, key, generate, attempt)
    w, h = job.cell(key)
    assert max(w, h) <= MAX_SIDE, f'{key}: {w}x{h} is over the {MAX_SIDE}px animate limit; use make = frames'
    tag = '' if attempt == 1 else f'-try{attempt}'
    for v in (only or s['views']):
        src = job.f(f'{key}_input_{v}.png')
        origin = roomy(view_image(job, key, v), src)
        for name, action in actions(s).items():
            part = f'-{name}' if name else ''
            result = call(job, f'{key}-animate{part}-{v}{tag}', ['animate', str(src), '--action', action, '--frames', str(s['count']),
                                                            '--transparent', '--name', f'{job.cfg["name"]}-{key}{part}-{v}{tag}'], generate)
            if result:
                for i, p in enumerate(pngs(result)[-s['count']:], 1):
                    to_palette(fit(Image.open(p), (w, h), origin), job.palette(key)).save(job.f(f'{key}_anim{part.replace("-", "_")}_{v}_{i}.png'))


def frames(job, key, generate):
    """Sheets over the animate limit: every distinct original frame restyled with the approved frame 0 as reference."""
    s = job.sheet(key)
    w, h = job.cell(key)
    sheet = Image.open(ROOT / s['png']).convert('RGBA')
    cells = enemy_sheet.cells_of(sheet, s['frames'], s['rows'])['D']
    prompt = job.f(job.cfg['prompts'][key]).read_text(encoding='utf-8').strip()
    seen = {cells[0].tobytes(): 0}
    for i, im in enumerate(cells[1:], 1):
        if im.tobytes() in seen:
            continue
        seen[im.tobytes()] = i
        src = job.f(f'{key}_orig_{i}.png')
        im.save(src)
        result = call(job, f'{key}-frame-{i}', ['edit', str(src), '--prompt', prompt, '--size', f'{w}x{h}',
                                                '--match', str(job.f(f'{key}_frame0_clean.png')), '--transparent',
                                                '--name', f'{job.cfg["name"]}-{key}-f{i}'], generate)
        if result:
            to_palette(Image.open(pngs(result)[0]), job.palette(key)).save(job.f(f'{key}_anim_D_{i}.png'))


def poses(job, key):
    """{view: [frame per game frame]} from the job's map."""
    s = job.sheet(key)
    if s['make'] == 'breathe':
        b = breathe(job.approved(key), s['pivot'])
        return {'D': [b[k] for k in s['breathe']]}
    if s.get('crops'):
        out = []
        for k in s['map']['*']:
            f = job.approved(key).copy()
            if k:
                for i, c in enumerate(s['crops']):
                    x0, y0, x1, y1 = c['box']
                    keep = c.get('still_above', y0)            # rows above this stay frame 0's (a body the legs hang from)
                    moved = Image.open(job.f(f'{key}_crop{i}_{k}.png')).convert('RGBA').crop((0, keep - y0, x1 - x0, y1 - y0))
                    f.paste(Image.new('RGBA', (x1 - x0, y1 - keep)), (x0, keep))
                    f.alpha_composite(moved, (x0, keep))
            out.append(f)
        return {'D': out}
    if s['make'] == 'frames':
        sheet = Image.open(ROOT / s['png']).convert('RGBA')
        cells = enemy_sheet.cells_of(sheet, s['frames'], s['rows'])['D']
        first = {}
        for i, im in enumerate(cells):
            first.setdefault(im.tobytes(), i)
        pick = lambda i: job.approved(key) if first[cells[i].tobytes()] == 0 else \
            Image.open(job.f(f'{key}_anim_D_{first[cells[i].tobytes()]}.png')).convert('RGBA')
        return {'D': [pick(i) for i in range(s['frames'])]}
    def frame(v, k):
        name, k = (k.split(':')[0], int(k.split(':')[1])) if isinstance(k, str) else ('', k)
        if k == 0:
            return view_image(job, key, v)
        part = f'_{name}' if name else ''
        return Image.open(job.f(f'{key}_anim{part}_{v}_{k}.png')).convert('RGBA')
    out = {}
    for v in s['views']:
        order = s['map'].get(v, s['map']['*'])
        out[v] = [anchored(job, key, frame(v, k)) for k in order]
    return out


def despeckled(im, most):
    """Islands of `most` opaque pixels or fewer (4-connected), cut loose from the creature by the
    animation, removed."""
    px = im.load()
    w, h = im.size
    seen = set()
    out = im.copy()
    for y in range(h):
        for x in range(w):
            if (x, y) in seen or not px[x, y][3]:
                continue
            group, todo = [], [(x, y)]
            seen.add((x, y))
            while todo:
                cx, cy = todo.pop()
                group.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and px[nx, ny][3]:
                        seen.add((nx, ny))
                        todo.append((nx, ny))
            if len(group) <= most:
                for gx, gy in group:
                    out.putpixel((gx, gy), (0, 0, 0, 0))
    return out


def anchored(job, key, im):
    """With an "anchor" {"at": [x, y], "colors": [...]}: the frame shifted so those colours' centre
    sits on the art pixel the code aims from (Namungumi's eye). Without one, unchanged."""
    if job.sheet(key).get('despeckle'):
        im = despeckled(im, job.sheet(key)['despeckle'])
    if job.sheet(key).get('clear_below'):   # {"row", "colors"}: colours that never belong low (Liderc's flame flecks by its legs)
        c = job.sheet(key)['clear_below']
        bad = {rgb(h) for h in c['colors']}
        im = im.copy()
        for y in range(c['row'], im.height):
            for x in range(im.width):
                if im.getpixel((x, y))[3] and im.getpixel((x, y))[:3] in bad:
                    im.putpixel((x, y), (0, 0, 0, 0))
    if job.sheet(key).get('ground'):       # standing creature: feet back on the approved ground line
        dy = job.approved(key).getbbox()[3] - im.getbbox()[3]
        if dy:
            out = Image.new('RGBA', im.size)
            out.paste(im, (0, dy))
            im = out
    a = job.sheet(key).get('anchor')
    if not a or not a.get('shift', True):   # shift false: the anchor only finds the eye (for the flash)
        return im
    colors = {rgb(c) for c in a['colors']}
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] and im.getpixel((x, y))[:3] in colors]
    assert pts, f'{key}: anchor colours not found in a frame'
    cx = round(sum(p[0] for p in pts) / len(pts)); cy = round(sum(p[1] for p in pts) / len(pts))
    dx, dy = a['at'][0] - cx, a['at'][1] - cy
    if not dx and not dy:
        return im
    out = Image.new('RGBA', im.size)
    out.paste(im, (dx, dy))
    assert out.getbbox()[3] - out.getbbox()[1] == im.getbbox()[3] - im.getbbox()[1], f'{key}: anchoring pushed a frame off the canvas'
    return out


def eye_at(job, key, im):
    """The anchor colours' centre in one frame (where its eye is drawn)."""
    colors = {rgb(c) for c in job.sheet(key)['anchor']['colors']}
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] and im.getpixel((x, y))[:3] in colors]
    assert pts, f'{key}: anchor colours not found in a frame'
    return round(sum(p[0] for p in pts) / len(pts)), round(sum(p[1] for p in pts) / len(pts))


def flashed(job, key, sheet):
    """The flash sheet: pixels of the flash colours within `radius` of each frame's eye turned to `to`."""
    f = job.sheet(key)['flash']
    colors, to = {rgb(c) for c in f['colors']}, rgb(f['to'])
    s = job.sheet(key)
    out = sheet.copy()
    w, h = job.cell(key)
    for d, cells in enumerate(enemy_sheet.cells_of(sheet, s['frames'], s['rows']).values()):
        for i, im in enumerate(cells):
            ox, oy = (i * w, d * h) if s['rows'] else ((d * s['frames'] + i) * w, 0)
            ex, ey = eye_at(job, key, im)
            for y in range(ey - f['radius'], ey + f['radius'] + 1):
                for x in range(ex - f['radius'], ex + f['radius'] + 1):
                    p = out.getpixel((ox + x, oy + y))
                    if p[3] and p[:3] in colors:
                        out.putpixel((ox + x, oy + y), to + (255,))
    return out


def review(frames, path, scale=4):
    w, h = frames[0].size
    out = Image.new('RGBA', (len(frames) * (w * scale + 4), h * scale), (0, 0, 0, 255))
    for i, f in enumerate(frames):
        out.alpha_composite(f.resize((w * scale, h * scale), Image.NEAREST), (i * (w * scale + 4), 0))
    out.save(path)


def pack(job, key):
    s = job.sheet(key)
    views = poses(job, key)
    assert all(len(v) == s['frames'] for v in views.values())
    sheet = enemy_sheet.sheet_of(views, s['rows'])
    sheet.save(job.f(f'{key}_sheet.png'))
    if s.get('flash'):
        flashed(job, key, sheet).save(job.f(f'{key}_flash_sheet.png'))
    cells = enemy_sheet.cells_of(sheet, s['frames'], s['rows'])
    rows = [cells[d] for d in enemy_sheet.ORDER if d in s['views'] or d == 'D']
    w, h = rows[0][0].size
    board = Image.new('RGBA', (s['frames'] * (w * 3 + 4), len(rows) * (h * 3 + 4)), (0, 0, 0, 255))
    for r, row in enumerate(rows):
        for c, f in enumerate(row):
            board.alpha_composite(f.resize((w * 3, h * 3), Image.NEAREST), (c * (w * 3 + 4), r * (h * 3 + 4)))
    board.save(job.f(f'{key}_review.png'))
    gif = [Image.alpha_composite(Image.new('RGBA', (w, h), (0, 0, 0, 255)), f).resize((w * 3, h * 3), Image.NEAREST)
           for f in cells['D']]
    gif[0].save(job.f(f'{key}_D.gif'), save_all=True, append_images=gif[1:], duration=s['ms'], loop=0)
    colors = {p[:3] for p in sheet.getdata() if p[3]}
    off = [c for c in colors if c not in fc.PALETTE]
    print(job.f(f'{key}_review.png'), sheet.size, len(colors), 'colours', 'OFF PALETTE' if off else 'on palette')


def install(job):
    manifest_path = ROOT / 'assets/enemies/redraws/installation.json'
    manifest = json.loads(manifest_path.read_text())
    battle = ROOT / 'src/battle.cpp'
    src = battle.read_text(encoding='utf-8')
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    todo = []
    for key, s in job.cfg['sheets'].items():
        todo.append((key, s, job.f(f'{key}_sheet.png')))
        if s.get('flash'):
            todo.append((key, dict(s, png=s['flash']['png']), job.f(f'{key}_flash_sheet.png')))
    for key, s, packed in todo:
        sheet = Image.open(packed).convert('RGBA')
        old = ROOT / s['png']
        assert sheet.size == Image.open(old).size, f'{key}: sheet size changed'
        dest = ROOT / 'assets/enemies/redraws' / Path(s['png']).name
        palette = sorted({'%02x%02x%02x' % p[:3] for p in sheet.getdata() if p[3]})
        tags = enemy_sheet.install(sheet, dest, s['frames'], s['rows'], ms=s['ms'], palette=palette,
                                   backup=str(ROOT / 'art/_backup' / f'pixellab_{job.cfg["id"]:02}_{stamp}'))
        assert Image.open(dest).convert('RGBA').tobytes() == sheet.tobytes()
        rel_old, rel_new = s['png'], dest.relative_to(ROOT).as_posix()
        if rel_old != rel_new:
            assert f'"{rel_old}"' in src, f'{rel_old} not in battle.cpp'
            src = src.replace(f'"{rel_old}"', f'"{rel_new}"')
        manifest['enemies'] = [e for e in manifest['enemies'] if e.get('png') != rel_new] + [dict(
            id=job.cfg['id'], sheet=key, png=rel_new, aseprite=dest.with_suffix('.aseprite').relative_to(ROOT).as_posix(),
            source=(job.dir / f'{key}_frame0_clean.png').relative_to(ROOT).as_posix(), frame_size=list(job.cell(key)),
            frames=s['frames'], rows=s['rows'], tags=tags, make=s['make'], frame_ms=s['ms'],
            job=job.path.relative_to(ROOT).as_posix())]
        print(f'installed {rel_new}')
    battle.write_text(src, encoding='utf-8', newline='')
    manifest_path.write_text(json.dumps(manifest, indent=2))
    subprocess.run([sys.executable, str(ROOT / 'tools/enemy_redraw_sheet.py'), '--complete', str(job.cfg['id'])], cwd=ROOT, check=True)


def board(out, kind, jobs):
    """One approval board: each job's frame 0s (kind frame0) or packed D animation (kind anim), 3x on black, labelled."""
    from PIL import ImageDraw
    rows = []
    for path in jobs:
        job = Job(path)
        for key, s in job.cfg['sheets'].items():
            if kind == 'frame0':
                src, new = job.f(f'source_{key}.png'), job.f(f'{key}_frame0_clean.png')
                if not new.exists():
                    continue
                ims = [Image.open(src).convert('RGBA'), Image.open(new).convert('RGBA')]
            else:
                sheet = job.f(f'{key}_sheet.png')
                if not sheet.exists():
                    continue
                cells = enemy_sheet.cells_of(Image.open(sheet).convert('RGBA'), s['frames'], s['rows'])
                ims = [f for v in s['views'] for f in cells[v]] if len(s['views']) * s['frames'] <= 16 else cells['D']
            rows.append((f"{job.cfg['id']:02} {job.cfg['name']} {key}", ims))
    sc = 3
    w = max(sum(i.width * sc + 6 for i in ims) for _, ims in rows) + 8
    h = sum(max(i.height for i in ims) * sc + 22 for _, ims in rows)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    y = 0
    for label, ims in rows:
        d.text((6, y + 4), label, fill=(220, 220, 220, 255))
        x = 6
        for i in ims:
            img.alpha_composite(i.resize((i.width * sc, i.height * sc), Image.NEAREST), (x, y + 18))
            x += i.width * sc + 6
        y += max(i.height for i in ims) * sc + 22
    img.save(out)
    print(out, img.size)


def main(argv):
    if argv[0] == 'board':                  # board OUT.png frame0|anim JOB.json ...
        return board(argv[1], argv[2], argv[3:])
    job = Job(argv[0])
    stage, rest = argv[1], argv[2:]
    generate = '--generate' in rest
    attempt = next((int(a[4:]) for a in rest if a.startswith('try=')), 1)
    rest = [a for a in rest if a != '--generate' and not a.startswith('try=')]
    key = rest[0] if rest else None
    if stage == 'install':
        return install(job)
    key = rest[0]
    {'source': lambda: source(job, key), 'edit': lambda: edit(job, key, generate, attempt), 'clean': lambda: clean(job, key, rest[1:]),
     'rotate': lambda: rotate(job, key, generate), 'animate': lambda: animate(job, key, generate, attempt, [a[5:] for a in rest if a.startswith('view=')] or None),
     'frames': lambda: frames(job, key, generate), 'pack': lambda: pack(job, key)}[stage]()


if __name__ == '__main__':
    main(sys.argv[1:])
