"""Prepare, animate and pack Lagopus review sheets from its approved first frame."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw

import enemy_sheet
import pixellab_enemy as pipeline

ROOT = Path(__file__).resolve().parents[1]
JOB = pipeline.Job(ROOT / 'art/enemies/pixellab/67_lagopus/job.json')
SIZE = (62, 45)


def fit(image, origin, ground=None):
    image = image.convert('RGBA')
    assert all(p[3] in (0, 255) for p in image.get_flattened_data()), 'Partial alpha needs review'
    box = image.getbbox()
    assert box and box[2] - box[0] <= SIZE[0] and box[3] - box[1] <= SIZE[1], 'Pose exceeds native canvas'
    x, y = origin
    x = max(-box[0], min(x, SIZE[0] - box[2]))
    y = (ground - box[3]) if ground is not None else max(-box[1], min(y, SIZE[1] - box[3]))
    assert box[1] + y >= 0 and box[3] + y <= SIZE[1]
    out = Image.new('RGBA', SIZE)
    out.paste(image, (x, y))
    return pipeline.to_palette(out, JOB.palette('idle'))


def prepare():
    approved = JOB.approved('idle')
    origin = pipeline.roomy(approved, JOB.f('idle_rotate_input.png'))
    result = json.loads(JOB.f('idle-rotate-result.json').read_text(encoding='utf-8-sig'))
    files = pipeline.pngs(result)
    records = {}
    for view in ('D', 'DR', 'R', 'UR', 'U'):
        if view == 'D':
            image = approved.copy()
        else:
            match = [p for p in files if p.stem.rsplit('-', 1)[0].split('-views-')[-1] == pipeline.VIEWS[view]]
            assert len(match) == 1
            image = fit(Image.open(match[0]), origin, approved.getbbox()[3])
            if view in JOB.sheet('idle')['views']:
                image.save(JOB.f(f'idle_view_{view}.png'))
        # The spread-wing design is already the neutral wingbeat pose. Lift
        # it off the ground, without resampling, for the airborne references.
        lift = min(8, max(0, image.getbbox()[1] - 2))
        airborne = Image.new('RGBA', SIZE)
        airborne.paste(image, (0, -lift))
        airborne.save(JOB.f('fly_frame0_clean.png' if view == 'D' else f'fly_view_{view}.png'))
        records[view] = {'lift': lift, 'standing_bounds': image.getbbox(), 'flight_bounds': airborne.getbbox()}
    JOB.f('flight_reference.json').write_text(json.dumps(records, indent=2) + '\n')
    print('Prepared three grounded and five airborne direction references; no pixels resampled', flush=True)


def animate_one(key, view, generate):
    sheet = JOB.sheet(key)
    path = JOB.f(f'{key}_input_{view}.png')
    origin = pipeline.roomy(pipeline.view_image(JOB, key, view), path)
    result = pipeline.call(JOB, f'{key}-animate-{view}',
                           ['animate', str(path), '--action', sheet['action'], '--frames', '4',
                            '--transparent', '--name', f'67-lagopus-{key}-{view}'], generate)
    if not result:
        return
    images = pipeline.pngs(result)
    assert len(images) in (4, 5), 'Expected four generated frames, optionally preceded by conditioning frame'
    for index, filename in enumerate(images[-4:], 1):
        ground = JOB.approved('idle').getbbox()[3] if key == 'idle' else None
        fit(Image.open(filename), origin, ground).save(JOB.f(f'{key}_anim_{view}_{index}.png'))
    print(f'{key} {view}: native frames saved', flush=True)


def animate(generate):
    failures = []
    tasks = [(key, view) for key in ('idle', 'fly') for view in JOB.sheet(key)['views']]
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(animate_one, key, view, generate): (key, view) for key, view in tasks}
        for future in as_completed(pending):
            try:
                future.result()
            except Exception as error:
                failures.append(f'{pending[future]}: {error}')
    if failures:
        raise RuntimeError('\n'.join(failures))


def pack():
    report = {'approved': False, 'installed': False, 'frame_size': SIZE, 'sheets': {}}
    for key in ('idle', 'fly'):
        pipeline.pack(JOB, key)
        cfg = JOB.sheet(key)
        png = JOB.f(f'{key}_sheet.png')
        ase = JOB.f(f'67_lagopus_{key}_review.aseprite')
        image = Image.open(png).convert('RGBA')
        enemy_sheet.pack(image, str(ase), cfg['frames'], False)
        subprocess.run([enemy_sheet.ASEPRITE, '-b', '--script-param', f'source={ase.as_posix()}',
                        '--script-param', 'durations=' + ('400,250,250' if key == 'idle' else '110'),
                        '--script-param', 'pal=' + ','.join('%02x%02x%02x' % c for c in JOB.palette('idle')),
                        '--script', str(ROOT / 'tools/sheet_meta.lua')], check=True)
        assert enemy_sheet.sheet_of(enemy_sheet.read(str(ase)), False).tobytes() == image.tobytes()
        cells = enemy_sheet.cells_of(image, cfg['frames'], False)
        palette = set(JOB.palette('idle'))
        assert all(p[3] in (0, 255) and (not p[3] or p[:3] in palette) for p in image.get_flattened_data())
        if key == 'idle':
            assert cells['D'][0].tobytes() == JOB.approved('idle').tobytes()
        board = Image.new('RGB', (35 + 62 * cfg['frames'], 45 * 8), (151, 151, 170))
        draw = ImageDraw.Draw(board)
        for row, view in enumerate(enemy_sheet.ORDER):
            draw.text((2, row * 45 + 17), view, fill=(0, 0, 0))
            for column, frame in enumerate(cells[view]):
                board.paste(frame, (35 + 62 * column, row * 45), frame)
            indices = [0, 1, 0, 2] if key == 'idle' else [0, 1, 2, 3]
            frames = [cells[view][i] for i in indices]
            frames[0].save(JOB.f(f'{key}_{view}_playback.gif'), save_all=True, append_images=frames[1:],
                           duration=[400, 250, 400, 250] if key == 'idle' else 110, loop=0, disposal=2)
        board.save(JOB.f(f'{key}_all_directions.png'))
        report['sheets'][key] = {'frames': cfg['frames'], 'size': list(image.size),
                                'aseprite': str(ase.relative_to(ROOT)), 'png': str(png.relative_to(ROOT)),
                                'round_trip_exact': True,
                                'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (png, ase)}}
    originals = json.loads(JOB.f('inputs.json').read_text())['sha256']
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in originals.items())
    report['originals_unchanged'] = True
    report['reported_animation_generations'] = sum(
        json.loads(path.read_text(encoding='utf-8-sig'))['cost']['generations']
        for path in [JOB.f('idle-rotate-result.json')] +
        [JOB.f(f'{key}-animate-{view}-result.json') for key in ('idle', 'fly') for view in JOB.sheet(key)['views']])
    JOB.f('animation_review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'animate', 'pack'])
    parser.add_argument('--generate', action='store_true')
    args = parser.parse_args()
    if args.stage == 'animate':
        animate(args.generate)
    else:
        globals()[args.stage]()
