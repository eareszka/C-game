"""Enemy 64 Dungavenhooter, first frame: checks and review. Front (D) only.

The Dungavenhooter of the Maine logging camps (Fearsome Creatures): a squat crocodilian with no mouth that
lies by the trails, pounds its victims to vapour with the spiked bone ball on its tail and sniffs them up
through the nostrils on the end of its snout.

The drawing is art/enemies/64_dungavenhooter_frame0_draft.aseprite, edited in Aseprite by the user and with
the pixel plugin's tools (mcp__aseprite__*), never rebuilt from text. Pose from the user's reference
(art/_backup/64_reference_20261016/): head low on our left looking down at the player, the tail curling over
the back to a large spiked ball at the top left. Yellow slit eyes under heavy brows and two bone horns (the
user chose yellow eyes, a bible exception, and no mouth). Earlier states: the typed-rows version and the
user's 15:28 edit in art/_backup/64_user_edit_20261016/.

Plugin trap: its draw_pixels and cut_selection work in the cel's own coordinates, and Aseprite trims the cel
to the drawing's box on save; draw_circle and draw_line use canvas coordinates. Shift draw_pixels by the
drawing's top-left corner (and extend the box with a draw_line pixel first if drawing above or left of it).
Drawing a transparent colour does nothing, and cut_selection cut the wrong area: there is no reliable erase.

    python art/enemies/64_dungavenhooter_pose_first.py [SCRATCH]   # check the draft; write 64_review.png
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
       'D': '362a0e', 'M': '685018', 'L': '876a1f',   # hide: shade, body, light (the old sheet's own)
       'B': 'cebe82',                                 # throat, belly, claws
       'c': '595965', 'C': 'a4aaba',                  # bone ball, spikes, horns: shade, body
       'W': 'fcfcfc',                                 # their lit edges
       'P': 'ec8476',                                 # nostril rims
       'E': 'f0bc3c'}                                 # the eyes (the original sprite's yellow)
DRAFT = HERE / '64_dungavenhooter_frame0_draft.aseprite'
BACKUP = ROOT / 'art/_backup'
REFERENCE = BACKUP / '64_reference_20261016/dungavenhooter_reference.webp'
USER_EDIT = BACKUP / '64_user_edit_20261016/64_dungavenhooter_frame0_draft.aseprite'
# colour pixels allowed to meet empty space: claw tips, and the horns (thin bone, no outline of their own)
bare = lambda p, c: (c == 'B' and p[1] >= 60) or (c in 'CcW' and 34 <= p[1] <= 37 and p[0] <= 30)

ORIGINALS = sorted((ROOT / 'assets/enemies').glob('64_*')) + [ROOT / 'art/enemies' / n for n in
                                                             ('64_views.aseprite', '64_views.png', '64_dungavenhooter.txt')]


def digest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ORIGINALS}


if __name__ == '__main__':
    scratch = Path(sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    before = digest()
    g = ff.read(DRAFT, PAL)
    for line in ff.checks(g, PAL, W, H, open_ok=bare, old='42 x 26 (columns 26-67, rows 39-64)', cap=224, max_colours=9):
        print(' ', line, flush=True)
    assert ff.pieces(set(g)) == 1, 'the drawing is in more than one piece'
    im = ff.image(g, PAL, W, H)
    assert ff.style_check(im, scratch, DRAFT.stem, tier='giant'), 'the bible checker fails'
    old = Image.open(ROOT / 'assets/enemies/64_dungavenhooter.png').convert('RGBA').crop((0, 0, W, H))   # D, frame 0
    ref = Image.open(REFERENCE).convert('RGBA')
    ref = ref.resize((W, round(ref.height * W / ref.width)), Image.Resampling.LANCZOS)
    ff.review([('FRONT', im), ('your edit', ff.saved(USER_EDIT)), ('reference', ref), ('was', old),
               ('PLAYER', ff.player()), ('shape', ff.silhouette(im))], HERE / '64_review.png')
    assert digest() == before, 'an original 64 file changed'
    print('originals unchanged:', ', '.join(before), flush=True)
