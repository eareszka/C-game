#pragma once
#include "story.h"
constexpr int GARDENER_ID=10007;
// Independent v16 footer; target is a planting index, direction is +1 or -1.
// initialized: 0 new, 1 approaching/watering, 2 returning to the street.
// remaining counts unpaused real seconds. The street route is rebuilt on load.
struct GardenerSave { unsigned magic; float x,y,remaining,anim; int target,direction,watering,facing,initialized; };
void gardener_reset();
GardenerSave gardener_save();
bool gardener_valid(const GardenerSave&);
bool gardener_restore(const GardenerSave&);
void gardener_tick(const Tilemap*,float);
// Check every full feet box and every pixel of the authored street sweep.
bool gardener_validate_route(const Tilemap*);
bool gardener_here(const StoryWhere&,StoryNpcPos*);
const char* gardener_line();
void gardener_face(int);
int gardener_facing();
void gardener_resume();
bool gardener_art_init(SDL_Renderer*);
void gardener_art_free();
bool gardener_draw(const StoryNpcPos&,SDL_Renderer*,const Camera*);
