#pragma once
#include "story.h"
constexpr int GRANDMOTHER_ID=10002;
enum GrandmaPhase { GM_COUCH,GM_LEAVE_HOME,GM_TO_SHOP,GM_FIND_SHELF,
    GM_TO_SHELF,GM_SEARCH,GM_TO_DESK,GM_DESK,GM_LEAVE_SHOP,GM_TO_HOME,GM_TO_COUCH };
struct GrandmotherSave {
    unsigned magic;
    float x,y,elapsed,anim,flash;
    int phase,location,facing,transfer_pending,transition_frame,shelf;
};
void grandmother_reset();
GrandmotherSave grandmother_save();
bool grandmother_valid(const GrandmotherSave& state);
bool grandmother_restore(const GrandmotherSave& state);
void grandmother_tick(const Tilemap* map,float dt);
bool grandmother_here(const StoryWhere& where,StoryNpcPos* out);
bool grandmother_draw(const StoryNpcPos& pos,SDL_Renderer* renderer,const Camera* camera);
bool grandmother_art_init(SDL_Renderer* renderer);
void grandmother_art_free();
int grandmother_reserved_shelf();
void grandmother_face(int facing);
void grandmother_resume();
int grandmother_facing();
