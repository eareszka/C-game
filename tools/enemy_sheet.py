"""An enemy sheet's .aseprite holds only the frames that are drawn; the game's
PNG (8 directions x the idle frames) is exported from it.

    python tools/enemy_sheet.py export assets/enemies/NN_name.aseprite
    python tools/enemy_sheet.py pack   assets/enemies/NN_name.png FRAMES [rows]
    python tools/enemy_sheet.py pack-all        (every sheet in ENEMY_SHEETS)

The .aseprite: the canvas is one cell, one tag per direction that is drawn
(D DR R UR U UL L DL), each tag the direction's idle frames. A direction
with no tag is not a copy in the file -- export fills it in:
    DR <- D      R <- DR      UR <- R      U <- UR
    UL <- UR mirrored      L <- R mirrored      DL <- DR mirrored
so a front-only enemy is one tag (D), a normal one five, and a left view is
drawn only when it isn't the right one's mirror. An .aseprite with no tags is
an old one-image sheet and exports as it is. The PNG keeps its layout (one
row, or one row per direction for a sheet too wide for a texture).

The game runs `export` itself when an .aseprite is newer than its PNG
(src/battle.cpp), so an edit saved in Aseprite shows in the next battle.

build_enemy.py's rebuild guard lives here too: built() records the PNG a
build wrote, hand_edited() says it has changed since (drawn over by hand).
"""
import sys, os, re, json, hashlib, subprocess, tempfile
from PIL import Image, ImageOps

ASEPRITE = r"C:\Program Files\Aseprite\Aseprite.exe"
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
SOURCE = {'DR': ('D', False), 'R': ('DR', False), 'UR': ('R', False), 'U': ('UR', False),   # a direction with no tag: (from, mirrored)
          'UL': ('UR', True), 'L': ('R', True), 'DL': ('DR', True)}
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FLAP_FRAMES = 4   # src/battle.cpp

def resolve(tags, d):
    """Direction d's frames from the tagged ones."""
    if d in tags: return tags[d]
    src, mirrored = SOURCE[d]
    fr = resolve(tags, src)
    return [ImageOps.mirror(f) for f in fr] if mirrored else fr

def cells_of(sheet, frames, rows):
    """{direction: its frames} cut from a full sheet."""
    fw, fh = (sheet.width // frames, sheet.height // 8) if rows else (sheet.width // (8 * frames), sheet.height)
    at = (lambda d, f: (f * fw, d * fh)) if rows else (lambda d, f: ((d * frames + f) * fw, 0))
    return {name: [sheet.crop((x, y, x + fw, y + fh)) for x, y in (at(d, f) for f in range(frames))] for d, name in enumerate(ORDER)}

def sheet_of(tags, rows):
    """The full sheet from the tagged frames."""
    frames = len(tags['D'])
    fw, fh = tags['D'][0].size
    out = Image.new('RGBA', (frames * fw, 8 * fh) if rows else (8 * frames * fw, fh), (0, 0, 0, 0))
    for d, name in enumerate(ORDER):
        for f, im in enumerate(resolve(tags, name)):
            out.paste(im, (f * fw, d * fh) if rows else ((d * frames + f) * fw, 0))
    return out

def read(ase):
    """An .aseprite's tagged frames {direction: frames}, or its one image if it has no tags."""
    with tempfile.TemporaryDirectory() as tmp:
        png, js = os.path.join(tmp, 's.png'), os.path.join(tmp, 's.json')
        subprocess.run([ASEPRITE, '-b', '--list-tags', ase, '--sheet', png, '--sheet-type', 'horizontal',
                        '--format', 'json-array', '--data', js], check=True, stdout=subprocess.DEVNULL)
        meta = json.load(open(js, encoding='utf-8'))
        strip = Image.open(png).convert('RGBA'); strip.load()
    if not meta['meta']['frameTags']: return strip
    box = [(f['frame']['x'], f['frame']['y'], f['frame']['x'] + f['frame']['w'], f['frame']['y'] + f['frame']['h']) for f in meta['frames']]
    tags = {t['name']: [strip.crop(box[i]) for i in range(t['from'], t['to'] + 1)] for t in meta['meta']['frameTags'] if t['name'] in ORDER}
    assert 'D' in tags, f'{ase}: no D tag (the front view every other direction falls back to)'
    assert len({len(v) for v in tags.values()}) == 1, f'{ase}: the direction tags differ in length: ' + ', '.join(f'{k} {len(v)}' for k, v in tags.items())
    return tags

def is_rows(png, cell_h):
    return os.path.exists(png) and Image.open(png).height >= 2 * cell_h

def export(ase):
    """Write the game's PNG beside the .aseprite; keeps the PNG's layout."""
    png = os.path.splitext(ase)[0] + '.png'
    got = read(ase)
    if isinstance(got, dict): got = sheet_of(got, is_rows(png, got['D'][0].height))
    got.save(png)
    return png

def pack(sheet, ase, frames, rows):
    """Write the .aseprite of a full sheet: only the directions that aren't
    another's copy or mirror, a tag each. Checked to export back pixel for pixel."""
    cells = cells_of(sheet, frames, rows)
    same = lambda a, b: all(x.tobytes() == y.tobytes() for x, y in zip(a, b))
    tags = {}
    for d in ORDER:
        if d == 'D' or not same(resolve(tags, d), cells[d]): tags[d] = cells[d]
    fw, fh = cells['D'][0].size
    strip = Image.new('RGBA', (fw * frames * len(tags), fh), (0, 0, 0, 0))
    for i, im in enumerate(f for d in tags for f in tags[d]): strip.paste(im, (i * fw, 0))
    with tempfile.TemporaryDirectory() as tmp:
        sp = os.path.join(tmp, 'strip.png'); strip.save(sp)
        subprocess.run([ASEPRITE, '-b', '--script-param', f'strip={sp}', '--script-param', f'fw={fw}',
                        '--script-param', 'tags=' + ','.join(f'{d}:{frames}' for d in tags), '--script-param', f'out={ase}',
                        '--script', os.path.join(HERE, 'pack_frames.lua')], check=True)
    assert sheet_of(read(ase), rows).tobytes() == sheet.tobytes(), f'{ase}: does not export back to its sheet'
    return list(tags)

# -- the rebuild guard --------------------------------------------------------
def _record(outdir): return os.path.join(outdir, 'built.json')
def _sha(png): return hashlib.sha1(open(png, 'rb').read()).hexdigest()
def _load(outdir): return json.load(open(_record(outdir))) if os.path.exists(_record(outdir)) else {}

def built(png):
    """Record the PNG a build just wrote."""
    outdir = os.path.dirname(png); rec = _load(outdir)
    rec[os.path.basename(png)] = _sha(png)
    json.dump(rec, open(_record(outdir), 'w'), indent=0, sort_keys=True)

def hand_edited(png):
    """True if this PNG was built, and has changed since (edited in Aseprite and exported)."""
    was = _load(os.path.dirname(png)).get(os.path.basename(png))
    return os.path.exists(png) and was is not None and _sha(png) != was

# -- every sheet the battle loads ---------------------------------------------
def battle_sheets():
    """[(png, frames, rows)] for every directional sheet in ENEMY_SHEETS (idle, flap, alt)."""
    src = open(os.path.join(ROOT, 'src', 'battle.cpp'), encoding='utf-8').read()
    table = src[src.index('ENEMY_SHEETS[] = {'):src.index('ENEMY_SHEET_COUNT')]
    out = []
    for row in re.findall(r'^\s*\{ ("assets/enemies/[^\n]*?) \},?\s*(?://[^\n]*)?$', table, re.M):
        f = [x.strip() for x in re.sub(r'\{[^}]*\}', 'LOOP', row).split(',')]   # path, loop, frames, rows, flap, alt, ...
        get = lambda i, default: f[i] if len(f) > i else default
        frames, rows = int(get(2, '3')), get(3, 'false') == 'true'
        path = lambda s: s.strip('"') if s.startswith('"') else None
        out.append((path(f[0]), frames, rows))
        if path(get(4, '')): out.append((path(f[4]), FLAP_FRAMES, False))
        if path(get(5, '')): out.append((path(f[5]), frames, rows))
    return out

def pack_all():
    for rel, frames, rows in battle_sheets():
        png = os.path.join(ROOT, rel); ase = os.path.splitext(png)[0] + '.aseprite'
        if not os.path.exists(png): print('MISSING', rel); continue
        sheet = Image.open(png).convert('RGBA')
        if (sheet.width % frames or sheet.height % 8) if rows else sheet.width % (8 * frames):
            print('SKIP (size does not divide into its frames)', rel, sheet.size, frames); continue
        if os.path.basename(png) not in _load(os.path.dirname(png)): built(png)
        note = ''
        if os.path.exists(ase) and os.path.getmtime(ase) > os.path.getmtime(png) + 2:   # drawn over by hand since the PNG was written
            got = read(ase)
            if isinstance(got, dict): got = sheet_of(got, rows)
            if got.size == sheet.size and got.tobytes() != sheet.tobytes():
                sheet = got; sheet.save(png); note = '  <- the .aseprite was newer: its edits kept, PNG updated'
        print(os.path.basename(ase), ' '.join(pack(sheet, ase, frames, rows)), note)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'export': print(export(sys.argv[2]))
    elif cmd == 'pack':
        png = sys.argv[2]
        print(pack(Image.open(png).convert('RGBA'), os.path.splitext(png)[0] + '.aseprite', int(sys.argv[3]), 'rows' in sys.argv[4:]))
    elif cmd == 'pack-all': pack_all()
    else: sys.exit(__doc__)
