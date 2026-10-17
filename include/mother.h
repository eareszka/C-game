#pragma once
#include "story.h"
// The girl's mother (room 3): cooks between the stove and the counter for a
// game hour, then walks to the book shop for a book -- a free shelf, then the
// desk, in line behind the grandmother if she has it -- and home again.
constexpr int MOTHER_ID = 10006;
enum MotherPhase { MO_KITCHEN, MO_LEAVE_HOME, MO_TO_SHOP, MO_FIND_SHELF, MO_TO_SHELF, MO_BROWSE,
    MO_TO_DESK, MO_QUEUE, MO_BUY, MO_LEAVE_SHOP, MO_TO_HOME, MO_TO_KITCHEN };
struct MotherSave {
    unsigned magic;
    float x, y, elapsed, anim, flash, pause;
    int phase, location, facing, transfer_pending, transition_frame, shelf, leg;
};
void mother_reset();
MotherSave mother_save();
bool mother_valid(const MotherSave& state);
bool mother_restore(const MotherSave& state);
void mother_tick(const Tilemap* map, float dt);
bool mother_here(const StoryWhere& where, StoryNpcPos* out);
bool mother_draw(const StoryNpcPos& pos, SDL_Renderer* renderer, const Camera* camera);
const char* mother_line();
void mother_face(int facing);
int mother_facing();
int mother_reserved_shelf();   // the shelf she is at or heading to, -1 none
bool mother_at_desk();         // at the desk or heading to it
bool mother_art_init(SDL_Renderer* renderer);
void mother_art_free();
