"""Enemy 83, first-frame draft: reference angle, lowered head, open mouth.

Literal pixel rows, drawn flat through the Aseprite pixel plugin. This file
creates only a separate draft and review; it does not alter the game assets.

    python art/enemies/83_beast_of_barrisdale_pose_first.py
"""
from pathlib import Path
import json
import sys
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'art/direction'))
from mcpc import Pixel
W, H = 98, 65
PAL = {'K':'000000', 'D':'474751', 'G':'595965', 'L':'848694',
       'r':'b6433d', 'm':'ec8476', 'l':'f0b890', 'c':'421618', 'W':'fcfcfc'}
RGB = {c:tuple(int(h[i:i+2],16) for i in (0,2,4)) for c,h in PAL.items()}
N4 = ((1,0),(-1,0),(0,1),(0,-1))


def block(g, x, y, text):
    for dy, row in enumerate(text.split()):
        for dx, c in enumerate(row):
            if c != '.':
                assert c in PAL, c
                g[x+dx,y+dy] = c


def spans(g, colour, rows, only=None):
    for y,x,n in rows:
        for dx in range(n):
            if only is None or g.get((x+dx,y)) == only:
                g[x+dx,y] = colour


def pose():
    g = {}
    # Three planted limbs, with hand-shaped bends and taper. Their roots
    # merge with the shoulder/body before one common silhouette is outlined.
    spans(g,'D',[(28,29,8),(29,28,8),(30,27,8),(31,26,8),(32,25,8),
                 (33,24,8),(34,23,8),(35,22,8),(36,21,8),(37,20,7),
                 (38,19,7),(39,18,7),(40,17,7),(41,16,7),(42,15,7),
                 (43,14,7),(44,13,7),(45,12,7),(46,11,7),(47,10,7),
                 (48,9,7),(49,9,6),(50,8,6),(51,8,6),(52,8,6),(53,8,6)])
    spans(g,'G',[(22,72,8),(23,72,9),(24,72,10),(25,73,10),(26,74,10),
                 (27,75,10),(28,76,9),(29,77,8),(30,78,8),(31,79,7),
                 (32,80,7),(33,80,7),(34,81,7),(35,81,7),(36,81,7),
                 (37,81,7),(38,82,6),(39,82,6),(40,82,6),(41,82,6),
                 (42,82,6),(43,83,5),(44,83,5),(45,83,5),(46,83,5),
                 (47,83,5),(48,83,5),(49,83,5),(50,83,5),(51,83,5),
                 (52,83,5),(53,83,5),(54,83,5)])
    spans(g,'L',[(24,77,5),(25,78,5),(26,79,4),(27,80,3),(28,81,2),
                 (29,81,3),(30,82,2),(31,82,2),(32,83,2),(33,83,2),
                 (34,84,2),(35,84,2),(36,84,2),(37,84,2),(38,85,1),
                 (39,85,1),(40,85,1),(41,85,1),(42,85,1),(43,85,1),
                 (44,85,1),(45,85,1),(46,85,1),(47,85,1),(48,85,1),
                 (49,85,1),(50,85,1),(51,85,1),(52,85,1)])
    spans(g,'G',[(28,43,10),(29,42,10),(30,41,10),(31,40,10),
                 (32,40,9),(33,39,9),(34,39,8),(35,39,8),(36,39,8),
                 (37,39,8),(38,38,8),(39,38,8),(40,38,8),(41,38,8),
                 (42,38,8),(43,38,7),(44,38,7),(45,38,7),(46,38,7),
                 (47,38,7),(48,39,6),(49,39,6),(50,39,6),(51,39,6),
                 (52,39,6),(53,39,6),(54,39,6),(55,39,6),(56,39,6)])
    spans(g,'L',[(30,43,5),(31,42,5),(32,42,4),(33,41,4),(34,41,3),
                 (35,41,3),(36,41,3),(37,41,3),(38,40,3),(39,40,3),
                 (40,40,3),(41,40,3),(42,40,3),(43,40,3),(44,40,3),
                 (45,40,3),(46,40,3),(47,40,3),(48,41,2),(49,41,2),
                 (50,41,2),(51,41,2),(52,41,2),(53,41,2),(54,41,2)])
    # Fleshy clawed extremities: varied toes, connected at their bases.
    block(g,3,52,'''
.....rrmmmr
....rmmmllmr
...rmmmllmmlrr....r
..rmmllmlmmlmmr..rml
.rmllmmrmmmlmmllrmmlr
lmmmr..rmmmmlrmmllmlmml
....l...rmmr..rmmr...ll
.........l.....l
''')
    block(g,34,55,'''
.....rmmmlmr
....rmmmllmmr...r
...rmmmlllmmmr.rml
..rmmllmlmmmllrmmlmr
.rmmllmrmmmlmmlllmlmmrl
lmmmr..rmmmmlrmmmr..rml
....l...rmmr..rmmr....l
.........l.....l
''')
    block(g,72,52,'''
.......rmmmlr
......rmmmllmr
.....rmmmlllmmr
...rrmmllmmlmllr...r
..rmmllmmrmmmlmmllrmml
.rmlmmr..rmmmmlrmmlllmmrl
lmmmr.....rmmr..rmmr...ll
....l.......l.....l
''')
    # The rear thigh grows continuously out of the haunch, with a broad
    # shoulder-facing surface and the shadow underneath the wing.
    spans(g,'G',[(22,64,12),(23,63,15),(24,62,18),(25,62,20),(26,61,21),
                 (27,60,24),(28,61,24),(29,61,24),(30,60,25),(31,60,25),
                 (32,60,25),(33,60,23),(34,60,20),(35,60,17),(36,59,16),
                 (37,58,13),(38,57,11),(39,55,10)])
    spans(g,'L',[(23,74,3),(24,72,6),(25,71,7),(26,70,8),(27,69,9),
                 (28,69,9),(29,70,8),(30,71,7),(31,72,6),(32,73,5)])
    # A single hunched torso, shoulder and neck, rather than stacked shapes.
    block(g,29,20,'''
..............GGGGGGGGGG
...........GGGGGGGGGGGGGGGGG
.........GGGGGGGGGGGGGGGGGGGGGGG
.......GGGGGGGGGGGGGGGGGGGGGGGGGGG
.....GGGGGLLLLLLLLGGGGGGGGGGGGGGGGGG
....GGGGLLLLLLLLLLLGGGGGGGGGGGGGGGGGG
...GGGLLLLLLLLLLLLLGGGGGGGGGGGGGGGGGGG
..GGGLLLLLLLLLLLLLGGGGGGGGGGGGGGGGGGGGG
.GGGLLLLLLLLLLLLGGGGGGGGGGGGGGGGGGGGGGG
GGGLLLLLLLLLLLLGGGGGGGGGGGGGGGGGGGGGGGG
GGLLLLLLLLLLLGGGGGGGGGGGGGGGGGGGGGGGGGG
GLLLLLLLLLLGGGGGGGGGGGGGGGGGGGGGGGGGGGG
LLLLLLLLLGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
LLLLLLLGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
LLLLLLGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
GGLLLGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
.GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
..GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
...GGGGGGGGGGGGGGGGGDDDDDDDDDDD
.....GGGGGGGGGGGGDDDDDDDDDDDD
........GGGGGGDDDDDDDDDDDD
''')
    # Head is carried below the shoulders, with its muzzle tipped down-left.
    block(g,22,27,'''
.............GGGGG
...........GGGGGGGG
.........GGLLLLGGGGG
.......GGLLLLLLGGGGG
......GGLLLLLLGGGGGG
.....GGLLLLLGGGGGGGG
....GGLLLLLGGGGGGGGG
....GGLLLLGGGGGGGGGG
...GGLLLLGGGGGGGGGG
...GGLLLGGGGGGGGGG
..GGLLLGGGGGGGGGG
..GLLLGGGGGGGGGG
.GLLLGGGGGGGGGG
.GLLGGGGGGGGGG
.GLGGGGGGGGGG
.GGGGGGGGGGG
.GGGGGGGGGG
.GGGGGGGGG
..GGGGGGG
..GGGGGG
...GGGG
....GG
''')
    # Membrane fan, scalloped rim, folded into one point on the shoulder.
    block(g,30,7,'''
.............G...........................G
............GGG............G............GG
....G......GGGGG..........GG...........GGG
....GG....GGmmmmGG.......GGGG.....G....GGmmG
.....GG..GGmmmmmmGG.....GGmmGG...GG...GGmmmGG
.....GGGGGmmmmmmmGGGGGGGGmmmGGGGGGGGGGmmmmmmG
......GmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
.....GrrmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
....GrrmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
...GrrmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
..GrrmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
..GrrmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
...GrrmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
....GrrmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
.....GrrmmmmmmmmmmmmmmmmmmmmmmmmmmmmGG
......GrrmmmmmmmmmmmmmmmmmmmmmmmmmmGG
.......GrrmmmmmmmmmmmmmmmmmmmmmmmmGG
........GrrmmmmmmmmmmmmmmmmmmmmmmGG
.........GrrmmmmmmmmmmmmmmmmmmmmGG
..........GrrmmmmmmmmmmmmmmmmmmGG
...........GrrmmmmmmmmmmmmmmmmGG
............GrrmmmmmmmmmmmmmmGG
.............GrrmmmmmmmmmmmmGG
..............GrrmmmmmmmmmmGG
...............GrrmmmmmmmGG
................GrrmmmmmG
.................GrrmmmGG
..................GrrmGG
...................GrrG
....................GG
''')
    # Light follows the membrane planes: three irregular fields, not bands.
    spans(g,'l',[(14,44,3),(15,44,5),(16,45,5),(17,46,5),(18,47,5),
                 (19,48,5),(20,49,4),(21,50,4),(22,51,3),(23,52,3),
                 (24,53,2),(25,54,2),(26,55,1),
                 (13,60,3),(14,59,5),(15,59,6),(16,59,7),(17,59,6),
                 (18,58,6),(19,58,5),(20,58,5),(21,57,5),(22,57,4),
                 (23,57,3),(24,57,2),(25,57,1),
                 (14,72,6),(15,71,6),(16,70,6),(17,69,5),(18,68,5),
                 (19,67,5),(20,66,5),(21,65,4),(22,64,4),(23,63,3)], only='m')
    # The far membrane plane stays shaded, not textured; near planes catch light.
    spans(g,'r',[(14,37,6),(15,37,7),(16,36,8),(17,35,10),(18,35,10),
                 (19,36,10),(20,37,10),(21,38,10),(22,39,10),(23,40,10),
                 (24,41,10),(25,42,10),(26,43,10),(27,44,9),(28,45,8),
                 (29,46,7),(30,47,6),(31,48,5),(32,49,4),(33,50,3)], only='m')
    # Outline once around the connected drawing, with colour left on thin tips.
    occupied=set(g)
    inner={p for p in occupied if all((p[0]+dx,p[1]+dy) in occupied for dx,dy in N4)}
    for x,y in occupied-inner:
        if any((x+dx,y+dy) in inner for dx,dy in N4):
            g[x,y]='K'
    # A shared border where membrane meets torso, avoiding a doubled outer rim.
    membrane={p for p,c in g.items() if c in 'rml' and p[1]<38}
    for x,y in membrane:
        for dx,dy in N4:
            q=(x+dx,y+dy)
            if g.get(q)=='G' and all((q[0]+ex,q[1]+ey) in inner for ex,ey in N4):
                g[q]='K'
    # Three structural wing fingers converge at the membrane's root.
    details={} 
    for y,x in enumerate([45,45,46,46,47,47,48,48,49,49,50,50,51,51,52,52,53,53,54,54,55,55,56],13): details[x,y]='K'
    for y,x in enumerate([61,61,61,60,60,60,60,59,59,59,59,58,58,58,58,57,57,57,57,56,56,56,56,56],11): details[x,y]='K'
    for y,x in enumerate([76,76,75,74,74,73,72,71,70,69,68,67,66,65,64,63,62,61,60,59,58],13): details[x,y]='K'
    # Shoulder folds interrupt rather than encircle the limb roots.
    details.update({(44,32):'K',(44,33):'K',(43,34):'K',(43,35):'K',
                    (42,36):'K',(47,37):'D',(48,38):'D',
                    (38,33):'K',(38,34):'K',(37,35):'K',(37,36):'K',
                    (36,37):'K',(36,38):'K',(35,39):'K',(35,40):'K',
                    (34,41):'K',(33,42):'K',(32,43):'K',
                    (35,32):'r',(36,32):'m',(35,33):'m',(36,33):'l',
                    (35,34):'r',(36,34):'m',
                    (30,37):'K',(31,37):'W',(30,38):'K',(31,38):'K'})
    for p,c in details.items():
        if p in inner: g[p]=c
    # Open downturned jaws; dark cavity and a few large readable teeth.
    block(g,22,39,'''
..rmmGGG
.rmmlGGG
.rmmlKGG
.rmWKKGG
rmWWccKGG
mWccccKGG
mWccccKG
rWcccWmK
rmWmmlmK
.rmmlmK
..rmmK
...rK
''')
    # Repair the jaw silhouette after the intentional muzzle redraw.
    for x,y in list(g):
        if 22<=x<=31 and 39<=y<=51 and g[x,y] not in 'KW':
            for dx,dy in N4:
                q=(x+dx,y+dy)
                if q not in g: g[q]='K'
    assert all(1<=x<W-1 and 1<=y<H-1 for x,y in g), 'Clipped extremity'
    return g


def draw_plugin(g):
    base=HERE/'83_beast_of_barrisdale_frame0_draft'
    px=Pixel()
    try:
        source=px.call('create_canvas',width=W,height=H,color_mode='rgb')['file_path']
        px.call('set_palette',sprite_path=source,colors=['#'+h for h in PAL.values()])
        pixels=[{'x':x,'y':y,'color':'#'+PAL[c]} for (x,y),c in sorted(g.items())]
        for at in range(0,len(pixels),800):
            px.call('draw_pixels',sprite_path=source,layer_name='Layer 1',frame_number=1,pixels=pixels[at:at+800])
        ase=str(base.with_suffix('.aseprite')).replace('\\','/')
        png=str(base.with_suffix('.png')).replace('\\','/')
        px.call('save_as',sprite_path=source,output_path=ase)
        px.call('export_sprite',sprite_path=ase,output_path=png,format='png',frame_number=1)
    finally:
        px.p.terminate()
    im=Image.open(png).convert('RGBA')
    assert im.size==(W,H)
    actual={}
    inv={v:k for k,v in RGB.items()}
    for y in range(H):
        for x in range(W):
            p=im.getpixel((x,y))
            assert p[3] in (0,255)
            if p[3]:actual[x,y]=inv[p[:3]]
    assert actual==g, 'Pixel plugin export differs from design'
    rows=[''.join(g.get((x,y),'.') for x in range(W)) for y in range(H)]
    base.with_suffix('.json').write_text(json.dumps({'pal':PAL,'width':W,'height':H,'frame0':rows},indent=2)+'\n')
    print(f'{base.name}: {len(g)} pixels, 0 export mismatches',flush=True)
    return im


def review(im):
    old=Image.open(ROOT/'assets/enemies/83_beast_of_barrisdale.png').convert('RGBA').crop((0,0,W,H))
    player=Image.open(ROOT/'assets/player_small.png').convert('RGBA').crop((0,0,14,20))
    panel=Image.new('RGBA',(376,H+13),(0,0,0,255))
    labels=ImageDraw.Draw(panel)
    for x,label,item in [(4,'DRAFT - FRAME 0',im),(110,'ORIGINAL - FRAME 0',old)]:
        labels.text((x,2),label,fill=(252,252,252,255))
        panel.alpha_composite(item,(x,13))
    labels.text((216,2),'PLAYER',fill=(252,252,252,255))
    panel.alpha_composite(player,(226,13+H-20))
    labels.text((270,2),'SILHOUETTE',fill=(252,252,252,255))
    silhouette=Image.new('RGBA',(W,H),(252,252,252,0))
    silhouette.putalpha(im.getchannel('A'))
    panel.alpha_composite(silhouette,(270,13))
    panel.resize((panel.width*5,panel.height*5),Image.Resampling.NEAREST).save(HERE/'83_review.png')
    black=Image.new('RGBA',im.size,(0,0,0,255));black.alpha_composite(im)
    black.resize((W*8,H*8),Image.Resampling.NEAREST).save(HERE/'83_frame0_preview.png')


if __name__=='__main__':
    review(draw_plugin(pose()))
