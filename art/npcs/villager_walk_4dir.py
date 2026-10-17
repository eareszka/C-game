"""Approved villagers: four cardinal views, two walking frames each.

Art is drawn through the installed Aseprite pixel MCP. The user-approved front
designs are read from the saved review sheet. Back and profile views are flat
native-pixel drawings; the old files and player remain unchanged.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'art/direction'))
from mcpc import Pixel
import fcremap

DIRECTIONS=('down','up','left','right')
MS=200


def put(g,c,rows):
    for y,a,b in rows:
        for x in range(a,b+1):
            assert (x,y) in g,(x,y)
            g[x,y]=c


def silhouette(rows):
    op={(x,y) for y,spans in rows.items() for a,b in spans for x in range(a,b+1)}
    return {q:('K' if any((q[0]+dx,q[1]+dy) not in op for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) else 'H') for q in op}


def back_view(front,name):
    g=dict(front)
    op=set(g)
    # Delete front-only face markings while retaining the head contour.
    for (x,y) in op:
        if 8<=y<=12 and all((x+dx,y+dy) in op for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
            g[x,y]='H'
    if name=='01_farmer':
        for x in (2,12):g.pop((x,7),None)
        put(g,'K',[(7,3,3),(7,11,11)])
        put(g,'C',[(6,5,9),(7,4,10)])
        put(g,'H',[(7,6,8),(14,4,10)])
        put(g,'S',[(12,7,7),(13,6,8)])
        put(g,'C',[(13,5,5),(13,9,9),(14,5,5),(14,9,9),(15,5,9),(16,5,9)])
    elif name=='02_apron_villager':
        put(g,'H',[(13,4,11),(14,4,10),(15,5,9),(16,4,10),(17,4,10)])
        put(g,'C',[(14,5,5),(14,9,9),(15,5,9),(16,6,8)])
        # The bun tie lies on the character's left: reverse its screen position.
        put(g,'H',[(6,9,9)])
        put(g,'C',[(7,5,5)])
    elif name=='03_elder':
        put(g,'S',[(8,5,9),(9,5,9),(10,6,8)])
        put(g,'C',[(13,5,9),(14,4,10),(15,5,9),(16,4,10),(17,5,9)])
        put(g,'H',[(13,6,8),(14,5,9),(16,4,4),(16,10,10)])
    else:
        put(g,'H',[(7,8,9)])
        put(g,'C',[(7,5,6),(13,5,9),(14,4,10),(15,5,9),(16,4,10),(17,5,9)])
        # Bag on the character's right, now screen-right; front collar is hidden.
        put(g,'H',[(14,5,5),(15,6,6),(16,7,9),(17,7,9)])
    return g


def right_profile(name):
    if name=='01_farmer':
        rows={4:[(5,8)],5:[(4,9)],6:[(4,10)],7:[(3,12)],8:[(4,10)],9:[(4,10)],10:[(4,11)],11:[(4,11)],12:[(5,10)],13:[(5,9)],14:[(5,10)],15:[(4,11)],16:[(5,10)],17:[(5,9)]}
    elif name=='02_apron_villager':
        rows={4:[(5,6)],5:[(4,9)],6:[(4,10)],7:[(4,10)],8:[(3,10)],9:[(3,10)],10:[(3,11)],11:[(3,11)],12:[(4,10)],13:[(4,10)],14:[(5,10)],15:[(4,11)],16:[(5,10)],17:[(5,9)]}
    elif name=='03_elder':
        rows={5:[(6,8)],6:[(5,9)],7:[(4,10)],8:[(4,10)],9:[(4,10)],10:[(4,11)],11:[(4,11)],12:[(5,10)],13:[(5,9)],14:[(5,10)],15:[(4,11)],16:[(5,10)],17:[(5,9)]}
    else:
        rows={6:[(6,9)],7:[(5,10)],8:[(4,10)],9:[(4,10)],10:[(4,11)],11:[(4,11)],12:[(5,11)],13:[(5,10)],14:[(5,10)],15:[(4,11)],16:[(5,10)],17:[(5,9)]}
    g=silhouette(rows)
    if name!='04_spectacled_villager':
        put(g,'S',[(8,7,9),(9,7,9),(10,7,10),(11,7,10),(12,7,9)])
        put(g,'K',[(9,9,9),(10,9,9)])
    if name=='01_farmer':
        put(g,'C',[(5,5,8),(6,5,9),(7,4,11),(13,8,8),(14,8,9),(15,6,9),(16,6,9),(17,6,8)])
        put(g,'H',[(6,5,9),(15,8,8)])
        put(g,'S',[(13,7,7),(15,9,9)])
    elif name=='02_apron_villager':
        put(g,'H',[(13,5,9),(14,6,9),(15,5,10),(16,6,9),(17,6,8)])
        put(g,'C',[(13,9,9),(14,9,9),(15,9,10),(16,9,9),(17,8,8)])
    elif name=='03_elder':
        put(g,'S',[(7,6,8),(8,6,9)])
        put(g,'H',[(9,6,6),(10,6,6),(11,6,6),(12,6,6)])
        put(g,'C',[(13,6,8),(14,6,9),(15,5,10),(16,6,9),(17,6,8)])
        put(g,'H',[(13,7,8),(14,8,9),(16,7,8)])
    else:
        put(g,'S',[(9,7,9),(10,7,10),(11,7,10),(12,7,10),(13,7,9)])
        put(g,'K',[(10,6,10),(11,8,8),(11,10,10),(12,8,10)])
        put(g,'C',[(14,6,9),(15,5,10),(16,6,9),(17,6,8)])
        put(g,'S',[(14,8,9)])
        put(g,'H',[(14,9,9),(15,8,8),(16,6,8),(17,6,8)])
        put(g,'S',[(16,7,7)])
    return g


def left_profile(right,name):
    # Reflect the flat profile, then draw the details of the opposite side.
    g={(14-x,y):c for (x,y),c in right.items()}
    if name=='02_apron_villager':
        put(g,'C',[(6,9,9)])
    elif name=='04_spectacled_villager':
        put(g,'C',[(7,7,8),(15,6,6),(16,6,8),(17,6,8)])
        put(g,'S',[(14,5,5)])
    return g


def walk(base,direction,phase):
    g={q:c for q,c in base.items() if q[1]<18}
    if direction in ('down','up'):
        # Alternating planted/lifted shoe, opposite arm raised by one pixel.
        for center in (5,9):
            planted=(center==5)==(phase==0)
            for x in range(center-1,center+2):g[x,18]='K'
            if planted:
                g[center,18]='H'
                for x in range(center-1,center+2):g[x,19]='K'
        raised=11 if phase==0 else 3
        outer=12 if raised==11 else 2
        g.pop((outer,15),None)
        g[raised,15]='K'
        g[outer,14]='K'
        g[raised,14]='S'
    else:
        # Near leg advances/retracts; the far shoe lifts instead of sliding.
        forward=phase==0
        if direction=='left':forward=not forward
        near=9 if forward else 5
        far=5 if forward else 9
        for x in range(near-1,near+2):g[x,18]='K'
        g[near,18]='H'
        for x in range(near-1,near+3):g[x,19]='K'
        for x in range(far-1,far+3):g[x,18]='K'
        # The near hand crosses the shirt on alternating beats.
        hand=10 if forward else 5
        other=5 if hand==10 else 10
        if (other,15) in g:g[other,15]=base.get((other,16),'C')
        if (hand,15) in g:g[hand,15]='S'
    return g


def draw_frame(p,path,frame,g,pal,layer='Layer 1'):
    # Explicit transparent pixels prevent a duplicated cel leaving old limbs.
    pixels=[dict(x=x,y=y,color='#'+pal[g[x,y]] if (x,y) in g else '#00000000') for y in range(20) for x in range(14)]
    r=p.call('draw_pixels',sprite_path=path,layer_name=layer,frame_number=frame,pixels=pixels)
    assert r['pixels_drawn']==280


def validate_frame(im,g,pal):
    assert im.size==(14,20)
    assert set(im.getchannel('A').getdata())=={0,255}
    for y in range(20):
        for x in range(14):
            expected=tuple(bytes.fromhex(pal[g[x,y]]))+(255,) if (x,y) in g else (0,0,0,0)
            assert im.getpixel((x,y))==expected,(x,y)
    colors={c[:3] for c in im.getdata() if c[3]}
    assert colors<=set(fcremap.PALETTE) and len(colors)<=4
    assert max(y for x,y in g)==19
    # Every pixel belongs to the character, not an isolated drawing artifact.
    remaining=set(g);stack=[remaining.pop()]
    while stack:
        x,y=stack.pop()
        for dx,dy in ((-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)):
            q=(x+dx,y+dy)
            if q in remaining:remaining.remove(q);stack.append(q)
    assert not remaining,remaining


def main():
    from PIL import Image,ImageDraw
    data=json.loads((HERE/'villagers_standing_drafts.json').read_text())['npcs']
    outputs=[HERE/(n['name']+'_walk_4dir.aseprite') for n in data]
    if any(p.exists() for p in outputs):raise SystemExit('Walk sheets already exist; preserve any user edits.')
    protected=list(HERE.glob('*.aseprite'))+[ROOT/'assets/player_small.png',ROOT/'assets/player_small.aseprite']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    scratch=ROOT/'build_tmp/npc_review';scratch.mkdir(exist_ok=True)
    source=HERE/'villagers_detailed_review.aseprite'
    all_frames=[];rendered=[]
    report=dict(frame_size=[14,20],sheet_size=[28,80],direction_rows=list(DIRECTIONS),frames_per_direction=2,duration_ms=MS,npcs=[],protected_sha256=hashes)
    p=Pixel()
    try:
        info=p.call('get_sprite_info',sprite_path=source.as_posix())
        assert (info['width'],info['height'],info['frame_count'])==(82,50,1)
        p.call('export_sprite',sprite_path=source.as_posix(),output_path=(scratch/'approved_walk_source.png').as_posix(),format='png',frame_number=1)
        approved=Image.open(scratch/'approved_walk_source.png').convert('RGBA')
        for i,(npc,out) in enumerate(zip(data,outputs)):
            name=npc['name'];pal=npc['palette'];inv={tuple(bytes.fromhex(c)):k for k,c in pal.items()}
            fr=approved.crop((4+i*20,28,18+i*20,48))
            front={(x,y):inv[fr.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if fr.getpixel((x,y))[3]}
            back=back_view(front,name);right=right_profile(name);left=left_profile(right,name)
            views=[front,back,left,right]
            frames=[walk(view,d,phase) for d,view in zip(DIRECTIONS,views) for phase in range(2)]
            for phase in (0,1):
                assert all(frames[phase].get((x,y))==c for (x,y),c in front.items() if y<=12),'Approved face changed'
            assert all(0<=x<14 and 0<=y<20 for g in frames for x,y in g)
            assert all(frames[2*d]!=frames[2*d+1] for d in range(4))
            all_frames.append(frames)
            canvas=p.call('create_canvas',width=14,height=20,color_mode='rgb')['file_path']
            p.call('set_palette',sprite_path=canvas,colors=['#'+c for c in pal.values()])
            p.call('set_frame_duration',sprite_path=canvas,frame_number=1,duration_ms=MS)
            ims=[]
            for f,g in enumerate(frames,1):
                if f>1:
                    assert p.call('add_frame',sprite_path=canvas,duration_ms=MS)['frame_number']==f
                draw_frame(p,canvas,f,g,pal)
            for d,label in enumerate(DIRECTIONS):
                p.call('create_tag',sprite_path=canvas,tag_name=label,from_frame=2*d+1,to_frame=2*d+2,direction='forward')
            p.call('save_as',sprite_path=canvas,output_path=out.as_posix())
            meta=p.call('get_sprite_info',sprite_path=out.as_posix());assert meta['frame_count']==8
            # Export each real saved animation cel and verify its exact pixels.
            for f,g in enumerate(frames,1):
                dest=scratch/(name+'_walk_'+str(f)+'.png')
                p.call('export_sprite',sprite_path=out.as_posix(),output_path=dest.as_posix(),format='png',frame_number=f)
                im=Image.open(dest).convert('RGBA');validate_frame(im,g,pal);ims.append(im)
            rendered.append(ims)
            atlas=p.call('create_canvas',width=28,height=80,color_mode='rgb')['file_path']
            p.call('set_palette',sprite_path=atlas,colors=['#'+c for c in pal.values()])
            pixels=[dict(x=x+(f%2)*14,y=y+(f//2)*20,color='#'+pal[c]) for f,g in enumerate(frames) for (x,y),c in g.items()]
            for at in range(0,len(pixels),700):p.call('draw_pixels',sprite_path=atlas,layer_name='Layer 1',frame_number=1,pixels=pixels[at:at+700])
            png=out.with_suffix('.png')
            p.call('export_sprite',sprite_path=atlas,output_path=png.as_posix(),format='png',frame_number=1)
            sheet=Image.open(png).convert('RGBA');assert sheet.size==(28,80)
            records=[]
            for f,g in enumerate(frames):
                x=(f%2)*14;y=(f//2)*20
                assert sheet.crop((x,y,x+14,y+20)).tobytes()==ims[f].tobytes()
                records.append(dict(filename=f'{name}_{DIRECTIONS[f//2]}_{f%2}',frame=dict(x=x,y=y,w=14,h=20),rotated=False,trimmed=False,spriteSourceSize=dict(x=0,y=0,w=14,h=20),sourceSize=dict(w=14,h=20),duration=MS))
            tags=[dict(name=d,**{'from':i*2,'to':i*2+1},direction='forward') for i,d in enumerate(DIRECTIONS)]
            metadata=dict(frames=records,meta=dict(app='Aseprite pixel MCP',image=png.name,format='RGBA8888',size=dict(w=28,h=80),scale='1',frameTags=tags),origin=dict(x=7,y=19))
            out.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
            report['npcs'].append(dict(name=name,frames=8,tags=list(DIRECTIONS),approved_front_head_preserved=True,palette_colors=4,all_frames_pixel_verified=True,all_walk_pairs_differ=True,baseline=19))

        # Two-frame animated contact sheet: columns NPCs; rows D U L R.
        board=p.call('create_canvas',width=84,height=100,color_mode='rgb')['file_path']
        p.call('set_palette',sprite_path=board,colors=list(dict.fromkeys('#'+v for n in data for v in n['palette'].values())))
        p.call('set_frame_duration',sprite_path=board,frame_number=1,duration_ms=MS)
        p.call('add_frame',sprite_path=board,duration_ms=MS)
        for phase in range(2):
            pixels=[]
            for i,npc in enumerate(data):
                for d in range(4):
                    pixels.extend(dict(x=x+2+i*20,y=y+2+d*24,color='#'+npc['palette'][c]) for (x,y),c in all_frames[i][d*2+phase].items())
            for at in range(0,len(pixels),700):p.call('draw_pixels',sprite_path=board,layer_name='Layer 1',frame_number=phase+1,pixels=pixels[at:at+700])
        p.call('create_tag',sprite_path=board,tag_name='all_walks',from_frame=1,to_frame=2,direction='forward')
        review=HERE/'villagers_walk_4dir_review.aseprite'
        p.call('save_as',sprite_path=board,output_path=review.as_posix())
        p.call('export_sprite',sprite_path=review.as_posix(),output_path=review.with_suffix('.png').as_posix(),format='png',frame_number=1)
        p.call('export_sprite',sprite_path=review.as_posix(),output_path=review.with_suffix('.gif').as_posix(),format='gif',frame_number=0)
    finally:p.p.terminate()
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
    report['approved_sources_unchanged']=True
    (HERE/'villagers_walk_4dir_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    # Human-readable, nearest-neighbour inspection of the actual saved cels.
    preview=Image.new('RGB',(880,570),(43,43,51));draw=ImageDraw.Draw(preview)
    for i,npc in enumerate(data):draw.text((75+i*200,8),npc['name'],fill='white')
    for d,label in enumerate(DIRECTIONS):
        y=35+d*132;draw.text((8,y+35),label.upper(),fill='white')
        for i,ims in enumerate(rendered):
            for phase in range(2):
                im=ims[d*2+phase];x=75+i*200+phase*90
                z=im.resize((84,120),Image.Resampling.NEAREST);preview.paste(z,(x,y),z)
    preview.save(HERE/'villagers_walk_4dir_comparison.png')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
