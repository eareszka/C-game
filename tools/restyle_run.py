"""The B + C restyle queue (docs/enemy-restyle-prompt.md) on top of tools/pixellab_enemy.py.

    python tools/restyle_run.py frame0 ID [try=N]   # job.json, guide base, paid edit, fold, snug frame, check
    python tools/restyle_run.py describe ID [--generate] # 3 candidates drawn at full size from "describe"; board and checks
    python tools/restyle_run.py pick   ID N         # candidate N becomes frame 0: bases, compare, review .aseprite
    python tools/restyle_run.py fold   ID [most=N]  # refold the latest draft, nothing paid
    python tools/restyle_run.py motion ID           # rotate, then animate every sheet (paid, about 1 a call)
    python tools/restyle_run.py board  ID           # every returned pose of every sheet, to choose from
    python tools/restyle_run.py pack   ID           # pack every sheet, loop GIF, review .aseprite

An enemy that must grow is described, not enlarged (the user, 2026-11-04): an enlarged sprite comes back blocky, keeping the
small sprite's pixels, while a description is drawn at its full size. Enemies that keep their size still use frame0.

Each enemy's words live in restyle_queue.json. A grown enemy's frame is set from its draft: the sheets it
loads become blank bases of that size (install compares sizes), "replaces" names the old sheet. Enemies that keep
their frame also keep their coded points' coordinates, ground line first.
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'art/direction'))
import enemy_sheet
import enemy_style as es
import fcremap as fc
import pixellab_enemy as pe

QUEUE = json.loads((ROOT / 'tools/restyle_queue.json').read_text(encoding='utf-8'))
TOOL = str(ROOT / 'tools/pixellab_enemy.py')
STYLE = """Redraw this as the same creature in the style of the reference: one coherent flat 2D pixel sprite on a transparent ground. Hard flat colour fills, at most three tones per material, with shade shapes that follow the body and light from the upper left. One pixel of black for the outline and the lines between parts. Real animals keep natural proportions and weight; monsters keep a clear, strong shape with an easy-to-find face. No chibi. No gradients, soft shading, dithering, hatching, speckle, fur or scale texture, and no antialiasing. No water or ground. Eyes are one solid mark of one or two pixels, never a ring, iris or glint. Every part needs a colour, because the game's background is pure black. Do not copy creatures from the reference."""
GUIDE = 'The supplied image is a coarse guide enlarged: redraw it at this full resolution, with crisp lines one pixel wide and fine one-pixel detail, never in blocky doubled pixels. Keep the whole creature inside the frame, feet included.'
src36 = (ROOT / 'art/enemies/pixellab/36_cu_sith/views.py').read_text(encoding='utf-8')
exec(ast.get_source_segment(src36, next(n for n in ast.parse(src36).body if isinstance(n, ast.FunctionDef) and n.name == 'flat')))


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class E:
    def __init__(self, id):
        self.id = id
        self.q = QUEUE[str(id)]
        self.s = es.sheets()[id]
        self.tier = es.tiers()[id]
        self.stem = Path(self.q.get('orig', self.s['path'])).stem
        self.dir = ROOT / 'art/enemies/pixellab' / self.q.get('folder', self.stem) / 'redo_bc'
        self.job = self.dir / 'job.json'
        self.rel = self.dir.relative_to(ROOT).as_posix()

    def paths(self):
        q = self.q.get('orig_sheets', {})
        out = {'idle': q.get('idle', self.s['path'])}
        if self.s['flap']:
            out['flap'] = q.get('flap', self.s['flap'])
        if self.s['alt']:
            out['alt'] = q.get('alt', self.s['alt'])
        return out

    def frames(self, key):
        return {'idle': self.s['frames'], 'flap': 4}.get(key, self.q.get('alt_frames', self.s['frames']))

    def cell(self):
        p = self.paths()['idle']
        im = Image.open(ROOT / p)
        return (im.width // self.s['frames'], im.height // 8) if self.s['rows'] else (im.width // (8 * self.s['frames']), im.height)


def write_job(e, cell=None):
    grown = e.q.get('grow', 1) != 1
    sheets = {}
    for key, p in e.paths().items():
        a = e.q.get(key, {})
        f = e.frames(key)
        s = {'frames': f, 'rows': e.s['rows'], 'ms': a.get('ms', 260), 'views': a.get('views', e.q['views']), 'make': e.q.get('make', 'animate'),
             'count': a.get('count', 4), 'action': a.get('action', ''), 'map': a.get('map', {'*': list(range(f)) if key == 'idle' else list(range(1, f + 1))}),
             'despeckle': 2}
        if e.q.get('ground', True):
            s['ground'] = True
        if grown:
            s['png'] = f'{e.rel}/base/{Path(p).name}'
            s['replaces'] = p
        else:
            s['png'] = p
        for k in ('anchor', 'pivot', 'breathe'):
            if k in a:
                s[k] = a[k]
        sheets[key] = s
    job = {'id': e.id, 'name': f'{e.id:02}-{e.stem.split("_", 1)[1].replace("_", "-")}-bc', 'dir': e.rel, 'description': e.q['desc'],
           'prompts': {k: 'prompt.txt' for k in sheets}, 'sheets': sheets}
    e.job.write_text(json.dumps(job, indent=2), encoding='utf-8')


def blank_bases(e, w, h):
    """Every sheet's base at cell w x h (only its size is read after frame 0)."""
    (e.dir / 'base').mkdir(parents=True, exist_ok=True)
    for key, p in e.paths().items():
        f = e.frames(key)
        size = (f * w, 8 * h) if e.s['rows'] else (8 * f * w, h)
        Image.new('RGBA', size).save(e.dir / 'base' / Path(p).name)


def guide_base(e):
    """The idle sheet enlarged nearest as PixelLab's guide, on a canvas with room on every side."""
    g = e.q['grow']
    cw, ch = e.cell()
    im = Image.open(ROOT / e.paths()['idle']).convert('RGBA').crop((0, 0, cw, ch))
    art = im.crop(im.getbbox())
    art = art.resize((round(art.width * g), round(art.height * g)), Image.NEAREST)
    w, h = max(32, art.width + 8), max(32, art.height + 8)
    blank_bases(e, w, h)
    idle = e.dir / 'base' / Path(e.paths()['idle']).name
    sheet = Image.open(idle).convert('RGBA')
    sheet.paste(art, ((w - art.width) // 2, h - art.height - 4))
    sheet.save(idle)


def latest_raw(e):
    def tag(p):
        m = re.search(r'-try(\d+)-result', p.name)
        return int(m.group(1)) if m else 1
    res = max(e.dir.glob('idle-edit*-result.json'), key=tag)
    r = json.loads(res.read_text(encoding='utf-8-sig'))
    return Image.open(next(f for f in r['files'] if f.lower().endswith('.png'))).convert('RGBA')


def nearest_palette(im):
    lab = {c: fc._lab(c) for c in fc.PALETTE}
    near = {}
    out = Image.new('RGBA', im.size)
    for i, p in enumerate(im.getdata()):
        if p[3] < 128:
            continue
        c = p[:3]
        if c not in near:
            l = fc._lab(c)
            near[c] = min(fc.PALETTE, key=lambda q: sum((a - b) ** 2 for a, b in zip(l, lab[q])))
        out.putpixel((i % im.width, i // im.width), near[c] + (255,))
    return out


def fold_colours(im, keep, black_l, limit=8, tones_ok=None):
    """Near-blacks to black; then the two closest colours merged (into the commoner) until the limits hold."""
    px = im.load()
    count = {}
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3]:
                c = px[x, y][:3]
                if fc._lab(c)[0] < black_l:
                    px[x, y] = (0, 0, 0, 255)
                    c = (0, 0, 0)
                count[c] = count.get(c, 0) + 1
    def merge_one():
        cols = [c for c in count if c != (0, 0, 0)]
        best = None
        for i, a in enumerate(cols):
            for b in cols[i + 1:]:
                if a in keep and b in keep:
                    continue
                d = sum((u - v) ** 2 for u, v in zip(fc._lab(a), fc._lab(b))) * (1 + min(count[a], count[b]) / 400)
                if best is None or d < best[0]:
                    best = (d, a, b)
        _, a, b = best
        lose, win = (a, b) if (a not in keep and (count[a] < count[b] or b in keep)) else (b, a)
        count[win] += count.pop(lose)
        for y in range(im.height):
            for x in range(im.width):
                if px[x, y][3] and px[x, y][:3] == lose:
                    px[x, y] = win + (255,)
    while len([c for c in count if c != (0, 0, 0)]) > limit:
        merge_one()
    for _ in range(8):
        if not any('shades' in text for _, text in es.check(im)[1]):
            break
        if len([c for c in count if c != (0, 0, 0) and c not in keep]) < 2:
            break
        merge_one()
    return im


def deblack(im, target=0.145, keep=()):
    """Blobs of black (not one-pixel seams) inside the body take the colour round them, and black with no colour
    beside it takes the darkest fill, until interior black is at the bible's limit. In place."""
    px, W, H = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    isb = lambda p: p[3] and p[:3] == (0, 0, 0)
    fills = {px[x, y][:3] for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] != (0, 0, 0)}
    if not fills:
        return im
    darkest = min(fills, key=lambda c: fc._lab(c)[0])
    thin = [(x, y) for y in range(H) for x in range(W) if isb(px[x, y])         # a doubled outline: its outer layer goes
            and any(not at(x + dx, y + dy)[3] for dx, dy in N4)
            and not any(at(x + dx, y + dy)[3] and not isb(at(x + dx, y + dy)) for dx, dy in N8)]
    for x, y in thin:
        px[x, y] = (0, 0, 0, 0)
    for need in (4, 3):
        for _ in range(6):
            if es.measure(im)['interior'] <= target:
                return im
            changes = []
            for y in range(H):
                for x in range(W):
                    if not isb(px[x, y]) or not all(at(x + dx, y + dy)[3] for dx, dy in N4):
                        continue
                    if sum(1 for dx, dy in N4 if isb(at(x + dx, y + dy))) >= need:
                        near = [at(x + dx, y + dy)[:3] for dx, dy in N8 if at(x + dx, y + dy)[3] and not isb(at(x + dx, y + dy))]
                        near = [c for c in near if c not in keep] or [darkest]
                        changes.append((x, y, max(set(near), key=near.count)))
            if not changes:
                break
            for x, y, c in changes:
                px[x, y] = c + (255,)
    return im


def fold(e, most=None):
    raw = latest_raw(e)
    im = nearest_palette(raw)
    (e.dir / 'idle_frame0_palette.png').write_bytes(b'')
    im.save(e.dir / 'idle_frame0_palette.png')
    keep = {hexrgb(h) for h in e.q.get('keep', [])}
    fold_colours(im, keep, e.q.get('black_l', 14))
    most = most if most is not None else e.q.get('most', 3 if max(im.size) < 70 else 6)
    flat(im, most, spare=tuple(keep))
    deblack(im, keep=keep)
    box = im.getbbox()
    art = im.crop(box)
    if e.q.get('grow', 1) != 1:
        side, top = e.q.get('side', 3), e.q.get('top', 3)
        bottom = 0 if e.q.get('ground', True) else top
        w, h = art.width + 2 * side, art.height + top + bottom
        blank_bases(e, w, h)
        out = Image.new('RGBA', (w, h))
        out.paste(art, (side, top))
    else:
        cw, ch = e.cell()
        src = Image.open(ROOT / e.paths()['idle']).convert('RGBA').crop((0, 0, cw, ch)).getbbox()
        assert art.width <= cw and art.height <= ch, f'{art.size} over the {cw}x{ch} frame: refold or retry'
        out = Image.new('RGBA', (cw, ch))
        x = max(0, min(cw - art.width, (src[0] + src[2] - art.width) // 2))
        y = max(0, src[3] - art.height)
        out.paste(art, (x, y))
    out.save(e.dir / 'idle_frame0_clean.png')
    print(e.id, 'frame', out.size, 'drawn', art.size, sorted('%02x%02x%02x' % c for c in {p[:3] for p in out.getdata() if p[3]}))
    for level, text in es.check(out, e.tier)[1]:
        print('   ', level, text)
    subprocess.run([r'C:\Program Files\Aseprite\Aseprite.exe', '-b', str(e.dir / 'idle_frame0_clean.png'), '--save-as', str(e.dir / 'idle_frame0_review.aseprite')], check=False)
    compare(e, out)


DESCRIBE_STYLE = ('Flat 2D game sprite. Hard flat colour fills, at most three tones per material, shade in clear steps lit from the upper left. '
                  'One pixel black outline and one pixel black lines between parts. Natural animal weight, not chibi. '
                  'No gradients, dithering, fur texture or antialiasing. A normal-sized head, not a big-headed cartoon. '
                  'Eyes are tiny solid dark dots with no white and no shine. Only the colours named. No ground.')
SEEDS = (1, 2, 3)   # an entry's "seeds" replaces these for a retry: earlier results stay saved


def fold_candidate(e, raw):
    """A described draft through the same fold as a restyled one, snug on the enemy's margins. Nothing else is written."""
    im = nearest_palette(raw)
    keep = {hexrgb(h) for h in e.q.get('keep', [])}
    fold_colours(im, keep, e.q.get('black_l', 14))
    flat(im, e.q.get('most', 3 if max(im.size) < 70 else 6), spare=tuple(keep))
    deblack(im, keep=keep)
    art = im.crop(im.getbbox())
    side, top = e.q.get('side', 3), e.q.get('top', 3)
    out = Image.new('RGBA', (art.width + 2 * side, art.height + top + (0 if e.q.get('ground', True) else top)))
    out.paste(art, (side, top))
    return out


def describe(e, generate):
    e.dir.mkdir(parents=True, exist_ok=True)
    write_job(e)
    (e.dir / 'prompt.txt').write_text(e.q['describe'] + '\n' + DESCRIBE_STYLE + '\n', encoding='utf-8')
    job = pe.Job(e.job)
    found = []
    for n in e.q.get('seeds', SEEDS):
        result = pe.call(job, f'idle-sprite-{n}', ['sprite', e.q['describe'] + ' ' + DESCRIBE_STYLE, '--size', e.q['size'], '--outline', 'single color black outline',
                                                   '--shading', 'basic shading', '--detail', 'medium detail', '--direction', e.q.get('direction', 'south'), '--transparent',
                                                   '--seed', str(n), '--name', f'{job.cfg["name"]}-idle-{n}'], generate)
        if result:
            raw = Image.open(pe.pngs(result)[0]).convert('RGBA')
            raw.save(e.dir / f'candidate_{n}_raw.png')
            out = fold_candidate(e, raw)
            out.save(e.dir / f'candidate_{n}.png')
            found.append((n, raw, out))
            print(e.id, 'candidate', n, 'raw', raw.size, 'drawn', out.getbbox(), [t for _, t in es.check(out.crop(out.getbbox()), e.tier)[1]])
    if found:
        candidates_board(e, found)


def candidates_board(e, found):
    cw, ch = e.cell()
    old = Image.open(ROOT / e.paths()['idle']).convert('RGBA').crop((0, 0, cw, ch))
    S = 4
    w = max(max(r.width, f.width) for _, r, f in found)
    h = max(max(r.height, f.height) for _, r, f in found + [(0, old, old)])
    o = Image.new('RGBA', (old.width * S + 3 * (w * S + 8), 2 * (h * S + 8)), (0, 0, 0, 255))
    o.paste((128, 128, 128, 255), (0, h * S + 8, o.width, o.height))
    for y in (0, h * S + 8):
        o.alpha_composite(old.resize((old.width * S, old.height * S), Image.NEAREST), (0, y + h * S - old.height * S))
        for i, (_, _, f) in enumerate(found):
            o.alpha_composite(f.resize((f.width * S, f.height * S), Image.NEAREST), (old.width * S + 8 + i * (w * S + 8), y + h * S - f.height * S))
    o.save(e.dir / 'candidates.png')
    print('board', e.dir / 'candidates.png', o.size)


def pick(e, n):
    out = Image.open(e.dir / f'candidate_{n}.png').convert('RGBA')
    out.save(e.dir / 'idle_frame0_clean.png')
    blank_bases(e, *out.size)
    subprocess.run([r'C:\Program Files\Aseprite\Aseprite.exe', '-b', str(e.dir / 'idle_frame0_clean.png'), '--save-as', str(e.dir / 'idle_frame0_review.aseprite')], check=False)
    compare(e, out)
    print(e.id, 'frame', out.size, 'checks', [t for _, t in es.check(out.crop(out.getbbox()), e.tier)[1]])


def rotate_source(e):
    """The views of a hand-finished pose (idle_source.png) that is not the front: all 8 of PixelLab's outputs saved, to be assigned by eye."""
    src = Image.open(e.dir / 'idle_source.png').convert('RGBA')
    src.save(e.dir / 'idle_frame0_clean.png')
    blank_bases(e, *src.size)
    write_job(e)
    job = pe.Job(e.job)
    origin = pe.roomy(job.approved('idle'), job.f('idle_rotate_input.png'))
    result = pe.call(job, 'idle-rotate', ['rotate', str(job.f('idle_rotate_input.png')), '--description', job.cfg['description'], '--as-is', '--transparent',
                                          '--name', f'{job.cfg["name"]}-idle-views'], True)
    ground = src.getbbox()[3]
    out = []
    for f in pe.pngs(result):
        name = f.stem.rsplit('-', 1)[0].split('-views-')[-1]
        im = pe.to_palette(pe.fit(Image.open(f), src.size, origin, ground), job.palette('idle'))
        im.save(e.dir / f'rotated_{name}.png')
        out.append((name, im))
    w, h = src.size
    S = 4
    o = Image.new('RGB', ((len(out) + 1) * (w * S + 6), h * S + 16), (70, 70, 70))
    from PIL import ImageDraw
    d = ImageDraw.Draw(o)
    for i, (name, im) in enumerate([('source', src)] + out):
        big = im.resize((w * S, h * S), Image.NEAREST)
        o.paste(big, (i * (w * S + 6), 16), big)
        d.text((i * (w * S + 6) + 2, 2), name, fill=(255, 255, 255))
    o.save(e.dir / 'rotated_board.png')
    print('board', e.dir / 'rotated_board.png', o.size)


def rotate_front(e):
    """The views of the approved front (idle_frame0_clean.png), saved as rotated_front_<label>.png, to be assigned by eye."""
    src = Image.open(e.dir / 'idle_frame0_clean.png').convert('RGBA')
    job = pe.Job(e.job)
    origin = pe.roomy(src, job.f('idle_rotate_front_input.png'))
    result = pe.call(job, 'idle-rotate-front', ['rotate', str(job.f('idle_rotate_front_input.png')), '--description', job.cfg['description'], '--as-is', '--transparent',
                                                '--name', f'{job.cfg["name"]}-front-views'], True)
    ground = src.getbbox()[3]
    out = []
    for f in pe.pngs(result):
        name = f.stem.rsplit('-', 1)[0].split('-views-')[-1]
        im = pe.to_palette(pe.fit(Image.open(f), src.size, origin, ground), job.palette('idle'))
        im.save(e.dir / f'rotated_front_{name}.png')
        out.append((name, im))
    from PIL import ImageDraw
    w, h = src.size
    S = 3
    o = Image.new('RGB', (4 * (w * S + 6), 2 * (h * S + 18)), (70, 70, 70))
    d = ImageDraw.Draw(o)
    for i, (name, im) in enumerate(out):
        x, y = (i % 4) * (w * S + 6), (i // 4) * (h * S + 18)
        big = im.resize((w * S, h * S), Image.NEAREST)
        o.paste(big, (x, y + 16), big)
        d.text((x + 2, y + 2), name, fill=(255, 255, 255))
    o.save(e.dir / 'rotated_front_board.png')
    print('board', e.dir / 'rotated_front_board.png', o.size)


def assign(e):
    """The views chosen by eye from rotate_source's outputs ("assigned" in the queue: {view: output name, or "source"}). Motion then keeps them."""
    S = 5
    frames = []
    for v, name in e.q['assigned'].items():
        im = Image.open(e.dir / ('idle_source.png' if name == 'source' else f'rotated_{name}.png')).convert('RGBA')
        im.save(e.dir / ('idle_frame0_clean.png' if v == 'D' else f'idle_view_{v}.png'))
        print(e.id, v, name, [t for _, t in es.check(im.crop(im.getbbox()), e.tier)[1]])
        frames.append(im)
    subprocess.run([r'C:\Program Files\Aseprite\Aseprite.exe', '-b', str(e.dir / 'idle_frame0_clean.png'), '--save-as', str(e.dir / 'idle_frame0_review.aseprite')], check=False)
    cw, ch = e.cell()
    w, h = frames[0].size
    o = Image.new('RGBA', (len(frames) * (w * S + 8), 2 * (h * S + 8)), (0, 0, 0, 255))
    o.paste((128, 128, 128, 255), (0, h * S + 8, o.width, o.height))
    for i, f in enumerate(frames):
        b = f.resize((w * S, h * S), Image.NEAREST)
        o.alpha_composite(b, (i * (w * S + 8), 0))
        o.alpha_composite(b, (i * (w * S + 8), h * S + 8))
    o.save(e.dir / 'views_review.png')
    print('board', e.dir / 'views_review.png', o.size)


def compare(e, new):
    cw, ch = e.cell()
    old = Image.open(ROOT / e.paths()['idle']).convert('RGBA').crop((0, 0, cw, ch))
    sc = 3 if max(new.size) < 110 else 2
    H = max(old.height, new.height) * sc
    o = Image.new('RGBA', (old.width * sc + 2 * new.width * sc + 12, H), (0, 0, 0, 255))
    o.alpha_composite(old.resize((old.width * sc, old.height * sc), Image.NEAREST), (0, H - old.height * sc))
    x = old.width * sc + 6
    o.alpha_composite(new.resize((new.width * sc, new.height * sc), Image.NEAREST), (x, H - new.height * sc))
    x += new.width * sc + 6
    o.paste((128, 128, 128, 255), (x, 0, o.width, H))
    o.alpha_composite(new.resize((new.width * sc, new.height * sc), Image.NEAREST), (x, H - new.height * sc))
    o.save(e.dir / 'frame0_compare.png')


def run(e, *args):
    p = subprocess.run([sys.executable, '-W', 'ignore', TOOL, str(e.job), *args], capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def frame0(e, attempt=1):
    e.dir.mkdir(parents=True, exist_ok=True)
    if e.q.get('grow', 1) != 1:
        guide_base(e)
    write_job(e)
    (e.dir / 'prompt.txt').write_text(' '.join(x for x in (e.q['prompt'], GUIDE if e.q.get('grow', 1) != 1 else '')) + '\n' + STYLE + '\n', encoding='utf-8')
    for a in (['source', 'idle'], ['edit', 'idle', f'try={attempt}'], ['edit', 'idle', f'try={attempt}', '--generate']):
        code, out = run(e, *a)
        print(out.strip()[-300:])
        assert code == 0, a
    fold(e)


PAD = re.compile(r'(frame0_clean|_view_|_anim)')


def pad_all(e, w, h):
    """Every working frame onto a bigger cell: centred, the ground row kept (rotated views or poses ran over)."""
    for p in e.dir.glob('*.png'):
        if PAD.search(p.name) and 'draft' not in p.name:
            im = Image.open(p).convert('RGBA')
            if im.size != (w, h):
                o = Image.new('RGBA', (w, h))
                o.paste(im, ((w - im.width) // 2, h - im.height))
                o.save(p)
    blank_bases(e, w, h)


def needed(e):
    w = h = 0
    for r in e.dir.glob('*-result.json'):
        if '-edit' in r.name:
            continue
        for f in json.loads(r.read_text(encoding='utf-8-sig'))['files']:
            if f.lower().endswith('.png'):
                b = Image.open(f).convert('RGBA').getbbox()
                if b:
                    w, h = max(w, b[2] - b[0]), max(h, b[3] - b[1])
    return w, h


def stage(e, *args):
    """A stage, growing a grown enemy's cell when a saved result won't fit, then rerun (saved results aren't repaid)."""
    for _ in range(3):
        code, out = run(e, *args)
        if code == 0:
            return out
        if 'leaves the' not in out or e.q.get('grow', 1) == 1:
            raise SystemExit(out[-900:])
        cw, ch = Image.open(e.dir / 'idle_frame0_clean.png').size
        w, h = needed(e)
        w, h = max(cw, w + 2), max(ch, h + 2)
        print(f'  cell {cw}x{ch} -> {w}x{h}')
        pad_all(e, w, h)
    raise SystemExit(out[-900:])


def motion(e):
    write_job(e)
    if len(e.q['views']) > 1 and 'assigned' not in e.q:     # (assigned views were chosen by eye: rotating again would relabel them)
        print(stage(e, 'rotate', 'idle', '--generate').strip()[-200:])
    for key in e.paths():
        if key != 'idle':
            a = e.q.get(key, {})
            for v in a.get('views', e.q['views']):
                base = a.get('from_view', v)     # a sheet drawn from another view (54's flap: its back, in the front's cells)
                src = e.dir / ('idle_frame0_clean.png' if base == 'D' else f'idle_view_{base}.png')
                dst = e.dir / (f'{key}_frame0_clean.png' if v == 'D' else f'{key}_view_{v}.png')
                dst.write_bytes(src.read_bytes())
        if e.q.get('make') != 'breathe':
            print(stage(e, 'animate', key, '--generate').strip()[-160:])
    keep = {hexrgb(h) for h in e.q.get('keep', [])}
    for p in e.dir.glob('*.png'):
        if re.search(r'(_view_|_anim)', p.name):
            im = Image.open(p).convert('RGBA')
            deblack(im, keep=keep)
            im.save(p)
    board(e)


def board(e):
    sc = 3 if e.cell()[0] < 110 else 2
    rows = []
    for key in e.paths():
        for v in e.q.get(key, {}).get('views', e.q['views']):
            base = e.dir / (f'{key}_frame0_clean.png' if v == 'D' else f'{key}_view_{v}.png')
            r = [Image.open(base).convert('RGBA')]
            i = 1
            while (e.dir / f'{key}_anim_{v}_{i}.png').exists():
                r.append(Image.open(e.dir / f'{key}_anim_{v}_{i}.png').convert('RGBA'))
                i += 1
            rows.append(r)
    w, h = rows[0][0].size
    n = max(len(r) for r in rows)
    o = Image.new('RGBA', (n * (w * sc + 3), len(rows) * (h * sc + 3)), (70, 70, 70, 255))
    for y, r in enumerate(rows):
        for x, f in enumerate(r):
            o.alpha_composite(f.resize((w * sc, h * sc), Image.NEAREST), (x * (w * sc + 3), y * (h * sc + 3)))
    o.save(e.dir / 'poses_board.png')
    print('board', e.dir / 'poses_board.png', o.size)


def pack(e):
    write_job(e)
    views = e.q['views']
    for key in e.paths():
        print(run(e, 'pack', key)[1].strip()[-150:])
    idle = Image.open(e.dir / 'idle_sheet.png').convert('RGBA')
    f = e.s['frames']
    cells = enemy_sheet.cells_of(idle, f, e.s['rows'])
    loop = e.q.get('idle', {}).get('loop', [0, 1, 0, 2] if f == 3 else list(range(f)))
    w, h = cells['D'][0].size
    sc = 3 if w < 70 else 2
    gif = []
    for k in loop:
        o = Image.new('RGB', (len(views) * w * sc, h * sc))
        for i, v in enumerate(views):
            im = cells[v][k].resize((w * sc, h * sc), Image.NEAREST)
            o.paste(im, (i * w * sc, 0), im)
        gif.append(o)
    gif[0].save(e.dir / 'idle_game_loop.gif', save_all=True, append_images=gif[1:], duration=260, loop=0)
    for key in e.paths():
        subprocess.run([r'C:\Program Files\Aseprite\Aseprite.exe', '-b', str(e.dir / f'{key}_sheet.png'), '--save-as', str(e.dir / f'{key}_sheet_review.aseprite')], check=False)
    for level, text in es.check(cells['D'][0], e.tier)[1]:
        print('   ', level, text)


def main():
    stage_name, id = sys.argv[1], int(sys.argv[2])
    e = E(id)
    args = dict(a.split('=') for a in sys.argv[3:] if '=' in a)
    if stage_name == 'describe':
        describe(e, '--generate' in sys.argv)
    elif stage_name == 'rotate_source':
        rotate_source(e)
    elif stage_name == 'rotate_front':
        rotate_front(e)
    elif stage_name == 'assign':
        assign(e)
    elif stage_name == 'pick':
        pick(e, int(sys.argv[3]))
    elif stage_name == 'frame0':
        frame0(e, int(args.get('try', 1)))
    elif stage_name == 'fold':
        fold(e, int(args['most']) if 'most' in args else None)
    elif stage_name == 'motion':
        motion(e)
    elif stage_name == 'board':
        board(e)
    elif stage_name == 'pack':
        pack(e)


if __name__ == '__main__':
    main()
