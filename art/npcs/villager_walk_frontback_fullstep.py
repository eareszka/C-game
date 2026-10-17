"""Match NPC down/up views to the player-based alternating full walking steps.

Copies the latest side-fixed eight-frame files, edits only frames 1-4 using
the player's front/back left and right step poses, and verifies frames 5-8 stay
pixel identical. All artwork is painted through the Aseprite pixel MCP.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'art/direction'))
from mcpc import Pixel
from villager_walk_sidefix import player_pixels,write_frame
from villager_walk_4dir import validate_frame

DIRS=('down','up','left','right')
PLAYER_BASES={'down':(1,2),'up':(4,5),'left':(6,7),'right':(8,9)}


def portrait(base,name,direction,phase):
    off=0
    g={q:c for q,c in base.items() if q[1]>9+off}
    if name=='01_farmer':
        rows={5:(5,9),6:(4,10),7:(3,11),8:(2,12),9:(2,12)}
    elif name=='02_apron_villager':
        rows={5:(8,10),6:(5,11),7:(4,11),8:(3,12),9:(2,12)}
        if direction=='up':rows={y:(14-b,14-a) for y,(a,b) in rows.items()}
    else:
        rows={6:(5,9),7:(4,10),8:(3,11),9:(2,12)}
    head={(x,y+off) for y,(a,b) in rows.items() for x in range(a,b+1)}
    op=set(g)|head
    for x,y in head:
        g[x,y]='K' if any((x+dx,y+dy) not in op for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) else 'H'

    def paint(c,spans,clothes=False):
        for y,a,b in spans:
            for x in range(a,b+1):
                q=(x,y+off)
                assert q in g,(name,direction,phase,q)
                if clothes and base.get(q)=='K':continue
                g[q]=c

    if name=='01_farmer':
        paint('C',[(6,5,9),(7,4,10),(8,3,11)])
        paint('H',[(7,4,10)])
    elif name=='02_apron_villager':
        tie=9 if direction=='down' else 5
        paint('C',[(7,tie,tie)])
    elif name=='04_spectacled_villager':
        paint('C',[(7,8,9)] if direction=='down' else [(7,5,6)])

    if direction=='down':
        # Clean cheeks and the approved vertical eye shapes, never the hero eyes.
        paint('S',[(10,4,10),(11,4,10),(12,4,10),(13,4,10)])
        if name=='01_farmer':
            paint('S',[(9,6,6)])
            paint('H',[(10,4,4),(10,10,10)])
        elif name=='02_apron_villager':
            paint('S',[(9,5,9)])
        elif name=='03_elder':
            paint('S',[(7,6,8),(8,5,9),(9,4,10)])
            paint('H',[(12,4,4),(12,10,10),(13,4,4),(13,10,10)])
        if name=='04_spectacled_villager':
            paint('K',[(11,4,6),(11,8,10),(12,4,4),(12,6,8),(12,10,10),(13,4,6),(13,8,10)])
        else:
            paint('K',[(10,5,5),(11,5,5),(10,9,9),(11,9,9)])
    else:
        # Back of the head: hair/nape, never front-facing eyes or glasses.
        if name=='02_apron_villager':paint('H',[(13,5,9)])
        if name=='03_elder':
            paint('S',[(7,6,8),(8,5,9),(9,5,9),(10,6,8)])
            paint('H',[(13,5,5),(13,9,9)])

    # Remove the protagonist's checks; leave its black joints and outside hands.
    shirt='H' if name=='02_apron_villager' else 'C'
    for q,c in list(g.items()):
        x,y=q
        if 14+off<=y<=16+off and 4<=x<=10 and base.get(q) in ('S','C'):g[q]=shirt
        if y>=18 and c=='C':g[q]='H'

    if name=='01_farmer':
        paint('H',[(14,5,9),(15,4,4),(15,10,10),(16,4,4),(16,10,10)],clothes=True)
        paint('C',[(14,5,5),(14,9,9),(15,5,9),(16,5,9)],clothes=True)
        if direction=='down':paint('S',[(14,7,7),(15,5,5),(15,9,9)],clothes=True)
        else:
            paint('H',[(15,6,8)],clothes=True)
    elif name=='02_apron_villager':
        if direction=='down':
            paint('C',[(14,6,8),(15,5,9),(16,4,10)],clothes=True)
            paint('S',[(14,7,7)],clothes=True)
            paint('H',[(16,7,7)],clothes=True)
        else:
            paint('C',[(15,5,9),(16,7,7)],clothes=True)
    elif name=='03_elder':
        if direction=='down':
            paint('H',[(14,5,5),(14,9,9),(15,6,6),(15,8,8),(16,7,7)],clothes=True)
            paint('S',[(14,7,7)],clothes=True)
        else:
            paint('H',[(14,5,9),(16,4,4),(16,10,10)],clothes=True)
    else:
        if direction=='down':
            paint('S',[(14,6,8)],clothes=True)
            paint('H',[(14,9,9),(15,5,8),(16,5,7)],clothes=True)
            paint('S',[(16,6,6)],clothes=True)
        else:
            paint('H',[(14,5,5),(15,6,9),(16,7,9)],clothes=True)

    body=lambda image:{q for q in image if q[1]>=14+off}
    assert body(g)==body(base),'Player body silhouette changed'
    assert all(g[q]=='K' for q,c in base.items() if q[1]>=14+off and c=='K')
    assert all(g[q]=='S' for q,c in base.items() if q[1]>=14+off and c=='S' and q[0] in (2,3,11,12))
    return g


def main():
    from PIL import Image,ImageDraw
    npcs=json.loads((HERE/'villagers_standing_drafts.json').read_text())['npcs']
    outputs=[HERE/(n['name']+'_walk_4dir_fullstep.aseprite') for n in npcs]
    if any(p.exists() for p in outputs):raise SystemExit('Full-step sheets exist: preserve any subsequent user edits.')
    protected=list(HERE.glob('*.aseprite'))+[ROOT/'assets/player_small.png',ROOT/'assets/player_small.aseprite']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    scratch=ROOT/'build_tmp/npc_review';scratch.mkdir(exist_ok=True)
    player=Image.open(ROOT/'assets/player_small.png').convert('RGBA')
    player_frame=lambda f:player.crop((f*14,0,(f+1)*14,20))
    report=dict(frame_size=[14,20],sheet_size=[28,80],directions=list(DIRS),frames_per_direction=2,
                player_base_indices=PLAYER_BASES,player_base_poses=['left_step','right_step'],npcs=[],protected_sha256=hashes)
    all_frames=[];all_images=[]
    p=Pixel()
    try:
        for npc,out in zip(npcs,outputs):
            name=npc['name'];pal=npc['palette'];inv={tuple(bytes.fromhex(c)):k for k,c in pal.items()}
            source=HERE/(name+'_walk_4dir_matched.aseprite')
            info=p.call('get_sprite_info',sprite_path=source.as_posix())
            assert (info['width'],info['height'],info['frame_count'],info['layers'])==(14,20,8,['Layer 1'])
            srcpng=scratch/(name+'_before_frontback.png')
            r=p.call('export_spritesheet',sprite_path=source.as_posix(),output_path=srcpng.as_posix(),layout='horizontal',padding=0,include_json=True)
            metadata=json.loads(Path(r['metadata_path']).read_text());records=metadata['frames'];records=list(records.values()) if isinstance(records,dict) else records
            strip=Image.open(srcpng).convert('RGBA');old=[]
            for record in records:
                b=record['frame'];old.append(strip.crop((b['x'],b['y'],b['x']+14,b['y']+20)))
            frames=[{(x,y):inv[im.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if im.getpixel((x,y))[3]} for im in old]
            for d in ('down','up'):
                for phase,index in enumerate(PLAYER_BASES[d]):frames[(0 if d=='down' else 2)+phase]=portrait(player_pixels(player_frame(index)),name,d,phase)
            assert all(frames[2*d]!=frames[2*d+1] for d in range(4))
            all_frames.append(frames)
            p.call('save_as',sprite_path=source.as_posix(),output_path=out.as_posix())
            for f in range(4):write_frame(p,out.as_posix(),f+1,frames[f],pal)
            ims=[]
            for f,g in enumerate(frames):
                dest=scratch/(name+'_fullstep_'+str(f)+'.png')
                p.call('export_sprite',sprite_path=out.as_posix(),output_path=dest.as_posix(),format='png',frame_number=f+1)
                im=Image.open(dest).convert('RGBA');validate_frame(im,g,pal);ims.append(im)
                if f>=4:assert im.tobytes()==old[f].tobytes(),'Corrected side view changed'
            all_images.append(ims)
            atlas=p.call('create_canvas',width=28,height=80,color_mode='rgb')['file_path']
            p.call('set_palette',sprite_path=atlas,colors=['#'+v for v in pal.values()])
            pixels=[dict(x=x+14*(f%2),y=y+20*(f//2),color='#'+pal[c]) for f,g in enumerate(frames) for (x,y),c in g.items()]
            for at in range(0,len(pixels),700):p.call('draw_pixels',sprite_path=atlas,layer_name='Layer 1',frame_number=1,pixels=pixels[at:at+700])
            p.call('export_sprite',sprite_path=atlas,output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
            sidecar=json.loads(source.with_suffix('.json').read_text());sidecar['meta']['image']=out.with_suffix('.png').name;sidecar['player_base_indices']=PLAYER_BASES
            out.with_suffix('.json').write_text(json.dumps(sidecar,indent=2)+'\n')
            report['npcs'].append(dict(name=name,left_right_pixel_identical=True,player_front_back_body_masks_preserved=True,frames=8,palette_colors=4,baseline=19))

        # Entire fullstep pack, with the actual player in the first column.
        board=p.call('create_canvas',width=104,height=100,color_mode='rgb')['file_path']
        p.call('set_palette',sprite_path=board,colors=list(dict.fromkeys(['#000000','#633e1b','#f0b890','#b6433d']+['#'+v for n in npcs for v in n['palette'].values()])))
        p.call('set_frame_duration',sprite_path=board,frame_number=1,duration_ms=200)
        p.call('add_frame',sprite_path=board,duration_ms=200)
        for phase in range(2):
            pixels=[]
            for d,label in enumerate(DIRS):
                ref=player_frame(PLAYER_BASES[label][phase])
                pixels.extend(dict(x=x+2,y=y+2+d*24,color='#%02x%02x%02x'%ref.getpixel((x,y))[:3]) for y in range(20) for x in range(14) if ref.getpixel((x,y))[3])
                for i,npc in enumerate(npcs):
                    pixels.extend(dict(x=x+22+i*20,y=y+2+d*24,color='#'+npc['palette'][c]) for (x,y),c in all_frames[i][d*2+phase].items())
            for at in range(0,len(pixels),700):p.call('draw_pixels',sprite_path=board,layer_name='Layer 1',frame_number=phase+1,pixels=pixels[at:at+700])
        p.call('create_tag',sprite_path=board,tag_name='fullstep_walks',from_frame=1,to_frame=2,direction='forward')
        review=HERE/'villagers_walk_fullstep_review.aseprite'
        p.call('save_as',sprite_path=board,output_path=review.as_posix())
        p.call('export_sprite',sprite_path=review.as_posix(),output_path=review.with_suffix('.png').as_posix(),format='png',frame_number=1)
        scaled=scratch/'walk_fullstep_preview_4x.aseprite'
        p.call('save_as',sprite_path=review.as_posix(),output_path=scaled.as_posix())
        p.call('scale_sprite',sprite_path=scaled.as_posix(),scale_x=4,scale_y=4,algorithm='nearest')
        p.call('export_sprite',sprite_path=scaled.as_posix(),output_path=(HERE/'villagers_walk_fullstep_preview.gif').as_posix(),format='gif',frame_number=0)
    finally:p.p.terminate()
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
    report['approved_and_previous_files_unchanged']=True
    (HERE/'villagers_walk_fullstep_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    preview=Image.new('RGB',(920,750),(43,43,51));draw=ImageDraw.Draw(preview)
    for i,label in enumerate(['Player base']+[n['name'] for n in npcs]):draw.text((95+i*160,8),label,fill='white')
    for row,(d,phase) in enumerate((('down',0),('down',1),('up',0),('up',1))):
        y=35+row*175;draw.text((8,y+45),d.upper()+' '+str(phase+1),fill='white')
        images=[player_frame(PLAYER_BASES[d][phase])]+[ims[(0 if d=='down' else 2)+phase] for ims in all_images]
        for i,im in enumerate(images):
            z=im.resize((112,160),Image.Resampling.NEAREST);preview.paste(z,(95+i*160,y),z)
    preview.save(HERE/'villagers_player_frontback_comparison.png')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
