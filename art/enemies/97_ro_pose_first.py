"""Enemy 97 Ro, first frame: checks and review. Front (D) only.

The Ro (the Mandaean books; abookofcreatures.com: "a hideous dragon with a winged body and a long scaly
tail"). Drawn from the user's reference (art/_backup/97_reference_20261016/ro_reference.webp: a maned dragon,
wolfish roaring head, bat wings with wrist claws, spiked tail with a leaf tip, big pale claws), in the old
sprite's red and gold palette (the user: "use the same color pallete"), standing on its back legs, facing the
player, jaws open in a roar, dark maroon mane. The old 130x81 giant frame and about the old front's size.

The drawing is art/enemies/97_ro_frame0_draft.aseprite, drawn with the pixel plugin's tools
(mcp__aseprite__*): each part outlined and filled on its own layer (wings, tail, legs, body, arms, mane, head)
so front parts cover back ones, then flattened, then details as pixels and strokes. It is never rebuilt from
text. Plugin traps: see art/enemies/64_dungavenhooter_pose_first.py.

    python art/enemies/97_ro_pose_first.py [SCRATCH]   # check the draft; write 97_review.png
"""
from pathlib import Path
import hashlib, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 130, 81                # the old sheet's frame
PAL = {'K': '000000',
       'R': '792727', 'r': 'b6433d', 's': '5d1e1f',   # hide: body, light, shade (and the wing membrane)
       'm': '531b1c', 'q': '421618',                  # mane, mane shade, the darker wing panel
       'c': '7c0a1b',                                 # tongue shade
       'z': '280e10',                                 # inside the mouth
       'g': 'd89830', 'G': 'f0bc3c', 'Y': 'fae488',   # belly, its light; the burning eyes
       'T': 'e8e0c0'}                                 # fangs, claws
DRAFT = HERE / '97_ro_frame0_draft.aseprite'
REFERENCE = ROOT / 'art/_backup/97_reference_20261016/ro_reference.webp'
bare = lambda p, c: c == 'T'                          # claw tips: bone, no outline of their own

ORIGINALS = sorted((ROOT / 'assets/enemies').glob('97_*')) + [ROOT / 'art/enemies' / n for n in
                                                             ('97_views.aseprite', '97_views.png', '97_ro.txt')]


def digest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ORIGINALS}


if __name__ == '__main__':
    scratch = Path(sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    before = digest()
    g = ff.read(DRAFT, PAL)
    for line in ff.checks(g, PAL, W, H, open_ok=bare, old='103 x 71 (columns 9-111, rows 10-80)', cap=224, max_colours=13):
        print(' ', line, flush=True)
    assert ff.pieces(set(g)) == 1, 'the drawing is in more than one piece'
    im = ff.image(g, PAL, W, H)
    assert ff.style_check(im, scratch, DRAFT.stem, tier='giant'), 'the bible checker fails'
    old = Image.open(ROOT / 'assets/enemies/97_ro.png').convert('RGBA').crop((0, 0, W, H))   # D, frame 0
    ref = Image.open(REFERENCE).convert('RGBA')
    ref = ref.resize((W, round(ref.height * W / ref.width)), Image.Resampling.LANCZOS)
    ff.review([('FRONT', im), ('reference', ref), ('was', old), ('PLAYER', ff.player()), ('shape', ff.silhouette(im))],
              HERE / '97_review.png')
    assert digest() == before, 'an original 97 file changed'
    print('originals unchanged:', ', '.join(before), flush=True)
