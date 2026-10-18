#include "courier.h"
#include "resident.h"
#include "resident_path.h"
#include "tilemap.h"
#include "towns.h"
#include "interior.h"
#include "collision.h"
#include "camera.h"
#include "save.h"
#include <SDL2/SDL_image.h>
#include <cassert>
#include <cstdio>
#include <cmath>
#include <cstring>
#include <vector>
#include <direct.h>
static Tilemap map;
static unsigned char explored[EXPLORE_H][EXPLORE_W];
static void roundtrip(CourierSave s) {
 assert(_chdir("build_tmp/courier_saves")==0);
 Player p={};p.equipped=(WeaponType)0;assert(save_write(387,10,20,p,explored));
 courier_reset();unsigned seed;float x,y;assert(save_read(&seed,&x,&y,&p,explored));
 auto after=courier_save();assert(!memcmp(&s,&after,sizeof(s)));
 assert(_chdir("../..")==0);
}
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SDL_SetMainReady();assert(SDL_Init(SDL_INIT_VIDEO)==0);IMG_Init(IMG_INIT_PNG);
 auto surface=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);auto r=SDL_CreateSoftwareRenderer(surface);
 tilemap_init_tile_cache(r);assert(story_people_init(r));tilemap_build_overworld_phase1(&map,387);tilemap_build_overworld_phase2(&map,387);
 _mkdir("build_tmp/courier_saves");resident_reset();assert(courier_valid(courier_save()));
 int doors[MAX_INTERIOR_DOORS],count=courier_doors(&map,doors,MAX_INTERIOR_DOORS),home=resident_town_door(&map,6);assert(count>1&&doors[count-1]==home);
 int total=0;for(int i=0;i<map.num_doors;i++){auto d=map.doors[i];auto t=map.towns[0];if(d.x>=t.x&&d.x<t.x+TOWN_W&&d.y>=t.y&&d.y<t.y+TOWN_H)total++;}assert(total==count);
 printf("Town 0: %d front doors, home last\n",count);
 InteriorMap room;interior_load(&room,6);interior_draw(&room,r,tilemap_get_town_tex());Camera camera={0,0,640,480,1,0,0};auto initial=courier_save();StoryNpcPos actor={COURIER_ID,initial.x,initial.y,-1};courier_draw(actor,r,&camera);SDL_RenderReadPixels(r,nullptr,SDL_PIXELFORMAT_RGBA32,surface->pixels,surface->pitch);assert(!IMG_SavePNG(surface,"build_tmp/npc_review/courier_couch.png"));
 courier_tick(&map,74.5f);assert(courier_save().phase==CR_SLEEP);courier_tick(&map,.5f);assert(courier_save().phase==CR_LEAVE_HOME);courier_reset();
 unsigned phases=0;int cycles=0;int visits[MAX_INTERIOR_DOORS]={};double delivery=0;
 for(int i=0;i<100000&&cycles<2;i++){
  auto before=courier_save();courier_tick(&map,.05f);auto s=courier_save();assert(courier_valid(s));
  if(s.location<0)assert(can_occupy(&map,s.x,s.y,tilemap_pixel_solid));else assert(interior_feet_fit(&room,s.x,s.y));
  if(!(phases&(1u<<s.phase))){phases|=1u<<s.phase;printf("phase %d room %d at %.0f %.0f\n",s.phase,s.location,s.x,s.y);roundtrip(s);}
  if(s.phase==CR_DELIVER && before.phase!=CR_DELIVER){delivery=s.elapsed;assert(s.stop>=0&&s.stop<count);auto stop=resident_outside(&map,doors[s.stop]);assert(std::hypot(s.x-stop.x,s.y-stop.y)<.1f);}
  else if(before.phase==CR_DELIVER){delivery+=s.phase==CR_DELIVER?s.elapsed-before.elapsed:3-before.elapsed;if(s.phase!=CR_DELIVER){assert(std::fabs(delivery-3)<.0001);visits[before.stop]++;}}
  if(before.phase!=CR_SLEEP&&s.phase==CR_SLEEP){cycles++;for(int j=0;j<count;j++)assert(visits[j]==cycles);}
 }
 if(cycles!=2){auto s=courier_save();printf("stalled phase %d stop %d elapsed %g at %g %g\n",s.phase,s.stop,s.elapsed,s.x,s.y);}
 assert(cycles==2&&phases==((1u<<6)-1));puts("PASS two couch/door/home cycles, every entrance once per round, exactly three-second stops and collision checks");
 auto talking=courier_save();talking.phase=CR_DELIVER;talking.location=-1;auto doorstep=resident_outside(&map,doors[0]);talking.x=doorstep.x;talking.y=doorstep.y;talking.elapsed=1;talking.stop=0;assert(courier_restore(talking));courier_face(FACE_LEFT);courier_tick(&map,10);auto frozen=courier_save();assert(!memcmp(&talking,&frozen,sizeof(talking)));courier_resume();courier_tick(&map,1);assert(std::fabs(courier_save().elapsed-2)<.001);
 StoryWhere where={STATE_OVERWORLD,&map,-1,-1,nullptr,false};assert(courier_here(where,&actor));assert(strstr(story_npc_answer(actor,where,1),"Bloom"));
 resident_reset();resident_advance_hour(&map);assert(courier_save().phase==CR_LEAVE_HOME);puts("PASS conversation pause/resume, Bloom dialogue, offscreen hour skip");
 // The v16 save lacks only the courier footer; all prior residents remain intact.
 roundtrip(courier_save());assert(_chdir("build_tmp/courier_saves")==0);FILE* f=fopen("save.dat","rb");assert(f);fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);std::vector<unsigned char> bytes(n);assert(fread(bytes.data(),1,n,f)==n);fclose(f);bytes.resize(n-sizeof(CourierSave));unsigned version=16;memcpy(bytes.data()+4,&version,4);f=fopen("save.dat","wb");assert(fwrite(bytes.data(),1,bytes.size(),f)==bytes.size());fclose(f);Player p={};unsigned seed;float x,y;assert(save_read(&seed,&x,&y,&p,explored));assert(courier_save().phase==CR_SLEEP&&courier_save().elapsed==0);assert(_chdir("../..")==0);
 puts("PASS save/load every phase and v16 migration; couriercheck passed");return 0;
}
