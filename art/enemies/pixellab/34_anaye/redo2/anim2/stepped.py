"""34 Anaye stepped like the cast (the user, 2026-11-04: "the same fps as other moving sprites so it doesnt look too smooth, like ... dingbat and beast of barr"): fewer poses from anim.py's c_N, each held 260 ms, STEP_MS (src/battle.cpp), as Dingbat and 83.
idle c_0 c_1; lift c_1 c_3 c_4 c_6; slam c_7 c_9 c_11 c_13. Writes review_stepped.png, lift.gif, slam.gif, both.gif; stepped.lua makes 34_review.aseprite (the one to open).

    python art/enemies/pixellab/34_anaye/redo2/anim2/stepped.py
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 130, 118, 260
IDLE, LIFT, SLAM = (0, 1), (1, 3, 4, 6), (7, 9, 11, 13)
fr = {i: Image.open(HERE / f'c_{i}.png').convert('RGBA') for i in {*IDLE, *LIFT, *SLAM}}
def gif(seq, name):
    big = []
    for i in seq:
        bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(fr[i]); big.append(bg.resize((W * 3, H * 3), 0).convert('P', palette=Image.ADAPTIVE))
    big[0].save(HERE / name, save_all=True, append_images=big[1:], duration=MS, loop=0)
gif(LIFT, 'lift.gif'); gif(SLAM, 'slam.gif'); gif(IDLE + IDLE + LIFT + SLAM, 'both.gif')
S = 3
seqs = (IDLE, LIFT, SLAM)
rev = Image.new('RGBA', (W * S * 4, H * S * 3), (0, 0, 0, 255))
for r, seq in enumerate(seqs):
    for c, i in enumerate(seq): rev.alpha_composite(fr[i].resize((W * S, H * S), 0), (c * W * S, r * H * S))
rev.save(HERE / 'review_stepped.png')
