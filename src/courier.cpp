#include "courier.h"
#include "resident.h"
#include "resident_path.h"
#include "interior.h"
#include "tilemap.h"
#include "towns.h"
#include "collision.h"
#include "camera.h"
#include "npc_sleep.h"
#include "battle.h"
#include <SDL2/SDL_image.h>
#include <algorithm>
#include <cmath>
#include <vector>
namespace {
using Point=ResidentPoint;
constexpr unsigned MAGIC=0x43555231;
constexpr int HOME=6;
constexpr float SPEED=90, SLEEP_TIME=3600.0f/48;
constexpr Point COUCH={251,218}; // floor at the front of room 6's couch
CourierSave c={MAGIC,COUCH.x,COUCH.y,0,0,0,CR_SLEEP,HOME,FACE_DOWN,0,0,0};
InteriorMap room;
std::vector<Point> route;
Point route_start={};size_t next=0;
bool moving=false,talking=false;
float retry=0;
int resume_facing=FACE_DOWN;
SDL_Texture *art=nullptr,*sleep_art=nullptr;
int location(int phase){return phase==CR_TO_DOOR||phase==CR_DELIVER||phase==CR_ENTER_HOME?-1:HOME;}
void phase(int p){c.phase=p;c.elapsed=0;route.clear();next=0;retry=0;moving=false;}
bool path(const Tilemap* map,Point target) {
    if(c.location<0)return resident_trail_route(map,{c.x,c.y},target,route,route_start,next);
    interior_load(&room,HOME);
    auto fits=[](Point p){return interior_feet_fit(&room,p.x,p.y);};
    return resident_find_route({c.x,c.y},target,4,0,0,160,120,false,fits,
        [&](Point a,Point b,bool){return resident_way_fits(a,b,fits);},route,route_start,next);
}
void transfer(const Tilemap* map,int home) {
    Point p;
    if(c.phase==CR_LEAVE_HOME){c.location=-1;p=resident_outside(map,home);c.stop=0;phase(CR_TO_DOOR);}
    else {c.location=HOME;p=resident_entry(HOME);phase(CR_TO_COUCH);}
    c.x=p.x;c.y=p.y;c.flash=ACTOR_APPEAR_T;c.transfer_pending=0;
}
}
int courier_doors(const Tilemap* map,int* out,int capacity) {
    if(!map||!out||capacity<=0)return 0;
    std::vector<int> doors;
    const auto& town=map->towns[0];
    int home=resident_town_door(map,HOME);
    for(int i=0;i<map->num_doors;i++) {
        const auto& d=map->doors[i];
        if(i!=home&&d.x>=town.x&&d.x<town.x+TOWN_W&&d.y>=town.y&&d.y<town.y+TOWN_H)doors.push_back(i);
    }
    std::sort(doors.begin(),doors.end(),[&](int a,int b){
        const auto& x=map->doors[a];const auto& y=map->doors[b];
        return x.y!=y.y?x.y<y.y:x.x!=y.x?x.x<y.x:a<b;
    });
    if(home>=0)doors.push_back(home);
    int n=std::min(capacity,(int)doors.size());
    std::copy_n(doors.begin(),n,out);return n;
}
void courier_reset(){c={MAGIC,COUCH.x,COUCH.y,0,0,0,CR_SLEEP,HOME,FACE_DOWN,0,0,0};route.clear();next=0;moving=talking=false;retry=0;}
CourierSave courier_save(){auto saved=c;if(talking)saved.facing=resume_facing;return saved;}
bool courier_valid(const CourierSave& s) {
    if(s.magic!=MAGIC||!std::isfinite(s.x)||!std::isfinite(s.y)||s.x<0||s.y<0||s.x>=MAP_WIDTH*TILE_SIZE||s.y>=MAP_HEIGHT*TILE_SIZE||
       !std::isfinite(s.elapsed)||s.elapsed<0||s.elapsed>(s.phase==CR_DELIVER?3:SLEEP_TIME)||
       !std::isfinite(s.anim)||s.anim<0||s.anim>=.8f||!std::isfinite(s.flash)||s.flash<0||s.flash>ACTOR_APPEAR_T||
       s.phase<CR_SLEEP||s.phase>CR_TO_COUCH||s.location!=location(s.phase)||s.stop<0||s.stop>=MAX_INTERIOR_DOORS||
       (s.transfer_pending!=0&&s.transfer_pending!=1)||s.transition_frame<0||s.transition_frame>2||
       (s.facing!=FACE_DOWN&&s.facing!=FACE_UP&&s.facing!=FACE_LEFT&&s.facing!=FACE_RIGHT))return false;
    if(s.location>=0){InteriorMap im;interior_load(&im,HOME);return interior_feet_fit(&im,s.x,s.y);}
    return true;
}
bool courier_restore(const CourierSave& s){if(!courier_valid(s))return false;courier_reset();c=s;return true;}
void courier_tick(const Tilemap* map,float dt) {
    if(!map||dt<=0||talking)return;
    int home=resident_town_door(map,HOME),doors[MAX_INTERIOR_DOORS];
    int count=courier_doors(map,doors,MAX_INTERIOR_DOORS);
    if(home<0||!count)return;
    moving=false;
    while(dt>0) {
        if(c.flash>0) {
            float used=std::min(dt,c.flash);c.flash-=used;dt-=used;
            if(c.flash==0&&c.transfer_pending)transfer(map,home);
            continue;
        }
        if(c.phase==CR_SLEEP||c.phase==CR_DELIVER) {
            float limit=c.phase==CR_SLEEP?SLEEP_TIME:3;
            float used=std::min(dt,limit-c.elapsed);c.elapsed+=used;dt-=used;
            c.anim=std::fmod(c.anim+used,.8f);
            // A skipped hour arrives in 1500 float steps; tolerate their
            // sub-millisecond accumulation error at the sleep boundary.
            if(c.elapsed<limit && !(c.phase==CR_SLEEP && limit-c.elapsed<.001f))return;
            if(c.phase==CR_SLEEP)phase(CR_LEAVE_HOME);
            else if(++c.stop<count)phase(CR_TO_DOOR);
            else {c.stop=count-1;phase(CR_ENTER_HOME);}
            continue;
        }
        Point target=c.phase==CR_TO_COUCH?COUCH:c.phase==CR_LEAVE_HOME?resident_entry(HOME):
            resident_outside(map,c.phase==CR_ENTER_HOME?home:doors[std::min(c.stop,count-1)]);
        if(route.empty()) {
            retry-=dt;if(retry>0)return;
            if(!path(map,target)){SDL_Log("Courier: path failed in phase %d at stop %d; retrying",c.phase,c.stop);retry=1;return;}
        }
        float distance=0;Point from={c.x,c.y};
        for(size_t i=next;i<route.size();i++){distance+=std::hypot(route[i].x-from.x,route[i].y-from.y);from=route[i];}
        float used=std::min(dt,distance/SPEED);
        if(distance<.01f){c.x=target.x;c.y=target.y;next=route.size();}
        else moving=resident_follow_route(route,next,route_start,c.x,c.y,c.facing,SPEED*used)||moving;
        c.anim=std::fmod(c.anim+used,.8f);dt-=used;
        if(next<route.size())return;
        if(c.phase==CR_TO_DOOR){phase(CR_DELIVER);c.facing=FACE_UP;}
        else if(c.phase==CR_TO_COUCH){phase(CR_SLEEP);c.facing=FACE_DOWN;}
        else {
            c.transition_frame=npc_walk_col(c.facing,(int)(c.anim/.2f));
            c.flash=ACTOR_APPEAR_T;c.transfer_pending=1;route.clear();next=0;moving=false;
        }
    }
}
bool courier_here(const StoryWhere& w,StoryNpcPos* out) {
    if(!w.map)return false;
    bool here=c.location<0?w.state==STATE_OVERWORLD:
        w.state==STATE_INTERIOR&&w.room==HOME&&w.door==resident_town_door(w.map,HOME);
    if(here)*out={COURIER_ID,c.x,c.y,-1};return here;
}
const char* courier_line(){return c.phase==CR_SLEEP?"zzzz":c.phase==CR_DELIVER?"A letter for this house. Need anything?":c.phase==CR_ENTER_HOME||c.phase==CR_TO_COUCH?"That's the last letter. Time to head home. Need anything?":"Making my rounds. Need anything?";}
void courier_face(int f){if(c.phase==CR_SLEEP)return;if(!talking)resume_facing=c.facing;talking=true;c.facing=f;}
int courier_facing(){return c.facing;}
void courier_resume(){if(talking)c.facing=resume_facing;talking=false;}
bool courier_art_init(SDL_Renderer* r){courier_art_free();art=IMG_LoadTexture(r,"assets/npcs/courier.png");sleep_art=IMG_LoadTexture(r,"assets/npcs/courier_sleep_simple.png");if(art)SDL_SetTextureScaleMode(art,SDL_ScaleModeNearest);if(sleep_art)SDL_SetTextureScaleMode(sleep_art,SDL_ScaleModeNearest);return art&&sleep_art;}
void courier_art_free(){if(art)SDL_DestroyTexture(art);if(sleep_art)SDL_DestroyTexture(sleep_art);art=sleep_art=nullptr;}
bool courier_draw(const StoryNpcPos& p,SDL_Renderer* r,const Camera* cam) {
    if(p.idx!=COURIER_ID)return false;
    if(!art||!sleep_art)return true;
    if(c.phase==CR_SLEEP){npc_sleep_draw(r,sleep_art,cam,264,224,true,c.elapsed);return true;}
    int col=c.flash>0?c.transition_frame:moving&&!talking?npc_walk_col(c.facing,(int)(c.anim/.2f)):0;
    SDL_Rect src={col*14,npc_sheet_row(c.facing)*20,14,20};
    SDL_Rect dst={cam_screen_x(cam,p.x),cam_screen_y(cam,p.y),(int)(28*cam->zoom),(int)(40*cam->zoom)};
    if(c.flash>0){float visibility=c.flash/ACTOR_APPEAR_T;if(!c.transfer_pending)visibility=1-visibility;draw_actor_appearance(r,art,src,dst,visibility);}
    else SDL_RenderCopy(r,art,&src,&dst);
    return true;
}
