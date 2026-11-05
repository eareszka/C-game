"""Makes one small change to a finished sprite with a brand-new agent, starting from the image as it is now. Nothing goes in the game.

    python -B tools/sprite_agent/touch_up.py 58 "make its arms thicker"

The agent reads only the rule, this enemy's brief, the note and the current sprite, and changes only what the note asks.
Hand edits to sprite.png carry through, because it starts from that image. The folder as it was is copied to
art/enemies/nes/_old/ first. The note is also saved in briefs.json, so a later full redraw keeps it. Afterwards it writes
compare.png in the job folder, before then after, and prints which files the agent opened.
"""
import json
import os
import shutil
import subprocess
import sys
import time

from PIL import Image

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import run as agent
import new_job
import run_tier
es = new_job.es

PROMPT = os.path.join(HERE, 'TOUCH_UP_PROMPT.md')


def compare(folder):
    """Before then after: large on black, then at the game's 2x on black."""
    a = Image.open(os.path.join(folder, 'before.png')).convert('RGBA')
    b = Image.open(os.path.join(folder, 'sprite.png')).convert('RGBA')
    k = 6 if max(a.size + b.size) <= 64 else 3 if max(a.size + b.size) <= 150 else 2
    pad = 16
    parts = [x.resize((x.width * s, x.height * s), Image.NEAREST) for x, s in ((a, k), (b, k), (a, 2), (b, 2))]
    out = Image.new('RGB', (sum(p.width for p in parts) + pad * 5, max(p.height for p in parts) + pad * 2), (0, 0, 0))
    x = pad
    for p in parts:
        out.paste(p, (x, out.height - pad - p.height), p)
        x += p.width + pad
    out.save(os.path.join(folder, 'compare.png'))


def main():
    if len(sys.argv) != 3 or not sys.argv[1].isdigit() or not sys.argv[2].strip():
        raise SystemExit(__doc__)
    i, note = int(sys.argv[1]), sys.argv[2].strip()
    os.chdir(ROOT)
    folder = run_tier.job_folder(i)
    if not folder or not os.path.exists(os.path.join(folder, 'sprite.png')):
        raise SystemExit('Enemy %d has no drawing yet. Draw it first: python -B tools/sprite_agent/run.py %d' % (i, i))
    if not os.path.exists(os.path.join(folder, 'agent_reply.txt')):
        raise SystemExit('Enemy %d is still being drawn. Wait for that run to finish.' % i)
    if not run_tier.claim(i):                  # with no reply file during the touch-up, a run would otherwise take it for unfinished
        raise SystemExit('A run is drawing enemy %d right now. Wait for that to finish.' % i)

    old = os.path.join('art', 'enemies', 'nes', '_old', '%s_%s' % (os.path.basename(folder), time.strftime('%Y%m%d_%H%M%S')))
    os.makedirs(os.path.dirname(old), exist_ok=True)
    shutil.copytree(folder, old)
    shutil.copyfile(os.path.join(folder, 'sprite.png'), os.path.join(folder, 'before.png'))
    with open(os.path.join(folder, 'EDIT.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# The change to make\n\n%s\n' % note)
    os.remove(os.path.join(folder, 'agent_reply.txt'))
    for stale in ('draw.py', 'compare.png'):
        if os.path.exists(os.path.join(folder, stale)):
            os.remove(os.path.join(folder, stale))
    shutil.copyfile(os.path.join(HERE, 'pix.py'), os.path.join(folder, 'pix.py'))   # the newest helpers
    shutil.copyfile(new_job.RULE, os.path.join(folder, 'RULE.md'))
    with open(os.path.join(folder, 'job.json'), encoding='utf-8') as f:
        job = json.load(f)
    with Image.open(os.path.join(folder, 'before.png')) as im:
        job['side'] = max(im.size)             # a touch-up keeps the size it has, even if its target has moved since
    job['touch_up'] = note
    with open(os.path.join(folder, 'job.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(job, f, indent=0)

    try:
        code = agent.run_agent(i, folder, PROMPT)
        made = code == 0 and os.path.exists(os.path.join(folder, 'agent_reply.txt'))
        if not made:                           # put the finished sprite back, so a failed run costs nothing
            shutil.copyfile(os.path.join(folder, 'before.png'), os.path.join(folder, 'sprite.png'))
            shutil.copyfile(os.path.join(old, 'agent_reply.txt'), os.path.join(folder, 'agent_reply.txt'))
    finally:
        run_tier.release(i)
    if not made:
        print('The touch-up failed, so the sprite is as it was. Run the same command again to retry.')
        return code or 1
    briefs_path = os.path.join(HERE, 'briefs.json')
    with open(briefs_path, encoding='utf-8') as f:
        briefs = json.load(f)
    briefs.setdefault(str(i), {}).setdefault('fixes', []).append(note)
    with open(briefs_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(briefs, f, indent=1, ensure_ascii=False)
    compare(folder)
    check = subprocess.run([sys.executable, '-B', os.path.join('tools', 'sprite_agent', 'check.py'), str(i)], capture_output=True, text=True, encoding='utf-8')
    print(check.stdout.strip().splitlines()[-1] if check.stdout.strip() else 'The checker printed nothing.')
    print('Before and after: %s' % os.path.join(folder, 'compare.png'))
    print('The earlier version is kept at: %s' % old)
    return 0


if __name__ == '__main__':
    sys.exit(main())
