"""One massive Aseprite sheet of all 101 enemies, for the user's final hand edits. The picks that keep their game sprite are on it to see, but an edit to one is saved aside, because no job holds it. It fills in as drawings finish. Nothing goes in the game.

    python -B tools/sprite_agent/edit_sheet.py make      # a new sheet, opened in Aseprite
    python -B tools/sprite_agent/edit_sheet.py open      # opens the newest sheet again
    python -B tools/sprite_agent/edit_sheet.py update    # one pass: saved edits go into each sprite.png, new drawings go on the sheet
    python -B tools/sprite_agent/edit_sheet.py watch     # the same pass every 30 seconds, until killed

Each sheet is art/enemies/nes/_sheets/edit_sheet_NN.aseprite, at real size, by tier and smallest first. Every enemy has its
cell from the start, sized for its target, so cells never move and drawings just fill in. Its layers:
  sprites   where to edit. A cell has room to grow, so an edit can go past the sprite's old edges.
  guides    locked. The cell lines and the names.
  black     locked and hidden. Turn it on to see the sprites as the game shows them.

sprite.png stays the truth, because everything else reads it. A pass finds a saved sheet by its date and looks only at
cells that differ from what the sheet last held (NN_base.png). An edited cell becomes that enemy's sprite.png, cropped to
its pixels, and the earlier one is kept in art/enemies/nes/_old/. The checker then runs on it, and what it says is printed
but changes nothing. If sprite.png changed after the sheet last saw it, the edit is saved beside the sheet instead of
overwriting that. Erasing a whole cell doesn't delete a sprite: the pass puts it back.

Aseprite doesn't notice a file changing on disk, so two things keep an open sheet right. A window opened by this tool runs
edit_sheet_open.lua, which paints each new drawing in from the sheet's inbox folder. And a save from a window that's behind
loses nothing, because the pass takes its edits and then puts back whatever that window didn't have.

Older sheets keep their own maps, so saving one still works, but only the newest one gets new drawings. run_tier.py never
redraws a sprite that was edited by hand. build_audit.py runs a pass first, so the audit always shows saved edits.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

ASEPRITE = r'C:\Program Files\Aseprite\Aseprite.exe'
NES = os.path.join(ROOT, 'art', 'enemies', 'nes')
SHEETS = os.path.join(NES, '_sheets')
BUILD_LUA = os.path.join(HERE, 'edit_sheet.lua')
OPEN_LUA = os.path.join(HERE, 'edit_sheet_open.lua')

WIDTH = 1400        # sheet width to wrap at
MARGIN = 8          # room around each sprite, for edits that go past its edges
ROOM = 1.1          # a cell's room for a sprite, against its target: the most a sprite can be and still fit its tier
LABEL = 13          # the name strip under each sprite
HEAD = 16           # the tier's title strip
POLL = 30           # seconds between passes when watching
STALE_LOCK = 600    # a lock this old is left over from a killed pass

_hash_cache = {}
_not_placed = set()


def clean(im):
    """RGBA with fully clear pixels all alike, because a clear pixel's colour means nothing and Aseprite may not keep it."""
    im = im.convert('RGBA')
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), im.getchannel('A').point(lambda a: 255 if a else 0))
    return out


def trimmed(im):
    im = clean(im)
    box = im.getbbox()
    return im.crop(box) if box else None


def pixel_hash(im):
    """The drawing itself: the same pixels give the same hash, however the PNG was saved."""
    return hashlib.sha1(('%dx%d' % im.size).encode() + im.tobytes()).hexdigest()


def file_hash(path):
    st = os.stat(path)
    key = (st.st_mtime_ns, st.st_size)
    if path not in _hash_cache or _hash_cache[path][0] != key:
        sprite = trimmed(Image.open(path))
        _hash_cache[path] = (key, pixel_hash(sprite) if sprite else None)
    return _hash_cache[path][1]


def job_folder(i):
    paths = [p for p in glob.glob(os.path.join(NES, '%02d_*' % i)) if os.path.isdir(p)]
    return paths[0] if paths else None


def is_finished(folder):
    """A folder with no agent_reply.txt is still being drawn."""
    return bool(folder) and os.path.exists(os.path.join(folder, 'agent_reply.txt')) and os.path.exists(os.path.join(folder, 'sprite.png'))


def usable(i, folder, sprite):
    """Finished, and either edited by hand or the right size. One that isn't is due to be redrawn, so an edit would be thrown away."""
    import run_tier
    return run_tier.hand_edited(folder) or run_tier.es.nes_fits(i, max(sprite.size))


def lay_out(ids, sprites, names):
    """Cells by tier, smallest first, on shelves with their sprites standing on one line. Returns cells, tier titles, size."""
    import run_tier
    es = run_tier.es
    tiers = es.tiers()
    font = ImageFont.truetype('arial.ttf', 11)
    cells, heads, y, wide = {}, [], 0, 0
    for tier in es.NES_SIDE:
        group = sorted((i for i in ids if tiers[i] == tier), key=lambda i: (es.nes_target(i)[0], i))
        if not group:
            continue
        lo, hi = es.NES_SIDE[tier]
        heads.append((tier, '%d px' % lo if lo == hi else '%d to %d px' % (lo, hi), y))
        y += HEAD
        room = {i: max(math.ceil(es.nes_target(i)[0] * ROOM), max(sprites[i].size) if i in sprites else 0) for i in group}
        rows, row, x = [], [], 0
        for i in group:
            label = '%d %s' % (i, names[i].title()[:18])
            w = max(room[i] + MARGIN * 2, int(font.getlength(label)) + 6)
            if row and x + w > WIDTH:
                rows.append(row)
                row, x = [], 0
            row.append((i, x, w, label))
            x += w
        rows.append(row)
        for row in rows:
            h = max(room[i] for i, _, _, _ in row) + MARGIN * 2 + LABEL
            for i, x, w, label in row:
                cells[str(i)] = dict(x=x, y=y, w=w, h=h, label=label, hash=None)
                wide = max(wide, x + w)
            y += h
    return cells, heads, (wide, y)


def cell_image(c, sprite):
    """A cell's sprites-layer picture: the sprite centred, standing just above its name."""
    out = Image.new('RGBA', (c['w'], c['h']), (0, 0, 0, 0))
    out.paste(sprite, ((c['w'] - sprite.width) // 2, max(0, c['h'] - LABEL - MARGIN - sprite.height)))
    return out


def guides_image(cells, heads, size):
    """Cell lines and white names on black plates, which read on Aseprite's checker and on the black layer alike."""
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.fontmode = '1'
    font = ImageFont.truetype('arial.ttf', 11)
    title = ImageFont.truetype('arialbd.ttf', 12)
    for c in cells.values():
        d.rectangle((c['x'], c['y'], c['x'] + c['w'] - 1, c['y'] + c['h'] - 1), outline=(96, 96, 108, 255))
        d.rectangle((c['x'] + 1, c['y'] + c['h'] - LABEL, c['x'] + c['w'] - 2, c['y'] + c['h'] - 2), fill=(0, 0, 0, 255))
        d.text((c['x'] + 3, c['y'] + c['h'] - LABEL - 1), c['label'], fill=(255, 255, 255, 255), font=font)
    for tier, sizes, y in heads:
        d.rectangle((0, y, size[0] - 1, y + HEAD - 1), fill=(38, 38, 46, 255))
        d.text((4, y + 1), '%s  %s' % (tier, sizes), fill=(255, 255, 255, 255), font=title)
    return out


def colours_image():
    """Every colour the agents are given, up to Aseprite's 256, so the palette panel offers those. Taken from the drawings so far and the jobs' palette."""
    seen = {}
    for png in sorted(glob.glob(os.path.join(NES, '[0-9]*', 'sprite.png'))):
        raw = clean(Image.open(png)).tobytes()
        for k in range(0, len(raw), 4):
            if raw[k + 3]:
                seen.setdefault(tuple(raw[k:k + 3]))
    colours = list(seen)[:256]
    out = Image.new('RGBA', (len(colours), 1))
    out.putdata([c + (255,) for c in colours])
    return out, len(seen)


def aseprite(*args):
    return subprocess.run([ASEPRITE, '-b', *args], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)


def sheet_maps():
    return sorted(glob.glob(os.path.join(SHEETS, 'edit_sheet_*.json')))


def inbox_of(stem):
    return stem + '_inbox'


def open_window(stem):
    with open(stem + '.json', encoding='utf-8') as f:
        seq = json.load(f).get('seq', 0)
    subprocess.Popen([ASEPRITE, stem + '.aseprite', '--script-param', 'inbox=' + inbox_of(stem), '--script-param', 'seq=%d' % seq, '--script', OPEN_LUA],
                     cwd=ROOT, close_fds=True, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)


def make(show=True):
    update_all()
    import run_tier
    es = run_tier.es
    os.chdir(ROOT)
    tiers = es.tiers()
    ids = list(range(len(tiers)))
    picks = [i for i in es.NES_ANCHORS if i not in es.NES_RESIZE]
    game_sheets = es.sheets()
    sprites = {}
    for i in picks:
        s = game_sheets[i]
        sprites[i] = trimmed(es.first_frame(s['path'], s['frames'], s['rows'])[0])
    for i in ids:
        folder = job_folder(i)
        if i not in picks and is_finished(folder):
            sprite = trimmed(Image.open(os.path.join(folder, 'sprite.png')))
            if sprite is not None and usable(i, folder, sprite):
                sprites[i] = sprite
    cells, heads, size = lay_out(ids, sprites, es.names())
    for i in picks:
        cells[str(i)]['pick'] = True
    layer = Image.new('RGBA', size, (0, 0, 0, 0))
    for i, sprite in sprites.items():
        c = cells[str(i)]
        c['hash'] = pixel_hash(sprite)
        layer.paste(cell_image(c, sprite), (c['x'], c['y']))
    os.makedirs(SHEETS, exist_ok=True)
    numbers = [int(os.path.basename(p)[len('edit_sheet_'):-len('.json')]) for p in sheet_maps()]
    stem = os.path.join(SHEETS, 'edit_sheet_%02d' % (max(numbers, default=0) + 1))
    os.makedirs(inbox_of(stem), exist_ok=True)
    work = tempfile.mkdtemp(prefix='edit_sheet_')
    try:
        files = dict(sprites=os.path.join(work, 'sprites.png'), guides=os.path.join(work, 'guides.png'),
                     black=os.path.join(work, 'black.png'), colours=os.path.join(work, 'colours.png'))
        layer.save(files['sprites'])
        guides_image(cells, heads, size).save(files['guides'])
        Image.new('RGBA', size, (0, 0, 0, 255)).save(files['black'])
        colours, total = colours_image()
        colours.save(files['colours'])
        args = ['--script-param', 'mode=build']
        for k, v in dict(files, out=stem + '.aseprite').items():
            args += ['--script-param', '%s=%s' % (k, v)]
        run = aseprite(*args, '--script', BUILD_LUA)
        if not os.path.exists(stem + '.aseprite'):
            raise SystemExit('Aseprite made no sheet:\n%s%s' % (run.stdout, run.stderr))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    layer.save(stem + '_base.png')
    with open(stem + '.json', 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(cells=cells, size=size, seq=0, taken=os.path.getmtime(stem + '.aseprite')), f, indent=0)
    print('%s.aseprite: %d cells, %d drawn so far, %dx%d px, %d colours.' % (stem, len(cells), len(sprites), size[0], size[1], total))
    if show:
        open_window(stem)
    return stem


def export_edits(stem):
    """The sheet as saved, without the guides. Any layer the user added counts, if it's showing."""
    work = tempfile.mkdtemp(prefix='edit_sheet_')
    try:
        out = os.path.join(work, 'flat.png')
        run = aseprite('--ignore-layer', 'guides', '--ignore-layer', 'black', '--frame-range', '0,0', stem + '.aseprite', '--save-as', out)
        if not os.path.exists(out):
            raise RuntimeError('Aseprite could not export %s: %s%s' % (stem, run.stdout, run.stderr))
        return clean(Image.open(out))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def paint(stem, base):
    """Makes the saved sheet's sprites layer match base. The user's other layers are left alone."""
    work = tempfile.mkdtemp(prefix='edit_sheet_')
    try:
        path = os.path.join(work, 'sprites.png')
        base.save(path)
        run = aseprite('--script-param', 'mode=fill', '--script-param', 'sheet=' + stem + '.aseprite', '--script-param', 'sprites=' + path, '--script', BUILD_LUA)
        if run.stdout.strip() or run.stderr.strip():
            say('%s: %s%s' % (os.path.basename(stem), run.stdout, run.stderr))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def differing(a, b):
    return int((np.asarray(a) != np.asarray(b)).any(axis=2).sum())


def say(text):
    print('%s %s' % (time.strftime('%H:%M:%S'), text), flush=True)


def run_checker(i):
    check = subprocess.run([sys.executable, '-B', os.path.join(HERE, 'check.py'), str(i)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    lines = check.stdout.strip().splitlines()
    notes = [x for x in lines if x.startswith(('FAIL', 'LOOK'))]
    return lines[0] if lines else 'The checker printed nothing.', notes


def take_cells(sheet, now, base, stem, check):
    """Edits saved on this sheet go into each sprite.png. Returns the ids changed."""
    changed = []
    for key, c in sorted(sheet['cells'].items(), key=lambda kv: int(kv[0])):
        i, rect = int(key), (c['x'], c['y'], c['x'] + c['w'], c['y'] + c['h'])
        part, old = now.crop(rect), base.crop(rect)
        if part.tobytes() == old.tobytes():
            continue
        new = trimmed(part)
        if new is None:             # a window that's behind has nothing here yet, or the cell was erased: the sprite stays
            continue
        if pixel_hash(new) in c.get('replaced', []):        # a window that's behind still shows the version a touch-up replaced
            continue
        folder = job_folder(i)
        if c.get('pick'):
            keep = os.path.join(SHEETS, 'not_taken_pick_%d_%s.png' % (i, time.strftime('%Y%m%d_%H%M%S')))
            new.save(keep)
            say('%d: not taken, because it is one of your picks and keeps its game sprite. Your edit is saved at %s' % (i, keep))
            continue
        if not c.get('hash') or not is_finished(folder):
            say('%d: not taken, because it has no finished drawing yet. Its cell will be overwritten when it does.' % i)
            continue
        sprite_path = os.path.join(folder, 'sprite.png')
        if file_hash(sprite_path) != c['hash']:
            keep = os.path.join(SHEETS, 'not_taken_%s_%s.png' % (os.path.basename(folder), time.strftime('%Y%m%d_%H%M%S')))
            new.save(keep)
            say('%d: not taken, because its sprite.png changed after the sheet last saw it. Your edit is saved at %s' % (i, keep))
            continue
        old_dir = os.path.join(NES, '_old')
        os.makedirs(old_dir, exist_ok=True)
        shutil.copyfile(sprite_path, os.path.join(old_dir, '%s_before_sheet_edit_%s.png' % (os.path.basename(folder), time.strftime('%Y%m%d_%H%M%S'))))
        new.save(sprite_path)
        c['hash'] = pixel_hash(new)
        base.paste(part, rect[:2])
        changed.append(i)
        say('%d: took the edit, %d pixels changed.' % (i, differing(part, old)))
        if check:
            first, notes = run_checker(i)
            say('   %s' % first)
            for note in notes:
                say('   %s' % note)
    blank_now, blank_base = now.copy(), base.copy()
    for c in sheet['cells'].values():
        rect = (c['x'], c['y'], c['x'] + c['w'], c['y'] + c['h'])
        blank_now.paste((0, 0, 0, 0), rect)
        blank_base.paste((0, 0, 0, 0), rect)
    stray = differing(blank_now, blank_base)
    if stray:
        say('%s: %d edited pixels are outside every cell, so they were ignored.' % (os.path.basename(stem), stray))
    return changed


def add_drawings(sheet, base, stem):
    """Puts each finished drawing the sheet doesn't have yet in its cell, and in the inbox for an open window. Returns the ids added."""
    added = []
    for key, c in sorted(sheet['cells'].items(), key=lambda kv: int(kv[0])):
        i = int(key)
        folder = job_folder(i)
        if c.get('pick') or not is_finished(folder):
            continue
        png = os.path.join(folder, 'sprite.png')
        h = file_hash(png)
        if h is None or h == c.get('hash') or (i, h) in _not_placed:
            continue
        sprite = trimmed(Image.open(png))
        if not usable(i, folder, sprite):
            _not_placed.add((i, h))
            continue
        if sprite.width > c['w'] or sprite.height > c['h'] - LABEL:
            say('%d: %dx%d is too big for its cell on %s, so it was left off. A new sheet (make) will fit it.' % (i, sprite.width, sprite.height, os.path.basename(stem)))
            _not_placed.add((i, h))
            continue
        if c.get('hash'):
            c.setdefault('replaced', []).append(c['hash'])
        c['hash'] = h
        cell = cell_image(c, sprite)
        base.paste(cell, (c['x'], c['y']))
        sheet['seq'] = sheet.get('seq', 0) + 1
        os.makedirs(inbox_of(stem), exist_ok=True)
        cell.save(os.path.join(inbox_of(stem), '%06d_%d_%d_%d_%d.png' % (sheet['seq'], c['x'], c['y'], c['w'], c['h'])))
        added.append(i)
    return added


def process(map_path, newest, check):
    stem = map_path[:-len('.json')]
    with open(map_path, encoding='utf-8') as f:
        sheet = json.load(f)
    path = stem + '.aseprite'
    saved = os.path.getmtime(path)
    changed, now = [], None
    base = clean(Image.open(stem + '_base.png'))
    if saved != sheet['taken']:
        now = export_edits(stem)
        if now.size != base.size:
            say('%s: its canvas changed size, so the cells no longer line up. Nothing was taken from it.' % os.path.basename(stem))
            sheet['taken'] = saved
            with open(map_path, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(sheet, f, indent=0)
            return [], []
        changed = take_cells(sheet, now, base, stem, check)
    added = add_drawings(sheet, base, stem) if newest else []
    behind = newest and (bool(added) or (now is not None and now.tobytes() != base.tobytes()))
    if not (now is not None or added):
        return [], []
    base.save(stem + '_base.png')
    if behind and os.path.getmtime(path) == saved:      # if the user saved again just now, leave it for the next pass
        paint(stem, base)
        saved = os.path.getmtime(path)
    if os.path.getmtime(path) == saved:
        sheet['taken'] = saved
    with open(map_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(sheet, f, indent=0)
    if added:
        say('Added to %s: %s' % (os.path.basename(stem), ' '.join(map(str, added))))
    return changed, added


def update_all(check=True):
    """One pass over every sheet, oldest first, so an edit on an old sheet reaches the newest in the same pass. Returns (ids edited, ids added)."""
    if not os.path.isdir(SHEETS):
        return [], []
    lock = os.path.join(SHEETS, 'pass.lock')
    if os.path.exists(lock) and time.time() - os.path.getmtime(lock) > STALE_LOCK:
        os.remove(lock)
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL))
    except FileExistsError:
        return [], []               # another pass is running, and it will do the same work
    try:
        edited, added = [], []
        maps = sheet_maps()
        for map_path in maps:
            e, a = process(map_path, map_path == maps[-1], check)
            edited += e
            added += a
        return edited, added
    finally:
        os.remove(lock)


def watch():
    say('Watching the edit sheets every %d seconds.' % POLL)
    while True:
        try:
            update_all()
        except Exception as e:      # a file caught mid-write, usually. The next pass tries again.
            say('%s: %s' % (type(e).__name__, e))
        time.sleep(POLL)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('what', choices=['make', 'open', 'update', 'watch'])
    ap.add_argument('--no-window', action='store_true', help='make: build the sheet without opening it')
    args = ap.parse_args()
    os.chdir(ROOT)
    if args.what == 'make':
        make(not args.no_window)
    elif args.what == 'open':
        maps = sheet_maps()
        if not maps:
            raise SystemExit('No sheet yet. Make one: python -B tools/sprite_agent/edit_sheet.py make')
        update_all()
        open_window(maps[-1][:-len('.json')])
    elif args.what == 'watch':
        watch()
    else:
        edited, added = update_all()
        print('Edits taken: %s. Drawings added: %s.' % (' '.join(map(str, edited)) or 'none', ' '.join(map(str, added)) or 'none'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
