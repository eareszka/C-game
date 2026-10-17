"""Detail the user-edited villagers through Aseprite MCP, preserving faces.

The saved layered review sheet is the current source of truth. Previous assets
remain untouched. Each revision stays 14x20 and uses its original four colours.
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

# Hand-placed detail strokes: (palette key, [(row, first x, last x), ...]).
DETAILS={
    '01_farmer':[
        ('H',[(6,4,10),(13,5,5),(13,9,9),(14,4,10),(16,4,4),(16,10,10)]),
        ('S',[(13,6,8),(15,5,5),(15,9,9)]),
        ('C',[(14,5,5),(14,9,9),(15,6,8)]),
        ('K',[(17,7,7)]),
    ],
    '02_apron_villager':[
        ('C',[(6,9,9),(14,5,9),(16,5,9),(17,4,10)]),
        ('S',[(13,7,7)]),
        ('H',[(16,6,8),(17,6,6),(17,8,8)]),
    ],
    '03_elder':[
        ('C',[(13,5,5),(13,9,9),(15,7,7),(16,7,7)]),
        ('H',[(14,5,5),(14,9,9),(15,6,6),(15,8,8),(16,9,10)]),
        ('K',[(15,7,7),(17,7,7)]),
    ],
    '04_spectacled_villager':[
        ('C',[(7,8,9)]),
        ('S',[(14,6,6),(14,8,8),(15,7,7)]),
        ('H',[(14,9,9),(15,8,8),(16,5,7),(17,5,7),(18,5,5),(18,9,9)]),
        ('S',[(16,6,6)]),
    ],
}


def main():
    from PIL import Image,ImageDraw
    oldreport=json.loads((HERE/'villagers_standing_drafts.json').read_text())
    npcs=oldreport['npcs']
    outputs=[HERE/(n['name']+'_standing_detailed_draft.aseprite') for n in npcs]
    if any(p.exists() for p in outputs):
        raise SystemExit('Detailed drafts exist; preserve any subsequent user edits.')
    protected=list(HERE.glob('*.aseprite'))+[ROOT/'assets/player_small.png',ROOT/'assets/player_small.aseprite']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    scratch=ROOT/'build_tmp/npc_review';scratch.mkdir(exist_ok=True)
    source=HERE/'villagers_standing_review.aseprite'
    before=[];after=[];report=dict(canvas=[14,20],source=str(source.relative_to(ROOT)),npcs=[],original_sha256=hashes)
    p=Pixel()
    try:
        p.call('export_sprite',sprite_path=source.as_posix(),output_path=(scratch/'edited_review_for_details.png').as_posix(),format='png',frame_number=1)
        saved=Image.open(scratch/'edited_review_for_details.png').convert('RGBA')
        assert saved.size==(98,24),'Inspect changed review layout before proceeding'
        for i,(npc,out) in enumerate(zip(npcs,outputs)):
            im=saved.crop((22+i*20,2,36+i*20,22));before.append(im)
            pal=npc['palette'];inv={tuple(bytes.fromhex(c)):k for k,c in pal.items()}
            g={(x,y):inv[im.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if im.getpixel((x,y))[3]}
            original=dict(g)
            for color,spans in DETAILS[npc['name']]:
                for y,a,b in spans:
                    for x in range(a,b+1):
                        assert (x,y) in g,(npc['name'],x,y)
                        assert y<8 or y>12,'User-edited face and eyes are protected'
                        assert not (y==15 and x in (4,10)),'User arm outlines are protected'
                        g[x,y]=color
            assert set(g)==set(original)
            assert all(g[x,y]==c for (x,y),c in original.items() if 8<=y<=12)
            canvas=p.call('create_canvas',width=14,height=20,color_mode='rgb')['file_path']
            p.call('set_palette',sprite_path=canvas,colors=['#'+c for c in pal.values()])
            pixels=[dict(x=x,y=y,color='#'+pal[c]) for (x,y),c in sorted(g.items())]
            r=p.call('draw_pixels',sprite_path=canvas,layer_name='Layer 1',frame_number=1,pixels=pixels)
            assert r['pixels_drawn']==len(pixels)
            p.call('save_as',sprite_path=canvas,output_path=out.as_posix())
            p.call('export_sprite',sprite_path=out.as_posix(),output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
            result=Image.open(out.with_suffix('.png')).convert('RGBA');after.append(result)
            assert result.size==(14,20)
            assert result.getchannel('A').tobytes()==im.getchannel('A').tobytes()
            assert set(result.getchannel('A').getdata())=={0,255}
            colors={c[:3] for c in result.getdata() if c[3]}
            assert len(colors)==4 and colors<=set(fcremap.PALETTE)
            for y in range(20):
                for x in range(14):
                    expected=tuple(bytes.fromhex(pal[g[x,y]]))+(255,) if (x,y) in g else (0,0,0,0)
                    assert result.getpixel((x,y))==expected
            report['npcs'].append(dict(name=npc['name'],palette=pal,changed_pixels=sum(g[q]!=original[q] for q in g),
                                      edited_face_preserved=True,edited_arm_outlines_preserved=True,
                                      silhouette_and_baseline_preserved=True,export_mismatches=0))
        # Upper row: user's saved versions. Lower row: detailed revisions.
        board=p.call('create_canvas',width=82,height=50,color_mode='rgb')['file_path']
        p.call('set_palette',sprite_path=board,colors=list(dict.fromkeys('#'+v for n in npcs for v in n['palette'].values())))
        for row,images in enumerate((before,after)):
            for i,(npc,im) in enumerate(zip(npcs,images)):
                layer='Layer 1' if row==0 and i==0 else ('Before - ' if row==0 else 'Detailed - ')+npc['name']
                if layer!='Layer 1':p.call('add_layer',sprite_path=board,layer_name=layer)
                pixels=[dict(x=x+4+i*20,y=y+2+row*26,color='#%02x%02x%02x'%im.getpixel((x,y))[:3]) for y in range(20) for x in range(14) if im.getpixel((x,y))[3]]
                p.call('draw_pixels',sprite_path=board,layer_name=layer,frame_number=1,pixels=pixels)
        review=HERE/'villagers_detailed_review.aseprite'
        p.call('save_as',sprite_path=board,output_path=review.as_posix())
        p.call('export_sprite',sprite_path=review.as_posix(),output_path=review.with_suffix('.png').as_posix(),format='png',frame_number=1)
    finally:p.p.terminate()
    # Fresh process verifies saved revisions, rather than trusting the draw call.
    p=Pixel()
    try:
        for out,im in zip(outputs,after):
            dest=scratch/(out.stem+'_reopened.png')
            p.call('export_sprite',sprite_path=out.as_posix(),output_path=dest.as_posix(),format='png',frame_number=1)
            assert Image.open(dest).convert('RGBA').tobytes()==im.tobytes()
    finally:p.p.terminate()
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
    report['reopened_exports_identical']=True;report['prior_drafts_and_player_unchanged']=True
    (HERE/'villagers_detailed_drafts.json').write_text(json.dumps(report,indent=2)+'\n')
    preview=Image.new('RGB',(920,600),(43,43,51));d=ImageDraw.Draw(preview)
    for row,images in enumerate((before,after)):
        for i,(npc,im) in enumerate(zip(npcs,images)):
            x=10+i*230;y=10+row*300
            d.text((x,y),('Before: ' if row==0 else 'Detailed: ')+npc['name'],fill='white')
            z=im.resize((140,200),Image.Resampling.NEAREST);preview.paste(z,(x+30,y+30),z)
            d.text((x,y+255),'Native',fill=(200,200,200));preview.paste(im,(x+55,y+250),im)
    preview.save(HERE/'villagers_detailed_comparison.png')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
