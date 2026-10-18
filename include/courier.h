#pragma once
#include "story.h"
constexpr int COURIER_ID=10008;
enum CourierPhase { CR_SLEEP, CR_LEAVE_HOME, CR_TO_DOOR, CR_DELIVER, CR_ENTER_HOME, CR_TO_COUCH };
struct CourierSave {
    unsigned magic;
    float x,y,elapsed,anim,flash;
    int phase,location,facing,transfer_pending,transition_frame,stop;
};
void courier_reset();
CourierSave courier_save();
bool courier_valid(const CourierSave&);
bool courier_restore(const CourierSave&);
void courier_tick(const Tilemap*,float);
bool courier_here(const StoryWhere&,StoryNpcPos*);
const char* courier_line();
void courier_face(int);
int courier_facing();
void courier_resume();
bool courier_art_init(SDL_Renderer*);
void courier_art_free();
bool courier_draw(const StoryNpcPos&,SDL_Renderer*,const Camera*);
// Stable north-to-south order, with home last. Includes every Town 0 entrance.
int courier_doors(const Tilemap*,int* out,int capacity);
