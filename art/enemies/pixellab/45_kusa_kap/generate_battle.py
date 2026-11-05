"""Collect saved PixelLab wingbeats without clipping their native pixels."""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import pixellab_enemy as pe

job = pe.Job(HERE / 'job.json')
generate = '--generate' in sys.argv
for view in job.sheet('idle')['views']:
    src = job.f(f'idle_input_{view}.png')
    origin = pe.roomy(pe.view_image(job, 'idle', view), src)
    result = pe.call(job, f'idle-animate-{view}', [
        'animate', str(src), '--action', job.sheet('idle')['action'],
        '--frames', '4', '--transparent', '--name', f'45-kusa-kap-idle-{view}'
    ], generate)
    if result:
        # Three pixels of transparent clearance each side; no resampling.
        for i, path in enumerate(pe.pngs(result)[-4:], 1):
            im = pe.fit(Image.open(path), (84, 65), (origin[0]+3, origin[1]+3))
            pe.to_palette(im, job.palette('idle')).save(job.f(f'idle_native_{view}_{i}.png'))
