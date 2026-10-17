"""Enemy 77 Hoga, first frame: checks and review. Front (D) only.

The Hoga of Lake Metztitlan (Mexico): half ox, half fish. A bull's head with pale crescent horns and a broad
tan muzzle, looking down at the player, on a slate-blue fish body with a pale belly, a gill line, a forked
tail, a dorsal fin and a near fin. It floats. The old design and about the old front's size (the user), in the
old 98x65 frame.

The drawing is art/enemies/77_hoga_frame0_draft.aseprite, drawn with the pixel plugin's tools
(mcp__aseprite__*): line art as polylines, flat fills, shade strokes, eyes and joins as pixels. It is never
rebuilt from text. Plugin traps: see art/enemies/64_dungavenhooter_pose_first.py.

    python art/enemies/77_hoga_pose_first.py [SCRATCH]   # check the draft; write 77_review.png
"""
from pathlib import Path
import hashlib, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 98, 65                 # the old sheet's frame
PAL = {'K': '000000',
       'D': '37387b', 'M': '375a94', 'L': '3e91cc',   # fish: shade, body, light (the old sheet's own)
       'B': 'a4aaba',                                 # belly
       'd': '583518', 'h': '8d6b4f',                  # ox hide: shade, body
       'T': 'd7a175',                                 # muzzle, forelock, horn shade
       'H': 'e8e0c0'}                                 # horns, eye whites
DRAFT = HERE / '77_hoga_frame0_draft.aseprite'

ORIGINALS = sorted((ROOT / 'assets/enemies').glob('77_*')) + [ROOT / 'art/enemies' / n for n in
                                                             ('77_views.aseprite', '77_views.png', '77_hoga.txt')]


def digest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ORIGINALS}


if __name__ == '__main__':
    scratch = Path(sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    before = digest()
    g = ff.read(DRAFT, PAL)
    for line in ff.checks(g, PAL, W, H, old='42 x 34 (columns 32-74, rows 22-56)', cap=70, max_colours=8):
        print(' ', line, flush=True)
    assert ff.pieces(set(g)) == 1, 'the drawing is in more than one piece'
    im = ff.image(g, PAL, W, H)
    assert ff.style_check(im, scratch, DRAFT.stem, tier='big'), 'the bible checker fails'
    old = Image.open(ROOT / 'assets/enemies/77_hoga.png').convert('RGBA').crop((0, 0, W, H))   # D, frame 0
    ff.review([('FRONT', im), ('was', old), ('PLAYER', ff.player()), ('shape', ff.silhouette(im))],
              HERE / '77_review.png')
    assert digest() == before, 'an original 77 file changed'
    print('originals unchanged:', ', '.join(before), flush=True)
