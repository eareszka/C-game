from pix import *

PAL = {
    'd': '235436',  # hide shade
    'm': '2c6c44',  # hide mid
    'l': '4fa667',  # hide light
    'g': '4edc4a',  # frill tips
    'p': 'a8f0bc',  # chest, teeth, claws
    'b': '815423',  # horn shade
    'h': 'c18a39',  # horn light
    'o': 'fc9838',  # eyes
}

# Left half, 22 columns; column 21 is the centre. Spaces only help counting.
HALF = [
    "..... .h... ..... ..... ..",
    "..... .hh.. ..... ..... ..",
    "..... .hb.. ..... ..... ..",
    "..... .hhb. ..... ..... ..",
    "..... ..hb. ..... ..... ..",
    "...h. ..hhb ..... ..... ..",
    "...hb ...hb b.... ..... ..",
    "....h b..hh b.... ..... ..",
    "..... .hhhh bb... ..... .g",
    "..... ..bbh hbb.. ..... gl",
    "..... ..... hhbb. ...g. ll",
    "..... ..... .hhbb .gllK ml",
    "..... ..... ..hbb Klllm Kl",
    "...g. ..... ..Kbd mlllm Kl",
    "...gl ..... .Kddm lllmm Kl",
    "...gl l...g Kmmmm lllmd Kl",
    "....g lld.g Kmlll lmmdK ml",
    "..... glmmd mllll mmdKm ll",
    "..... .gmmd dlllm mdKmm ll",
    "..... ..Kdd mllmm dKmml ll",
    "..... ...Kd mKKmm mmmll lm",
    "..... ...dd mmKKK mmlll lm",
    "..... ..Kdm mmdKK Kmlll lm",
    "..... ..dmm mKoKd Kmlll lm",
    "..... ..dmK mKoKm mmlll lm",
    "..... .dmKd mmKdm mKlml lm",
    "..... ..dKm mmdmm mllml lm",
    "..... .gdKm dKdmK lllml lm",
    "..... ..mKd KmdmK llmml lm",
    "..... ...dK mddKl lmmll lm",
    "..... ...dd KdKll lmmll ll",
    "..... .ddmd mKKll mmlll ll",
    "....d mllmm mKmll mmllK ll",
    "...dm llKmm dKlll mmlKK ll",
    "...dm lmmmd KKmll mmlll lm",
    "..dml lmmKK Kmmll mmmmm mm",
    "..dml mmKdd ddKKK KKKKK KK",
    "..dKl mKddd ddKpK pKpKp Kp",
    "..dmK mKddd ddKpK KKKKK KK",
    "..dmm mKddd dddKK mmmmm lm",
    ".dmlm mKKdd ddddK dmmmm mm",
    ".dmlm dKmmd ddddd KKKKK KK",
    ".dmmd KKmll mmddl ppppp pp",
    ".dmmd dKmll mmddl ppppp KK",
    ".dKKm dKmlm mmddl pppKK pp",
    ".dlmK dKmmm mdddl pKKpp pp",
    ".dlmd ...dm mmmdd lKppp pp",
    ".dlmd ...dl mmmdd lppKK KK",
    "dllmd ....d lmmmd dlKpp pp",
    "dlmmd ....d mmmmd dlppp pp",
    "dKKd. ....d mmmmm ddlpK KK",
    "dlmK. ....d mmmdm ddlKp pp",
    "dlmd. ....d mlmmm dddlp pp",
    "dlmmd ....d mlmmd dddlK KK",
    ".dlmd ...dm llmmd ddddl pp",
    ".dlmd ...dm llmmm dKddd dd",
    ".dlmm d..dm lmmmd K.... ..",
    "dllmm d.dml lmmdK ..... ..",
    "dlmKm d.dlm Kmmd. ..... ..",
    "dlKml K.dlK mlKmd ..... ..",
    "pp.pp ..pp. pp.pp ..... ..",
]
HALF = [r.replace(' ', '') for r in HALF]
bad = [i for i, r in enumerate(HALF) if len(r) != 22]
assert not bad, bad

SWAP = {'h': 'b', 'b': 'h'}
rows = []
for y, r in enumerate(HALF):
    right = ''
    for x in range(20, -1, -1):
        c = SWAP.get(r[x], r[x])
        # Light comes from the upper left: the far side of the hide loses its highlight.
        if c == 'l' and (y < 41 or x < 15):
            c = 'm'
        right += c
    rows.append(r + right)

im = grid(rows, PAL)
im = outline(im)
save(im)
