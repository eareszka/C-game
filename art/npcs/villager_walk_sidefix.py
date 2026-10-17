"""Rebuild only NPC left/right views from the game's actual player frames.

The first four cels (down/up) are copied without pixel changes. Player passing
and step frames supply the anatomy, body outline, hands, feet, and baseline;
native pixel edits add each approved villager's identity and non-player eyes.
All drawing and animation exports go through the installed Aseprite pixel MCP.
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

PLAYER_COLORS={(0,0,0):'K',(99,62,27):'H',(240,184,144):'S',(182,67,61):'C'}
DIRS=('down','up','left','right')
PLAYER_BASES={'left':(6,7),'right':(8,9)}


def player_pixels(im):
    return {(x,y):PLAYER_COLORS[im.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if im.getpixel((x,y))[3]}


def profile(base,name,direction,phase):
    # Player idle head is one pixel above its stride head. Keep that real bob.
    off=-1 if phase==0 else 0
    g=dict(base)
    if name=='01_farmer':
        rows={5:(5,9),6:(4,10),7:(3,11),8:(2,12),9:(2,12)}
    elif name=='02_apron_villager':
        rows={5:(4,6),6:(3,10),7:(3,11),8:(2,12),9:(2,12)}
        if direction=='left':rows={y:(14-b,14-a) for y,(a,b) in rows.items()}
    else:
        rows={6:(5,9),7:(4,10),8:(3,11),9:(2,12)}
    # New hair/hat silhouette above the original face; body geometry is retained.
    g={q:c for q,c in g.items() if q[1]>9+off}
    head={(x,y+off) for y,(a,b) in rows.items() for x in range(a,b+1)}
    op=set(g)|head
    for x,y in head:
        g[x,y]='K' if any((x+dx,y+dy) not in op for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) else 'H'

    def paint(c,spans,clothes=False):
        for y,a,b in spans:
            for x in range(a,b+1):
                q=(x,y+off)
                assert q in g,(name,direction,phase,q)
                # Retain the player's actual black limb boundaries and hand pose.
                if clothes and (base.get(q)=='K' or (y==16 and base.get(q)=='S')):continue
                g[q]=c

    if name=='01_farmer':
        paint('C',[(6,5,9),(7,4,10),(8,3,11)])
        paint('H',[(7,4,10)])
    elif name=='02_apron_villager' and direction=='left':
        paint('C',[(7,9,9)])
    elif name=='03_elder':
        scalp=[(7,7,8),(8,6,9),(9,7,10),(10,8,10)]
        if direction=='left':scalp=[(y,14-b,14-a) for y,a,b in scalp]
        paint('S',scalp)
    elif name=='04_spectacled_villager' and direction=='left':
        paint('C',[(7,8,9)])

    # Replace the protagonist's horizontal two-pixel eye with the NPC eye style.
    if name=='04_spectacled_villager':
        glasses=[(11,6,10),(12,8,8),(12,10,10),(13,8,10)]
        if direction=='left':glasses=[(y,14-b,14-a) for y,a,b in glasses]
        paint('K',glasses)
        lens=9 if direction=='right' else 5
        paint('S',[(12,lens,lens)])
    else:
        eye=9 if direction=='right' else 5
        old_extra=8 if direction=='right' else 6
        paint('S',[(12,old_extra,old_extra)])
        paint('K',[(11,eye,eye),(12,eye,eye)])

    # Player checks become the NPC's clothes; skin at the hands is preserved.
    shirt='H' if name=='02_apron_villager' else 'C'
    for q,c in list(g.items()):
        x,y=q
        if y in (14+off,15+off) and base.get(q) in ('S','C'):
            g[q]=shirt
        if name=='02_apron_villager' and y==16+off and base.get(q)=='C':g[q]='H'
        if y>=18 and c=='C':g[q]='H'
    # A small open neckline instead of the player's plaid shirt.
    if base.get((7,14+off))=='S':g[7,14+off]='S'
    if name=='01_farmer':
        back=6 if direction=='right' else 8
        shoulder=5 if direction=='right' else 9
        front=9 if direction=='right' else 5
        paint('H',[(14,back,back),(15,shoulder,shoulder)],clothes=True)
        paint('S',[(15,front,front)],clothes=True)
    elif name=='02_apron_villager':
        front=[(14,8,8),(15,8,9),(16,8,8)]
        if direction=='left':front=[(y,14-b,14-a) for y,a,b in front]
        paint('C',front,clothes=True)
    elif name=='03_elder':
        collar=8 if direction=='right' else 6
        paint('H',[(14,collar,collar),(15,7,7)],clothes=True)
    elif direction=='right':
        # The satchel is on the character's right, visible from this side.
        paint('H',[(14,8,8),(15,5,5),(15,7,7),(16,6,6),(16,8,8)],clothes=True)

    assert all(0<=x<14 and 0<=y<20 for x,y in g)
    body=lambda image:{q for q in image if q[1]>=14+off}
    assert body(g)==body(base),'The player body outline must be retained'
    assert all(g[q]=='K' for q,c in base.items() if q[1]>=14+off and c=='K')
    return g


def write_frame(p,path,f,g,pal):
    pixels=[dict(x=x,y=y,color='#'+pal[g[x,y]] if (x,y) in g else '#00000000') for y in range(20) for x in range(14)]
    assert p.call('draw_pixels',sprite_path=path,layer_name='Layer 1',frame_number=f,pixels=pixels)['pixels_drawn']==280


def main():
    from PIL import Image,ImageDraw
    npcs=json.loads((HERE/'villagers_standing_drafts.json').read_text())['npcs']
    outputs=[HERE/(n['name']+'_walk_4dir_sidefix.aseprite') for n in npcs]
    if any(p.exists() for p in outputs):raise SystemExit('Side revisions already exist: protect any user edits.')
    protected=list(HERE.glob('*.aseprite'))+[ROOT/'assets/player_small.png',ROOT/'assets/player_small.aseprite']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    scratch=ROOT/'build_tmp/npc_review';scratch.mkdir(exist_ok=True)
    player=Image.open(ROOT/'assets/player_small.png').convert('RGBA')
    player_frame=lambda f:player.crop((f*14,0,(f+1)*14,20))
    all_frames=[];all_images=[]
    report=dict(frame_size=[14,20],sheet_size=[28,80],directions=list(DIRS),frames_per_direction=2,
                player_base_indices=PLAYER_BASES,player_base_poses=['passing','stride'],npcs=[],protected_sha256=hashes)
    p=Pixel()
    try:
        for npc,out in zip(npcs,outputs):
            name=npc['name'];pal=npc['palette'];inv={tuple(bytes.fromhex(c)):k for k,c in pal.items()}
            source=HERE/(name+'_walk_4dir.aseprite')
            info=p.call('get_sprite_info',sprite_path=source.as_posix())
            assert (info['width'],info['height'],info['frame_count'],info['layers'])==(14,20,8,['Layer 1'])
            srcpng=scratch/(name+'_before_sidefix.png')
            exported=p.call('export_spritesheet',sprite_path=source.as_posix(),output_path=srcpng.as_posix(),layout='horizontal',padding=0,include_json=True)
            metadata=json.loads(Path(exported['metadata_path']).read_text())
            records=metadata['frames'];records=list(records.values()) if isinstance(records,dict) else records
            strip=Image.open(srcpng).convert('RGBA');old=[]
            for record in records:
                b=record['frame'];old.append(strip.crop((b['x'],b['y'],b['x']+14,b['y']+20)))
            frames=[{(x,y):inv[im.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if im.getpixel((x,y))[3]} for im in old]
            for d,indices in PLAYER_BASES.items():
                for phase,index in enumerate(indices):frames[4+(2 if d=='right' else 0)+phase]=profile(player_pixels(player_frame(index)),name,d,phase)
            assert frames[4]!=frames[5] and frames[6]!=frames[7]
            all_frames.append(frames)
            p.call('save_as',sprite_path=source.as_posix(),output_path=out.as_posix())
            for f in range(4,8):write_frame(p,out.as_posix(),f+1,frames[f],pal)
            ims=[]
            for f,g in enumerate(frames):
                dest=scratch/(name+'_sidefix_'+str(f)+'.png')
                p.call('export_sprite',sprite_path=out.as_posix(),output_path=dest.as_posix(),format='png',frame_number=f+1)
                im=Image.open(dest).convert('RGBA');ims.append(im)
                assert im.size==(14,20) and set(im.getchannel('A').getdata())=={0,255}
                assert {c[:3] for c in im.getdata() if c[3]}<=set(fcremap.PALETTE)
                assert len({c[:3] for c in im.getdata() if c[3]})<=4
                if f<4:assert im.tobytes()==old[f].tobytes(),'Down/up changed'
                for y in range(20):
                    for x in range(14):
                        expected=tuple(bytes.fromhex(pal[g[x,y]]))+(255,) if (x,y) in g else (0,0,0,0)
                        assert im.getpixel((x,y))==expected
                remaining=set(g);stack=[remaining.pop()]
                while stack:
                    x,y=stack.pop()
                    for dx,dy in ((-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)):
                        q=(x+dx,y+dy)
                        if q in remaining:remaining.remove(q);stack.append(q)
                assert not remaining,(name,f,remaining)
                assert max(y for x,y in g)==19
            all_images.append(ims)
            atlas=p.call('create_canvas',width=28,height=80,color_mode='rgb')['file_path']
            p.call('set_palette',sprite_path=atlas,colors=['#'+v for v in pal.values()])
            pixels=[dict(x=x+14*(f%2),y=y+20*(f//2),color='#'+pal[c]) for f,g in enumerate(frames) for (x,y),c in g.items()]
            for at in range(0,len(pixels),700):p.call('draw_pixels',sprite_path=atlas,layer_name='Layer 1',frame_number=1,pixels=pixels[at:at+700])
            p.call('export_sprite',sprite_path=atlas,output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
            sidecar=json.loads(source.with_suffix('.json').read_text());sidecar['meta']['image']=out.with_suffix('.png').name
            sidecar['player_side_bases']=PLAYER_BASES
            out.with_suffix('.json').write_text(json.dumps(sidecar,indent=2)+'\n')
            report['npcs'].append(dict(name=name,down_up_pixel_identical=True,player_body_masks_preserved=True,frames=8,palette_colors=4,baseline=19))

        # Animated review, player reference first, then the four revised NPCs.
        board=p.call('create_canvas',width=104,height=100,color_mode='rgb')['file_path']
        p.call('set_palette',sprite_path=board,colors=list(dict.fromkeys(['#000000','#633e1b','#f0b890','#b6433d']+['#'+v for n in npcs for v in n['palette'].values()])))
        p.call('set_frame_duration',sprite_path=board,frame_number=1,duration_ms=200)
        p.call('add_frame',sprite_path=board,duration_ms=200)
        player_rows=((0,1),(3,4),(6,7),(8,9))
        for phase in range(2):
            pixels=[]
            for d in range(4):
                ref=player_frame(player_rows[d][phase])
                pixels.extend(dict(x=x+2,y=y+2+d*24,color='#%02x%02x%02x'%ref.getpixel((x,y))[:3]) for y in range(20) for x in range(14) if ref.getpixel((x,y))[3])
                for i,npc in enumerate(npcs):
                    pixels.extend(dict(x=x+22+i*20,y=y+2+d*24,color='#'+npc['palette'][c]) for (x,y),c in all_frames[i][d*2+phase].items())
            for at in range(0,len(pixels),700):p.call('draw_pixels',sprite_path=board,layer_name='Layer 1',frame_number=phase+1,pixels=pixels[at:at+700])
        p.call('create_tag',sprite_path=board,tag_name='player_and_npc_walks',from_frame=1,to_frame=2,direction='forward')
        review=HERE/'villagers_walk_sidefix_review.aseprite'
        p.call('save_as',sprite_path=board,output_path=review.as_posix())
        p.call('export_sprite',sprite_path=review.as_posix(),output_path=review.with_suffix('.png').as_posix(),format='png',frame_number=1)
        # Scaled preview is a separate artifact, never a change to native frames.
        scaled=scratch/'walk_sidefix_preview_4x.aseprite'
        p.call('save_as',sprite_path=review.as_posix(),output_path=scaled.as_posix())
        p.call('scale_sprite',sprite_path=scaled.as_posix(),scale_x=4,scale_y=4,algorithm='nearest')
        p.call('export_sprite',sprite_path=scaled.as_posix(),output_path=(HERE/'villagers_walk_sidefix_preview.gif').as_posix(),format='gif',frame_number=0)
    finally:p.p.terminate()
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
    report['approved_and_original_files_unchanged']=True
    (HERE/'villagers_walk_sidefix_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    preview=Image.new('RGB',(920,750),(43,43,51));draw=ImageDraw.Draw(preview)
    for i,label in enumerate(['Player base']+[n['name'] for n in npcs]):draw.text((95+i*160,8),label,fill='white')
    for row,(d,phase) in enumerate((('left',0),('left',1),('right',0),('right',1))):
        y=35+row*175;draw.text((8,y+45),d.upper()+' '+str(phase+1),fill='white')
        images=[player_frame(PLAYER_BASES[d][phase])]+[ims[4+(2 if d=='right' else 0)+phase] for ims in all_images]
        for i,im in enumerate(images):
            z=im.resize((112,160),Image.Resampling.NEAREST);preview.paste(z,(95+i*160,y),z)
    preview.save(HERE/'villagers_player_side_comparison.png')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
