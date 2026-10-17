#pragma once
#include "story.h"
constexpr int SAILOR_FISHER_ID=10005;
enum SailorFisherPhase { SF_SLEEP,SF_TO_EXIT,SF_DISSOLVE_HOME,SF_APPEAR_OUT,
    SF_TO_WATER,SF_FISH,SF_TO_HOME,SF_DISSOLVE_OUT,SF_APPEAR_HOME,SF_TO_BED };
struct SailorFisherSave { unsigned magic; double epoch; };
struct SailorFisherView {
    float x,y,visibility;
    int phase,location,facing,frame;
    double cycle_seconds,return_departure,fishing_start;
};
void sailor_fisher_reset();
SailorFisherSave sailor_fisher_save();
bool sailor_fisher_valid(const SailorFisherSave& saved);
bool sailor_fisher_restore(const SailorFisherSave& saved);
void sailor_fisher_tick(const Tilemap* map,float dt);
SailorFisherView sailor_fisher_view();
const char* sailor_fisher_line();
bool sailor_fisher_here(const StoryWhere& where,StoryNpcPos* out);
bool sailor_fisher_draw(const StoryNpcPos& pos,SDL_Renderer* renderer,const Camera* camera);
bool sailor_fisher_art_init(SDL_Renderer* renderer);
void sailor_fisher_art_free();
