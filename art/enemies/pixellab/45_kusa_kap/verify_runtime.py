"""Compare original and review sheets with the existing battlecensus binary."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE = ROOT / 'build_tmp/kusa_kap_battle_review'
env = dict(os.environ, SDL_VIDEODRIVER='dummy')
env['SHOT_FRAMES'] = '60:pose_1,150:pose_2,300:pose_3'
env['PATH'] = r'C:\msys64\mingw64\bin;' + env.get('PATH', '')
records = {}
for kind in ('original', 'review'):
    stage = STAGE / kind
    stage.mkdir(parents=True, exist_ok=True)
    if not (stage / 'assets').exists():
        shutil.copytree(ROOT / 'assets', stage / 'assets')
    if kind == 'review':
        # Only the disposable staged copy is changed; no Aseprite source is
        # copied beside it, so runtime auto-export cannot replace the draft.
        target = stage / 'assets/enemies/45_kusa_kap.png'
        shutil.copy2(HERE / 'battle/45_kusa_kap.png', target)
        ase = target.with_suffix('.aseprite')
        if ase.exists():
            ase.rename(ase.with_suffix('.aseprite.preserved'))
    shots = stage / 'shots'
    shots.mkdir(exist_ok=True)
    result = subprocess.run([str(ROOT / 'battlecensus.exe'), '45', '3872026', '12', str(shots)],
                            cwd=stage, env=env, capture_output=True, text=True, timeout=120)
    (stage / 'stdout.txt').write_text(result.stdout)
    (stage / 'stderr.txt').write_text(result.stderr)
    records[kind] = {'exit_code': result.returncode, 'stdout': result.stdout,
                     'screenshots': [p.name for p in shots.glob('*.png')]}
records['gameplay_stdout_equal'] = records['original']['stdout'] == records['review']['stdout']
inputs = json.loads((HERE / 'inputs.json').read_text())
records['original_hashes_preserved'] = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest()==h for p,h in inputs['sha256'].items())
(STAGE / 'verification.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
assert all(records[k]['exit_code']==0 for k in ('original','review'))
assert records['gameplay_stdout_equal'] and records['original_hashes_preserved']
