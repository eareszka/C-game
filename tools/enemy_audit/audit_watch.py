"""Tells a Claude session when the enemy style audit has fallen behind the game.

build_audit.py records which battle sheets the page was built from in last_build.json. This compares that record with what
ENEMY_SHEETS in src/battle.cpp loads now, and with the done list in art/enemies/redraw_status.json.

  python -B -u tools/enemy_audit/audit_watch.py          one line per change once it has settled, until killed. Run it under a monitor.
  python -B tools/enemy_audit/audit_watch.py --check     says what is behind and exits, with 1 if anything is.

It only reports. Publishing the page needs the Artifact tool, so a session has to do that part.
"""
import glob
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
os.chdir(ROOT)
sys.path.insert(0, 'tools')
import enemy_style as es

STAMP = os.path.join(HERE, 'last_build.json')
STATUS = os.path.join('art', 'enemies', 'redraw_status.json')
POLL = 20       # seconds between looks
SETTLE = 60     # an install writes several sheets, so wait until they stop changing
BROKEN = 300    # say so if the table can't be read for this long; silence would look like nothing changed

_hashes = {}


def file_hash(path):
    if not os.path.exists(path):
        return None
    st = os.stat(path)
    key = (st.st_mtime_ns, st.st_size)
    if path not in _hashes or _hashes[path][0] != key:
        with open(path, 'rb') as f:
            _hashes[path] = (key, hashlib.sha1(f.read()).hexdigest())
    return _hashes[path][1]


def drawings():
    """Each finished new drawing's hash (tools/sprite_agent). A folder with no agent_reply.txt is still being drawn."""
    out = {}
    for reply in glob.glob(os.path.join('art', 'enemies', 'nes', '[0-9]*', 'agent_reply.txt')):
        folder = os.path.dirname(reply)
        out[os.path.basename(folder).split('_')[0].lstrip('0') or '0'] = file_hash(os.path.join(folder, 'sprite.png'))
    return out


def snapshot():
    """Every battle sheet's hash, and who is done. Reads the table each time, because an install can add a sheet."""
    sheets = {}
    for i, s in enumerate(es.sheets()):
        for v in s.values():
            if isinstance(v, str) and v.endswith('.png'):
                sheets.setdefault(str(i), {})[v] = file_hash(v)
    with open(STATUS, encoding='utf-8') as f:
        done = sorted(json.load(f)['done'])
    return dict(sheets=sheets, done=done, drawings=drawings(), boards={os.path.basename(p): file_hash(p) for p in glob.glob(os.path.join('art', 'enemies', 'nes', '_boards', '*.png'))})


def write_stamp(snap):
    with open(STAMP, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(snap, built=time.strftime('%Y-%m-%d %H:%M')), f, indent=0, sort_keys=True)
        f.write('\n')


def last_build():
    if not os.path.exists(STAMP):
        return None
    with open(STAMP, encoding='utf-8') as f:
        return json.load(f)


def behind(now, then):
    """{enemy id: what differs} between two snapshots."""
    out = {}
    for i in set(now['sheets']) | set(then['sheets']):
        a, b = now['sheets'].get(i, {}), then['sheets'].get(i, {})
        changed = sorted(os.path.basename(p) for p in set(a) | set(b) if a.get(p) != b.get(p))
        if changed:
            out[int(i)] = changed
    for i in set(now['done']) ^ set(then['done']):
        out.setdefault(i, []).append('done list')
    a, b = now.get('drawings', {}), then.get('drawings', {})
    for i in set(a) | set(b):
        if a.get(i) != b.get(i):
            out.setdefault(int(i), []).append('new drawing')
    a, b = now.get('boards', {}), then.get('boards', {})
    fresh = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    if fresh:
        out['boards'] = fresh
    return out


def describe(gap):
    names = es.names()
    parts = ['%d %s (%s)' % (i, names[i], ', '.join(gap[i])) for i in sorted(k for k in gap if k != 'boards')]
    if 'boards' in gap:
        parts.append('review board %s' % ', '.join(gap['boards']))
    return 'AUDIT BEHIND: ' + '; '.join(parts)


def check():
    then = last_build()
    if then is None:
        print('AUDIT BEHIND: no build recorded yet')
        return 1
    gap = behind(snapshot(), then)
    print(describe(gap) if gap else 'Audit is current, built %s.' % then['built'])
    return 1 if gap else 0


def watch():
    pending, since, reported = None, 0.0, None
    failing_since, warned = None, False
    while True:
        try:
            now = snapshot()
            failing_since, warned = None, False
        except Exception as e:      # battle.cpp or the status file can be caught mid-edit
            failing_since = failing_since or time.time()
            if not warned and time.time() - failing_since >= BROKEN:
                print('AUDIT WATCH ERROR: %s: %s' % (type(e).__name__, e), flush=True)
                warned = True
            time.sleep(POLL)
            continue
        then = last_build()
        gap = {} if then is None else behind(now, then)
        if then is None and reported != 'no build':
            print('AUDIT BEHIND: no build recorded yet', flush=True)
            reported = 'no build'
        elif gap != pending:
            pending, since = gap, time.time()
        elif not gap:
            reported = None
        elif gap != reported and time.time() - since >= SETTLE:
            print(describe(gap), flush=True)
            reported = gap
        time.sleep(POLL)


if __name__ == '__main__':
    sys.exit(check() if '--check' in sys.argv else watch())
