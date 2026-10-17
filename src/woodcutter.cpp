#include "woodcutter.h"
#include "resident.h"
#include "resident_path.h"
#include "interior.h"
#include "tilemap.h"
#include "camera.h"
#include "collision.h"
#include "battle.h"
#include <SDL2/SDL_image.h>
#include <algorithm>
#include <cmath>
#include <vector>

namespace {
using Point=ResidentPoint;
constexpr unsigned MAGIC=0x57444331;
constexpr int HOME=6;                               // the tall red-brick house right of the book shop
constexpr int FIRST_TREE_X=80,FIRST_TREE_Y=66;      // town-0 tiles: right of the trail from the player's house
constexpr float SPEED=90,HOURS2=2*3600.0f/48.0f;    // two game hours, in world-clock seconds
constexpr float BEAT=.2f;                           // four chopping cels: ready, raised, impact, recovery
constexpr int TREE_SEARCH=150,TREE_TRIES=8;         // tiles round the felled tree; paths tried, nearest first
// Room 6 (house6_design.py): the floor before the sofa and before the bed.
constexpr Point COUCH={251,218},BED={396,224};
WoodcutterSave w={MAGIC,0,0,0,0,0,WC_CHOP,-1,FACE_RIGHT,0,0,-1,-1};
InteriorMap room;
std::vector<Point> route;
Point route_start={};size_t next=0;
bool moving=false;
float retry=0;
int last_beat=-1;
SDL_Texture* art=nullptr;
SDL_Texture* chop_art=nullptr;

bool outdoors(){return w.location<0;}
bool tree_standing(const Tilemap* map,int tx,int ty) {
    return tx>=0&&ty>=0&&tx<MAP_WIDTH&&ty<MAP_HEIGHT&&map->overlay[ty][tx]==TILE_TREE;
}
// Where to stand to chop tree (tx, ty): left of it facing right (as at his
// first tree), else right, below, above -- the first side the feet fit.
bool stand_spot(const Tilemap* map,int tx,int ty,Point* at,int* facing) {
    const struct { float x,y; int face; } sides[4]={
        {tx*32.0f-21,(ty+1)*32.0f-41,FACE_RIGHT},{(tx+1)*32.0f-7,(ty+1)*32.0f-41,FACE_LEFT},
        {tx*32.0f+2,(ty+1)*32.0f-27,FACE_UP},{tx*32.0f+2,ty*32.0f-41,FACE_DOWN}};
    for(const auto& s:sides)
        if(can_occupy(map,s.x,s.y,tilemap_pixel_solid)){*at={s.x,s.y};*facing=s.face;return true;}
    return false;
}
bool fits(const Tilemap* map,Point p) {
    return outdoors()?can_occupy(map,p.x,p.y,tilemap_pixel_solid):interior_feet_fit(&room,p.x,p.y);
}
// Every pixel of the way fits: he walks every one between.
bool segment(const Tilemap* map,Point a,Point b) {
    int n=std::max(1,(int)std::ceil(std::hypot(a.x-b.x,a.y-b.y)));
    for(int i=0;i<=n;i++)if(!fits(map,{a.x+(b.x-a.x)*i/n,a.y+(b.y-a.y)*i/n}))return false;
    return true;
}
// Indoors, the furniture-aware search the others use; outdoors, the trail.
bool path(const Tilemap* map,Point target) {
    if(outdoors())return resident_trail_route(map,{w.x,w.y},target,route,route_start,next);
    interior_load(&room,w.location);
    return resident_find_route({w.x,w.y},target,4,0,0,160,120,false,
        [&](Point p){return fits(map,p);},[&](Point a,Point b,bool){return segment(map,a,b);},
        route,route_start,next);
}
void phase(int p,bool keep_elapsed=false) {
    w.phase=p;if(!keep_elapsed)w.elapsed=0;
    if(p==WC_CHOP){w.anim=0;last_beat=-1;}
    route.clear();next=0;retry=0;moving=false;
}
// The standing tree nearest (fx, fy) that he has a side to stand at; when
// `walk`, also one he can walk to from where he is (the route is kept).
// ponytail: tries the TREE_TRIES nearest; a farther reachable tree behind
// that many unreachable ones reads as none left.
bool find_tree(const Tilemap* map,int fx,int fy,bool walk) {
    struct Candidate { int d2,x,y; };
    std::vector<Candidate> found;
    for(int y=std::max(0,fy-TREE_SEARCH);y<=std::min(MAP_HEIGHT-1,fy+TREE_SEARCH);y++)
        for(int x=std::max(0,fx-TREE_SEARCH);x<=std::min(MAP_WIDTH-1,fx+TREE_SEARCH);x++)
            if(map->overlay[y][x]==TILE_TREE)found.push_back({(x-fx)*(x-fx)+(y-fy)*(y-fy),x,y});
    std::sort(found.begin(),found.end(),[](const Candidate& a,const Candidate& b){return a.d2<b.d2;});
    int tries=0;
    for(const auto& c:found) {
        Point at;int face;
        if(!stand_spot(map,c.x,c.y,&at,&face))continue;
        if(walk&&!path(map,at)) {if(++tries>=TREE_TRIES)break;continue;}
        w.tree_x=c.x;w.tree_y=c.y;
        return true;
    }
    return false;
}
// His tree is gone: on to the nearest still standing, or home to the sofa.
void retarget(const Tilemap* map) {
    int fx=w.tree_x,fy=w.tree_y;
    phase(WC_TO_TREE,true);
    if(!find_tree(map,fx,fy,true))phase(WC_NO_TREES_HOME);
}
Point tree_spot(const Tilemap* map,int* facing) {
    Point at={w.x,w.y};int face=w.facing;
    stand_spot(map,w.tree_x,w.tree_y,&at,&face);
    if(facing)*facing=face;
    return at;
}
Point destination(const Tilemap* map,int door) {
    switch(w.phase) {
    case WC_TO_TREE:case WC_TO_WORK:return tree_spot(map,nullptr);
    case WC_TO_HOME:case WC_NO_TREES_HOME:return resident_outside(map,door);
    case WC_LEAVE_HOME:return resident_entry(HOME);
    case WC_TO_COUCH:return COUCH;
    default:return BED;
    }
}
void transfer(const Tilemap* map,int door) {
    Point p;
    if(w.phase==WC_LEAVE_HOME){w.location=-1;p=resident_outside(map,door);phase(WC_TO_WORK);}
    else {w.location=HOME;p=resident_entry(HOME);phase(w.phase==WC_NO_TREES_HOME?WC_TO_COUCH:WC_TO_BED);}
    w.x=p.x;w.y=p.y;w.flash=ACTOR_APPEAR_T;w.transfer_pending=0;
}
}

void woodcutter_reset() {
    w={MAGIC,0,0,0,0,0,WC_CHOP,-1,FACE_RIGHT,0,0,-1,-1};
    route.clear();next=0;moving=false;retry=0;last_beat=-1;
}
WoodcutterSave woodcutter_save(){return w;}
void woodcutter_face(int facing){
    // Talking must not turn an active axe swing away from its tree.
    if(w.phase!=WC_CHOP)w.facing=facing;
}
int woodcutter_facing(){return w.facing;}

void woodcutter_tick(const Tilemap* map,float dt) {
    if(!map||dt<=0)return;
    int door=resident_town_door(map,HOME);
    if(door<0)return;
    if(w.tree_x<0) {   // a new game: at his first tree, already chopping
        w.tree_x=map->towns[0].x+FIRST_TREE_X;w.tree_y=map->towns[0].y+FIRST_TREE_Y;
        Point at=tree_spot(map,&w.facing);w.x=at.x;w.y=at.y;
    }
    moving=false;
    if(w.flash>0) {
        w.flash=std::max(0.0f,w.flash-dt);
        if(w.flash==0&&w.transfer_pending)transfer(map,door);
        return;
    }
    bool after_tree=w.phase==WC_CHOP||w.phase==WC_TO_TREE||w.phase==WC_TO_WORK;
    if(after_tree&&!tree_standing(map,w.tree_x,w.tree_y)){retarget(map);return;}
    switch(w.phase) {
    case WC_CHOP: {
        tree_spot(map,&w.facing);
        w.elapsed+=dt;w.anim=std::fmod(w.anim+dt,4*BEAT);
        // One tree impact per swing, on the axe's contact cel.
        int beat=(int)(w.anim/BEAT);
        if(beat!=last_beat&&beat==2)tilemap_jitter_tile(w.tree_x,w.tree_y);
        last_beat=beat;
        if(w.elapsed>=HOURS2)phase(WC_TO_HOME);
        return;
    }
    case WC_SLEEP:
        w.elapsed+=dt;
        if(w.elapsed>=HOURS2)phase(find_tree(map,w.tree_x,w.tree_y,false)?WC_LEAVE_HOME:WC_TO_COUCH);
        return;
    case WC_COUCH:
        w.elapsed+=dt;w.facing=FACE_DOWN;
        if(w.elapsed>=HOURS2)phase(WC_COUCH_TO_BED);
        return;
    default:break;
    }
    if(route.empty()) {
        retry-=dt;if(retry>0)return;
        if(!path(map,destination(map,door))) {
            if(w.phase==WC_TO_WORK||w.phase==WC_TO_TREE)retarget(map);   // that tree cannot be walked to
            else retry=3;
            return;
        }
    }
    moving=resident_follow_route(route,next,route_start,w.x,w.y,w.facing,SPEED*dt);
    w.anim=moving?std::fmod(w.anim+dt,4*BEAT):0;
    if(next<route.size())return;
    switch(w.phase) {
    case WC_TO_TREE:case WC_TO_WORK:phase(WC_CHOP,w.phase==WC_TO_TREE);tree_spot(map,&w.facing);break;
    case WC_TO_BED:case WC_COUCH_TO_BED:phase(WC_SLEEP);break;
    case WC_TO_COUCH:phase(WC_COUCH);w.facing=FACE_DOWN;break;
    default:   // at a door: through it
        w.transition_frame=npc_walk_col(w.facing,(int)(w.anim/BEAT));
        w.flash=ACTOR_APPEAR_T;w.transfer_pending=1;route.clear();next=0;moving=false;
    }
}

bool woodcutter_valid(const WoodcutterSave& s) {
    if(s.magic!=MAGIC||!std::isfinite(s.x)||!std::isfinite(s.y)||s.x<0||s.y<0||
       s.x>=MAP_WIDTH*TILE_SIZE||s.y>=MAP_HEIGHT*TILE_SIZE||
       !std::isfinite(s.elapsed)||s.elapsed<0||s.elapsed>HOURS2+.1f||
       !std::isfinite(s.anim)||s.anim<0||s.anim>=4*BEAT||
       !std::isfinite(s.flash)||s.flash<0||s.flash>ACTOR_APPEAR_T||
       s.phase<WC_CHOP||s.phase>WC_COUCH_TO_BED||
       (s.transfer_pending!=0&&s.transfer_pending!=1)||s.transition_frame<0||s.transition_frame>2||
       s.tree_x<-1||s.tree_y<-1||s.tree_x>=MAP_WIDTH||s.tree_y>=MAP_HEIGHT||
       (s.facing!=FACE_UP&&s.facing!=FACE_DOWN&&s.facing!=FACE_LEFT&&s.facing!=FACE_RIGHT))return false;
    bool out=s.phase==WC_CHOP||s.phase==WC_TO_TREE||s.phase==WC_TO_HOME||s.phase==WC_TO_WORK||s.phase==WC_NO_TREES_HOME;
    if(s.location!=(out?-1:HOME))return false;
    if(!out){InteriorMap im;interior_load(&im,HOME);return interior_feet_fit(&im,s.x,s.y);}
    return true;
}
bool woodcutter_restore(const WoodcutterSave& saved) {
    if(!woodcutter_valid(saved))return false;
    woodcutter_reset();w=saved;return true;
}
bool woodcutter_here(const StoryWhere& where,StoryNpcPos* out) {
    if(!where.map||w.tree_x<0)return false;
    bool here=outdoors()?where.state==STATE_OVERWORLD:
        where.state==STATE_INTERIOR&&where.room==HOME&&where.door>=0&&where.door==resident_town_door(where.map,HOME);
    if(here)*out={WOODCUTTER_ID,w.x,w.y,-1};
    return here;
}
const char* woodcutter_line() {
    switch(w.phase) {
    case WC_CHOP:return "Chopping away at these trees is so relaxing, you know. You gotta try it sometime.";
    case WC_TO_TREE:return "Stop targeting my trees.";
    case WC_TO_HOME:return "Got all the wood I need for today. Might sell some to the store later for a pretty penny.";
    case WC_TO_BED:case WC_COUCH_TO_BED:return "Get out of my house. I wanna rest after a long day.";
    case WC_SLEEP:return "zzzz";
    case WC_LEAVE_HOME:case WC_TO_WORK:return "On my way to get more wood. Hopefully today I can finally knock one tree down.";
    default:return "Well, look at that. You ruined all my fun. Now there's nothing left for me to chop away at. Get lost, kid.";
    }
}
bool woodcutter_art_init(SDL_Renderer* r) {
    woodcutter_art_free();art=IMG_LoadTexture(r,"assets/npcs/woodcutter.png");
    chop_art=IMG_LoadTexture(r,"assets/npcs/woodcutter_chop.png");
    if(art)SDL_SetTextureScaleMode(art,SDL_ScaleModeNearest);
    if(chop_art)SDL_SetTextureScaleMode(chop_art,SDL_ScaleModeNearest);
    return art!=nullptr&&chop_art!=nullptr;
}
void woodcutter_art_free(){if(art)SDL_DestroyTexture(art);if(chop_art)SDL_DestroyTexture(chop_art);art=chop_art=nullptr;}
bool woodcutter_draw(const StoryNpcPos& p,SDL_Renderer* r,const Camera* cam) {
    if(p.idx!=WOODCUTTER_ID)return false;
    if(!art||!chop_art)return true;
    bool stepping=moving;
    int col=w.flash>0?w.transition_frame:stepping?npc_walk_col(w.facing,(int)(w.anim/BEAT)):0;
    SDL_Rect src={col*14,npc_sheet_row(w.facing)*20,14,20};
    SDL_Rect dst={cam_screen_x(cam,p.x),cam_screen_y(cam,p.y),(int)(28*cam->zoom),(int)(40*cam->zoom)};
    if(w.flash>0) {
        float visibility=w.flash/ACTOR_APPEAR_T;
        if(!w.transfer_pending)visibility=1-visibility;
        draw_actor_appearance(r,art,src,dst,visibility);
    } else if(w.phase==WC_CHOP) {
        int frame=(int)(w.anim/BEAT)%4;
        src={(npc_sheet_row(w.facing)*4+frame)*40,0,40,40};
        dst={cam_screen_x(cam,p.x-24),cam_screen_y(cam,p.y-24),
             (int)(80*cam->zoom),(int)(80*cam->zoom)};
        SDL_RenderCopy(r,chop_art,&src,&dst);
    } else if(w.phase==WC_SLEEP) {   // lying on the bed
        src={0,0,14,20};
        dst={cam_screen_x(cam,406),cam_screen_y(cam,210),(int)(20*cam->zoom),(int)(32*cam->zoom)};
        SDL_RenderCopyEx(r,art,&src,&dst,90,nullptr,SDL_FLIP_NONE);   // head to the headboard, right
    } else if(w.phase==WC_COUCH) {   // standing on the seat, facing down, reads as sat
        src={0,0,14,20};dst.y=cam_screen_y(cam,p.y-22);
        SDL_RenderCopy(r,art,&src,&dst);
    } else SDL_RenderCopy(r,art,&src,&dst);
    return true;
}
