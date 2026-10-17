#include "sailor_fisher.h"
#include "resident.h"
#include "npc_sleep.h"
#include "resident_path.h"
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
constexpr unsigned MAGIC=0x53414931;
constexpr double CYCLE=43200,SLEEP=7200,SPEED=90,RATE=48;
constexpr Point BED={486,300};   // feet (500,334), before the front bed (room 3, head against the right wall)
SailorFisherSave saved={MAGIC,-1};
SailorFisherView view={BED.x,BED.y,1,SF_SLEEP,3,FACE_RIGHT,0,0,0,0};
SDL_Texture *art=nullptr,*fishing=nullptr,*sleep_art=nullptr;
std::vector<Point> indoor,outdoor;
double durations[10]={},inside_length=0,outside_length=0;
const Tilemap* planned_map=nullptr;
int planned_x=-1,planned_y=-1;
bool ready=false,failed=false;
int door_for(const Tilemap* map) {
    if(!map)return -1;
    const auto& t=map->towns[0];
    for(int i=0;i<map->num_doors;i++) {
        const auto& d=map->doors[i];
        if(d.interior_id==3&&d.x>=t.x&&d.x<t.x+TOWN_W&&d.y>=t.y&&d.y<t.y+TOWN_H)return i;
    }
    return -1;
}
double length(const std::vector<Point>& points) {
    double total=0;for(size_t i=1;i<points.size();i++)total+=std::hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);
    return total;
}
bool prepare(const Tilemap* map) {
    if((ready||failed)&&planned_map==map&&planned_x==map->towns[0].x&&planned_y==map->towns[0].y)return ready;
    ready=false;failed=true;planned_map=map;planned_x=map->towns[0].x;planned_y=map->towns[0].y;
    SDL_Log("Sailor fisher: planning town 0 shoreline route");
    int door=door_for(map);if(door<0)return false;
    InteriorMap room;interior_load(&room,3);
    Player player={};player.width=28;player.height=40;InteriorPlayer ip={};
    interior_player_init(&ip,&player,&room);Point entry={ip.x,ip.y};
    Overworld ow={};overworld_stand_before_door_idx(&ow,&player,map,door);Point exit={ow.x,ow.y};
    // F1 reports sprite origins. Keep the requested point town-relative on all seeds.
    Point water={(float)(map->towns[0].x*TILE_SIZE+2766),(float)(map->towns[0].y*TILE_SIZE+2451)};
    std::vector<Point> candidates;
    for(int dy=-TILE_SIZE;dy<=TILE_SIZE;dy++)for(int dx=-TILE_SIZE;dx<=TILE_SIZE;dx++)
        if(dx*dx+dy*dy<=TILE_SIZE*TILE_SIZE)candidates.push_back({(float)dx,(float)dy});
    std::sort(candidates.begin(),candidates.end(),[](Point a,Point b){return a.x*a.x+a.y*a.y<b.x*b.x+b.y*b.y;});
    bool shore=false;
    for(Point delta:candidates){Point q={water.x+delta.x,water.y+delta.y};
        if(can_occupy(map,q.x,q.y,tilemap_pixel_solid)&&tilemap_pixel_water(map,q.x-44,q.y+34)) {water=q;shore=true;break;}}
    if(!shore){SDL_Log("Sailor fisher: no valid west shoreline within one tile");return false;}
    auto find=[&](Point start,Point target,bool outside,std::vector<Point>& route) {
        auto fits=[&](Point p){return outside?can_occupy(map,p.x,p.y,tilemap_pixel_solid):interior_feet_fit(&room,p.x,p.y);};
        auto segment=[&](Point a,Point b,bool){return resident_way_fits(a,b,fits);};
        Point origin;size_t next;int step=outside?8:4;
        int ox=outside?map->towns[0].x*TILE_SIZE:0,oy=outside?map->towns[0].y*TILE_SIZE:0;
        if(!resident_find_route(start,target,step,ox,oy,outside?TOWN_W*4:160,outside?TOWN_H*4:120,
            false,fits,segment,route,origin,next))return false;
        route.insert(route.begin(),start);return true;
    };
    Point origin;size_t next;
    if(!find(BED,entry,false,indoor))return false;
    // The shared trail-first route; the old whole-town search it replaced
    // took ~3 s on every load.
    if(!resident_trail_route(map,exit,water,outdoor,origin,next)){SDL_Log("Sailor fisher: no route; stationary at home");return false;}
    outdoor.insert(outdoor.begin(),exit);
    inside_length=length(indoor);outside_length=length(outdoor);
    const double in=inside_length/SPEED*RATE,out=outside_length/SPEED*RATE,fade=ACTOR_APPEAR_T*RATE;
    durations[SF_SLEEP]=SLEEP;durations[SF_TO_EXIT]=in;
    durations[SF_DISSOLVE_HOME]=fade;durations[SF_APPEAR_OUT]=fade;durations[SF_TO_WATER]=out;
    durations[SF_FISH]=CYCLE-SLEEP-2*(in+out+2*fade);
    durations[SF_TO_HOME]=out;durations[SF_DISSOLVE_OUT]=fade;
    durations[SF_APPEAR_HOME]=fade;durations[SF_TO_BED]=in;
    if(durations[SF_FISH]<=0){SDL_Log("SailorFisher: journey exceeds twelve-hour cycle");return false;}
    planned_map=map;planned_x=map->towns[0].x;planned_y=map->towns[0].y;ready=true;
    return true;
}
void place(const std::vector<Point>& route,double distance,bool reverse,double seconds,bool walking) {
    double remain=std::max(0.0,distance);
    for(size_t i=1;i<route.size();i++) {
        Point a=reverse?route[route.size()-i]:route[i-1];
        Point b=reverse?route[route.size()-1-i]:route[i];
        double d=std::hypot(b.x-a.x,b.y-a.y);if(d<.001)continue;
        if(remain<=d||i+1==route.size()) {
            double t=std::min(1.0,remain/d);
            view.x=(float)(a.x+(b.x-a.x)*t);view.y=(float)(a.y+(b.y-a.y)*t);
            view.facing=std::fabs(b.x-a.x)>std::fabs(b.y-a.y)?(b.x<a.x?FACE_LEFT:FACE_RIGHT):(b.y<a.y?FACE_UP:FACE_DOWN);
            view.frame=walking?npc_walk_col(view.facing,(int)(seconds/.2)):0;return;
        }
        remain-=d;
    }
}
}

void sailor_fisher_reset(){saved={MAGIC,-1};view={BED.x,BED.y,1,SF_SLEEP,3,FACE_RIGHT,0,0,0,0};}
SailorFisherSave sailor_fisher_save(){return saved;}
bool sailor_fisher_valid(const SailorFisherSave& s){return s.magic==MAGIC&&std::isfinite(s.epoch)&&(s.epoch==-1||s.epoch>=0);}
bool sailor_fisher_restore(const SailorFisherSave& s){if(!sailor_fisher_valid(s))return false;saved=s;return true;}
SailorFisherView sailor_fisher_view(){return view;}
const char* sailor_fisher_line(){
    switch(view.phase) {
    case SF_SLEEP:return "Zzzz...";
    case SF_FISH:return "Good day! Just doing a little fishing. What do you need?";
    case SF_TO_HOME:return "Good day! I'm heading home. What do you need?";
    case SF_TO_BED:return "Good evening! About to turn in. What do you need?";
    case SF_TO_EXIT:return "Good morning! What do you need?";
    case SF_TO_WATER:return "Good day! I'm off to the river. What do you need?";
    default:return nullptr;
    }
}
void sailor_fisher_tick(const Tilemap* map,float dt) {
    if(!map||dt<=0)return;
    if(!prepare(map)){
        view={BED.x,BED.y,1,SF_SLEEP,3,FACE_LEFT,0,0,0,0};
        return;
    }
    double now=resident_save().world_seconds;
    if(saved.epoch<0)saved.epoch=std::max(0.0,now-dt*RATE);
    double t=std::fmod(std::max(0.0,now-saved.epoch),CYCLE),offset=0;
    view={BED.x,BED.y,1,SF_SLEEP,3,FACE_RIGHT,0,t,0,0};
    const double outbound=durations[SF_TO_EXIT]+durations[SF_DISSOLVE_HOME]+durations[SF_APPEAR_OUT]+durations[SF_TO_WATER];
    bool first=now-saved.epoch<CYCLE;
    view.fishing_start=first?0:outbound;
    view.return_departure=CYCLE-SLEEP-outbound;
    const int order[]={SF_TO_EXIT,SF_DISSOLVE_HOME,SF_APPEAR_OUT,SF_TO_WATER,SF_FISH,SF_TO_HOME,SF_DISSOLVE_OUT,SF_APPEAR_HOME,SF_TO_BED,SF_SLEEP};
    int phase=SF_SLEEP;
    double elapsed=0;
    for(int candidate:order) {
        double duration=durations[candidate];
        if(first&&candidate>=SF_TO_EXIT&&candidate<=SF_TO_WATER)duration=0;
        if(first&&candidate==SF_FISH)duration+=outbound;
        if(t<offset+duration){phase=candidate;elapsed=t-offset;break;}
        offset+=duration;
    }
    view.phase=phase;
    switch(phase) {
    case SF_SLEEP:break;
    case SF_TO_EXIT:place(indoor,elapsed/RATE*SPEED,false,elapsed/RATE,true);break;
    case SF_DISSOLVE_HOME:
        place(indoor,inside_length,false,durations[SF_TO_EXIT]/RATE,true);
        view.visibility=(float)(1-elapsed/durations[phase]);break;
    case SF_APPEAR_OUT:
        place(indoor,inside_length,false,durations[SF_TO_EXIT]/RATE,true);
        view.x=outdoor.front().x;view.y=outdoor.front().y;view.location=-1;
        view.visibility=(float)(elapsed/durations[phase]);break;
    case SF_TO_WATER:
        view.location=-1;place(outdoor,elapsed/RATE*SPEED,false,elapsed/RATE,true);break;
    case SF_FISH:
        view.location=-1;view.x=outdoor.back().x;view.y=outdoor.back().y;view.facing=FACE_LEFT;
        view.frame=(int)(elapsed/RATE/.6)%2;break;
    case SF_TO_HOME:
        view.location=-1;place(outdoor,elapsed/RATE*SPEED,true,elapsed/RATE,true);break;
    case SF_DISSOLVE_OUT:
        view.location=-1;place(outdoor,outside_length,true,durations[SF_TO_HOME]/RATE,true);
        view.visibility=(float)(1-elapsed/durations[phase]);break;
    case SF_APPEAR_HOME:
        place(outdoor,outside_length,true,durations[SF_TO_HOME]/RATE,true);
        view.x=indoor.back().x;view.y=indoor.back().y;
        view.visibility=(float)(elapsed/durations[phase]);break;
    case SF_TO_BED:place(indoor,elapsed/RATE*SPEED,true,elapsed/RATE,true);break;
    }
}
bool sailor_fisher_here(const StoryWhere& w,StoryNpcPos* out) {
    bool here=view.location<0?w.state==STATE_OVERWORLD:
        w.state==STATE_INTERIOR&&w.room==3&&w.door==door_for(w.map);
    if(!here)return false;*out={SAILOR_FISHER_ID,view.x,view.y,-1};return true;
}
bool sailor_fisher_art_init(SDL_Renderer* r) {
    sailor_fisher_art_free();art=IMG_LoadTexture(r,"assets/npcs/sailor.png");
    fishing=IMG_LoadTexture(r,"assets/npcs/sailor_fisher_fishing.png");
    sleep_art=IMG_LoadTexture(r,"assets/npcs/sailor_sleep_simple.png");
    if(art)SDL_SetTextureScaleMode(art,SDL_ScaleModeNearest);
    if(fishing)SDL_SetTextureScaleMode(fishing,SDL_ScaleModeNearest);
    if(sleep_art)SDL_SetTextureScaleMode(sleep_art,SDL_ScaleModeNearest);
    return art&&fishing&&sleep_art;
}
void sailor_fisher_art_free(){if(art)SDL_DestroyTexture(art);if(fishing)SDL_DestroyTexture(fishing);if(sleep_art)SDL_DestroyTexture(sleep_art);art=fishing=sleep_art=nullptr;}
bool sailor_fisher_draw(const StoryNpcPos& p,SDL_Renderer* r,const Camera* c) {
    if(p.idx!=SAILOR_FISHER_ID)return false;if(!art||!fishing)return true;
    SDL_Rect src={view.frame*14,npc_sheet_row(view.facing)*20,14,20};
    SDL_Rect dst={cam_screen_x(c,p.x),cam_screen_y(c,p.y),(int)(28*c->zoom),(int)(40*c->zoom)};
    if(view.phase==SF_SLEEP) {
        float bx,by;npc_bed_centre(208,110,true,&bx,&by);   // room 3's front bed (house3_design.py)
        npc_sleep_draw(r,sleep_art,c,bx,by,true,resident_save().world_seconds/48.0);
    } else if(view.phase==SF_FISH) {
        src={view.frame*40,0,40,28};dst.x=cam_screen_x(c,p.x-52);dst.y=cam_screen_y(c,p.y-16);dst.w=(int)(80*c->zoom);dst.h=(int)(56*c->zoom);
        SDL_RenderCopy(r,fishing,&src,&dst);
    } else if(view.phase==SF_DISSOLVE_HOME||view.phase==SF_APPEAR_OUT||view.phase==SF_DISSOLVE_OUT||view.phase==SF_APPEAR_HOME)
        draw_actor_appearance(r,art,src,dst,view.visibility);
    else SDL_RenderCopy(r,art,&src,&dst);
    return true;
}
