"""Aseprite cleanup, runtime-compatible sheet, and exact-timing review playback."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'art/direction'))
import first_frame as ff
import enemy_sheet as es
import fcremap as fc

SIZE = (78, 59)
WORK_SIZE = (110, 91)
BATTLE = HERE / 'battle'
BATTLE.mkdir(exist_ok=True)

def padded(im):
    out = Image.new('RGBA', WORK_SIZE)
    out.paste(im, (16, 16))
    return out

def clean(im, view, index):
    if im.size == (84, 65):
        larger = Image.new('RGBA', WORK_SIZE)
        larger.paste(im, (13, 13))
        im = larger
    raw = BATTLE / f'{view}_{index}_before_cleanup.png'
    out = BATTLE / f'{view}_{index}.png'
    im.save(raw)
    prey = []
    if view in ('D', 'DR', 'R', 'UR', 'U'):
        ref = BATTLE / f'prey_reference_{view}.png'
        if view == 'D':
            Image.open(HERE / 'idle_frame0_clean_v3.png').save(ref)
        else:
            original = es.cells_of(Image.open(ROOT / 'assets/enemies/45_kusa_kap.png').convert('RGBA'),3,False)
            original[view][0].save(ref)
        prey = ['--script-param', f'prey={ref.as_posix()}', '--script-param', f'front={int(view=="D")}',
                '--script-param', f'back={int(view=="U")}']
    subprocess.run([ff.ASEPRITE, '-b', '--script-param', f'dir={HERE.as_posix()}',
                    '--script-param', f'input={raw.as_posix()}', '--script-param', f'output={out.as_posix()}',
                    '--script-param', 'native=1',
                    *prey,
                    '--script', str(HERE / 'cleanup.lua')], check=True)
    cleaned = Image.open(out).convert('RGBA')
    native = cleaned.crop((16,16,94,75))
    assert sum(p[3]>0 for p in cleaned.getdata()) == sum(p[3]>0 for p in native.getdata()), 'clipped art'
    native.save(BATTLE / f'{view}_{index}_native.png')
    return native

views = {}
for view in ('D', 'DR', 'R', 'UR', 'U'):
    first = padded(Image.open(HERE / ('idle_frame0_clean_v3.png' if view == 'D' else f'idle_view_{view}.png')).convert('RGBA'))
    # 1 is the generated upstroke, 3 the downstroke; raw results remain intact.
    generated = [Image.open(HERE / f'idle_native_{view}_{n}.png').convert('RGBA') for n in (1, 3)]
    views[view] = [first.crop((16,16,94,75)) if view == 'D' else clean(first, view, 0)] + [clean(im, view, i+1) for i, im in enumerate(generated)]
for view, src in {'UL': 'UR', 'L': 'R', 'DL': 'DR'}.items():
    views[view] = [clean(padded(ImageOps.mirror(im)), view, n) for n, im in enumerate(views[src])]

report = {'approved_design': True, 'approved_animation': False, 'installed': False,
          'frame_size': SIZE, 'original_frame_size': [78, 59], 'working_padding_each_side': 16,
          'resampled_pixels': False, 'runtime_loop': [0, 1, 0, 2],
          'runtime_loop_ms': [400, 250, 400, 250], 'frames': {}, 'failures': []}

for view in es.ORDER:
    report['frames'][view] = []
    for n, im in enumerate(views[view]):
        px = list(im.getdata())
        colors = sorted({p[:3] for p in px if p[3]})
        pal = {('K' if c == (0, 0, 0) else str(i)): '%02x%02x%02x' % c for i, c in enumerate(colors)}
        inv = {tuple(bytes.fromhex(c)): k for k, c in pal.items()}
        g = {(x,y): inv[im.getpixel((x,y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]}
        row = {'bounds': im.getbbox(), 'colors': len(colors),
               'off_palette': sum(p[:3] not in fc.PALETTE for p in px if p[3]),
               'partial_alpha': sum(p[3] not in (0,255) for p in px), 'tile_violations': []}
        for y in range(0, im.height, 16):
            for x in range(0, im.width, 16):
                colors_here = {p[:3] for p in im.crop((x,y,min(x+16,im.width),min(y+16,im.height))).getdata() if p[3]}
                if len(colors_here)>4: row['tile_violations'].append([x,y,len(colors_here)])
        try:
            row['outline_checks'] = ff.checks(g, pal, *SIZE, cap=65)
        except AssertionError as e:
            row['outline_failure'] = str(e)
        if row['off_palette'] or row['partial_alpha'] or row['tile_violations'] or 'outline_failure' in row:
            report['failures'].append(f'{view}:{n}')
        report['frames'][view].append(row)
    # Runtime-order GIF is independently inspected in each direction.
    playback = [views[view][n] for n in report['runtime_loop']]
    playback[0].save(BATTLE / f'{view}_playback.gif', save_all=True, append_images=playback[1:],
                     duration=report['runtime_loop_ms'], disposal=2, loop=0)

assert views['D'][0].tobytes() == Image.open(HERE / 'idle_frame0_clean_v3.png').convert('RGBA').tobytes()
sheet = es.sheet_of(views, False)
sheet.save(BATTLE / '45_kusa_kap.png')
es.pack(sheet, str(BATTLE / '45_kusa_kap.aseprite'), 3, False)
subprocess.run([ff.ASEPRITE, '-b', '--script-param', f'source={(BATTLE / "45_kusa_kap.aseprite").as_posix()}',
                '--script-param', 'durations=400,250,250', '--script', str(ROOT / 'tools/sheet_meta.lua')], check=True)
report['runtime_roundtrip_exact'] = es.sheet_of(es.read(str(BATTLE / '45_kusa_kap.aseprite')), False).tobytes() == sheet.tobytes()

# A review file has the repeated neutral pose explicitly, so its playback is
# exactly the game loop rather than Aseprite's ordinary 0/1/2 sequence.
all_frames = [views[v][n] for v in es.ORDER for n in report['runtime_loop']]
colors = sorted({p[:3] for im in all_frames for p in im.getdata() if p[3]})
pal = {('K' if c == (0,0,0) else str(i)): '%02x%02x%02x' % c for i,c in enumerate(colors)}
inv = {tuple(bytes.fromhex(c)): k for k,c in pal.items()}
grids = [{(x,y): inv[im.getpixel((x,y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]} for im in all_frames]
review = BATTLE / '45_kusa_kap_playback_review.aseprite'
ff.aseprite_frames(grids, pal, *SIZE, review, ms=400, tags={v:(i*4+1,i*4+4) for i,v in enumerate(es.ORDER)})
lua = BATTLE / 'playback_timing.lua'
lua.write_text('local s=app.open(app.params.source)\nlocal t={0.4,0.25,0.4,0.25}\nfor i,f in ipairs(s.frames) do f.duration=t[(i-1)%4+1] end\ns:saveAs(app.params.source)\ns:close()\n')
subprocess.run([ff.ASEPRITE, '-b', '--script-param', f'source={review.as_posix()}', '--script', str(lua)],check=True)
report['review_roundtrip_exact'] = ff.same_as_draft(review, all_frames)

board = Image.new('RGBA',(30+SIZE[0]*3,SIZE[1]*8),(151,151,170,255))
draw = ImageDraw.Draw(board)
for i,v in enumerate(es.ORDER):
    draw.text((2,i*SIZE[1]+25),v,fill='black')
    for j,im in enumerate(views[v]): board.alpha_composite(im,(30+j*SIZE[0],i*SIZE[1]))
board.resize((board.width*3,board.height*3),Image.Resampling.NEAREST).save(BATTLE / 'all_directions.png')
inputs = json.loads((HERE / 'inputs.json').read_text())
report['original_hashes_preserved'] = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest()==h for p,h in inputs['sha256'].items())
(BATTLE / 'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='frames'},indent=2))
