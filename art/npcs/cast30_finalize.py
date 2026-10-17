"""Give native Aseprite tags the player's four-beat cadence and audit the pack."""
from pathlib import Path
import json,sys,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'art/npcs/cast30';TMP=ROOT/'build_tmp/npc_review/cast30'
sys.path.insert(0,str(ROOT/'art/direction'))
from mcpc import Pixel
from villager_walk_sidefix import write_frame
from villager_walk_4dir import validate_frame

def main():
 manifest=json.loads((HERE/'manifest.json').read_text());p=Pixel()
 try:
  for n in manifest['designs']:
   path=HERE/(n['name']+'.aseprite');atlas=Image.open(path.with_suffix('.png')).convert('RGBA');pal=n['palette'];inv={tuple(bytes.fromhex(c)):k for k,c in pal.items()}
   unique=[atlas.crop((14*(i%3),20*(i//3),14*(i%3+1),20*(i//3+1))) for i in range(12)]
   expected=[unique[3*d+pose] for d in range(4) for pose in (1,0,2)]
   def reopen(suffix):
    r=p.call('export_spritesheet',sprite_path=path.as_posix(),output_path=(TMP/(n['name']+suffix+'.png')).as_posix(),layout='horizontal',padding=0,include_json=True)
    m=json.loads(Path(r['metadata_path']).read_text());rec=m['frames'];rec=list(rec.values()) if isinstance(rec,dict) else rec
    strip=Image.open(r['spritesheet_path']).convert('RGBA');cells=[strip.crop((f['frame']['x'],f['frame']['y'],f['frame']['x']+14,f['frame']['y']+20)) for f in rec]
    return m,rec,cells
   meta,rec,actual=reopen('_before_tag_fix')
   # Do not erase a user's saved edits if a review happened during generation.
   assert len(actual)==12 and all(a.tobytes()==b.tobytes() for a,b in zip(actual,unique)),(path,'saved edits differ from generated atlas')
   for d,tag in enumerate(('down','up','left','right')):
    for phase in (0,1):
     im=expected[3*d+phase];g={(x,y):inv[im.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if im.getpixel((x,y))[3]}
     write_frame(p,path.as_posix(),3*d+phase+1,g,pal)
    p.call('delete_tag',sprite_path=path.as_posix(),tag_name=tag)
    p.call('create_tag',sprite_path=path.as_posix(),tag_name=tag,from_frame=3*d+1,to_frame=3*d+3,direction='pingpong')
   meta,rec,actual=reopen('_final_verified')
   assert len(actual)==12 and all(a.tobytes()==b.tobytes() for a,b in zip(actual,expected))
   assert all(f['duration']==200 for f in rec)
   tags=sorted(meta['meta']['frameTags'],key=lambda t:t['from'])
   assert [(t['name'],t['from'],t['to'],t['direction']) for t in tags]==[(tag,3*d,3*d+2,'pingpong') for d,tag in enumerate(('down','up','left','right'))]
   for i,im in enumerate(unique):
    g={(x,y):inv[im.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if im.getpixel((x,y))[3]};validate_frame(im,g,pal)
   assert all(len({unique[3*d+j].tobytes() for j in range(3)})==3 for d in range(4)),(n['name'],'duplicate directional poses')
   data=json.loads(path.with_suffix('.json').read_text());data['native_aseprite']=dict(stored_pose_order=['step_a','standing','step_b'],tag_playback='pingpong',idle_frames_zero_based=[1,4,7,10],note='PNG/JSON atlas keeps standing, step_a, step_b order. Native tag loops step_a, standing, step_b, standing.')
   path.with_suffix('.json').write_text(json.dumps(data,indent=2)+'\n')
   print(n['name']+': native tags play exact four-beat player cadence; all saved cels and atlas verified',flush=True)
  # Independently reopen every animated page. Standing beats must be identical,
  # and both walking beats must differ; this also catches inherited cel residue.
  for page in range(1,4):
   path=HERE/f'cast30_page{page}_review.aseprite'
   r=p.call('export_spritesheet',sprite_path=path.as_posix(),output_path=(TMP/f'page{page}_final_verified.png').as_posix(),layout='horizontal',padding=0,include_json=True)
   meta=json.loads(Path(r['metadata_path']).read_text());rec=list(meta['frames'].values());strip=Image.open(r['spritesheet_path']).convert('RGBA')
   ims=[strip.crop((f['frame']['x'],f['frame']['y'],f['frame']['x']+104,f['frame']['y']+200)) for f in rec]
   assert len(ims)==4 and ims[1].tobytes()==ims[3].tobytes() and ims[0].tobytes()!=ims[2].tobytes()
   for beat,pose in enumerate((1,0,2,0)):
    for local in range(10):
     n=manifest['designs'][(page-1)*10+local];atlas=Image.open(HERE/(n['name']+'.png')).convert('RGBA')
     for d in range(4):
      x=2+20*(local%5);y=2+100*(local//5)+24*d
      assert ims[beat].crop((x,y,x+14,y+20)).tobytes()==atlas.crop((14*pose,20*d,14*(pose+1),20*(d+1))).tobytes()
   print(f'Review page {page}: all 160 posed placements verified',flush=True)
   preview=TMP/f'page{page}_preview_3x.aseprite'
   p.call('save_as',sprite_path=path.as_posix(),output_path=preview.as_posix())
   p.call('scale_sprite',sprite_path=preview.as_posix(),scale_x=3,scale_y=3,algorithm='nearest')
   p.call('export_sprite',sprite_path=preview.as_posix(),output_path=(HERE/f'cast30_page{page}_animated.gif').as_posix(),format='gif',frame_number=0)
 finally:p.p.terminate()
 assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in manifest['protected_sha256'].items())
 manifest['native_tags_player_cadence_verified']=True;manifest['all_three_review_pages_independently_verified']=True
 manifest['output_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.suffix in ('.aseprite','.png','.json') and p.name!='manifest.json'}
 (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('FINAL VALIDATION PASSED',flush=True)

if __name__=='__main__':main()
