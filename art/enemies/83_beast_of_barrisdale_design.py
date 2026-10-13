"""83 Beast of Barrisdale: user's first frame, planted idle and tucked flight.

Both loops have ten 130ms frames, preserving the existing 1.3s attack clock.
The airborne sheet uses Enemy::alt_pose throughout phase two, including hover.
All game direction cells retain the one authored left-facing view.

Author with the Aseprite pixel plugin:
    python art/enemies/83_beast_of_barrisdale_design.py

Original edits: 83_beast_of_barrisdale_frame0_user1.aseprite / _user_frame.png.
One transparent column is added on either side: original pixel positions about
its centre are unchanged, with room for the user's leftmost claw outline.
"""
from pathlib import Path
import json, math, sys
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'art/direction'))
sys.path.insert(0,str(ROOT/'tools'))
from mcpc import Pixel
import flat_parts

SOURCE_W, W, H, STEP_MS = 98, 100, 65, 130
PAL={'K':'000000','D':'474751','G':'595965','L':'848694',
     'r':'b6433d','m':'ec8476','l':'f0b890','c':'421618','W':'fcfcfc'}
RGB={c:tuple(int(h[i:i+2],16) for i in (0,2,4)) for c,h in PAL.items()}
LETTER={rgb:c for c,rgb in RGB.items()}
N4=((1,0),(-1,0),(0,1),(0,-1))
ORDER=('D','DR','R','UR','U','UL','L','DL')

# The pink wing and its complete grey/black rim, excluding the user's head,
# ear, haunch and the raised belly claw. Bounds are in original art coordinates.
WING_ROWS={**{y:(30,76) for y in range(6,21)},
           21:(35,68),22:(35,65),23:(37,64),24:(38,63),25:(39,62),
           26:(40,60),27:(41,59),28:(41,58),29:(42,57),30:(43,55),
           31:(44,54),32:(45,53),33:(46,52),34:(47,51),35:(48,50)}
GROUND_WING=(0,0,-1,-2,-1,0,1,2,1,0)
GROUND_BREATH=(0,0,0,0,0,1,1,1,1,0)
AIR_WING=(0,-2,-3,-3,-2,0,3,6,7,4)
AIR_BOB=(0,0,-1,-1,-1,0,0,1,1,1)
AIR_LEG_BEND=(0,0,1,1,2,2,1,1,0,0)
# Bullet anchors correspond to the visible mouth, wingtips and planted/tucked
# feet in the verified pixel poses. Pad +1 in X is applied by anchors().
MOUTH=(25,43)
WING_TIPS=((31,16),(70,6))
GROUND_FEET=((11,54),(40,57),(77,53))
AIR_FEET=((16, 47), (35, 48), (56, 44))


def user_frame():
    im=Image.open(HERE/'83_beast_of_barrisdale_user_frame.png').convert('RGBA')
    assert im.size==(SOURCE_W,H)
    g={}
    for y in range(H):
        for x in range(SOURCE_W):
            p=im.getpixel((x,y))
            assert p[3] in (0,255),('partial alpha',x,y,p)
            if p[3]:
                assert p[:3] in LETTER,('off-palette',x,y,p)
                g[x,y]=LETTER[p[:3]]
    return g


def in_wing(p):
    x,y=p
    return y in WING_ROWS and WING_ROWS[y][0]<=x<=WING_ROWS[y][1]


def block(g,x,y,text):
    for dy,row in enumerate(text.split()):
        for dx,c in enumerate(row):
            if c!='.':g[x+dx,y+dy]=c


def tucked_body(master):
    # Repose complete limbs, rather than shortening the standing limbs into
    # stumps. The user's head (including both eyes) and raised claw stay intact.
    standing=lambda p:(p[0]<=19 and p[1]>=41) or (35<=p[0]<=45 and p[1]>=40) or (p[0]>=70 and p[1]>=34) or (p[1]>=50 and not (20<=p[0]<=32 and p[1]<=50))
    body={p:c for p,c in master.items() if not standing(p)}
    # The small fourth claw also relaxes in flight instead of splaying flat.
    body={p:c for p,c in body.items() if not (54<=p[0]<=66 and p[1]>=42)}
    block(body,59,42,'''
KmlmmK
KrllmmK
KmlmlmK
.KmlmmK
.KmmKrK
..KmrK.K
...KK
''')
    legs={}
    # Far leg folds behind the muzzle; relaxed toes hang below its ankle.
    block(legs,13,39,'''
.KDDDGGK
.KDDGGGK
.KDDGGGGKK
..KDDGGGGGGKK
...KDDGGGGGGGGKK
....KKDDGGGGGGGGKK
......KKDDGGGGGGGGGGrrK
........KKDDGGGGGGGrrmmK
..........KKGGGGGGGrmmlK
............KKKKKKKKrmmK
....................KmrK
.....................KK
''')
    # Near shin bends inward; the narrow wrist turns into curled talons,
    # rather than a wide, flat planted palm.
    block(legs,35,38,'''
.KGGLLGGK
.KGLLLGGK
.KGLLLGGK
.KGLLGGGK
..KGLLGGGK
...KGLLGGGKK
....KGGLLGGGK
.....KGGGrrmK
......KGrmmlmK
.......KrmlmmK
........KmlmrK
........KmmKrK
.........KrK.K
..........KK
''')
    # Rear ankle folds forward under the haunch. Its toes point down and
    # curl back, with a different height from the front pair.
    block(legs,63,32,'''
..........KGGLLGK
..........KGLLLGGK
..........KGLLLGGK
...........KGLLGGGK
...........KGGLLGGGK
..........KKGGLLGGGK
.........KGGGLLGGGGK
........KGGLLGGGGGK
.......KGGLLGGGGKK
......KGGLLGGGKK
.....KrrmllGKK
....KrmmllmK
....KrmllmmK
....KrmlmmK
.....KmmKrK
.....KmrK.K
......KK
''')
    # The far ankle is partly hidden by the chest, with a clear gap from
    # the muzzle. Keep its wrist joined to the shoulder silhouette.
    legs={p:c for p,c in legs.items() if not (p[0]<39 and c in 'rml')}
    block(legs,32,40,'''
.KGGGGK
.KGrrmK
.KrmmlK
.KrmlmK
..KmmK
..KmrK
...KK
''')
    # Body/head own the roots and cover the far limbs, sharing the outline.
    return {**legs,**body}


def wing_point(p,amount):
    # A 2D flap about the attachment. No reflection, colour blending or 3D form.
    x,y=p
    sx=1+(amount/7)*0.14
    sy=1-amount/29
    return (52+(x-52)*sx,35+(y-35)*sy)


def moved_wing(wing,amount):
    if amount==0:return dict(wing)
    sx=1+(amount/7)*0.14;sy=1-amount/29
    bounds=[wing_point(p,amount) for p in wing]
    out={}
    for y in range(math.floor(min(p[1] for p in bounds))-1,math.ceil(max(p[1] for p in bounds))+2):
        for x in range(math.floor(min(p[0] for p in bounds))-1,math.ceil(max(p[0] for p in bounds))+2):
            q=(round(52+(x-52)/sx),round(35+(y-35)/sy))
            if q in wing:out[x,y]=wing[q]
    return out


def outline_join(g,moved):
    # Close newly exposed colour only; touching body surfaces remain joined.
    for x,y in moved:
        if g.get((x,y),'K') not in 'KW':
            for dx,dy in N4:
                q=(x+dx,y+dy)
                if q not in g:g[q]='K'
    return g


def leg_root(x):
    # Padded canvas coordinates; keep the muzzle and shoulder untouched.
    if x<=18:return 37
    if 33<=x<=47:return 36
    if 53<=x<=84:return 35
    return H


def flexed_y(x,y,amount):
    root=leg_root(x)
    return y+round(max(0,y-root)*amount/16)


def flex_legs(g,amount,bob):
    if not amount:return g
    out={}
    # Inverse nearest-pixel sampling keeps the flex continuous and opaque.
    for y in range(H):
        for x in range(W):
            root=leg_root(x)+bob
            sy=round(root+(y-root)/(1+amount/16)) if y>=root else y
            c=g.get((x,sy))
            if c is not None:out[x,y]=c
    return out


def frames(air=False):
    master=user_frame()
    wing={p:c for p,c in master.items() if in_wing(p)}
    source=tucked_body(master) if air else master
    body={p:c for p,c in source.items() if not in_wing(p)}
    # Hidden shoulder surface is exposed by a beat, not a hole cut into the body.
    under={p:'G' for p in wing if p[1]>=24}
    body={**under,**body}
    out=[]
    for i,amount in enumerate(AIR_WING if air else GROUND_WING):
        moved=moved_wing(wing,amount)
        g={**body,**moved}
        if amount:outline_join(g,set(moved))
        if air:
            g={(x+1,y+AIR_BOB[i]):c for (x,y),c in g.items()}
        else:
            b=GROUND_BREATH[i]
            g={(x+1,y+b if y<50 else y):c for (x,y),c in g.items()}
        bad=[p for p in g if not (1<=p[0]<W-1 and 1<=p[1]<H-1)]
        assert not bad,('clipped',air,i,bad[:10])
        if air:
            # Propagate the user's exact first-frame corrections, including erased
            # pixels, through the existing wingbeat and vertical body motion.
            patch=HERE/'83_beast_of_barrisdale_air_user_patch.json'
            if patch.exists():
                for x,y,c in json.loads(patch.read_text()):
                    point=(x,y+AIR_BOB[i])
                    if c is None:g.pop(point,None)
                    else:g[point]=c
        if air:
            g=flex_legs(g,AIR_LEG_BEND[i],AIR_BOB[i])
            # Composite the complete flap last: edits to the shoulder or legs
            # must never paint the body over the wing membrane/rim.
            foreground={(x+1,y+AIR_BOB[i]):c for (x,y),c in moved.items()}
            g.update(foreground)
            if amount:outline_join(g,set(foreground))
        if air:
            final_patch=HERE/'83_beast_of_barrisdale_air_final_patch.json'
            if final_patch.exists():
                for x,y,c in json.loads(final_patch.read_text())[i]:
                    if c is None:g.pop((x,y),None)
                    else:g[x,y]=c
        out.append(g)
    if not air:
        assert out[0]=={(x+1,y):c for (x,y),c in master.items()},'User frame changed'
        # Grounded claws remain pixel-for-pixel planted through the breathing.
        feet={p:c for p,c in out[0].items() if p[1]>=51}
        assert all({p:c for p,c in g.items() if p[1]>=51}==feet for g in out)
    if not air:
        # Saliva follows the jaw using the existing white and grey palette.
        for i,g in enumerate(out):
            b=GROUND_BREATH[i]
            strand={(27,50+b):'W',(27,51+b):'L',(27,52+b):'W'}
            for x,y in strand:
                for dx,dy in N4:
                    if (x+dx,y+dy) not in g:g[x+dx,y+dy]='K'
            g.update(strand)
    return out


def anchors(air=False):
    out=[]
    for i,amount in enumerate(AIR_WING if air else GROUND_WING):
        b=AIR_BOB[i] if air else GROUND_BREATH[i]
        tips=[(round(x)+1,round(y)+b) for x,y in (wing_point(p,amount) for p in WING_TIPS)]
        mouth=(MOUTH[0]+1,MOUTH[1]+b)
        feet=[(x+1,(flexed_y(x+1,y,AIR_LEG_BEND[i])+b) if air else y) for x,y in (AIR_FEET if air else GROUND_FEET)]
        out.append({'mouth':mouth,'wings':tips,'feet':feet})
    return out


def image(g,bg=None):return flat_parts.image(g,PAL,W,H,bg)


def author(fs,name):
    px=Pixel()
    base=HERE/name
    try:
        source=px.call('create_canvas',width=W,height=H,color_mode='rgb')['file_path']
        px.call('set_palette',sprite_path=source,colors=['#'+h for h in PAL.values()])
        for i,g in enumerate(fs,1):
            if i>1:
                px.call('add_frame',sprite_path=source,duration_ms=STEP_MS)
                clear=[{'x':x,'y':y,'color':'#00000000'} for y in range(H) for x in range(W)]
                for at in range(0,len(clear),800):px.call('draw_pixels',sprite_path=source,layer_name='Layer 1',frame_number=i,pixels=clear[at:at+800])
            else:px.call('set_frame_duration',sprite_path=source,frame_number=1,duration_ms=STEP_MS)
            pix=[{'x':x,'y':y,'color':'#'+PAL[c]} for (x,y),c in g.items()]
            for at in range(0,len(pix),800):px.call('draw_pixels',sprite_path=source,layer_name='Layer 1',frame_number=i,pixels=pix[at:at+800])
            print(name,'frame',i,flush=True)
        px.call('create_tag',sprite_path=source,tag_name='D',from_frame=1,to_frame=len(fs),direction='forward')
        ase=str(base.with_suffix('.aseprite')).replace('\\','/')
        png=str(base.with_suffix('.png')).replace('\\','/')
        px.call('save_as',sprite_path=source,output_path=ase)
        px.call('export_spritesheet',sprite_path=ase,output_path=png,layout='horizontal',padding=0,include_json=False)
    finally:px.p.terminate()
    im=Image.open(png).convert('RGBA')
    assert im.size==(len(fs)*W,H)
    for i,g in enumerate(fs):assert im.crop((i*W,0,(i+1)*W,H)).tobytes()==image(g).tobytes(),('plugin mismatch',i)
    print(name,': 0 plugin export mismatches',flush=True)
    return im


def review(idle,air):
    palette=[ch for rgb in RGB.values() for ch in rgb]+[0]*(768-27)
    colour_index={rgb:i for i,rgb in enumerate(RGB.values())}
    both=[]
    board=Image.new('RGB',(5*W,4*(H+12)),(0,0,0));label=ImageDraw.Draw(board)
    for kind,strip in enumerate((idle,air)):
        gif=[]
        for i in range(len(GROUND_WING)):
            cell=strip.crop((i*W,0,(i+1)*W,H))
            p=Image.new('P',(W,H));p.putpalette(palette)
            p.putdata([colour_index[c[:3]] if c[3] else 0 for c in cell.getdata()])
            gif.append(p.resize((W*5,H*5),Image.Resampling.NEAREST))
            x=(i%5)*W;y=(kind*2+i//5)*(H+12);label.text((x+2,y+1),('IDLE ' if kind==0 else 'AIR ')+str(i),fill=(252,252,252))
            board.paste(p.convert('RGB'),(x,y+12))
        gif[0].save(HERE/('83_idle_review.gif' if kind==0 else '83_air_review.gif'),save_all=True,append_images=gif[1:],duration=STEP_MS,loop=0,disposal=2,optimize=False)
    board.resize((board.width*4,board.height*4),Image.Resampling.NEAREST).save(HERE/'83_animation_review.png')
    for i in range(len(GROUND_WING)):
        row=Image.new('RGBA',(2*W,H),(0,0,0,255))
        row.alpha_composite(idle.crop((i*W,0,(i+1)*W,H)),(0,0));row.alpha_composite(air.crop((i*W,0,(i+1)*W,H)),(W,0))
        both.append(row.convert('RGB').resize((2*W*5,H*5),Image.Resampling.NEAREST))
    both[0].save(HERE/'83_review.gif',save_all=True,append_images=both[1:],duration=STEP_MS,loop=0,disposal=2)


if __name__=='__main__':
    idle_frames=frames();air_frames=frames(True)
    idle=author(idle_frames,'83_beast_of_barrisdale_idle_draft')
    air=author(air_frames,'83_beast_of_barrisdale_air_draft')
    for name,fs in [('83_beast_of_barrisdale',idle_frames),('83_beast_of_barrisdale_fly',air_frames)]:
        flat_parts.write(str(HERE/name),fs,PAL,W,H,dirs='down',view=ORDER,rows_sheet=True)
    (HERE/'83_beast_of_barrisdale_anchors.json').write_text(json.dumps({'idle':anchors(),'air':anchors(True)},indent=2)+'\n')
    review(idle,air)

