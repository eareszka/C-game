#include "resident.h"
#include "resident_path.h"
#include "grandmother.h"
#include "fisher.h"
#include "woodcutter.h"
#include "interior.h"
#include "overworld.h"
#include "collision.h"
#include "towns.h"
#include "battle.h"
#include <SDL2/SDL_image.h>
#include <algorithm>
#include <cmath>
#include <queue>
#include <vector>
#include <functional>

namespace {
constexpr unsigned MAGIC = 0x52544e31;
constexpr float SPEED = 90.0f, FLASH_STEP = ACTOR_APPEAR_T;
constexpr double ACTIVITY_HOUR = 3600;
ResidentSave state = {0,0,336,224,0,RES_WORK,4,FACE_UP,0,MAGIC};
SDL_Texture* art = nullptr;
using Point=ResidentPoint;
// Stove -> one tile down -> left -> counter -> down -> right -> stove.
const Point KITCHEN_LOOP[] = {{368,216},{368,248},{296,248},
                              {296,216},{296,248},{368,248}};
std::vector<Point> route;
Point route_start={};
size_t next_point = 0;
bool moving = false;
bool hold_transition_pose = false;
float anim = 0, retry = 0;
int walk_frame() {
    return npc_walk_col(state.facing,(int)(anim/.2f));
}
InteriorMap room;
int home_door = -1, parents_door = -1;
uint16_t trail_mask[5][16][16] = {};
bool trail_mask_loaded = false;

bool load_trail_mask() {
    if(trail_mask_loaded)return true;
    // Town 0's trail is drawn in atlas columns 0..15, rows 6..10.
    // Transparent red corners belong to the grass, not the trail.
    SDL_Surface* sheet=IMG_Load("assets/tileset.png");
    if(!sheet)return false;
    SDL_Surface* crop=SDL_CreateRGBSurfaceWithFormat(0,256,80,32,SDL_PIXELFORMAT_RGBA32);
    if(!crop){SDL_FreeSurface(sheet);return false;}
    SDL_Rect src={0,96,256,80};
    SDL_BlitSurface(sheet,&src,crop,nullptr);SDL_FreeSurface(sheet);
    for(int y=0;y<80;y++)for(int x=0;x<256;x++) {
        Uint8 r,g,b,a;
        Uint32 pixel=*(Uint32*)((Uint8*)crop->pixels+y*crop->pitch+x*4);
        SDL_GetRGBA(pixel,crop->format,&r,&g,&b,&a);
        if(a && ((r==0xd7&&g==0xa1&&b==0x75)||(r==0x8d&&g==0x6b&&b==0x4f)))
            trail_mask[y/16][x/16][y%16]|=1u<<(x%16);
    }
    SDL_FreeSurface(crop);trail_mask_loaded=true;return true;
}
bool trail_pixel(const Tilemap* map,float x,float y) {
    if(x<0||y<0||x>=MAP_WIDTH*TILE_SIZE||y>=MAP_HEIGHT*TILE_SIZE)return false;
    int tile=map->tiles[(int)y/TILE_SIZE][(int)x/TILE_SIZE];
    if(tile==TILE_PATH||tile==TILE_ROAD)return true;
    int index=tile-TILE_TOWN0_BASE,col=index%TOWN0_SHEET_COLS,row=index/TOWN0_SHEET_COLS;
    if(index<0||col>=16||row<6||row>10)return false;
    int px=((int)x%TILE_SIZE)/2,py=((int)y%TILE_SIZE)/2;
    return (trail_mask[row-6][col][py]>>px)&1;
}

int door_for(const Tilemap* map,int interior){return resident_town_door(map,interior);}
Point outside(const Tilemap* map,int door){return resident_outside(map,door);}
Point entry(int interior){return resident_entry(interior);}
bool fits(const Tilemap* map, float x,float y) {
    return state.location<0 ? resident_on_trail(map,x,y,true) && can_occupy(map,x,y,tilemap_pixel_solid)
                            : interior_feet_fit(&room,x,y);
}
bool segment(const Tilemap* map, Point a,Point b,bool require_trail=true) {
    int n=std::max(1,(int)std::ceil(std::hypot(b.x-a.x,b.y-a.y)/2));
    for(int i=1;i<=n;i++) {
        float x=a.x+(b.x-a.x)*i/n,y=a.y+(b.y-a.y)*i/n;
        if(require_trail ? !fits(map,x,y) : !can_occupy(map,x,y,tilemap_pixel_solid))return false;
    }
    return true;
}

// A* on a fine feet grid. Outdoors every sampled step must keep the whole
// feet box on the visible trail. Interiors use the player's furniture collision.
bool path(const Tilemap* map, Point target) {
    if(state.location>=0) interior_load(&room,state.location);
    int step=state.location<0?8:4,ox=0,oy=0,w=640/step,h=480/step;
    if(state.location<0) {
        ox=(map->towns[0].x+50)*TILE_SIZE;oy=(map->towns[0].y+60)*TILE_SIZE;
        w=85*TILE_SIZE/step;h=50*TILE_SIZE/step;
    }
    Point start={state.x,state.y};
    bool rejoin=state.location<0 && !resident_on_trail(map,start.x,start.y,true);
    return resident_find_route(start,target,step,ox,oy,w,h,rejoin,
        [&](Point p){return fits(map,p.x,p.y);},
        [&](Point a,Point b,bool trail){return segment(map,a,b,trail);},
        route,route_start,next_point);
}

constexpr unsigned CLERK_MAGIC=0x434c4b31;
const Point SHELF_STOPS[]={{235,196},{371,196},{434,308},{374,257}};
const float SHELF_PAUSES[]={3,4,3,4};
BookshopClerkSave clerk={CLERK_MAGIC,235,196,3,0,0,FACE_UP,1};
InteriorMap clerk_room;
Point shelf_targets[4],clerk_route_start={};
std::vector<Point> clerk_route;
size_t clerk_next=0;
bool shelves_ready=false,clerk_moving=false,clerk_talking=false;
int clerk_resume_facing=FACE_UP;
float clerk_retry=0;
SDL_Texture* clerk_art=nullptr;

bool clerk_segment(Point a,Point b) {
    int n=std::max(1,(int)std::ceil(std::hypot(b.x-a.x,b.y-a.y)/2));
    for(int i=0;i<=n;i++)
        if(!interior_feet_fit(&clerk_room,a.x+(b.x-a.x)*i/n,a.y+(b.y-a.y)*i/n))return false;
    return true;
}
bool prepare_shelves() {
    if(shelves_ready)return true;
    interior_load(&clerk_room,1);
    for(int i=0;i<4;i++) {
        float best=1e20f;bool found=false;
        for(int dy=-24;dy<=24;dy++)for(int dx=-24;dx<=24;dx++) {
            float d=(float)(dx*dx+dy*dy);
            Point p={SHELF_STOPS[i].x+dx,SHELF_STOPS[i].y+dy};
            if(d<=24*24 && d<best && interior_feet_fit(&clerk_room,p.x,p.y)) {
                shelf_targets[i]=p;best=d;found=true;
            }
        }
        if(!found){SDL_Log("Bookshop clerk: shelf %d has no clear approach",i);return false;}
    }
    shelves_ready=true;
    return true;
}
void clerk_tick(float dt) {
    if(clerk_talking || !prepare_shelves())return;
    clerk_moving=false;
    if(clerk.browsing) {
        clerk.facing=FACE_UP;clerk.anim=0;
        clerk.pause=std::max(0.0f,clerk.pause-dt);
        if(clerk.pause==0){clerk.browsing=0;clerk.stop=(clerk.stop+1)%4;}
        return;
    }
    if(clerk_route.empty()) {
        if(grandmother_reserved_shelf()==clerk.stop) {
            clerk.facing=FACE_UP;clerk.anim=0;return;
        }
        clerk_retry-=dt;if(clerk_retry>0)return;
        if(!resident_find_route({clerk.x,clerk.y},shelf_targets[clerk.stop],4,0,0,160,120,false,
            [](Point p){return interior_feet_fit(&clerk_room,p.x,p.y);},
            [](Point a,Point b,bool){return clerk_segment(a,b);},
            clerk_route,clerk_route_start,clerk_next)) {clerk_retry=3;return;}
    }
    clerk_moving=resident_follow_route(clerk_route,clerk_next,clerk_route_start,clerk.x,clerk.y,clerk.facing,SPEED*dt);
    clerk.anim=clerk_moving?std::fmod(clerk.anim+dt,.8f):0;
    if(clerk_next==clerk_route.size()) {
        clerk.browsing=1;clerk.pause=SHELF_PAUSES[clerk.stop];clerk.facing=FACE_UP;
        clerk.anim=0;clerk_moving=false;clerk_route.clear();clerk_next=0;
    }
}
Point destination(const Tilemap* map) {
    switch(state.phase) {
    case RES_WORK: return KITCHEN_LOOP[state.kitchen_leg];
    case RES_LEAVE_HOME: return entry(4);
    case RES_TO_PARENTS: return outside(map,parents_door);
    case RES_TO_BED: return {224,224}; // feet (238,258), just below left bed
    case RES_LEAVE_PARENTS: return entry(3);
    case RES_TO_HOME: return outside(map,home_door);
    default: return {336,224}; // feet (350,258), between counter and stove
    }
}
void change(int phase) {state.phase=phase;state.activity_seconds=0;state.kitchen_leg=0;state.kitchen_pause=0;route.clear();next_point=0;retry=0;}
void transfer(const Tilemap* map) {
    Point p;
    if(state.phase==RES_LEAVE_HOME) {state.location=-1;p=outside(map,home_door);change(RES_TO_PARENTS);}
    else if(state.phase==RES_TO_PARENTS) {state.location=3;p=entry(3);change(RES_TO_BED);}
    else if(state.phase==RES_LEAVE_PARENTS) {state.location=-1;p=outside(map,parents_door);change(RES_TO_HOME);}
    else {state.location=4;p=entry(4);change(RES_TO_WORK);}
    state.x=p.x;state.y=p.y;state.flash=FLASH_STEP;state.transfer_pending=0;
}
}

bool resident_on_trail(const Tilemap* map,float x,float y,bool allow_door_approach) {
    if(!map||!load_trail_mask())return false;
    int doors[4]={-1,-1,-1,-1};
    if(allow_door_approach){doors[0]=door_for(map,4);doors[1]=door_for(map,3);doors[2]=door_for(map,5);doors[3]=door_for(map,1);}
    for(int py=HB_Y1;py<=HB_Y2;py+=2)
        for(int px=HB_X1;px<=HB_X2;px+=2) {
            float fx=x+px,fy=y+py;
            if(trail_pixel(map,fx,fy))continue;
            bool approach=false;
            for(int d:doors)if(d>=0) {
                const auto& door=map->doors[d];
                float cx=(door.x+door.w*.5f)*TILE_SIZE,bottom=(door.y+1)*TILE_SIZE;
                // A 16px-wide straight walk from the door down onto its trail.
                if(std::fabs(fx-cx)<=8 && fy>=bottom-8 && fy<=bottom+48)approach=true;
            }
            if(!approach)return false;
        }
    return true;
}
void resident_reset() {
    state={0,0,336,224,0,RES_WORK,4,FACE_UP,0,MAGIC};
    route.clear();next_point=0;moving=false;hold_transition_pose=false;anim=retry=0;
    bookshop_clerk_reset();
    grandmother_reset();
    fisher_reset();
    woodcutter_reset();
}
ResidentSave resident_save(){return state;}
void resident_face(int facing){state.facing=facing;}
bool resident_restore(const ResidentSave& s) {
    if(s.magic!=MAGIC||!std::isfinite(s.world_seconds)||s.world_seconds<0||
       !std::isfinite(s.activity_seconds)||s.activity_seconds<0||s.activity_seconds>10800||
       !std::isfinite(s.x)||!std::isfinite(s.y)||s.x<0||s.y<0||s.x>=MAP_WIDTH*TILE_SIZE||s.y>=MAP_HEIGHT*TILE_SIZE||
       !std::isfinite(s.flash)||s.flash<0||s.flash>FLASH_STEP||
       (s.transfer_pending!=0 && s.transfer_pending!=1)||
       s.kitchen_leg<0||s.kitchen_leg>=6||
       !std::isfinite(s.kitchen_pause)||s.kitchen_pause<0||s.kitchen_pause>2||
       s.transition_frame<0||s.transition_frame>2||
       s.phase<RES_WORK||s.phase>RES_TO_WORK||
       s.location!=(s.phase==RES_TO_HOME||s.phase==RES_TO_PARENTS?-1:
                    s.phase==RES_TO_BED||s.phase==RES_SLEEP||s.phase==RES_LEAVE_PARENTS?3:4))return false;
    resident_reset();state=s;
    hold_transition_pose=s.flash>0;
    // Older saves used three-hour activities; finish them on the next tick
    // if the new one-hour duration has already elapsed.
    state.activity_seconds=std::min(state.activity_seconds,ACTIVITY_HOUR);
    return true;
}
static void girl_tick(const Tilemap* map,float dt) {
    if(dt<=0||!map)return;
    state.world_seconds+=dt*48.0;moving=false;
    home_door=door_for(map,4);parents_door=door_for(map,3);
    if(home_door<0||parents_door<0)return;
    if(state.flash>0) {
        state.flash=std::max(0.0f,state.flash-dt);
        if(state.flash==0 && state.transfer_pending)transfer(map);
        return;
    }
    if(state.phase==RES_WORK||state.phase==RES_SLEEP) {
        state.activity_seconds+=dt*48.0;
        if(state.activity_seconds>=ACTIVITY_HOUR) {
            change(state.phase==RES_WORK?RES_LEAVE_HOME:RES_LEAVE_PARENTS);
            return;
        }
        if(state.phase==RES_SLEEP)return;
    }
    if(state.phase==RES_WORK && state.kitchen_pause>0) {
        state.kitchen_pause=std::max(0.0f,state.kitchen_pause-dt);
        state.facing=FACE_UP;anim=0;
        return;
    }
    if(route.empty()) {
        retry-=dt;if(retry>0)return;
        if(!path(map,destination(map))){retry=3;return;}
    }
    // Never waits for the player, who walks through.
    moving=resident_follow_route(route,next_point,route_start,state.x,state.y,state.facing,SPEED*dt);
    if(moving){anim+=dt;hold_transition_pose=false;}else anim=0;
    if(next_point==route.size()) {
        moving=false;
        if(state.phase==RES_WORK) {
            if(state.kitchen_leg==0||state.kitchen_leg==3) {
                state.facing=FACE_UP;
                state.kitchen_pause=2.0f;
                anim=0;
            }
            state.kitchen_leg=(state.kitchen_leg+1)%6;
            route.clear();next_point=0;
        }
        else if(state.phase==RES_TO_WORK){change(RES_WORK);state.facing=FACE_RIGHT;}
        else if(state.phase==RES_TO_BED){change(RES_SLEEP);state.facing=FACE_LEFT;}
        else {
            state.transition_frame=walk_frame();
            hold_transition_pose=true;
            state.flash=FLASH_STEP;state.transfer_pending=1;route.clear();
        }
    }
}
void resident_tick(const Tilemap* map,float dt) {
    if(dt<=0||!map)return;
    girl_tick(map,dt); // owns the shared clock; never advance it per resident
    grandmother_tick(map,dt);
    clerk_tick(dt);
    fisher_tick(map,dt);
    woodcutter_tick(map,dt);
}
void resident_advance_hour(const Tilemap* map) {
    if(!map)return;
    const double target=state.world_seconds+3600;
    // Simulate the skipped 75 real seconds in normal-sized steps so walking,
    // doors, sleep and activity boundaries all advance together.
    for(int i=0;i<1500;i++)resident_tick(map,.05f);
    state.world_seconds=target;
}
bool resident_here(const StoryWhere& w,StoryNpcPos* out) {
    bool here=state.location<0?w.state==STATE_OVERWORLD:
        w.state==STATE_INTERIOR && w.room==state.location && w.door==door_for(w.map,state.location);
    if(!here)return false;
    *out={RESIDENT_STORY_ID,state.x,state.y,-1};return true;
}
const char* resident_line() {
    switch(state.phase) {
    case RES_LEAVE_HOME: case RES_TO_PARENTS: return "heading over to my parents house right now, please leave me";
    case RES_TO_BED: return "time for bed *yawnnnnn*";
    case RES_SLEEP: return "zzzz";
    case RES_LEAVE_PARENTS: case RES_TO_HOME: case RES_TO_WORK: return "Sorry i'm busy at the moment";
    default: return "these new stoves scare me, i'm always afraid of a sudden gas leak"; // at home
    }
}
bool resident_art_init(SDL_Renderer* r) {
    resident_art_free();
    art=IMG_LoadTexture(r,"assets/npcs/girl.png");
    clerk_art=IMG_LoadTexture(r,"assets/npcs/glasses.png");
    if(art)SDL_SetTextureScaleMode(art,SDL_ScaleModeNearest);
    if(clerk_art)SDL_SetTextureScaleMode(clerk_art,SDL_ScaleModeNearest);
    return art != nullptr && clerk_art != nullptr && grandmother_art_init(r) && woodcutter_art_init(r) && fisher_art_init(r);
}
void resident_art_free(){if(art)SDL_DestroyTexture(art);art=nullptr;if(clerk_art)SDL_DestroyTexture(clerk_art);clerk_art=nullptr;grandmother_art_free();woodcutter_art_free();fisher_art_free();}
bool resident_draw(const StoryNpcPos& p,SDL_Renderer* r,const Camera* c) {
    if(fisher_draw(p,r,c))return true;
    if(grandmother_draw(p,r,c)||woodcutter_draw(p,r,c))return true;
    if(p.idx==BOOKSHOP_CLERK_ID) {
        if(!clerk_art)return true;
        int col=clerk_moving&&!clerk_talking?npc_walk_col(clerk.facing,(int)(clerk.anim/.2f)):0;
        SDL_Rect src={col*14,npc_sheet_row(clerk.facing)*20,14,20};
        SDL_Rect dst={cam_screen_x(c,p.x),cam_screen_y(c,p.y),(int)(28*c->zoom),(int)(40*c->zoom)};
        SDL_RenderCopy(r,clerk_art,&src,&dst);return true;
    }
    if(p.idx!=RESIDENT_STORY_ID)return false;
    if(!art)return true;
    int row=npc_sheet_row(state.facing);
    int col=state.flash>0||hold_transition_pose?state.transition_frame:moving?walk_frame():0;
    SDL_Rect src={col*14,row*20,14,20};
    SDL_Rect dst={cam_screen_x(c,p.x),cam_screen_y(c,p.y),(int)(28*c->zoom),(int)(40*c->zoom)};
    SDL_Texture* tex=art;
    if(state.flash>0) {
        float visibility=state.flash/FLASH_STEP;
        if(!state.transfer_pending)visibility=1-visibility;
        draw_actor_appearance(r,tex,src,dst,visibility);
        return true;
    }
    if(state.phase==RES_SLEEP) {
        src={0,0,14,20};
        dst={cam_screen_x(c,232),cam_screen_y(c,204),(int)(20*c->zoom),(int)(32*c->zoom)};
        SDL_RenderCopyEx(r,tex,&src,&dst,-90,nullptr,SDL_FLIP_NONE);
    } else SDL_RenderCopy(r,tex,&src,&dst);
    return true;
}

void bookshop_clerk_reset() {
    clerk={CLERK_MAGIC,235,196,3,0,0,FACE_UP,1};
    clerk_route.clear();clerk_next=0;clerk_retry=0;
    shelves_ready=clerk_moving=clerk_talking=false;
}
BookshopClerkSave bookshop_clerk_save() {
    auto saved=clerk;
    if(clerk_talking)saved.facing=clerk_resume_facing;
    return saved;
}
bool bookshop_clerk_valid(const BookshopClerkSave& s) {
    if(s.magic!=CLERK_MAGIC || !std::isfinite(s.x)||!std::isfinite(s.y) ||
       s.x<0||s.x>=640||s.y<0||s.y>=480 ||
       !std::isfinite(s.pause)||s.pause<0||s.pause>4 ||
       !std::isfinite(s.anim)||s.anim<0||s.anim>=.8f ||
       s.stop<0||s.stop>3 || (s.browsing!=0&&s.browsing!=1) ||
       (s.facing!=FACE_UP&&s.facing!=FACE_DOWN&&s.facing!=FACE_LEFT&&s.facing!=FACE_RIGHT))return false;
    InteriorMap im;interior_load(&im,1);
    return interior_feet_fit(&im,s.x,s.y);
}
bool bookshop_clerk_restore(const BookshopClerkSave& s) {
    if(!bookshop_clerk_valid(s))return false;
    bookshop_clerk_reset();clerk=s;return true;
}
bool bookshop_clerk_here(const StoryWhere& w,StoryNpcPos* out) {
    if(!w.map||w.state!=STATE_INTERIOR||w.room!=1||w.door<0||w.door!=door_for(w.map,1))return false;
    *out={BOOKSHOP_CLERK_ID,clerk.x,clerk.y,-1};return true;
}
void bookshop_clerk_face(int facing) {
    if(!clerk_talking)clerk_resume_facing=clerk.facing;
    clerk_talking=true;clerk.facing=facing;
}
void bookshop_clerk_resume() {
    clerk_talking=false;clerk.facing=clerk.browsing?FACE_UP:clerk_resume_facing;
}
int bookshop_clerk_facing(){return clerk.facing;}
