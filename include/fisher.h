#pragma once
#include "story.h"
constexpr int FISHER_ID=10004;
enum FisherPhase { FI_SLEEP,FI_TO_EXIT,FI_DISSOLVE_HOME,FI_APPEAR_OUT,
    FI_TO_WATER,FI_FISH,FI_TO_HOME,FI_DISSOLVE_OUT,FI_APPEAR_HOME,FI_TO_BED };
struct FisherSave { unsigned magic; double epoch; };
struct FisherView {
    float x,y,visibility;
    int phase,location,facing,frame;
    double cycle_seconds,return_departure,fishing_start;
};
void fisher_reset();
FisherSave fisher_save();
bool fisher_valid(const FisherSave& saved);
bool fisher_restore(const FisherSave& saved);
void fisher_tick(const Tilemap* map,float dt);
FisherView fisher_view();
const char* fisher_line();
bool fisher_here(const StoryWhere& where,StoryNpcPos* out);
bool fisher_draw(const StoryNpcPos& pos,SDL_Renderer* renderer,const Camera* camera);
bool fisher_art_init(SDL_Renderer* renderer);
void fisher_art_free();
