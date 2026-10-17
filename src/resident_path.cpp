#include "resident_path.h"
#include "entity.h"
#include "interior.h"
#include "overworld.h"
#include "towns.h"
#include "resident.h"
#include "collision.h"
#include <unordered_map>
#include <cstdint>
#include <SDL2/SDL.h>
#include <algorithm>
#include <cmath>
#include <queue>

bool resident_find_route(ResidentPoint start, ResidentPoint target, int step, int ox, int oy, int w, int h,
                bool rejoin, const std::function<bool(ResidentPoint)>& fits,
                const std::function<bool(ResidentPoint,ResidentPoint,bool)>& segment,
                std::vector<ResidentPoint>& route, ResidentPoint& route_start, size_t& next_point,
                const std::function<float(ResidentPoint)>& weight) {
    auto point=[&](int i)->ResidentPoint {return {(float)(ox+i%w*step),(float)(oy+i/w*step)};};
    auto nearest=[&](ResidentPoint p,bool rejoin=false)->int {
        int cx=(int)std::round((p.x-ox)/step),cy=(int)std::round((p.y-oy)/step);
        float best=1e20f; int found=-1;
        for(int y=cy-6;y<=cy+6;y++) for(int x=cx-6;x<=cx+6;x++) {
            if(x<0||y<0||x>=w||y>=h) continue;
            int i=y*w+x; ResidentPoint q=point(i);
            float d=std::hypot(q.x-p.x,q.y-p.y);
            if(d<best && fits(q) && segment(p,q,!rejoin)) {best=d;found=i;}
        }
        return found;
    };
    int a=nearest(start,rejoin),b=nearest(target);
    if(a<0||b<0) {SDL_Log("Resident: inaccessible endpoint (%.0f %.0f -> %.0f %.0f)",start.x,start.y,target.x,target.y);return false;}
    struct Open {float score;int i;bool operator<(const Open& p)const{return score>p.score;}};
    std::priority_queue<Open> open;
    std::vector<float> cost(w*h,1e20f);
    std::vector<int> parent(w*h,-1);
    std::vector<unsigned char> closed(w*h,0);
    cost[a]=0;open.push({0,a});
    while(!open.empty()) {
        int i=open.top().i;open.pop();if(closed[i])continue;closed[i]=1;
        if(i==b)break;
        ResidentPoint p=point(i);
        const int dx[8]={1,-1,0,0,1,1,-1,-1};
        const int dy[8]={0,0,1,-1,1,-1,1,-1};
        for(int d=0;d<8;d++) {
            int x=i%w+dx[d],y=i/w+dy[d];
            if(x<0||y<0||x>=w||y>=h)continue;
            int j=y*w+x;if(closed[j])continue;ResidentPoint q=point(j);
            if(!segment(p,q,true))continue;
            float nc=cost[i]+step*(d<4?1.0f:1.41421356237f)*(weight?weight(q):1.0f);
            if(nc>=cost[j])continue;
            cost[j]=nc;parent[j]=i;ResidentPoint end=point(b);
            open.push({nc+std::hypot(q.x-end.x,q.y-end.y),j});
        }
    }
    if(!closed[b]){SDL_Log("Resident: no route to %.0f %.0f",target.x,target.y);return false;}
    route.clear();route.push_back(target);
    for(int i=b;i!=a;i=parent[i])route.push_back(point(i));
    route.push_back(point(a));std::reverse(route.begin(),route.end());next_point=0;
    {
        // Join visible waypoints into straight runs. The entire feet box is
        // sampled along every proposed line in every area, so bends cannot
        // cut across grass, walls or furniture.
        std::vector<ResidentPoint> smooth;
        ResidentPoint anchor=start;size_t first=0;
        if(rejoin){smooth.push_back(route[0]);anchor=route[0];first=1;}
        while(first<route.size()) {
            size_t last=first;
            for(size_t j=first;j<route.size();j++) {
                if(!segment(anchor,route[j],true))break;
                last=j;
            }
            smooth.push_back(route[last]);anchor=route[last];first=last+1;
        }
        route.swap(smooth);
    }
    route_start=start;
    return true;
}

bool resident_follow_route(const std::vector<ResidentPoint>& route, size_t& next_point, ResidentPoint route_start,
                           float& x, float& y, int& facing, float budget) {
    bool moved=false;
    while(next_point<route.size() && budget>0) {
        ResidentPoint p=route[next_point];float dx=p.x-x,dy=p.y-y,d=std::hypot(dx,dy);
        if(d<.01f){next_point++;continue;}
        // Face along the whole leg, so an exact 45-degree one cannot flicker.
        ResidentPoint from=next_point?route[next_point-1]:route_start;
        float hx=p.x-from.x,hy=p.y-from.y;
        facing=std::fabs(hx)>std::fabs(hy)?(hx<0?FACE_LEFT:FACE_RIGHT):(hy<0?FACE_UP:FACE_DOWN);
        float step=std::min(d,budget);
        x+=dx/d*step;y+=dy/d*step;budget-=step;moved=true;
        if(step==d)next_point++;
    }
    return moved;
}

static bool town_door(const Tilemap* map, int i, int interior) {
    const auto& t=map->towns[0];
    const auto& d=map->doors[i];
    return d.interior_id==interior&&d.x>=t.x&&d.x<t.x+TOWN_W&&d.y>=t.y&&d.y<t.y+TOWN_H;
}
int resident_town_door(const Tilemap* map, int interior) {
    if(!map)return -1;
    // Asked thousands of times a search (resident_on_trail). Town 0 has one
    // door per room, so a remembered index that still fits is the answer --
    // checked rather than trusted, so a rebuilt world finds its own.
    static int known[16]={-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1};
    int* cached=interior>=0&&interior<16?&known[interior]:nullptr;
    if(cached&&*cached>=0&&*cached<map->num_doors&&town_door(map,*cached,interior))return *cached;
    for(int i=0;i<map->num_doors;i++)
        if(town_door(map,i,interior)){if(cached)*cached=i;return i;}
    return -1;
}
ResidentPoint resident_outside(const Tilemap* map, int door) {
    Overworld ow={};Player player={};player.width=28;player.height=40;
    overworld_stand_before_door_idx(&ow,&player,map,door);
    return {ow.x,ow.y};
}
ResidentPoint resident_entry(int interior) {
    InteriorMap im;interior_load(&im,interior);
    InteriorPlayer ip={};Player player={};interior_player_init(&ip,&player,&im);
    return {ip.x,ip.y};
}

namespace {
bool walkable(const Tilemap* map,ResidentPoint p){return can_occupy(map,p.x,p.y,tilemap_pixel_solid);}
bool trail_at(const Tilemap* map,ResidentPoint p){return resident_on_trail(map,p.x,p.y,false);}
// What the feet at a whole pixel stand on, remembered for one search: the
// grid's edges share their pixels, each asked by up to sixteen.
enum { KNOWN=1, WALKABLE=2, TRAIL=4 };
std::unordered_map<uint64_t,uint8_t> memo;
uint8_t ground(const Tilemap* map,ResidentPoint p) {
    int x=(int)std::lround(p.x),y=(int)std::lround(p.y);
    uint8_t& g=memo[(uint64_t)(uint32_t)x<<32|(uint32_t)y];
    if(!g) {
        ResidentPoint q={(float)x,(float)y};
        g=KNOWN|(walkable(map,q)?WALKABLE:0);
        if(g&WALKABLE&&trail_at(map,q))g|=TRAIL;
    }
    return g;
}
bool trail_here(const Tilemap* map,ResidentPoint p){return ground(map,p)&TRAIL;}
// The way fits, and keeps to the trail too when `trail`: every other pixel
// over grass (an art pixel, as the player's feet are asked), every fourth
// along the trail, which has nothing that thin.
bool clear_way(const Tilemap* map,ResidentPoint a,ResidentPoint b,bool trail) {
    int n=std::max(1,(int)std::ceil(std::hypot(a.x-b.x,a.y-b.y)/(trail?4:2)));
    for(int i=0;i<=n;i++) {
        ResidentPoint p={a.x+(b.x-a.x)*i/n,a.y+(b.y-a.y)*i/n};
        if(!(ground(map,p)&(trail?TRAIL:WALKABLE)))return false;
    }
    return true;
}
// clear_way over grass, outside a search (nothing remembered).
bool clear_way_now(const Tilemap* map,ResidentPoint a,ResidentPoint b) {
    int n=std::max(1,(int)std::ceil(std::hypot(a.x-b.x,a.y-b.y)));
    for(int i=0;i<=n;i++)if(!walkable(map,{a.x+(b.x-a.x)*i/n,a.y+(b.y-a.y)*i/n}))return false;
    return true;
}
// The trail point nearest p reachable straight across the grass: offsets
// tried nearest first, so the first that works is the answer.
constexpr int GRASS_REACH=16*TILE_SIZE,GRASS_STEP=8;
bool trail_access(const Tilemap* map,ResidentPoint p,ResidentPoint* out) {
    if(trail_at(map,p)){*out=p;return true;}
    static std::vector<ResidentPoint> offsets;
    if(offsets.empty()) {
        for(int dy=-GRASS_REACH;dy<=GRASS_REACH;dy+=GRASS_STEP)
            for(int dx=-GRASS_REACH;dx<=GRASS_REACH;dx+=GRASS_STEP)
                if(dx*dx+dy*dy<=GRASS_REACH*GRASS_REACH)offsets.push_back({(float)dx,(float)dy});
        std::sort(offsets.begin(),offsets.end(),[](ResidentPoint a,ResidentPoint b){return a.x*a.x+a.y*a.y<b.x*b.x+b.y*b.y;});
    }
    for(ResidentPoint o:offsets) {
        ResidentPoint q={p.x+o.x,p.y+o.y};
        if(trail_at(map,q)&&clear_way_now(map,p,q)){*out=q;return true;}
    }
    return false;
}
// The trail point nearest p over any ground, for an end too far from the
// trail for a straight walk to it; and a search over the grass between two
// points, its own route appended to out. Unweighted, so it heads straight
// for its end and opens little.
bool nearest_trail(const Tilemap* map,ResidentPoint p,ResidentPoint* out) {
    constexpr int REACH=48*TILE_SIZE,STEP=16;
    static std::vector<ResidentPoint> offsets;
    if(offsets.empty()) {
        for(int dy=-REACH;dy<=REACH;dy+=STEP)for(int dx=-REACH;dx<=REACH;dx+=STEP)
            if(dx*dx+dy*dy<=REACH*REACH)offsets.push_back({(float)dx,(float)dy});
        std::sort(offsets.begin(),offsets.end(),[](ResidentPoint a,ResidentPoint b){return a.x*a.x+a.y*a.y<b.x*b.x+b.y*b.y;});
    }
    for(ResidentPoint o:offsets){ResidentPoint q={p.x+o.x,p.y+o.y};if(trail_here(map,q)){*out=q;return true;}}
    return false;
}
bool grass_leg(const Tilemap* map,ResidentPoint a,ResidentPoint b,std::vector<ResidentPoint>& out) {
    // A coarse grid first (a quarter of the cells); the fine one only where
    // the woods leave gaps too narrow for it.
    for(int step:{16,8}) {
        const int margin=12*TILE_SIZE;
        int ox=(int)std::min(a.x,b.x)-margin,oy=(int)std::min(a.y,b.y)-margin;
        int w=((int)std::max(a.x,b.x)+margin-ox)/step,h=((int)std::max(a.y,b.y)+margin-oy)/step;
        std::vector<ResidentPoint> leg;ResidentPoint origin;size_t next;
        if(!resident_find_route(a,b,step,ox,oy,w,h,false,
            [&](ResidentPoint p){return ground(map,p)&WALKABLE;},
            [&](ResidentPoint p,ResidentPoint q,bool){return clear_way(map,p,q,false);},leg,origin,next))continue;
        out.insert(out.end(),leg.begin(),leg.end());
        return true;
    }
    return false;
}
bool trail_route(const Tilemap* map,ResidentPoint start,ResidentPoint target,std::vector<ResidentPoint>& out) {
    ResidentPoint on,off;
    bool straight_on=trail_access(map,start,&on),straight_off=trail_access(map,target,&off);
    if((!straight_on&&!nearest_trail(map,start,&on))||(!straight_off&&!nearest_trail(map,target,&off)))return false;
    out.clear();
    if(on.x!=start.x||on.y!=start.y) {
        if(straight_on)out.push_back(on);
        else if(!grass_leg(map,start,on,out))return false;
    }
    // Trails wind, so the box round both ends is wide; only trail cells are
    // ever opened, so its size costs little.
    const int step=16,margin=40*TILE_SIZE;
    int ox=(int)std::min(on.x,off.x)-margin,oy=(int)std::min(on.y,off.y)-margin;
    int w=((int)std::max(on.x,off.x)+margin-ox)/step,h=((int)std::max(on.y,off.y)+margin-oy)/step;
    std::vector<ResidentPoint> trail;ResidentPoint origin;size_t next;
    if(!resident_find_route(on,off,step,ox,oy,w,h,false,
        [&](ResidentPoint p){return trail_here(map,p);},
        [&](ResidentPoint a,ResidentPoint b,bool){return clear_way(map,a,b,true);},trail,origin,next))return false;
    out.insert(out.end(),trail.begin(),trail.end());
    if(off.x!=target.x||off.y!=target.y) {
        if(straight_off)out.push_back(target);
        else if(!grass_leg(map,off,target,out))return false;
    }
    return true;
}
}
bool resident_trail_route(const Tilemap* map, ResidentPoint start, ResidentPoint target,
                          std::vector<ResidentPoint>& route, ResidentPoint& route_start, size_t& next_point) {
    std::vector<ResidentPoint> out;
    memo.clear();
    bool found=trail_route(map,start,target,out);
    memo.clear();
    if(!found)return false;
    route.swap(out);route_start=start;next_point=0;
    return true;
}
