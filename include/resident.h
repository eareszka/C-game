#pragma once
#include "story.h"

// Saved explicitly after the existing save record. Coordinates are sprite origins.
struct ResidentSave {
    double world_seconds;
    double activity_seconds;
    float x, y, flash;
    int phase, location, facing, transfer_pending;
    unsigned magic;
    int kitchen_leg;
    float kitchen_pause;
    int transition_frame;
};
enum ResidentPhase { RES_WORK, RES_LEAVE_HOME, RES_TO_PARENTS, RES_TO_BED,
    RES_SLEEP, RES_LEAVE_PARENTS, RES_TO_HOME, RES_TO_WORK };
void resident_reset();
ResidentSave resident_save();
void resident_face(int facing);   // spoken to: turn to the player
bool resident_restore(const ResidentSave& saved);
void resident_tick(const Tilemap* map, float dt);
void resident_advance_hour(const Tilemap* map);
// Entire feet box must fit the visible trail; optionally allow narrow door approaches.
bool resident_on_trail(const Tilemap* map, float x, float y, bool allow_door_approach = false);
bool resident_here(const StoryWhere& where, StoryNpcPos* out);
bool resident_draw(const StoryNpcPos& pos, SDL_Renderer* renderer, const Camera* camera);
const char* resident_line();
bool resident_art_init(SDL_Renderer* renderer);
void resident_art_free();
constexpr int RESIDENT_STORY_ID = 10000;
constexpr int BOOKSHOP_CLERK_ID = 10001;
// Separate footer: the original resident save layout remains compatible.
struct BookshopClerkSave {
    unsigned magic;
    float x, y, pause, anim;
    int stop, facing, browsing;
};
BookshopClerkSave bookshop_clerk_save();
bool bookshop_clerk_valid(const BookshopClerkSave& saved);
bool bookshop_clerk_restore(const BookshopClerkSave& saved);
void bookshop_clerk_reset();
bool bookshop_clerk_here(const StoryWhere& where, StoryNpcPos* out);
void bookshop_clerk_face(int facing);
int bookshop_clerk_facing();
void bookshop_clerk_resume();
