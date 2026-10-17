#include "mother.h"
#include "bookshop.h"
#include "resident.h"
#include "resident_path.h"
#include "interior.h"
#include "tilemap.h"
#include "camera.h"
#include "battle.h"
#include <SDL2/SDL_image.h>
#include <algorithm>
#include <cmath>
#include <vector>

namespace {
using Point = ResidentPoint;
constexpr unsigned MAGIC = 0x4d4f5431;
constexpr int HOME = 3;                                  // the girl's parents' house
constexpr float SPEED = 90, BEAT = .2f;
constexpr float KITCHEN_TIME = 3600 / 48.0f;             // one game hour, as the girl's
constexpr float SURFACE_PAUSE = 2, BROWSE_TIME = 5, BUY_TIME = 5;   // as the grandmother's
// Room 3's kitchen (house3_design.py): the floor before the stove and before
// the counter, facing them.
constexpr Point STOVE = {216, 220}, COUNTER = {283, 220};
MotherSave m = {MAGIC, STOVE.x, STOVE.y, 0, 0, 0, SURFACE_PAUSE, MO_KITCHEN, HOME, FACE_UP, 0, 0, -1, 1};
InteriorMap room;
std::vector<Point> route;
Point route_start = {};
size_t next = 0;
bool moving = false;
float retry = 0;
SDL_Texture* art = nullptr;

bool fits(Point p) { return interior_feet_fit(&room, p.x, p.y); }
bool path(const Tilemap* map, Point target) {
    if (m.location < 0) return resident_trail_route(map, {m.x, m.y}, target, route, route_start, next);
    interior_load(&room, m.location);
    return resident_find_route({m.x, m.y}, target, 4, 0, 0, 160, 120, false,
        [](Point p) { return fits(p); },
        [](Point a, Point b, bool) { return resident_way_fits(a, b, [](Point p) { return fits(p); }); },
        route, route_start, next);
}
void phase(int p) {
    m.phase = p; m.elapsed = 0; m.pause = 0;
    route.clear(); next = 0; retry = 0; moving = false;
}
Point destination(const Tilemap* map) {
    switch (m.phase) {
    case MO_KITCHEN:    return m.leg ? COUNTER : STOVE;
    case MO_LEAVE_HOME: return resident_entry(HOME);
    case MO_TO_SHOP:    return resident_outside(map, resident_town_door(map, BOOKSHOP_ROOM));
    case MO_TO_SHELF:   return BOOKSHOP_SHELF[m.shelf];
    case MO_TO_DESK:    return BOOKSHOP_DESK;
    case MO_QUEUE:      return BOOKSHOP_QUEUE;
    case MO_LEAVE_SHOP: return resident_entry(BOOKSHOP_ROOM);
    case MO_TO_HOME:    return resident_outside(map, resident_town_door(map, HOME));
    default:            return STOVE;   // MO_TO_KITCHEN
    }
}
void transfer(const Tilemap* map) {
    Point p;
    switch (m.phase) {
    case MO_LEAVE_HOME:  m.location = -1; p = resident_outside(map, resident_town_door(map, HOME)); phase(MO_TO_SHOP); break;
    case MO_TO_SHOP:     m.location = BOOKSHOP_ROOM; p = resident_entry(BOOKSHOP_ROOM); phase(MO_FIND_SHELF); break;
    case MO_LEAVE_SHOP:  m.location = -1; p = resident_outside(map, resident_town_door(map, BOOKSHOP_ROOM)); phase(MO_TO_HOME); break;
    default:             m.location = HOME; p = resident_entry(HOME); phase(MO_TO_KITCHEN); break;
    }
    m.x = p.x; m.y = p.y; m.flash = ACTOR_APPEAR_T; m.transfer_pending = 0;
}
int location_of(int phase) {
    if (phase == MO_TO_SHOP || phase == MO_TO_HOME) return -1;
    if (phase == MO_KITCHEN || phase == MO_LEAVE_HOME || phase == MO_TO_KITCHEN) return HOME;
    return BOOKSHOP_ROOM;
}
}

void mother_reset() {
    m = {MAGIC, STOVE.x, STOVE.y, 0, 0, 0, SURFACE_PAUSE, MO_KITCHEN, HOME, FACE_UP, 0, 0, -1, 1};
    route.clear(); next = 0; moving = false; retry = 0;
}
MotherSave mother_save() { return m; }
void mother_face(int facing) { m.facing = facing; }
int mother_facing() { return m.facing; }
int mother_reserved_shelf() {
    return m.phase == MO_TO_SHELF || m.phase == MO_BROWSE || m.phase == MO_TO_DESK ? m.shelf : -1;
}
bool mother_at_desk() { return m.phase == MO_TO_DESK || m.phase == MO_BUY; }

void mother_tick(const Tilemap* map, float dt) {
    if (!map || dt <= 0) return;
    if (resident_town_door(map, HOME) < 0 || resident_town_door(map, BOOKSHOP_ROOM) < 0) return;
    moving = false;
    if (m.flash > 0) {
        m.flash = std::max(0.0f, m.flash - dt);
        if (m.flash == 0 && m.transfer_pending) transfer(map);
        return;
    }
    switch (m.phase) {
    case MO_KITCHEN:   // the hour runs while she walks between the two as well
        m.elapsed += dt;
        if (m.elapsed >= KITCHEN_TIME) { phase(MO_LEAVE_HOME); return; }
        if (m.pause > 0) { m.pause = std::max(0.0f, m.pause - dt); m.facing = FACE_UP; m.anim = 0; return; }
        break;
    case MO_FIND_SHELF:   // the first shelf nobody holds; none free, she waits by the door
        for (int s = 0; s < BOOKSHOP_SHELVES; s++)
            if (!bookshop_shelf_taken(s, SHOP_MOTHER)) { m.shelf = s; phase(MO_TO_SHELF); break; }
        return;
    case MO_BROWSE:
        m.elapsed += dt; m.facing = FACE_UP; m.anim = 0;
        if (m.elapsed >= BROWSE_TIME) phase(bookshop_desk_taken(SHOP_MOTHER) ? MO_QUEUE : MO_TO_DESK);
        return;
    case MO_BUY:
        m.elapsed += dt; m.facing = FACE_UP; m.anim = 0;
        if (m.elapsed >= BUY_TIME) { m.shelf = -1; phase(MO_LEAVE_SHOP); }
        return;
    case MO_QUEUE:   // in line: the moment the desk is free she steps up
        if (!bookshop_desk_taken(SHOP_MOTHER)) { phase(MO_TO_DESK); return; }
        break;
    default: break;
    }
    if (route.empty()) {
        retry -= dt; if (retry > 0) return;
        if (!path(map, destination(map))) { retry = 3; return; }
    }
    moving = resident_follow_route(route, next, route_start, m.x, m.y, m.facing, SPEED * dt);
    m.anim = moving ? std::fmod(m.anim + dt, 4 * BEAT) : 0;
    if (next < route.size()) return;
    switch (m.phase) {
    case MO_KITCHEN:   // at the stove or the counter: a moment there, then the other
        m.pause = SURFACE_PAUSE; m.facing = FACE_UP; m.leg ^= 1; route.clear(); next = 0; moving = false; break;
    case MO_TO_KITCHEN: phase(MO_KITCHEN); m.leg = 1; m.pause = SURFACE_PAUSE; m.facing = FACE_UP; break;
    case MO_TO_SHELF:   phase(MO_BROWSE); m.facing = FACE_UP; break;
    case MO_TO_DESK:    phase(MO_BUY); m.facing = FACE_UP; break;
    case MO_QUEUE:      m.facing = FACE_UP; m.anim = 0; moving = false; break;   // waiting
    default:            // at a door: through it
        m.transition_frame = npc_walk_col(m.facing, (int)(m.anim / BEAT));
        m.flash = ACTOR_APPEAR_T; m.transfer_pending = 1; route.clear(); next = 0; moving = false;
    }
}

bool mother_valid(const MotherSave& s) {
    if (s.magic != MAGIC || !std::isfinite(s.x) || !std::isfinite(s.y) || s.x < 0 || s.y < 0 ||
        s.x >= MAP_WIDTH * TILE_SIZE || s.y >= MAP_HEIGHT * TILE_SIZE ||
        !std::isfinite(s.elapsed) || s.elapsed < 0 || s.elapsed > KITCHEN_TIME + .1f ||
        !std::isfinite(s.anim) || s.anim < 0 || s.anim >= 4 * BEAT ||
        !std::isfinite(s.flash) || s.flash < 0 || s.flash > ACTOR_APPEAR_T ||
        !std::isfinite(s.pause) || s.pause < 0 || s.pause > SURFACE_PAUSE ||
        s.phase < MO_KITCHEN || s.phase > MO_TO_KITCHEN || s.location != location_of(s.phase) ||
        (s.transfer_pending != 0 && s.transfer_pending != 1) || s.transition_frame < 0 || s.transition_frame > 2 ||
        s.shelf < -1 || s.shelf >= BOOKSHOP_SHELVES || (s.leg != 0 && s.leg != 1) ||
        ((s.phase == MO_TO_SHELF || s.phase == MO_BROWSE) && s.shelf < 0) ||
        (s.facing != FACE_UP && s.facing != FACE_DOWN && s.facing != FACE_LEFT && s.facing != FACE_RIGHT)) return false;
    if (s.location >= 0) { InteriorMap im; interior_load(&im, s.location); return interior_feet_fit(&im, s.x, s.y); }
    return true;
}
bool mother_restore(const MotherSave& s) {
    if (!mother_valid(s)) return false;
    mother_reset(); m = s; return true;
}
bool mother_here(const StoryWhere& w, StoryNpcPos* out) {
    if (!w.map) return false;
    bool here = m.location < 0 ? w.state == STATE_OVERWORLD :
        w.state == STATE_INTERIOR && w.room == m.location && w.door >= 0 &&
        w.door == resident_town_door(w.map, m.location);
    if (here) *out = {MOTHER_ID, m.x, m.y, -1};
    return here;
}
// Placeholders until the user's lines (one per state, numbered as listed).
const char* mother_line() {
    switch (m.phase) {
    case MO_KITCHEN:    return "Supper won't make itself.";                             // 1 cooking
    case MO_LEAVE_HOME: return "Off to the book shop. Mind the stove for me.";          // 2 to the front door
    case MO_TO_SHOP:    return "I'm on my way to the book shop.";                       // 3 walking there
    case MO_FIND_SHELF:
    case MO_TO_SHELF:   return "Let's see what's new on the shelves.";                  // 4 to a shelf
    case MO_BROWSE:     return "Hmm, which one...";                                     // 5 browsing
    case MO_TO_DESK:    return "This one will do.";                                     // 6 to the desk
    case MO_QUEUE:      return "I'll wait my turn.";                                    // 7 in line
    case MO_BUY:        return "Just this one, please.";                                // 8 buying
    case MO_LEAVE_SHOP: return "Got my book.";                                          // 9 leaving
    case MO_TO_HOME:    return "Heading home to read.";                                 // 10 walking home
    default:            return "Back to the kitchen.";                                  // 11 to the kitchen
    }
}
bool mother_art_init(SDL_Renderer* r) {
    mother_art_free();
    art = IMG_LoadTexture(r, "assets/npcs/flower_seller.png");
    if (art) SDL_SetTextureScaleMode(art, SDL_ScaleModeNearest);
    return art != nullptr;
}
void mother_art_free() { if (art) SDL_DestroyTexture(art); art = nullptr; }
bool mother_draw(const StoryNpcPos& p, SDL_Renderer* r, const Camera* cam) {
    if (p.idx != MOTHER_ID) return false;
    if (!art) return true;
    int col = m.flash > 0 ? m.transition_frame : moving ? npc_walk_col(m.facing, (int)(m.anim / BEAT)) : 0;
    SDL_Rect src = {col * 14, npc_sheet_row(m.facing) * 20, 14, 20};
    SDL_Rect dst = {cam_screen_x(cam, p.x), cam_screen_y(cam, p.y), (int)(28 * cam->zoom), (int)(40 * cam->zoom)};
    if (m.flash > 0) {
        float visibility = m.flash / ACTOR_APPEAR_T;
        if (!m.transfer_pending) visibility = 1 - visibility;
        draw_actor_appearance(r, art, src, dst, visibility);
    } else SDL_RenderCopy(r, art, &src, &dst);
    return true;
}
