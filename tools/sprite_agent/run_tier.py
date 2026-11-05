"""Draws a whole tier's first idle frames, one sprite at a time, each with its own brand-new agent (run.py). Nothing goes in the game.

    python -B tools/sprite_agent/run_tier.py LOW           # the tier's unfinished sprites, then a review board
    python -B tools/sprite_agent/run_tier.py LOW --list    # what it would draw, and stop
    python -B tools/sprite_agent/run_tier.py LOW --limit 3 # at most 3 sprites this time
    python -B tools/sprite_agent/run_tier.py LOW --reverse # largest first
    python -B tools/sprite_agent/run_tier.py LOW --agent codex  # each sprite drawn by a brand-new Codex, not Claude

Tiers: LOW MEDIUM UPPER HARD SEVERE ELITE BOSS1 BOSS2 BOSS3. The user's picks aren't drawn, except the 10 in NES_RESIZE, which
get drawn larger. It's safe to run again:
a sprite that finished with no checker failures, or that the user edited by hand, is skipped, so a stopped run carries on where it left off. It stops after
two failures in a row, which usually means a usage limit. To redo one sprite: python -B tools/sprite_agent/run.py ID

Two runs can share the work. Each claims a sprite before drawing it, and skips one the other has or has finished, so they
meet in the middle without drawing the same sprite twice. A claim from a run that has died doesn't count.
"""
import argparse
import ctypes
import glob
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import run as agent
import new_job
es = new_job.es

BOARDS = os.path.join('art', 'enemies', 'nes', '_boards')
CLAIMS = os.path.join(tempfile.gettempdir(), 'c_game_sprite_claims')


def job_folder(i):
    paths = [p for p in glob.glob(os.path.join('art', 'enemies', 'nes', '%02d_*' % i)) if os.path.isdir(p)]
    return paths[0] if paths else None


def hand_edited(folder):
    """The user saved over sprite.png after its agent finished, because the agent's reply is always written last."""
    return os.path.getmtime(os.path.join(folder, 'sprite.png')) > os.path.getmtime(os.path.join(folder, 'agent_reply.txt')) + 1


def finished(i):
    folder = job_folder(i)
    if not folder or not os.path.exists(os.path.join(folder, 'agent_reply.txt')) or not os.path.exists(os.path.join(folder, 'sprite.png')):
        return False
    if hand_edited(folder):                 # the user's edit is final: a rerun never redraws it, whatever the checker says
        return True
    check = subprocess.run([sys.executable, '-B', os.path.join('tools', 'sprite_agent', 'check.py'), str(i)], capture_output=True, text=True, encoding='utf-8')
    if check.returncode:
        return False
    with Image.open(os.path.join(folder, 'sprite.png')) as im:    # the job's own target can be out of date if sizes changed since
        return es.nes_fits(i, max(im.size))


def process_alive(pid):
    """Windows only, and not os.kill(pid, 0), which on Windows sends the process a Ctrl+C."""
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    code = ctypes.c_ulong()
    known = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(handle)
    return bool(known) and code.value == 259


def claim_path(i):
    return os.path.join(CLAIMS, '%d.claim' % i)


def being_drawn(i):
    """Another live run has this sprite. A job cut off by a kill is free at once, because its claim died with its run."""
    try:
        with open(claim_path(i), encoding='utf-8') as f:
            pid = int(f.read().strip() or 0)
    except (OSError, ValueError):
        pid = 0
    return bool(pid) and pid != os.getpid() and process_alive(pid)


def claim(i):
    """True if this run now has the sprite."""
    os.makedirs(CLAIMS, exist_ok=True)
    if being_drawn(i):
        return False
    try:
        if os.path.exists(claim_path(i)):       # left by a run that has died
            os.remove(claim_path(i))
        fd = os.open(claim_path(i), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        return False                            # the other run got there first
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    return True


def release(i):
    try:
        os.remove(claim_path(i))
    except OSError:
        pass


def board(tier, ids):
    """Each sprite now, then its new drawing, at the game's 2x on black."""
    sheets, names = es.sheets(), es.names()
    font = ImageFont.truetype('arial.ttf', 14)
    items = []
    for i in ids:
        now = es.first_frame(sheets[i]['path'], sheets[i]['frames'], sheets[i]['rows'])[0]
        folder = job_folder(i)
        png = os.path.join(folder, 'sprite.png') if folder else None
        new = Image.open(png).convert('RGBA') if png and os.path.exists(png) and os.path.exists(os.path.join(folder, 'agent_reply.txt')) else None
        items.append((i, names[i].title(), now, new))
    width, pad, x, y, shelf = 1500, 16, 16, 16, 0
    place = []
    for i, name, now, new in items:
        w = now.width * 2 + (new.width * 2 + 12 if new else 60) + 12
        h = max(now.height, new.height if new else 0) * 2 + 24
        w = max(w, 150)
        if x + w > width - pad:
            x, y, shelf = pad, y + shelf + pad, 0
        place.append((i, name, now, new, x, y, h))
        x += w + pad
        shelf = max(shelf, h)
    out = Image.new('RGB', (width, y + shelf + pad), (0, 0, 0))
    draw = ImageDraw.Draw(out)
    for i, name, now, new, px, py, h in place:
        a = now.resize((now.width * 2, now.height * 2), Image.NEAREST)
        out.paste(a, (px, py + h - 24 - a.height), a)
        if new:
            b = new.resize((new.width * 2, new.height * 2), Image.NEAREST)
            out.paste(b, (px + a.width + 12, py + h - 24 - b.height), b)
        draw.text((px, py + h - 20), '%d %s%s' % (i, name[:18], '' if new else ' (not drawn)'), fill=(235, 235, 235), font=font)
    os.makedirs(BOARDS, exist_ok=True)
    path = os.path.join(BOARDS, '%s.png' % tier)
    out.save(path)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tier', type=str.upper)
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--reverse', action='store_true', help='largest first')
    ap.add_argument('--agent', choices=['claude', 'codex'], default='claude', help='who draws: the prompt, rule, briefs and checker are the same')
    args = ap.parse_args()
    os.chdir(ROOT)
    tiers, names = es.tiers(), es.names()
    if args.tier not in es.NES_SIDE:
        raise SystemExit('Tier must be one of: %s' % ' '.join(es.NES_SIDE))
    ids = sorted((i for i in range(len(tiers)) if tiers[i] == args.tier and (i not in es.NES_ANCHORS or i in es.NES_RESIZE)), key=lambda i: (es.nes_target(i)[0], i), reverse=args.reverse)
    todo = [i for i in ids if not finished(i)]
    print('%s: %d to redraw, %d already finished, %d to draw now: %s' % (args.tier, len(ids), len(ids) - len(todo), len(todo), ' '.join(map(str, todo))))
    if args.list:
        for i in todo:
            print('  %d %s, %d px' % (i, names[i].title(), es.nes_target(i)[0]))
        return 0
    if args.limit is not None:
        todo = todo[:args.limit]
    failed, bad_in_a_row = [], 0
    for n, i in enumerate(todo, 1):
        print('--- %d of %d: %d %s' % (n, len(todo), i, names[i].title()), flush=True)
        if not claim(i):
            print('The other run has this one, so moving on.', flush=True)
            continue
        if finished(i):                         # checked after claiming, so the other run can't be part way through it
            release(i)
            print('The other run has finished this one, so moving on.', flush=True)
            continue
        try:
            code = agent.draw(i, args.agent)
        finally:
            release(i)
        if code == 0 and finished(i):
            bad_in_a_row = 0
            continue
        failed.append(i)
        bad_in_a_row += 1
        if bad_in_a_row >= 2:
            print('Stopping after two failures in a row. This is often a usage limit. Run the same command again to carry on.')
            break
    left = [i for i in ids if not finished(i)]
    theirs = [i for i in left if being_drawn(i)]
    left = [i for i in left if i not in theirs]    # the other run is on these, so they don't stop this one
    path = board(args.tier, ids)
    print('=== %s: %d of %d finished.' % (args.tier, len(ids) - len(left) - len(theirs), len(ids)))
    if theirs:
        print('The other run is still drawing: %s' % ' '.join(map(str, theirs)))
    if failed:
        print('Failed this run: %s' % ' '.join(map(str, failed)))
    if left:
        print('Still to draw: %s' % ' '.join(map(str, left)))
    print('Review board: %s' % path)
    return 1 if left else 0


if __name__ == '__main__':
    sys.exit(main())
