#include "grandmother.h"
#include "resident.h"
#include "resident_path.h"
#include "bookshop.h"
#include "interior.h"
#include "overworld.h"
#include "collision.h"
#include "towns.h"
#include "battle.h"
#include <SDL2/SDL_image.h>
#include <algorithm>
#include <cmath>

namespace {
using Point=ResidentPoint;
constexpr unsigned MAGIC=0x47524d31;
constexpr float SPEED=90,COUCH_TIME=1800.0f/48.0f;
constexpr Point COUCH={292,216};
GrandmotherSave g={MAGIC,COUCH.x,COUCH.y,0,0,0,GM_COUCH,5,FACE_DOWN,0,0,-1};
InteriorMap room;
std::vector<Point> route;
Point route_start={};size_t next=0;
bool moving=false;
bool talking=false;
int resume_facing=FACE_DOWN;
float retry=0;
SDL_Texture* art=nullptr;
SDL_Texture* seated=nullptr;
int door_for(const Tilemap* map,int interior){return resident_town_door(map,interior);}
Point entry(int interior){return resident_entry(interior);}
Point outside(const Tilemap* map,int door){return resident_outside(map,door);}
bool fits(const Tilemap* map,Point p) {
    return g.location<0?resident_on_trail(map,p.x,p.y,true)&&can_occupy(map,p.x,p.y,tilemap_pixel_solid):
        interior_feet_fit(&room,p.x,p.y);
}
bool segment(const Tilemap* map,Point a,Point b) {
    int n=std::max(1,(int)std::ceil(std::hypot(a.x-b.x,a.y-b.y)/2));
    for(int i=0;i<=n;i++)if(!fits(map,{a.x+(b.x-a.x)*i/n,a.y+(b.y-a.y)*i/n}))return false;
    return true;
}
bool path(const Tilemap* map,Point target) {
    if(g.location>=0)interior_load(&room,g.location);
    bool outdoors=g.location<0;int step=outdoors?8:4;
    int ox=outdoors?(map->towns[0].x+50)*TILE_SIZE:0;
    int oy=outdoors?(map->towns[0].y+60)*TILE_SIZE:0;
    return resident_find_route({g.x,g.y},target,step,ox,oy,
        outdoors?85*TILE_SIZE/step:160,outdoors?50*TILE_SIZE/step:120,false,
        [&](Point p){return fits(map,p);},
        [&](Point a,Point b,bool){return segment(map,a,b);},route,route_start,next);
}
void phase(int p) {g.phase=p;g.elapsed=0;route.clear();next=0;retry=0;moving=false;}
Point destination(const Tilemap* map) {
    switch(g.phase) {
    case GM_LEAVE_HOME:return entry(5);
    case GM_TO_SHOP:return outside(map,door_for(map,1));
    case GM_TO_SHELF:return BOOKSHOP_SHELF[g.shelf];
    case GM_TO_DESK:return BOOKSHOP_DESK;
    case GM_LEAVE_SHOP:return entry(1);
    case GM_TO_HOME:return outside(map,door_for(map,5));
    default:return COUCH;
    }
}
void transfer(const Tilemap* map) {
    Point p;
    switch(g.phase) {
    case GM_LEAVE_HOME:g.location=-1;p=outside(map,door_for(map,5));phase(GM_TO_SHOP);break;
    case GM_TO_SHOP:g.location=1;p=entry(1);phase(GM_FIND_SHELF);break;
    case GM_LEAVE_SHOP:g.location=-1;p=outside(map,door_for(map,1));phase(GM_TO_HOME);break;
    default:g.location=5;p=entry(5);phase(GM_TO_COUCH);break;
    }
    g.x=p.x;g.y=p.y;g.flash=ACTOR_APPEAR_T;g.transfer_pending=0;
}
}
void grandmother_reset() {
    g={MAGIC,COUCH.x,COUCH.y,0,0,0,GM_COUCH,5,FACE_DOWN,0,0,-1};
    route.clear();next=0;moving=talking=false;retry=0;
}
GrandmotherSave grandmother_save(){auto saved=g;if(talking)saved.facing=resume_facing;return saved;}
void grandmother_face(int facing){if(!talking)resume_facing=g.facing;talking=true;g.facing=facing;}
void grandmother_resume(){talking=false;g.facing=resume_facing;}
int grandmother_facing(){return g.facing;}
int grandmother_reserved_shelf() {
    if(g.shelf<0)return -1;
    if(g.phase==GM_TO_SHELF||g.phase==GM_SEARCH)return g.shelf;
    if(g.phase==GM_TO_DESK)return g.shelf; // let her clear the aisle before the worker approaches
    return -1;
}
void grandmother_tick(const Tilemap* map,float dt) {
    if(!map||dt<=0||talking)return;
    moving=false;
    if(door_for(map,1)<0||door_for(map,5)<0)return;
    if(g.flash>0) {
        g.flash=std::max(0.0f,g.flash-dt);
        if(g.flash==0&&g.transfer_pending)transfer(map);
        return;
    }
    if(g.phase==GM_COUCH||g.phase==GM_SEARCH||g.phase==GM_DESK) {
        g.elapsed+=dt;g.anim=0;
        g.facing=g.phase==GM_COUCH?FACE_DOWN:FACE_UP;
        float duration=g.phase==GM_COUCH?COUCH_TIME:5;
        // Browsing on while someone else has the desk.
        if(g.phase==GM_SEARCH&&g.elapsed>=duration&&bookshop_desk_taken(SHOP_GRANDMOTHER)){g.elapsed=duration;return;}
        if(g.elapsed>=duration)phase(g.phase==GM_COUCH?GM_LEAVE_HOME:g.phase==GM_SEARCH?GM_TO_DESK:GM_LEAVE_SHOP);
        return;
    }
    if(g.phase==GM_FIND_SHELF) {
        for(int shelf:{2,3}) {
            if(bookshop_shelf_taken(shelf,SHOP_GRANDMOTHER))continue;
            g.shelf=shelf;phase(GM_TO_SHELF);break;
        }
        return;
    }
    if(route.empty()) {
        retry-=dt;if(retry>0)return;
        if(!path(map,destination(map))){retry=3;return;}
    }
    moving=resident_follow_route(route,next,route_start,g.x,g.y,g.facing,SPEED*dt);
    g.anim=moving?std::fmod(g.anim+dt,.8f):0;
    if(next==route.size()) {
        if(g.phase==GM_TO_COUCH){phase(GM_COUCH);g.shelf=-1;g.facing=FACE_DOWN;}
        else if(g.phase==GM_TO_SHELF){phase(GM_SEARCH);g.facing=FACE_UP;}
        else if(g.phase==GM_TO_DESK){phase(GM_DESK);g.shelf=-1;g.facing=FACE_UP;}
        else {
            g.transition_frame=npc_walk_col(g.facing,(int)(g.anim/.2f));
            g.flash=ACTOR_APPEAR_T;g.transfer_pending=1;route.clear();next=0;moving=false;
        }
    }
}
bool grandmother_valid(const GrandmotherSave& s) {
    if(s.magic!=MAGIC||!std::isfinite(s.x)||!std::isfinite(s.y)||s.x<0||s.y<0||
       s.x>=MAP_WIDTH*TILE_SIZE||s.y>=MAP_HEIGHT*TILE_SIZE||
       !std::isfinite(s.elapsed)||s.elapsed<0||s.elapsed>COUCH_TIME+.1f||
       !std::isfinite(s.anim)||s.anim<0||s.anim>=.8f||
       !std::isfinite(s.flash)||s.flash<0||s.flash>ACTOR_APPEAR_T||
       s.phase<GM_COUCH||s.phase>GM_TO_COUCH||s.shelf< -1||s.shelf>3||
       (s.transfer_pending!=0&&s.transfer_pending!=1)||s.transition_frame<0||s.transition_frame>2||
       (s.facing!=FACE_UP&&s.facing!=FACE_DOWN&&s.facing!=FACE_LEFT&&s.facing!=FACE_RIGHT))return false;
    int location=s.phase==GM_TO_SHOP||s.phase==GM_TO_HOME?-1:
        s.phase==GM_COUCH||s.phase==GM_LEAVE_HOME||s.phase==GM_TO_COUCH?5:1;
    if(s.location!=location || ((s.phase==GM_TO_SHELF||s.phase==GM_SEARCH)&&s.shelf<0))return false;
    if(location>=0) {InteriorMap im;interior_load(&im,location);return interior_feet_fit(&im,s.x,s.y);}
    return true;
}
bool grandmother_restore(const GrandmotherSave& saved) {
    if(!grandmother_valid(saved))return false;
    grandmother_reset();g=saved;return true;
}
bool grandmother_here(const StoryWhere& w,StoryNpcPos* out) {
    if(!w.map)return false;
    bool here=g.location<0?w.state==STATE_OVERWORLD:
        w.state==STATE_INTERIOR&&w.room==g.location&&w.door>=0&&w.door==door_for(w.map,g.location);
    if(here)*out={GRANDMOTHER_ID,g.x,g.y,-1};return here;
}
bool grandmother_art_init(SDL_Renderer* r) {
    grandmother_art_free();art=IMG_LoadTexture(r,"assets/npcs/grandmother.png");
    seated=IMG_LoadTexture(r,"assets/npcs/grandmother_seated.png");
    if(art)SDL_SetTextureScaleMode(art,SDL_ScaleModeNearest);
    if(seated)SDL_SetTextureScaleMode(seated,SDL_ScaleModeNearest);
    return art&&seated;
}
void grandmother_art_free() {
    if(art)SDL_DestroyTexture(art);if(seated)SDL_DestroyTexture(seated);art=seated=nullptr;
}
bool grandmother_draw(const StoryNpcPos& p,SDL_Renderer* r,const Camera* cam) {
    if(p.idx!=GRANDMOTHER_ID)return false;
    if(!art||!seated)return true;
    int col=g.flash>0?g.transition_frame:moving&&!talking?npc_walk_col(g.facing,(int)(g.anim/.2f)):0;
    SDL_Rect src={col*14,npc_sheet_row(g.facing)*20,14,20};
    SDL_Rect dst={cam_screen_x(cam,p.x),cam_screen_y(cam,p.y),(int)(28*cam->zoom),(int)(40*cam->zoom)};
    if(g.phase==GM_COUCH) {
        src={0,0,14,20};dst.y=cam_screen_y(cam,p.y-18);
        SDL_RenderCopy(r,seated,&src,&dst);
    } else if(g.flash>0) {
        float visibility=g.flash/ACTOR_APPEAR_T;
        if(!g.transfer_pending)visibility=1-visibility;
        draw_actor_appearance(r,art,src,dst,visibility);
    } else SDL_RenderCopy(r,art,&src,&dst);
    return true;
}
