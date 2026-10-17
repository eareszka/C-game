"""Four original 14x20 villager stills, painted through the Aseprite pixel MCP.

The player is a scale reference, not a recolouring base. Each NPC is a separate
flat drawing with a distinct silhouette and eye treatment. No game integration.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'art/direction'))
from mcpc import Pixel
import fcremap

HERE = Path(__file__).resolve().parent
NPCS = [
    dict(name='01_farmer', eyes='single-pixel dot eyes',
         pal=dict(K='000000', S='f0b890', H='633e1b', C='235436'),
         shape={4:[(5,9)],5:[(4,10)],6:[(3,11)],7:[(2,12)],8:[(3,11)],9:[(3,11)],10:[(3,11)],11:[(3,11)],12:[(4,10)],13:[(4,10)],14:[(3,11)],15:[(2,12)],16:[(3,11)],17:[(4,10)],18:[(4,6),(8,10)],19:[(4,6),(8,10)]}),
    dict(name='02_apron_villager', eyes='two inward-slanting eyes',
         pal=dict(K='000000', S='f0b890', H='b6433d', C='e8e0c0'),
         shape={4:[(8,10)],5:[(5,11)],6:[(4,11)],7:[(3,12)],8:[(3,12)],9:[(3,12)],10:[(3,12)],11:[(3,12)],12:[(3,12)],13:[(3,12)],14:[(3,11)],15:[(2,12)],16:[(3,11)],17:[(3,11)],18:[(4,6),(8,10)],19:[(4,6),(8,10)]}),
    dict(name='03_elder', eyes='closed smiling arches',
         pal=dict(K='000000', S='f0b890', H='9797aa', C='2850a0'),
         shape={5:[(5,9)],6:[(4,10)],7:[(3,11)],8:[(3,11)],9:[(3,11)],10:[(3,11)],11:[(3,11)],12:[(3,11)],13:[(4,10)],14:[(3,11)],15:[(2,12)],16:[(3,11)],17:[(4,10)],18:[(4,6),(8,10)],19:[(4,6),(8,10)]}),
    dict(name='04_spectacled_villager', eyes='round spectacle lenses joined by a bridge',
         pal=dict(K='000000', S='f0b890', H='633e1b', C='fc74b4'),
         shape={6:[(5,9)],7:[(4,10)],8:[(3,11)],9:[(2,12)],10:[(2,12)],11:[(3,11)],12:[(3,11)],13:[(4,10)],14:[(3,11)],15:[(2,12)],16:[(3,11)],17:[(4,10)],18:[(4,6),(8,10)],19:[(4,6),(8,10)]}),
]


def drawing(npc):
    op={(x,y) for y,spans in npc['shape'].items() for a,b in spans for x in range(a,b+1)}
    g={p:('K' if any((p[0]+dx,p[1]+dy) not in op for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) else 'H') for p in op}

    def paint(c,spans):
        for y,a,b in spans:
            for x in range(a,b+1):
                assert (x,y) in op,(npc['name'],x,y)
                g[x,y]=c

    name=npc['name']
    if name=='01_farmer':
        paint('C',[(5,5,9),(6,4,10),(7,3,11)])
        paint('S',[(8,5,9),(9,4,10),(10,4,10),(11,4,10),(12,5,9),
                   (15,3,3),(15,11,11)])
        paint('C',[(13,5,9),(14,4,10),(15,5,9),(16,4,10),(17,5,9)])
        paint('H',[(14,5,5),(14,9,9),(15,5,5),(15,9,9),(18,5,5),(18,9,9)])
        paint('K',[(10,5,5),(10,9,9)])
    elif name=='02_apron_villager':
        paint('S',[(8,5,9),(9,4,10),(10,4,10),(11,4,10),(12,5,9),
                   (15,3,3),(15,11,11)])
        paint('C',[(13,6,8),(14,6,8),(15,5,9),(16,5,9),(17,5,9)])
        # Slanted marks, unlike the hero's two horizontal two-pixel eyes.
        paint('K',[(10,5,5),(11,6,6),(11,8,8),(10,9,9),(12,7,7)])
    elif name=='03_elder':
        paint('S',[(7,5,9),(8,4,10),(9,4,10),(10,4,10),(11,4,10),
                   (15,3,3),(15,11,11)])
        paint('H',[(12,4,10),(13,5,9)])
        paint('C',[(14,4,10),(15,5,9),(16,4,10),(17,5,9)])
        paint('K',[(9,5,5),(9,9,9),(10,4,4),(10,6,6),(10,8,8),(10,10,10),
                   (12,7,7),(15,7,7),(16,7,7)])
        paint('H',[(18,5,5),(18,9,9)])
    else:
        paint('S',[(9,5,9),(10,4,10),(11,4,10),(12,4,10),(13,5,9),
                   (15,3,3),(15,11,11)])
        paint('C',[(14,4,10),(15,5,9),(16,4,10),(17,5,9),(18,5,5),(18,9,9)])
        # Small round frames, with skin-colour lens centres, no added white.
        paint('K',[(10,4,6),(10,8,10),(11,4,4),(11,6,8),(11,10,10),
                   (12,4,6),(12,8,10)])
    return g


def main():
    from PIL import Image,ImageDraw
    outputs=[HERE/(n['name']+'_standing_draft.aseprite') for n in NPCS]
    if any(p.exists() for p in outputs) and '--refresh-unreviewed' not in sys.argv:
        raise SystemExit('Review drafts already exist: preserve possible user edits.')
    protected=[ROOT/'assets/player_small.png',ROOT/'assets/player_small.aseprite']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    player=Image.open(protected[0]).convert('RGBA').crop((0,0,14,20))
    report=dict(canvas=[14,20],pose='front standing',protected_sha256=hashes,npcs=[])
    images=[]
    p=Pixel()
    try:
        for npc,out in zip(NPCS,outputs):
            g=drawing(npc);pal=npc['pal']
            assert {tuple(bytes.fromhex(c)) for c in pal.values()}<=set(fcremap.PALETTE)
            source=p.call('create_canvas',width=14,height=20,color_mode='rgb')['file_path']
            p.call('set_palette',sprite_path=source,colors=['#'+c for c in pal.values()])
            pixels=[dict(x=x,y=y,color='#'+pal[c]) for (x,y),c in sorted(g.items())]
            r=p.call('draw_pixels',sprite_path=source,layer_name='Layer 1',frame_number=1,pixels=pixels)
            assert r['pixels_drawn']==len(pixels)
            p.call('save_as',sprite_path=source,output_path=out.as_posix())
            p.call('export_sprite',sprite_path=out.as_posix(),output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
            info=p.call('get_sprite_info',sprite_path=out.as_posix())
            assert info['frame_count']==1 and (info['width'],info['height'])==(14,20)
            im=Image.open(out.with_suffix('.png')).convert('RGBA')
            expected={(x,y):tuple(bytes.fromhex(pal[c]))+(255,) for (x,y),c in g.items()}
            actual={(x,y):im.getpixel((x,y)) for y in range(20) for x in range(14) if im.getpixel((x,y))[3]}
            assert expected==actual
            assert set(im.getchannel('A').getdata())=={0,255}
            assert len({c[:3] for c in actual.values()})==4
            images.append(im)
            report['npcs'].append(dict(name=npc['name'],eyes=npc['eyes'],palette=pal,occupied_bounds=im.getchannel('A').getbbox(),pixels=len(g),export_mismatches=0))
        # Comparison document: existing player at left, then the four new NPCs.
        # This is a review board, not an in-game sprite sheet.
        review=p.call('create_canvas',width=98,height=24,color_mode='rgb')['file_path']
        review_colors=list(dict.fromkeys('#'+c for n in NPCS for c in n['pal'].values()))
        p.call('set_palette',sprite_path=review,colors=review_colors)
        for i,(label,im) in enumerate([('Reference - player',player)]+[(n['name'],im) for n,im in zip(NPCS,images)]):
            layer='Layer 1' if i==0 else label
            if i:p.call('add_layer',sprite_path=review,layer_name=layer)
            pix=[dict(x=x+2+i*20,y=y+2,color='#%02x%02x%02x'%im.getpixel((x,y))[:3]) for y in range(20) for x in range(14) if im.getpixel((x,y))[3]]
            p.call('draw_pixels',sprite_path=review,layer_name=layer,frame_number=1,pixels=pix)
        reviewout=HERE/'villagers_standing_review.aseprite'
        p.call('save_as',sprite_path=review,output_path=reviewout.as_posix())
        p.call('export_sprite',sprite_path=reviewout.as_posix(),output_path=reviewout.with_suffix('.png').as_posix(),format='png',frame_number=1)
    finally:p.p.terminate()
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
    report['originals_unchanged']=True
    (HERE/'villagers_standing_drafts.json').write_text(json.dumps(report,indent=2)+'\n')
    # Labelled inspection board assembled from actual plugin exports.
    board=Image.new('RGB',(1100,330),(43,43,51));d=ImageDraw.Draw(board)
    for i,(label,im) in enumerate([('Player reference',player)]+[(n['name'],im) for n,im in zip(NPCS,images)]):
        x=10+i*220;d.text((x,12),label,fill='white')
        z=im.resize((140,200),Image.Resampling.NEAREST);board.paste(z,(x+25,40),z)
        d.text((x,265),'Native',fill=(200,200,200));board.paste(im,(x+55,260),im)
    board.save(HERE/'villagers_standing_comparison.png')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
