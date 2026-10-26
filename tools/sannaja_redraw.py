"""Sannaja's turn redrawn whole, frame by frame, by PixelLab.

    python tools/sannaja_redraw.py [--generate] [--from K]

The 18 frames tools/sannaja_turn.py builds out of moved parts are only pose guides here: each is
sent to PixelLab's edit route as the layout, with the previous accepted frame as the style
reference (frame 0: the legs' approved frame), and comes back as one coherent creature. Each is
cleaned to the palette, put through the sprite bible's lines, and accepted only if its feet, ground
line and bounds match its guide -- else retried once, else the run stops for a person to look.
Paid calls only with --generate.
"""
import json, os, sys, time
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import enemy_sheet
import pixellab_enemy as pe
import sannaja_turn as st

D = os.path.join(ROOT, 'art/enemies/pixellab/52_sannaja')
W, H = 354, 225
N = 18
JOB = os.path.join(D, 'job_turn3.json')
PROMPT = """Redraw this frame of enemy 52 Sannaja, the biggest monster and a final boss, as one whole, coherent creature, exactly 354x225 native pixels, transparent background, in exactly this pose and placement: the supplied frame is a rough guide that only shows where everything is. A colossal living mountain of grey rock bound by red flesh, walking backwards to the right on cracked stone-pillar legs; as it backs away the front end of its body comes into view at the left. Its legs, body and head are one connected animal: far legs behind near legs, the rock underside of its body over the tops of the legs, a band of red flesh wrapping each leg where it meets the body, the long neck of red flesh over stone vertebrae in front of the body. Keep exactly the legs the guide shows, each where the guide has it: no extra legs and none missing; a lifted leg stays raised with its foot off the ground.{head} Match the reference frame's design, colours and lighting exactly, so this frame follows it in an animation.
Draw it like the reference: big simple flat-toned shapes, dark/mid/light ramps placed by form, a one-pixel black outline, thin black separation lines where parts overlap, no gradients, dithering, hatching or texture. Use only the reference's colours."""
HEAD = " At the upper left its mouthless red head hangs on the neck, dark hair swept back like a flame, its eyes shut under heavy red lids."


def feet(img):
    """Legs in view: column runs of rock across a band through the middle of the legs (rows 120-150;
    the body is above it, the head is red and dark)."""
    px = img.load()
    cols = sorted({x for y in range(120, 150) for x in range(img.width) if px[x, y][3] and px[x, y][:3] in st.ROCK})
    runs, prev = 0, None
    for x in cols:
        if prev is None or x > prev + 3:
            runs += 1
        prev = x
    return runs


def guides():
    """18 guides: frame 0 the exact legs frame; 1-10 PixelLab's half-size walk (one whole creature,
    walk-back-animate-result.json) scaled 2x and carried right; 11 the exact legs frame at the end of the
    walk; 12-17 the head lowering from the built turn (its legs exact, the head and neck one piece)."""
    turn_built = enemy_sheet.cells_of(Image.open(os.path.join(D, 'turn_sheet.png')).convert('RGBA'), N, True)['D']
    legs0 = enemy_sheet.cells_of(Image.open(os.path.join(ROOT, 'assets/enemies/redraws/52_sannaja.png')).convert('RGBA'), 8, True)['D'][0]
    legs0.save(os.path.join(D, 'legs0_frame0_clean.png'))
    half_in = legs0.resize((177, 113), Image.NEAREST)
    origin = pe.roomy(half_in, os.path.join(D, 'walk_half_roomy.png'))
    walk = pe.pngs(json.load(open(os.path.join(D, 'walk-half-animate-result.json'), encoding='utf-8-sig')))
    out = []
    for k in range(N):
        if k == 0:
            g = legs0
        elif k <= 10:
            half = Image.open(walk[k]).convert('RGBA')
            big = half.resize((half.width * 2, half.height * 2), Image.NEAREST)
            g = Image.new('RGBA', (W, H))
            g.alpha_composite(big.crop((-2 * origin[0], -2 * origin[1], -2 * origin[0] + W, -2 * origin[1] + H)))
            shifted = Image.new('RGBA', (W, H)); dx = round(st.WALK * k / 11)
            shifted.alpha_composite(g.crop((0, 0, W - dx, H)), (dx, 0)); g = shifted
        else:
            g = turn_built[k] if k >= 12 else turn_built[11]
        g.save(os.path.join(D, f'source_t{k:02}.png')); g.save(os.path.join(D, f'guide_t{k:02}.png'))
        out.append(g)
    return out


def job(turn):
    sheets, prompts = {}, {}
    for k, g in enumerate(turn):
        key = f't{k:02}'
        head = k >= 13                                   # the head is in view from the turn's 14th frame (the 13th hides it above)
        with open(os.path.join(D, f'prompt_{key}.txt'), 'w', encoding='utf-8') as fh:
            fh.write(PROMPT.format(head=HEAD if head else ''))
        prompts[key] = f'prompt_{key}.txt'
        sheets[key] = {'png': 'assets/enemies/redraws/52_sannaja.png', 'frames': 8, 'rows': True, 'ms': 133,
                       'views': ['D'], 'make': 'none', 'from': 'legs0' if k == 0 else f't{k - 1:02}'}
    sheets['legs0'] = sheets['t00'] | {'from': None}
    json.dump({'id': 52, 'name': '52-sannaja', 'dir': 'art/enemies/pixellab/52_sannaja', 'description': '',
               'prompts': prompts, 'sheets': sheets}, open(JOB, 'w'), indent=2)


def clean(key, palette):
    draft = Image.open(os.path.join(D, f'{key}_frame0_draft.png')).convert('RGBA')
    c = pe.despeckled(pe.to_palette(draft, palette), 20)
    c = st.outline(st.bible(st.outline(c)))
    c.save(os.path.join(D, f'{key}_frame0_clean.png'))
    return c


def align(frame, guide):
    """PixelLab sometimes places the whole creature a few pixels off its guide: move the whole frame
    (never a part) so its left edge and ground line sit where the guide's do."""
    fb, gb = frame.getbbox(), guide.getbbox()
    dx, dy = gb[0] - fb[0], gb[3] - fb[3]
    if not dx and not dy:
        return frame
    out = Image.new('RGBA', frame.size)
    out.alpha_composite(frame.crop((max(0, -dx), max(0, -dy), frame.width, frame.height)), (max(0, dx), max(0, dy)))
    return st.outline(out)


def material(c):
    if not c[3]:
        return 0
    return 2 if c[:3] in st.FLESH else 1        # rock, its lines and the rest count together


def similarity(frame, guide):
    """How much of the creature is still where the guide put rock and flesh (accepted frames: about 0.97)."""
    fp, gp = frame.load(), guide.load(); same = tot = 0
    for y in range(frame.height):
        for x in range(frame.width):
            a, b = material(fp[x, y]), material(gp[x, y])
            if a or b:
                tot += 1; same += a == b
    return same / tot


STRICT = """Keep the supplied frame of enemy 52 Sannaja exactly as it is: the same 354x225 pixels, every leg, foot, flesh band and the body exactly where and how the guide draws them, including the part of a leg cut off at the right edge. Change no shapes and invent nothing: no faces, no drapes, no new parts. Only clean it into crisp pixel art in the style and colours of the reference frame: one-pixel black outlines, flat dark/mid/light ramps, thin separation lines, no gradients, dithering or texture."""


def accept(frame, guide):
    n, off, ib, iso, o = bible_numbers(frame)
    fb, gb = frame.getbbox(), guide.getbbox()
    checks = {'colours<=9': n <= 9, 'on palette': off == 0, 'outline': o > 0.999, 'interior 9.35-14.49': 9.35 <= ib <= 14.49,
              'isolated<1%': iso < 1.0, 'feet': feet(frame) == feet(guide), 'ground': abs(fb[3] - gb[3]) <= 2,
              'bounds': all(abs(a - b) <= 6 for a, b in zip(fb, gb)), 'similar>=0.93': similarity(frame, guide) >= 0.93}
    return all(checks.values()), checks, (n, ib, iso, feet(frame), feet(guide))


def bible_numbers(im):
    sys.path.insert(0, os.path.join(ROOT, 'art/direction'))
    import fcremap
    px = im.load(); W, H = im.size
    op = [(x, y) for y in range(H) for x in range(W) if px[x, y][3]]
    e = [(x, y) for x, y in op if any(0 <= x + dx < W and 0 <= y + dy < H and not px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    black = sum(px[q][:3] == (0, 0, 0) for q in op); eb = sum(px[q][:3] == (0, 0, 0) for q in e)
    cols = {px[q][:3] for q in op}
    iso = sum(1 for x, y in op if px[x, y][:3] != (0, 0, 0) and all(
        0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] != px[x, y][:3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
    return len(cols), sum(c not in fcremap.PALETTE for c in cols), 100 * (black - eb) / len(op), 100 * iso / len(op), eb / len(e)


def main(argv):
    generate = '--generate' in argv
    start = int(argv[argv.index('--from') + 1]) if '--from' in argv else 0
    turn = guides()
    job(turn)
    j = pe.Job(JOB)
    palette = sorted({p[:3] for f in (turn[0], turn[N - 1]) for p in f.getdata() if p[3]})   # the approved art's own colours (the guides carry raw ones)
    log = []
    for k in range(N):                                   # the ends and the head frames are exact: kept as they are
        if k == 0 or k >= 11:
            turn[k].save(os.path.join(D, f't{k:02}_frame0_clean.png'))
    first_try = int(argv[argv.index('--try') + 1]) if '--try' in argv else 1   # resume past an attempt that already ran
    for k in range(max(start, 1), 11):
        key = f't{k:02}'
        tries = [first_try + i for i in range(3)] if k == start else [1, 2, 3]   # up to three tries a frame
        for attempt in tries:
            if True:                                      # every try keeps the guide's shapes outright (the user)
                with open(os.path.join(D, f'prompt_{key}.txt'), 'w', encoding='utf-8') as fh:
                    fh.write(STRICT)
            try:
                pe.edit(j, key, generate, attempt)
            except AssertionError as err:
                tag = '' if attempt == 1 else f'-try{attempt}'
                stderr = os.path.join(D, f'{key}-edit{tag}-stderr.txt')
                if os.path.exists(stderr) and 'could not reach PixelLab' in open(stderr, encoding='utf-8').read():
                    print(key, 'try', attempt, 'network error -- waiting 30 s', flush=True)
                    time.sleep(30)
                    continue                                  # the next attempt number; nothing was returned to collect
                raise
            if not generate:
                break
            frame = align(clean(key, palette), turn[k])
            frame.save(os.path.join(D, f'{key}_frame0_clean.png'))
            ok, checks, nums = accept(frame, turn[k])
            print(key, 'try', attempt, 'ok' if ok else 'FAIL', nums, [c for c, v in checks.items() if not v], flush=True)
            log.append({'frame': key, 'try': attempt, 'ok': ok, 'checks': checks})
            if ok:
                break
        else:
            json.dump(log, open(os.path.join(D, 'redraw_log.json'), 'w'), indent=1)
            raise SystemExit(f'{key}: failed twice -- stopping for review')
    json.dump(log, open(os.path.join(D, 'redraw_log.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
