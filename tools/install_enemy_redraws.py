"""Install the eight reviewed first poses using the existing sheet exporter.

Keeps original assets and frame dimensions/counts. Only D is drawn; the
project's normal direction fallback and one-pixel breathing derive the rest.
No generated side views or attack drawings are implied by this installation.
"""
from pathlib import Path
from datetime import datetime
from collections import Counter
import hashlib
import json
import shutil
import sys
from PIL import Image

import enemy_sheet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'art/direction'))
from fcremap import PALETTE

# id, original runtime basename, reviewed first pose, frame count, rows, body pivot
ENTRIES = [
    (17, '17_qiqirn', '17_qiqirn_frame0_draft', 3, False, 23),
    (41, '41_sasnalkahi', '41_sasnalkahi_frame0_draft', 5, False, 43),
    (49, '49_physeter', '49_physeter_frame0_draft', 8, True, 105),
    (51, '51_aspidochelone', '51_aspidochelone_frame0_no_water', 8, True, 57),
    (64, '64_dungavenhooter', '64_dungavenhooter_frame0_draft', 8, False, 46),
    (76, '76_loch_oich_monster', '76_loch_oich_frame0_draft', 5, False, 41),
    (77, '77_hoga', '77_hoga_frame0_draft', 5, False, 43),
    (97, '97_ro', '97_ro_demonic_frame0_draft', 8, True, 56),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def breathe(im, pivot):
    """build_enemy.poses' row shifts, without its added padding row.

    Frame zero is byte-identical to the approved pose. All rows beneath the
    pivot stay fixed; the upper form rises or settles by exactly one pixel.
    """
    w, h = im.size
    inhale = Image.new('RGBA', im.size)
    inhale.paste(im.crop((0, 1, w, pivot+1)), (0, 0))
    inhale.paste(im.crop((0, pivot, w, h)), (0, pivot))
    settle = Image.new('RGBA', im.size)
    settle.paste(im.crop((0, 0, w, pivot)), (0, 1))
    settle.paste(im.crop((0, pivot+1, w, h)), (0, pivot+1))
    assert im.getbbox()[1] > 0, 'Breathing needs one transparent row above the pose'
    return [im, inhale, settle]


def install():
    dest = ROOT/'assets/enemies/redraws'
    if dest.exists():
        # Resume only the first PNG written before an interrupted initial pack.
        # A completed or independently edited installation is never overwritten.
        assert {p.name for p in dest.iterdir()} <= {'17_qiqirn.png'}, f'Refusing to replace an existing installation: {dest}'
    backup = ROOT/'art/_backup'/('enemy_redraw_install_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    protected = {}
    for _, basename, art, _, _, _ in ENTRIES:
        for p in [ROOT/f'assets/enemies/{basename}{ext}' for ext in ('.png', '.aseprite')]:
            protected[p.relative_to(ROOT).as_posix()] = sha(p)
            shutil.copy2(p, backup/p.name)
        for ext in ('.png', '.aseprite'):
            p = ROOT/f'art/enemies/{art}{ext}'
            protected[p.relative_to(ROOT).as_posix()] = sha(p)
    for ext in ('.png', '.aseprite'):
        p = ROOT/f'assets/enemies/17_qiqirn_run{ext}'
        protected[p.relative_to(ROOT).as_posix()] = sha(p)
        shutil.copy2(p, backup/p.name)
    shutil.copy2(ROOT/'src/battle.cpp', backup/'battle.cpp')
    dest.mkdir(exist_ok=True)
    records=[]
    for enemy_id, basename, art, n, rows, pivot in ENTRIES:
        source = ROOT/f'art/enemies/{art}.png'
        im = Image.open(source).convert('RGBA')
        old = Image.open(ROOT/f'assets/enemies/{basename}.png').convert('RGBA')
        cell = (old.width//n,old.height//8) if rows else (old.width//(8*n),old.height)
        assert im.size == cell, (enemy_id, im.size, cell)
        assert all(c[:3] in PALETTE and c[3] in (0,255) for c in im.getdata() if c[3])
        poses = breathe(im, pivot)
        order = {3:[0,1,2],4:[0,1,0,2],5:[0,1,0,2,0],8:[0,0,1,1,0,0,2,2]}[n]
        tagged={'D':[poses[k] for k in order]}
        sheet=enemy_sheet.sheet_of(tagged, rows)
        png=dest/f'{basename}.png'
        colors=Counter(c[:3] for c in im.getdata() if c[3])
        tags=enemy_sheet.install(sheet,png,n,rows,ms=260,palette=['%02x%02x%02x'%c for c in colors])
        got=Image.open(png).convert('RGBA')
        cells=enemy_sheet.cells_of(got,n,rows)
        assert got.size==old.size
        assert cells['D'][0].tobytes()==im.tobytes()
        assert len({f.tobytes() for f in cells['D']})==3
        assert all(f.crop((0,pivot+1,im.width,im.height)).tobytes()==im.crop((0,pivot+1,im.width,im.height)).tobytes() for f in cells['D'])
        records.append(dict(id=enemy_id,source=source.relative_to(ROOT).as_posix(),png=png.relative_to(ROOT).as_posix(),
                            aseprite=png.with_suffix('.aseprite').relative_to(ROOT).as_posix(),frame_size=list(im.size),
                            frames=n,rows=rows,tags=tags,body_pivot=pivot,frame_zero_exact=True,
                            png_sha256=sha(png),aseprite_sha256=sha(png.with_suffix('.aseprite'))))
        if enemy_id==17:
            # The runtime selects this sheet during galloping. Use the new pose
            # there too, without inventing a full run cycle or changing its timing.
            run=dest/'17_qiqirn_run.png'
            sheet=enemy_sheet.sheet_of({'D':[poses[k] for k in (0,1,0,2)]},False)
            enemy_sheet.install(sheet,run,4,False,ms=260,palette=['%02x%02x%02x'%c for c in colors])
            assert Image.open(run).size==Image.open(ROOT/'assets/enemies/17_qiqirn_run.png').size
            records[-1]['run_png']=run.relative_to(ROOT).as_posix()
        print(f'Installed {enemy_id:02}: {png.name}, {n} frames, {im.width}x{im.height}',flush=True)
    for rel,h in protected.items():
        assert sha(ROOT/rel)==h, f'Protected source changed: {rel}'
    manifest=dict(enemies=records,backup=backup.relative_to(ROOT).as_posix(),protected_sources=protected,
                  rendering='One drawn pose, project direction fallback (left views mirrored), three subtle breathing states resampled into existing frame counts',
                  limitations='Distinct directional, attack and Qiqirn gallop drawings have not been created; gameplay hooks/frame counts retained',paid_calls=0)
    (dest/'installation.json').write_text(json.dumps(manifest,indent=2))
    print('All source hashes preserved; frame zero exact; native dimensions, layouts, frame counts and foot placement verified.')


if __name__=='__main__':
    install()
