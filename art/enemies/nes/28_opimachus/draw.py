from pix import *

Y = 'f0bc3c'
G = 'c18a39'
T = 'd7a175'
D = '94703d'
B = '633e1b'
R = 'b6433d'
C = '7c0a1b'
H = 'ec8476'
K = '000000'
PAL = {'Y': Y, 'G': G, 'T': T, 'D': D, 'B': B, 'R': R, 'C': C, 'H': H}

im = canvas(60, 60)

# --- striped curled tail (left) ---
stamp(im, grid([
    ".....TTBBB..",
    "...TTTTBBBB.",
    "..BTTT..BBB.",
    ".BBB.....BB.",
    "BBB.........",
    "TTT.........",
    "TTT.........",
    "TTT.........",
    "BBB.........",
    "BBB.........",
    "TTTT........",
    ".TTTT.......",
    "..BBBTTTBB..",
    "...BBTTTBBB.",
    "....BTTTBBB.",
], PAL), 0, 27)

# --- folded wing (right): shoulder scallops over long feathers ---
stamp(im, grid([
    "...TTTTTT....",
    "..TTTTTTTTT..",
    ".TTTTTTTTTTD.",
    "TTTTTTTTTTTDD",
    "TTKTTTKTTTKDD",
    "TKDTTKDTTKDDD",
    "KDDKKDDKKDDKD",
    "TDDKTDDKTDDKD",
    "TDDKTDDKTDDKD",
    "TDDDKTDDKTDKD",
    "TDDDKTDDKTDKD",
    "TDDDKTDDKTDKD",
    "TDDDDKTDDKDKD",
    "TDDDDKTDDKDKD",
    "DDDDDKDDDKDD.",
    ".DDDDDKDDDKD.",
    "..DDDDDBBBB..",
], PAL), 29, 25)

# --- rear haunch (left) ---
stamp(im, grid([
    "...TTTTT...",
    ".TTTTTTTTT.",
    "TTTTTTTTTTD",
    "TTTTTTTTTTD",
    "TTTTTTKKTTD",
    "TTTTTKTTTDD",
    "TTTTKTTTTDD",
    "TTTKTTTTDDD",
    "TTTKTTTDDDD",
    "DDDKKKKKKDD",
    "TTTTTTTDDD.",
    "TKTKTKTKD..",
], PAL), 9, 30)
rect(im, 15, 29, 1, 10, K)

# --- torso ---
rect(im, 16, 24, 13, 15, T)
rect(im, 21, 28, 3, 11, D)
rect(im, 29, 28, 1, 14, K)

# --- forelegs ---
LEG = [
    "DDDD",
    "DDDD",
    "TDDD",
    "TTDD",
    "TTTD",
    "TTTD",
    "TKKD",
    "TTTD",
    "TTTD",
    "TTTD",
    "TTTD",
    "TTTD",
]
stamp(im, grid(LEG, PAL), 16, 27)
stamp(im, grid(LEG, PAL), 25, 27)
rect(im, 20, 27, 1, 12, K)
rect(im, 24, 27, 1, 12, K)
PAW = ["TTTTTD", "TTTTDD", "TKTKTK"]
stamp(im, grid(PAW, PAL), 15, 39)
stamp(im, grid(PAW, PAL), 24, 39)

# --- mane ruff: five chunky tufts ---
stamp(im, grid([
    ".......YYYYYYYYYYY.......",
    ".....YYYYYYYYYYYYYGG.....",
    "...YYYYYYYYYYYYYYYGGGG...",
    ".YYYYYYYYYYYYYYYYYYYGGGG.",
    "YYYYYYGKYYYYYYYGKYYGGGGGG",
    "YYYGKYYYYYYYYYYYYYYGKYYGG",
    "YYYGKYYYGKYYYYYGKYYGKYYGG",
    ".YYGKYYYGKYYYYYGKYYGKYGG.",
    "..YG.YYYGKYYYYYGKYYG.YG..",
    "...G..YYGKYYYYGKYG....G..",
    "......YG..YYYG..G........",
    "...........YYG...........",
    "............G............",
], PAL), 10, 15)

# --- red chest charm ---
stamp(im, grid([
    ".R.",
    "HRC",
    "RRC",
    "RRC",
    ".C.",
], PAL), 21, 28)

# --- crest ---
stamp(im, grid([
    "...RRR..RRR..RRR...",
    "..RRHR..RHR..RHRR..",
    ".RH.KR..RKR..RK.RC.",
    ".RR..R.RRKRC.R..RC.",
    "..RR.RRRHRRRCR.RC..",
    "...RRRCRRRRRCRCC...",
    "....RCRRCRCRRCC....",
    ".....CCRRCRRCC.....",
    ".......CCCCC.......",
], PAL), 13, 0)

# --- head ---
stamp(im, grid([
    "...DDDDD...",
    ".DDDDDDDBB.",
    "DDTTDDDTTDB",
    "DTTTTDTTTTB",
    "DTKKTYTKKTB",
    "DDTTYYYTTDB",
    "KDDDYYGDDBK",
    ".KDDYYGDBK.",
    "..KKYYGKK..",
    "....KGK....",
], PAL), 17, 8)

im = outline(im)
save(im)
