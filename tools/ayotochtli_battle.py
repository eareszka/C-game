"""Generate and pack the approved Ayotochtli's complete battle animation drafts.

Stages: poses, cycles, rolls, pack. Paid stages default to dry runs; add --generate
only for user-authorized requests. Each job has a separate workspace and ledger.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageOps

import enemy_sheet

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/enemies/pixellab/66_ayotochtli'
BATTLE = ART / 'battle'
WORK = ROOT / 'pixellab-out/66-ayotochtli-battle'
sys.path.insert(0, str(ROOT / 'art/direction'))
import fcremap as fc

SIZE = (48, 35)
MAX_WORKERS = 3
VIEWS = {'D': 'south', 'DR': 'south-east', 'R': 'east', 'UR': 'north-east', 'U': 'north'}
APPROVED = Image.open(ART / 'frame0_review.png').convert('RGBA')
PALETTE = sorted({p[:3] for p in APPROVED.get_flattened_data() if p[3]})
LAB = {c: fc._lab(c) for c in PALETTE}
BALL_PROMPT = ('Curl this tan armored turtle-rabbit into a compact round shell ball. '
               'Tuck head, feet and tail inside; fold ears flat against the shell. '
               'Broad dark seams on a tan armored sphere, no visible legs or face. '
               'Keep the exact palette, one-pixel black outlines and flat shading. '
               'Transparent 48x36 canvas; ball about 19x19 pixels, centered at x24, grounded at y34. No effects or extra objects.')
REST_DESCRIPTION = ('Ayotochtli, the approved small tan armored turtle-rabbit: broad segmented shell, '
                    'long rabbit ears with pink interiors, pointed snout, short clawed feet and armored tail. '
                    'Same nine-color palette and flat black outlines. Preserve anatomy, creature size and ground line.')
IDLE_ACTION = ('In-place resting and defensive hunch cycle, facing the same direction throughout. '
               'Start in the supplied resting pose. At the midpoint draw the head and neck down into the shell, '
               'lower the long ears, tuck the limbs and tail close, and bunch the broad shell bands slightly. '
               'Then ease out to a relaxed resting pose. Tiny restrained breathing, no running, rolling or camera movement. '
               'Preserve exact anatomy, size, black one-pixel outlines, flat fills and colors. '
               'No effects, extra parts, dithering or textured scales. Keep the same ground line and framing.')
ROLL_ACTION = ('Seamless continuous forward tumbling of this compact curled armored shell ball, '
               'in place and facing the same travel direction. Quarter-turn steps: broad shell seams rotate around '
               'the round ball surface to show genuine end-over-end rolling, returning to the starting orientation. '
               'Head, long ears, legs and tail stay tucked tightly into the ball throughout; do not stand up or run. '
               'Keep a stable round silhouette and tiny ground contact bob, exact native scale, black one-pixel '
               'outlines and simple flat tan shell palette. Transparent background, no motion trails, smoke, '
               'camera motion, drifting or extra objects.')


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def pngs(result):
    return [Path(p) for p in result['files'] if p.lower().endswith('.png')]


def call(name, request, estimate, generate):
    result_path = BATTLE / f'{name}-result.json'
    if generate and result_path.exists():
        print(f'{name}: reuse saved result', flush=True)
        return load_json(result_path)
    request = list(request)
    if request[0] == 'animate':
        image = Image.open(request[1]).convert('RGBA')
        bounds = image.getbbox()
        if image.size == SIZE and bounds and bounds[3] - bounds[1] >= SIZE[1] * 0.95:
            padded = Image.new('RGBA', (48, 43))
            padded.paste(image, (0, 4))
            source = Path(request[1])
            destination = source.with_name(source.stem + '-motion-padded.png')
            padded.save(destination)
            request[1] = str(destination)
    workspace = WORK / name
    ledger = workspace / 'ledger.jsonl'
    if generate and ledger.exists():
        events = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
        resolved = {e['run'] for e in events if e['kind'] == 'outcome' and e.get('status') == 'ok'}
        assert not any(e['kind'] == 'intent' and e['run'] not in resolved for e in events), (
            f'{name}: existing unresolved request; inspect ledger and collect job before retrying')
        assert not events, f'{name}: ledger already exists; collect existing output rather than submit again'
    common = ['pixellab-cli', '--json', '--workspace', str(workspace), '--subject', name]
    if request[0] == 'edit' and '--match' not in request:
        assert len(request[request.index('--prompt') + 1]) <= 500, 'Simple edit prompt exceeds API limit'
        size = Image.open(request[1]).size
        assert all(side % 4 == 0 for side in size), 'Simple edit needs source dimensions divisible by four'
    env = dict(os.environ, PIXELLAB_ASSUME_YES='0')
    dry = subprocess.run(common + ['--dry-run'] + request, capture_output=True, text=True, env=env, cwd=ROOT)
    (BATTLE / f'{name}-dry-run.stderr.txt').write_text(dry.stderr, encoding='utf-8')
    assert dry.returncode == 0, f'{name} dry run failed: {dry.stderr}'
    data = json.loads(dry.stdout)
    assert data['dry_run'] and data['estimated_cost']['generations'] <= estimate, f'{name}: unexpected estimate'
    (BATTLE / f'{name}-dry-run.json').write_text(dry.stdout, encoding='utf-8')
    print(f"{name}: dry run {data['route']}, estimated {data['estimated_cost']['generations']} generations", flush=True)
    if not generate:
        return data
    paid = subprocess.run(common + ['--yes'] + request, capture_output=True, text=True, env=env, cwd=ROOT)
    (BATTLE / f'{name}-stderr.txt').write_text(paid.stderr, encoding='utf-8')
    assert paid.returncode == 0, f'{name} failed; inspect saved stderr and ledger before retrying: {paid.stderr}'
    result_path.write_text(paid.stdout, encoding='utf-8')
    result = json.loads(paid.stdout)
    print(f"{name}: complete, reported {result['cost']['generations']} generations", flush=True)
    return result


def batch(jobs, generate):
    failures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(call, name, args, cost, generate): name for name, args, cost in jobs}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as error:
                failures.append(f'{futures[future]}: {error}')
    if failures:
        raise RuntimeError('\n'.join(failures))


def clean(path, align=False):
    im = Image.open(path).convert('RGBA')
    if im.size == (48, 43):
        bounds = im.getbbox()
        assert bounds and bounds[3] - bounds[1] <= 35, f'{path}: motion exceeds native height; review before cropping'
        native = Image.new('RGBA', SIZE)
        native.paste(im, (0, 35 - bounds[3]))
        im = native
    if im.size == (48, 36):
        # The simple edit route needs dimensions divisible by four. Restore
        # the native canvas without resampling or dropping opaque pixels.
        bounds = im.getbbox()
        if bounds and bounds[3] > 35:
            dy = 35 - bounds[3]
            assert bounds[1] + dy >= 0
            shifted = Image.new('RGBA', im.size)
            shifted.paste(im, (0, dy))
            im = shifted
        im = im.crop((0, 0, 48, 35))
    assert im.size == SIZE, f'{path}: unexpected size {im.size}'
    data = list(im.get_flattened_data())
    assert all(p[3] in (0, 255) for p in data), f'{path}: partial transparency requires review'
    mapping = {}
    for p in data:
        if p[3] and p[:3] not in mapping:
            lab = fc._lab(p[:3])
            mapping[p[:3]] = min(PALETTE, key=lambda c: sum((a-b)**2 for a, b in zip(lab, LAB[c])))
    im.putdata([(*mapping[p[:3]], 255) if p[3] else (0, 0, 0, 0) for p in data])
    bounds = im.getbbox()
    assert bounds, f'{path}: empty image'
    if align:
        target = APPROVED.getbbox()
        dx, dy = round((target[0] + target[2] - bounds[0] - bounds[2]) / 2), target[3] - bounds[3]
        assert 0 <= bounds[0] + dx and bounds[2] + dx <= SIZE[0]
        assert 0 <= bounds[1] + dy and bounds[3] + dy <= SIZE[1]
        shifted = Image.new('RGBA', SIZE)
        shifted.paste(im, (dx, dy))
        im = shifted
    return im


def direction_inputs(name, kind):
    files = pngs(load_json(BATTLE / f'{name}-result.json'))
    for tag, direction in VIEWS.items():
        if kind == 'idle' and tag == 'D':
            image = APPROVED.copy()
        elif kind == 'roll' and tag == 'D':
            image = Image.open(BATTLE / 'inputs/roll-pose.png').convert('RGBA')
        else:
            expected = f'ayotochtli-{"rest" if kind == "idle" else "roll"}-views-{direction}'
            selected = [p for p in files if p.stem.rsplit('-', 1)[0] == expected]
            assert len(selected) == 1, f'{tag}: ambiguous rotation files {selected}'
            image = clean(selected[0], align=True)
        destination = BATTLE / 'inputs' / f'{kind}-{tag}.png'
        if destination.exists():
            assert Image.open(destination).convert('RGBA').tobytes() == image.tobytes(), 'Existing direction input changed'
        else:
            image.save(destination)


def poses(generate):
    padded = Image.new('RGBA', (48, 36))
    padded.paste(APPROVED, (0, 0))
    padded.save(BATTLE / 'inputs/edit-padded.png')
    batch([
        ('rest-views', ['rotate', str(ART / 'frame0_review.png'), '--description', REST_DESCRIPTION,
                        '--transparent', '--name', 'ayotochtli-rest-views'], 3),
        ('roll-pose-v3', ['edit', str(BATTLE / 'inputs/edit-padded.png'), '--prompt', BALL_PROMPT,
                       '--size', '48x36', '--transparent', '--name', 'ayotochtli-roll-pose'], 1),
    ], generate)
    if generate:
        direction_inputs('rest-views', 'idle')
        clean(pngs(load_json(BATTLE / 'roll-pose-v3-result.json'))[0], align=True).save(BATTLE / 'inputs/roll-pose.png')


def cycles(generate):
    jobs = [('roll-views', ['rotate', str(BATTLE / 'inputs/roll-pose.png'), '--description',
                          'The same Ayotochtli curled into a compact spherical armored tan shell ball, '
                          'head ears legs and tail tucked inside, broad shell seams, flat black outlines. '
                          'Do not uncurl the ball or invent a face or limbs.',
                          '--transparent', '--name', 'ayotochtli-roll-views'], 3)]
    jobs += [(f'idle-{tag}', ['animate', str(BATTLE / f'inputs/idle-{tag}.png'), '--action', IDLE_ACTION,
                             '--frames', '4', '--transparent', '--name', f'ayotochtli-idle-{tag}'], 1)
             for tag in VIEWS]
    batch(jobs, generate)
    if generate:
        direction_inputs('roll-views', 'roll')


def idles(generate):
    # The standing directions can animate while the independent curled pose
    # is being generated. Each view uses its own output folder and ledger.
    direction_inputs('rest-views', 'idle')
    batch([(f'idle-{tag}', ['animate', str(BATTLE / f'inputs/idle-{tag}.png'), '--action', IDLE_ACTION,
                           '--frames', '4', '--transparent', '--name', f'ayotochtli-idle-{tag}'], 1)
           for tag in VIEWS], generate)


def rollviews(generate):
    batch([('roll-views', ['rotate', str(BATTLE / 'inputs/roll-pose.png'), '--description',
                          'The same Ayotochtli curled into a compact spherical armored tan shell ball, '
                          'head ears legs and tail tucked inside, broad shell seams, flat black outlines. '
                          'Do not uncurl the ball or invent a face or limbs.',
                          '--transparent', '--name', 'ayotochtli-roll-views'], 3)], generate)
    if generate:
        direction_inputs('roll-views', 'roll')


def rolls(generate):
    batch([(f'roll-{tag}', ['animate', str(BATTLE / f'inputs/roll-{tag}.png'), '--action', ROLL_ACTION,
                           '--frames', '4', '--transparent', '--name', f'ayotochtli-roll-{tag}'], 1)
           for tag in VIEWS], generate)


def recover(_generate=False):
    def collect(name):
        destination = BATTLE / f'{name}-result.json'
        if destination.exists():
            print(f'{name}: already collected', flush=True)
            return
        error = (BATTLE / f'{name}-stderr.txt').read_text(encoding='utf-8')
        match = re.search(r'/background-jobs/([0-9a-f-]{36})', error)
        assert match, f'{name}: no submitted job ID; do not guess or resubmit'
        job = match.group(1)
        request = ['pixellab-cli', '--json', '--workspace', str(WORK / name), '--subject', name,
                   'job', 'show', job, '--kind', 'animations', '--name', f'ayotochtli-{name}']
        result = subprocess.run(request, capture_output=True, text=True, cwd=ROOT)
        (BATTLE / f'{name}-collection-stderr.txt').write_text(result.stderr, encoding='utf-8')
        assert result.returncode == 0, result.stderr
        (BATTLE / f'{name}-collection.json').write_text(result.stdout, encoding='utf-8')
        data = json.loads(result.stdout)
        assert len(data['files']) in (4, 5), f'{name}: unexpected collected image count'
        manifests = list(Path(data['files'][0]).parent.glob('*.manifest.json'))
        assert len(manifests) == 1
        manifest = load_json(manifests[0])
        data.update(cost=manifest['cost'], ids={'background_job_id': job},
                    manifest=str(manifests[0]), recovered=True)
        destination.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        print(f'{name}: recovered {len(data["files"])} frames from existing job, no new generation', flush=True)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(collect, name) for name in ('idle-UR', 'roll-R', 'roll-UR')]
        for future in as_completed(futures):
            future.result()


def last_roll(generate):
    # The prior roll-U call failed DNS resolution before submission. Balance
    # 1957 confirms the other twelve jobs were charged, with this one absent.
    destination = BATTLE / 'roll-U-result.json'
    if destination.exists():
        print('roll-U: already collected', flush=True)
        return
    result = call('roll-U-network-retry', ['animate', str(BATTLE / 'inputs/roll-U.png'), '--action', ROLL_ACTION,
                  '--frames', '4', '--transparent', '--name', 'ayotochtli-roll-U'], 1, generate)
    if generate:
        destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


def pack_kind(kind):
    views, records = {}, {}
    for tag in VIEWS:
        paths = pngs(load_json(BATTLE / f'{kind}-{tag}-result.json'))
        assert len(paths) in (4, 5), f'{kind}-{tag}: expected four frames or source plus four'
        generated = [clean(path) for path in paths]
        indices = [0, len(paths)//2, len(paths)-1] if kind == 'idle' else [0, 1, 2, 3]
        generated[0] = Image.open(BATTLE / f'inputs/{kind}-{tag}.png').convert('RGBA')
        views[tag] = [generated[i] for i in indices]
        assert len({im.tobytes() for im in views[tag]}) >= (2 if kind == 'idle' else 3), f'{kind}-{tag}: insufficient motion'
        records[tag] = {'sampled_indices': indices, 'bounds': [im.getbbox() for im in views[tag]]}
    for tag, source in {'UL': 'UR', 'L': 'R', 'DL': 'DR'}.items():
        views[tag] = [ImageOps.mirror(im) for im in views[source]]
    sheet = enemy_sheet.sheet_of(views, False)
    png = BATTLE / f'66_ayotochtli_{kind}.png'
    ase = png.with_suffix('.aseprite')
    count = 3 if kind == 'idle' else 4
    sheet.save(png)
    enemy_sheet.pack(sheet, str(ase), count, False)
    subprocess.run([enemy_sheet.ASEPRITE, '-b', '--script-param', f'source={ase.as_posix()}',
                    '--script-param', 'ms=' + ('400' if kind == 'idle' else '70'), '--script-param',
                    'durations=' + ('400,250,250' if kind == 'idle' else '70'), '--script-param',
                    'pal=' + ','.join('%02x%02x%02x' % c for c in PALETTE),
                    '--script', str(ROOT / 'tools/sheet_meta.lua')], check=True)
    assert enemy_sheet.sheet_of(enemy_sheet.read(str(ase)), False).tobytes() == sheet.tobytes()
    assert sheet.size == (48 * 8 * count, 35)
    if kind == 'idle':
        assert views['D'][0].tobytes() == APPROVED.tobytes()
    board = Image.new('RGB', (40 + 48 * count, 35 * 8), (151, 151, 170))
    draw = ImageDraw.Draw(board)
    for row, tag in enumerate(enemy_sheet.ORDER):
        draw.text((3, 35*row + 12), tag, fill=(0, 0, 0))
        for col, image in enumerate(views[tag]):
            board.paste(image, (40 + 48*col, 35*row), image)
        order, duration = ([0, 1, 0, 2], [400, 250, 400, 250]) if kind == 'idle' else ([0, 1, 2, 3], 70)
        playback = [views[tag][i] for i in order]
        playback[0].save(BATTLE / f'{kind}-{tag}.gif', save_all=True, append_images=playback[1:],
                         duration=duration, loop=0, disposal=2)
    board.save(BATTLE / f'{kind}-all-directions.png')
    return {'png': str(png.relative_to(ROOT)), 'aseprite': str(ase.relative_to(ROOT)),
            'frames_per_direction': count, 'directions': enemy_sheet.ORDER, 'size': list(sheet.size),
            'round_trip_exact': True, 'source_selection': records,
            'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (png, ase)}}


def pack():
    reports = {kind: pack_kind(kind) for kind in ('idle', 'roll')}
    jobs = ['rest-views', 'roll-pose-v3', 'roll-views'] + [f'{kind}-{tag}' for kind in ('idle', 'roll') for tag in VIEWS]
    results = [load_json(BATTLE / f'{name}-result.json') for name in jobs]
    inputs = load_json(ART / 'inputs.json')
    assert all(hashlib.sha256((ROOT / n).read_bytes()).hexdigest() == h for n, h in inputs['sha256'].items())
    report = {'approved': False, 'installed': False, 'frame_size': SIZE,
              'palette': ['%02x%02x%02x' % c for c in PALETTE], 'sheets': reports,
              'original_assets_unchanged': True, 'reported_generations': sum(r['cost']['generations'] for r in results),
              'standing_loop': [0, 1, 0, 2], 'standing_ms': [400, 250, 400, 250], 'rolling_frame_ms': 70}
    (BATTLE / 'review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['poses', 'idles', 'rollviews', 'cycles', 'rolls', 'recover', 'last-roll', 'pack'])
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--workers', type=int, choices=[1, 2, 3], default=3)
    args = parser.parse_args()
    MAX_WORKERS = args.workers
    BATTLE.mkdir(parents=True, exist_ok=True)
    (BATTLE / 'inputs').mkdir(exist_ok=True)
    if args.stage == 'pack':
        pack()
    else:
        globals()[args.stage.replace('-', '_')](args.generate)
