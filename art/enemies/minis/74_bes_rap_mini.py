"""74 Bes Rap's map mini: the Jah Hut pig spirit that lives at the roots of the pokok ara tree and "blows its
saliva" at whoever gathers its fruit, so they sicken "foaming at the mouth" -- crouched like a gargoyle, waiting,
then springing at you with its jaw dropped and its arms flung out, at the player's scale, four views, two frames
(tools/minis.py).

Its battle sheet has one view, its front. Through PixelLab (art/enemies/pixellab/74_bes_rap/mini, pixellab-out/
74-mini, four generations): eight rotations of its battle front, then its front, back and side each given a
pounce -- gathering low on its haunches, then springing, jaw open, arms out. Shrunk to 20 px they lost its face,
teeth and spikes and scattered its shade into specks, so its grids are drawn by hand from them (G): its ears, its
eyes, its long snout with its pale tip, its bared teeth, the line of pale spikes down its back, its thin arms
apart from its body, its big dark haunches; one black outline round it all, and between its parts. Two frames:
crouched, then in the spring -- arms flung out, jaw dropped, legs stretched -- lifted LIFT px off the ground. The
right view is the left mirrored.
20 px tall: its battle height (55 px) at the minis' one scale, 28/79. Three of its battle colours and black, one
ramp: its pink, its dark red (its haunches, its shade), its pale pink (its snout's tip, its teeth, the grey spikes
down its back; high and sparse).

Its chase: the pounce (chase_speed() and chase_frame(), src/main.cpp) -- crouched still at the roots, then a leap.

    python art/enemies/minis/74_bes_rap_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'L': 'f0b890', 'M': 'ec8476', 'D': 'b6433d'}
CHASE = 'pounce'
HEIGHT = 20
LIFT = 2                                         # its spring, off the ground

# By hand, from its PixelLab pounces (pixellab-out/74-mini/animations: v1 front, v2 back, v3 side): M its pink, D its
# dark red, L its pale pink, K its eyes and open mouth; the outline is drawn round them. 0 crouched, 1 sprung.
G = {}
G['D0'] = ["....M....M......",
           "....MM..MM......",
           "....MMMMMMM.....",
           "....MKMMKMMMLL..",
           "....MMMMMMMMLL..",
           "....MLLLLLMM....",
           ".....MMMMMM.....",
           "...L.MMMMMM.L...",
           "..MMMMMMMMMMMM..",
           "..MM.MMMMMM.MM..",
           "..MM.MMMMMM.MM..",
           "..MM.MDMMDM.MM..",
           ".MMDDMDMMDMDDMM.",
           ".MMDDDDMMDDDDMM.",
           ".MMDDDDMMDDDDDM.",
           ".MMDDDD..DDDDDM.",
           "MMMM........MMMM"]
G['D1'] = ["....M....M......",
           "....MM..MM......",
           "....MMMMMMM.....",
           "....MKMMKMMMLL..",
           "....MMMMMMMMLL..",
           "....MLLLLLMM....",
           "....MKKKKKM.....",
           "...LMLLLLLM.L...",
           "MMMMMMMMMMMMMMMM",
           "M...MMMMMMMM...M",
           ".....MMMMMM.....",
           ".....MDMMDM.....",
           "....DDMMMMDD....",
           "...MDDD..DDDM...",
           "...MM......MM...",
           "..MMM......MMM.."]
G['U0'] = ["....M....M......",
           "....MM..MM......",
           "....MMMMMM......",
           "....MMMMMMM.....",
           "....MMMMMMM.....",
           ".....MMMMMM.....",
           ".....MMLMMM.....",
           "...M.MMLMMM.M...",
           "..MMMMMLMMMMMM..",
           "..MM.MMLMMM.MM..",
           "..MM.MMLMMM.MM..",
           "..MM.MMLMMM.MM..",
           ".MMDDMMMMMMDDMM.",
           ".MMDDDDMMDDDDMM.",
           ".MMDDDDMMDDDDDM.",
           ".MMDDDD..DDDDDM.",
           "MMMM........MMMM"]
G['U1'] = ["....M....M......",
           "....MM..MM......",
           "....MMMMMM......",
           "....MMMMMMM.....",
           "....MMMMMMM.....",
           ".....MMMMMM.....",
           ".....MMLMMM.....",
           "...M.MMLMMM.M...",
           "MMMMMMMLMMMMMMMM",
           "M...MMMLMMMM...M",
           ".....MMLMMM.....",
           ".....MDMMDM.....",
           "....DDMMMMDD....",
           "...MDDD..DDDM...",
           "...MM......MM...",
           "..MMM......MMM.."]
G['L0'] = [".......MM.........",
           "......MMM.........",
           "LLMMMMMMMM........",
           "LLMMMKMMMM........",
           ".MLLLLMMMM........",
           "..MMMMMMMML.......",
           "......MMMMML......",
           "......MMMMMML.....",
           ".....MMMMMMMML....",
           ".....MM.MMMMMML...",
           ".....MM.MMMMMMM...",
           ".....MM.MDDDDMM...",
           ".....MM.DDDDDDM...",
           ".....MM.DDDDDDDM..",
           "....MMM.DDDDDDDM..",
           "........MMMMMMMMMM"]
G['L1'] = [".......MM.........",
           "......MMM.........",
           "LLMMMMMMMM........",
           "LLMMMKMMMM........",
           ".MLLLLMMMM........",
           "..KKKK.MMML.......",
           ".LLLLMMMMMML......",
           "MMMMMMMMMMMML.....",
           "M....MMMMMMMML....",
           ".....MMMMMMMMMLL..",
           "......MDDDDDMMM...",
           ".....DDDDDDDDMM...",
           "....MM.....DDMM...",
           "...MM.......MMMM.."]
G = {k: '\n'.join(v) for k, v in G.items()}


def grid(s, lift):
    """A drawn grid, centred, its bottom row lift px off the ground, one black outline round it, its eyes and mouth
    black inside."""
    rows = s.strip(chr(10)).split(chr(10))
    h, w = len(rows), max(map(len, rows))
    g = {(x + (minis.W - w) // 2, y + minis.H - 1 - h - lift): c
         for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}
    out = ff.outline({p: ('M' if c == 'K' else c) for p, c in g.items()})
    out.update({p: 'K' for p, c in g.items() if c == 'K'})
    return out


FRAMES = {v: [grid(G[v + '0'], 0), grid(G[v + '1'], LIFT)] for v in 'DUL'}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(74, 'bes_rap', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(74, CHASE, FRAMES, PAL)
