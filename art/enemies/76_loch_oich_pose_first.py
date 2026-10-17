"""Enemy 76 Loch Oich Monster, first frame: checks and review. Front (D) only.

The Loch Oich Monster (Scotland): a dog's head on a Loch Ness body. A brown dog's head turned a little to our
right -- long floppy ear, pale boxy muzzle, black nose, a glinting eye -- on a long neck rising out of a
slippery eel body coiled low, the tail curling up on the left, a back coil and a fin. The old front's pose and
size (the user: "similar to its current front facing frame, but front only"), in the old 98x65 frame.

The drawing is art/enemies/76_loch_oich_frame0_draft.aseprite, drawn with the pixel plugin's tools
(mcp__aseprite__*): line art as polylines, flat fills, shade strokes, eyes and joins as pixels. It is never
rebuilt from text. Plugin traps: see art/enemies/64_dungavenhooter_pose_first.py.

    python art/enemies/76_loch_oich_pose_first.py [SCRATCH]   # check the draft; write 76_review.png
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
       'D': '633e1b', 'M': '94703d', 'L': 'c18a39',   # dog-brown hide: shade (ears, fin, back coil), body, sheen
       'B': 'd7a175',                                 # muzzle, throat, belly (the old sheet's own)
       'W': 'fcfcfc'}                                 # the eye's glint
DRAFT = HERE / '76_loch_oich_frame0_draft.aseprite'

ORIGINALS = sorted((ROOT / 'assets/enemies').glob('76_*')) + [ROOT / 'art/enemies' / n for n in
                                                             ('76_views.aseprite', '76_views.png', '76_loch_oich_monster.txt')]


def digest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ORIGINALS}


if __name__ == '__main__':
    scratch = Path(sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    before = digest()
    g = ff.read(DRAFT, PAL)
    for line in ff.checks(g, PAL, W, H, old='38 x 48 (columns 30-67, rows 11-58)', cap=70, max_colours=8):
        print(' ', line, flush=True)
    assert ff.pieces(set(g)) == 1, 'the drawing is in more than one piece'
    im = ff.image(g, PAL, W, H)
    assert ff.style_check(im, scratch, DRAFT.stem, tier='big'), 'the bible checker fails'
    old = Image.open(ROOT / 'assets/enemies/76_loch_oich_monster.png').convert('RGBA').crop((0, 0, W, H))   # D, frame 0
    ff.review([('FRONT', im), ('was', old), ('PLAYER', ff.player()), ('shape', ff.silhouette(im))],
              HERE / '76_review.png')
    assert digest() == before, 'an original 76 file changed'
    print('originals unchanged:', ', '.join(before), flush=True)
