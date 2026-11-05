"""34 Anaye's lift and slam through PixelLab: dry run, then with --generate the paid call. A saved result is reused, never resubmitted.

    python art/enemies/pixellab/34_anaye/redo_bc/anim/call.py [--generate]
"""
import json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
env = dict(os.environ, PIXELLAB_ASSUME_YES='0')
go = '--generate' in sys.argv
def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8-sig', env=env, cwd=ROOT)
for n in ('lift', 'slam'):
    saved = HERE / f'{n}-result.json'
    if saved.exists():
        print(n, 'saved result, not resubmitted'); continue
    ws = ROOT / 'pixellab-out/34-anaye-bc-anim' / n
    if go and (ws / 'ledger.jsonl').exists() and (ws / 'ledger.jsonl').read_text().strip():
        raise SystemExit(f'{n}: a ledger exists without a saved result; collect it with pixellab-cli job show')
    action = (HERE / f'{n}.txt').read_text(encoding='utf-8-sig').strip()
    req = ['animate', str(HERE / 'input.png'), '--action', action, '--frames', '8', '--transparent', '--name', n]
    common = ['pixellab-cli', '--json', '--workspace', str(ws), '--subject', n]
    dry = run(common + ['--dry-run'] + req)
    assert dry.returncode == 0, dry.stderr
    data = json.loads(dry.stdout)
    print(n, 'dry run', data['route'], data['estimated_cost'])
    if not go: continue
    paid = run(common + ['--yes'] + req)
    (HERE / f'{n}-stderr.txt').write_text(paid.stderr, encoding='utf-8')
    assert paid.returncode == 0, f'{n} failed: see {n}-stderr.txt and the ledger before retrying'
    saved.write_text(paid.stdout, encoding='utf-8')
    r = json.loads(paid.stdout)
    print(n, 'done', r['cost'], len(r['files']), 'files')
