"""Checks one job's sprite.png against the rule and writes review.png to look at. While the job is being drawn it runs draw.py first.

    python -B tools/sprite_agent/check.py 42

Prints FAIL for what breaks the rule and LOOK for what a person should judge. Exit code 1 if anything fails.
"""
import ast
import glob
import json
import os
import subprocess
import sys

from PIL import Image

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
os.chdir(ROOT)
sys.path.insert(0, 'tools')
import enemy_style as es
import first_frame as ff


def scale_for(side):
    return 6 if side <= 64 else 3 if side <= 150 else 2


def review(sprite, folder):
    """The sprite large on black and on grey, then at the game's real 2x beside the player, on black."""
    k = scale_for(max(sprite.size))
    big = sprite.resize((sprite.width * k, sprite.height * k), Image.NEAREST)
    x2 = sprite.resize((sprite.width * 2, sprite.height * 2), Image.NEAREST)
    player = ff.player().resize((28, 40), Image.NEAREST)
    pad = 16
    width = big.width * 2 + x2.width + player.width + pad * 6
    height = max(big.height, x2.height, player.height) + pad * 2
    out = Image.new('RGB', (width, height), (0, 0, 0))
    grey_x = pad * 2 + big.width - pad // 2
    out.paste((132, 134, 148), (grey_x, 0, grey_x + big.width + pad, height))
    out.paste(big, (pad, height - pad - big.height), big)
    out.paste(big, (grey_x + pad // 2, height - pad - big.height), big)
    game_x = grey_x + big.width + pad * 2
    out.paste(x2, (game_x, height - pad - x2.height), x2)
    out.paste(player, (game_x + x2.width + pad, height - pad - player.height), player)
    out.save(os.path.join(folder, 'review.png'))
    return out.size


def loops_in(path):
    """Line numbers of the loops and comprehensions in a draw.py. Loops are what make identical bricks and scales."""
    with open(path, encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return []                  # running it reports that
    banned = (ast.For, ast.AsyncFor, ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
    return sorted({n.lineno for n in ast.walk(tree) if isinstance(n, banned)})


def main():
    i = int(sys.argv[1])
    paths = [p for p in glob.glob(os.path.join('art', 'enemies', 'nes', '%02d_*' % i)) if os.path.isdir(p)]
    if not paths:
        raise SystemExit('No job folder for %d.' % i)
    folder = paths[0]
    with open(os.path.join(folder, 'job.json'), encoding='utf-8') as f:
        job = json.load(f)
    strict = job.get('rule_version') if job.get('rule_version') in (2, 3) else False      # jobs keep the checks of the rule they were made under
    draw_py = os.path.join(folder, 'draw.py')
    if strict and os.path.exists(draw_py) and loops_in(draw_py):
        print('FAIL  draw.py uses a loop or comprehension on line %s. Place every shape yourself, so no two are identical.' % ', '.join(map(str, loops_in(draw_py))))
        print('1 failures.')
        return 1
    # A finished drawing is final: sprite.png is the truth, and it may have been edited by hand. Only a job with no
    # reply yet, an agent mid-drawing, runs draw.py.
    if not os.path.exists(os.path.join(folder, 'agent_reply.txt')):
        if not os.path.exists(os.path.join(folder, 'draw.py')):
            raise SystemExit('No draw.py in %s yet.' % folder)
        run = subprocess.run([sys.executable, '-B', 'draw.py'], cwd=folder, capture_output=True, text=True, timeout=120)
        if run.returncode:
            print('draw.py failed:')
            print((run.stderr or run.stdout)[-1500:])
            return 1
    sprite = Image.open(os.path.join(folder, 'sprite.png')).convert('RGBA')
    sprite = sprite.crop(sprite.getbbox())
    results = es.check_nes(sprite, job['side'], job['colours'], job.get('tolerance', es.nes_loose_tolerance(job['side'])), strict=strict)
    size = review(sprite, folder)
    used = {c[:3] for _, c in sprite.getcolors(sprite.width * sprite.height) if c[3]} - {(0, 0, 0)}
    print('%dx%d, target %d on the longer side, %d colours plus black.' % (sprite.width, sprite.height, job['side'], len(used)))
    for level, text in results:
        print('%s  %s' % (level, text))
    fails = sum(1 for level, _ in results if level == 'FAIL')
    print('review.png is written, %dx%d: large on black, large on grey, then at game size beside the player.' % size)
    print('No failures.' if not fails else '%d failures.' % fails)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
