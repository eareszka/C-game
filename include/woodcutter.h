#pragma once
#include "story.h"
// Town 0's woodcutter: chops at a tree two game hours, walks home (room 6),
// sleeps two hours, walks back out. He never fells a tree; when his tree is
// felled he moves to the standing one nearest it, and with none left on foot
// he spends chopping time on his sofa.
constexpr int WOODCUTTER_ID=10003;
enum WoodcutterPhase { WC_CHOP,WC_TO_TREE,WC_TO_HOME,WC_TO_BED,WC_SLEEP,WC_LEAVE_HOME,
    WC_TO_WORK,WC_NO_TREES_HOME,WC_TO_COUCH,WC_COUCH,WC_COUCH_TO_BED };
struct WoodcutterSave {
    unsigned magic;
    float x,y,elapsed,anim,flash;
    int phase,location,facing,transfer_pending,transition_frame,tree_x,tree_y;
};
void woodcutter_reset();
WoodcutterSave woodcutter_save();
bool woodcutter_valid(const WoodcutterSave& state);
bool woodcutter_restore(const WoodcutterSave& state);
void woodcutter_tick(const Tilemap* map,float dt);
bool woodcutter_here(const StoryWhere& where,StoryNpcPos* out);
bool woodcutter_draw(const StoryNpcPos& pos,SDL_Renderer* renderer,const Camera* camera);
const char* woodcutter_line();
void woodcutter_face(int facing);
int woodcutter_facing();
bool woodcutter_art_init(SDL_Renderer* renderer);
void woodcutter_art_free();
