"""59 Tripodero's dance with its legs alternating (the user, 2026-10-28: stepping right it lifts the leg on the
screen's right, stepping left the leg on the screen's left -- "not the same leg"). PixelLab lifted the
screen-right leg in every frame it drew, a left-step request included, and cutting its legs out to swap them
tore the body (it shares their browns). So the step left is the step right (walk_anim_<v>_3) mirrored whole:
the lifted leg on the screen's left, its snout and tail swaying to the other side for that step. Front and
back only (D, U); in the three-quarter and side views the legs overlap. Writes walk_anim_step_<v>_1.png for
the job's map: step left, planted, step right, planted (Tripodero::update, src/enemies.cpp).

    python art/enemies/pixellab/59_tripodero/dance.py
"""
from pathlib import Path
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent

for v in ('D', 'U'):
    ImageOps.mirror(Image.open(HERE / f'walk_anim_{v}_3.png').convert('RGBA')).save(HERE / f'walk_anim_step_{v}_1.png')
    print(v, 'step left written')
