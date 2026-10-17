// The story's state, people and boss sites. See include/story.h.
#include "core.h"
#include "story.h"
#include "fisher.h"
#include "sailor_fisher.h"
#include "resident.h"
#include "grandmother.h"
#include "woodcutter.h"
#include "mother.h"
#include "tilemap.h"
#include "towns.h"      // TOWN_W/H: is a door in a town's footprint
#include "interior.h"   // IMAP_TILE
#include "battle.h"     // enemy_sheet_info: a boss's idle sheet, drawn on the map
#include "camera.h"
#include "crafting.h"   // the keeper's wood and book
#include "dungeon.h"    // dungeon_wiring_for: the bat's tree
#include <SDL2/SDL_image.h>
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static_assert(BOSS_SITE_COUNT == STORY_BOSS_COUNT, "Tilemap::boss_sites is one row a story boss");

static StoryFlags s_flags;
StoryFlags* story_flags() { return &s_flags; }

int story_boss_index(int enemy_id) {
    for (int i = 0; i < STORY_BOSS_COUNT; i++)
        if (STORY_BOSSES[i] == enemy_id) return i;
    return -1;
}
bool story_beaten(int enemy_id) {
    int i = story_boss_index(enemy_id);
    return i >= 0 && ((s_flags.beaten >> i) & 1u);
}
void story_mark_beaten(int enemy_id) {
    int i = story_boss_index(enemy_id);
    if (i >= 0) s_flags.beaten |= 1u << i;
}

// The bits of each tier, in story order.
static const uint32_t TIER1_BITS = (1u << STORY_TIER1) - 1;                          // 06 23 49 30
static const uint32_t TIER2_BITS = ((1u << STORY_TIER2) - 1) << STORY_TIER1;         // 52 44 98
static const uint32_t ANAYE_BIT  = 1u << STORY_ANAYE;
static const uint32_t SWARM_BIT  = 1u << STORY_SWARM;

StoryStage story_stage() {
    uint32_t b = s_flags.beaten;
    if ((b & TIER1_BITS) != TIER1_BITS) return STORY_ARC1;
    if ((b & TIER2_BITS) != TIER2_BITS) return STORY_TURN;
    if (!(b & ANAYE_BIT))               return STORY_DESCENT;
    if (!(b & SWARM_BIT))               return STORY_OPEN;
    return STORY_AMNESIA;
}
void story_set_stage(StoryStage s) {
    static const uint32_t UP_TO[STORY_STAGE_COUNT] = {
        0, TIER1_BITS, TIER1_BITS | TIER2_BITS, TIER1_BITS | TIER2_BITS | ANAYE_BIT,
        TIER1_BITS | TIER2_BITS | ANAYE_BIT | SWARM_BIT };
    s_flags.beaten = UP_TO[s];
}
int story_tier2_kills() {
    int n = 0;
    for (int i = STORY_TIER1; i < STORY_TIER1 + STORY_TIER2; i++) n += (s_flags.beaten >> i) & 1u;
    return n;
}

// ── Boss sites ───────────────────────────────────────────────────────────────

bool story_site_active(const Tilemap* map, int i) {
    if (i < 0 || i >= STORY_BOSS_COUNT || map->boss_sites[i].x < 0) return false;
    if ((s_flags.beaten >> i) & 1u) return false;
    StoryStage st = story_stage();
    if (i < STORY_TIER1)               return true;
    if (i < STORY_TIER1 + STORY_TIER2) return st >= STORY_TURN;
    if (i == STORY_ANAYE)              return st == STORY_DESCENT;
    return false;
}

// The boss's idle sheet, frame 0, as its stand-in on the map: loaded once
// each, sized from the sheet's layout. w, h are art pixels, drawn at the
// camera's zoom. Nothing drawn yet = a red box.
struct SiteArt { SDL_Texture* tex; int w, h; bool tried; };
static SiteArt s_art[STORY_BOSS_COUNT];
static const SiteArt& site_art(SDL_Renderer* ren, int i) {
    SiteArt& a = s_art[i];
    if (!a.tried && ren) {
        a.tried = true;
        int frames = 1; bool rows = false;
        if (const char* path = enemy_sheet_info(STORY_BOSSES[i], &frames, &rows)) {
            a.tex = IMG_LoadTexture(ren, path);
            if (a.tex) {
                int tw = 0, th = 0;
                SDL_QueryTexture(a.tex, nullptr, nullptr, &tw, &th);
                a.w = tw / (frames > 0 ? frames : 1);
                a.h = rows ? th / 8 : th;
            }
        }
    }
    return a;
}
// A site's ground point: the tile's bottom middle, in world pixels.
static void site_foot(const Tilemap* map, int i, float* fx, float* fy) {
    *fx = (map->boss_sites[i].x + 0.5f) * TILE_SIZE;
    *fy = (map->boss_sites[i].y + 1.0f) * TILE_SIZE;
}

int story_site_touch(const Tilemap* map, float pcx, float pcy) {
    for (int i = 0; i < STORY_BOSS_COUNT; i++) {
        if (!story_site_active(map, i)) continue;
        float fx, fy;
        site_foot(map, i, &fx, &fy);
        // Its drawn body, or a tile of it before the sheet is known.
        const SiteArt& a = s_art[i];
        float hw = a.tex ? a.w * 0.5f : 16.0f, hh = a.tex ? a.h * 0.6f : 16.0f;
        float dx = wrap_dpx(pcx - fx), dy = wrap_dpy(pcy - fy);
        if (dx >= -hw - 6.0f && dx <= hw + 6.0f && dy >= -hh && dy <= 20.0f) return i;
    }
    return -1;
}

void story_site_flash_at(const Tilemap* map, int i, float* x, float* y) {
    float fx, fy;
    site_foot(map, i, &fx, &fy);
    const SiteArt& a = s_art[i];
    *x = fx;
    *y = fy - (a.tex ? a.h * 0.5f : 16.0f);
}

void story_sites_draw(SDL_Renderer* ren, const Camera* cam, const Tilemap* map) {
    for (int i = 0; i < STORY_BOSS_COUNT; i++) {
        if (!story_site_active(map, i)) continue;
        float fx, fy;
        site_foot(map, i, &fx, &fy);
        const SiteArt& a = site_art(ren, i);
        float z = cam->zoom;
        // ponytail: drawn at its canonical position only; a site at the seam
        // shows from one side. Wrap it like the tiles if one ever lands there.
        if (a.tex) {
            SDL_Rect src = { 0, 0, a.w, a.h };
            SDL_Rect dst = { cam_px(cam, fx) - (int)(a.w * z * 0.5f), cam_py(cam, fy) - (int)(a.h * z), (int)(a.w * z), (int)(a.h * z) };
            SDL_RenderCopy(ren, a.tex, &src, &dst);
        } else {
            SDL_Rect r = { cam_px(cam, fx) - (int)(16 * z), cam_py(cam, fy) - (int)(32 * z), (int)(32 * z), (int)(32 * z) };
            SDL_SetRenderDrawColor(ren, 200, 30, 30, 255);
            SDL_RenderFillRect(ren, &r);
        }
    }
}

// ── Leads ────────────────────────────────────────────────────────────────────

// The ground each boss's site is laid on (tilemap.cpp, the boss-site stage),
// as the leads say it. Story order.
static const char* const SITE_GROUND[STORY_BOSS_COUNT] = {
    "in the grass", "in the sand", "on the sea", "in the sand", "in the snow", "on the shore", "in the woods", "at the hole", "in the deep" };
static const char* const DIR8[8] = { "east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east" };

// "north-east, far, <what>." for a tile offset (wrapped already); lower case,
// to sit inside a sentence.
static void dir_text(int dx, int dy, const char* what, char* buf, int n) {
    const float PI8 = 3.14159265f / 8.0f;
    int oct = (int)floorf((atan2f((float)dy, (float)dx) + PI8) / (2.0f * PI8));
    oct = ((oct % 8) + 8) % 8;
    float d = sqrtf((float)dx * dx + (float)dy * dy);
    const char* how_far = d < 150.0f ? "not far" : d < 400.0f ? "far" : "very far";
    snprintf(buf, n, "%s, %s, %s.", DIR8[oct], how_far, what);
}

void story_lead(const Tilemap* map, int from_tx, int from_ty, int boss, char* buf, int n) {
    int i = story_boss_index(boss);
    if (i < 0 || map->boss_sites[i].x < 0) { snprintf(buf, n, "Where it is, nobody knows."); return; }
    dir_text(wrap_dx(map->boss_sites[i].x - from_tx), wrap_dy(map->boss_sites[i].y - from_ty), SITE_GROUND[i], buf, n);
    buf[0] = (char)toupper((unsigned char)buf[0]);   // a sentence of its own
}

// ── The lighthouse keeper's errand ───────────────────────────────────────────

int story_quest_tree(const Tilemap* map) {
    if (map->towns[1].x < 0) return -1;
    int cx = map->towns[1].x + TOWN_W / 2, cy = map->towns[1].y + TOWN_H / 2, best = -1;
    long best_d2 = 0;
    for (int i = 0; i < map->num_dungeon_entrances; i++) {
        const DungeonEntrance& e = map->dungeon_entrances[i];
        if (e.type != DUNGEON_ENT_LARGE_TREE) continue;
        long dx = wrap_dx(e.x - cx), dy = wrap_dy(e.y - cy), d2 = dx * dx + dy * dy;
        if (best < 0 || d2 < best_d2) { best = i; best_d2 = d2; }
    }
    return best;
}

bool story_boat_spot(const Tilemap* map, int* tx, int* ty) {
    if (map->wharf_tip.x < 0) return false;
    static const int SEA_DX[4] = { -1, 1, 0, 0 }, SEA_DY[4] = { 0, 0, -1, 1 };   // ocean_side: W E N S
    *tx = wrap_x(map->wharf_tip.x + SEA_DX[map->ocean_side & 3]);
    *ty = wrap_y(map->wharf_tip.y + SEA_DY[map->ocean_side & 3]);
    return true;
}
bool story_boat_ready(const Player* player) {
    return (s_flags.quest & STORY_Q_BOAT_WOOD) && player->sail > 0;
}

bool story_quest_pin(const Tilemap* map, unsigned map_seed, unsigned dungeon_seed, const Player* player) {
    if (!(s_flags.quest & STORY_Q_SAIL_TOLD) || player->sail > 0) return false;
    int tree = story_quest_tree(map);
    return tree >= 0 && dungeon_wiring_for(map, map_seed, tree).seed == dungeon_seed;
}

// What the keeper says in the first arc: the errand, step by step. The wood
// is taken and the book given on the talk that brings enough.
static const int KEEPER_WOOD = 250;
static void keeper_line(const StoryWhere& w, char* buf, int n) {
    Player* pl = w.player;
    int tx = MAP_WIDTH / 2, ty = MAP_HEIGHT / 2;   // the keeper's door, for directions
    if (w.door >= 0 && w.door < w.map->num_doors) { tx = w.map->doors[w.door].x; ty = w.map->doors[w.door].y; }
    char where[96] = "in a tree nobody has found.";
    if (int t = story_quest_tree(w.map); t >= 0)
        dir_text(wrap_dx(w.map->dungeon_entrances[t].x - tx), wrap_dy(w.map->dungeon_entrances[t].y - ty), "in the great tree", where, sizeof(where));
    if (!(s_flags.quest & STORY_Q_BOAT_WOOD)) {
        int wood = item_count(pl, ITEM_WOOD);
        if (wood < KEEPER_WOOD) {
            snprintf(buf, n, "The boat will not float as she is. Bring me %d wood and I will make her sound. You have %d.", KEEPER_WOOD, wood);
            return;
        }
        item_slot(pl, ITEM_WOOD) -= KEEPER_WOOD;
        s_flags.quest |= STORY_Q_BOAT_WOOD | STORY_Q_SAIL_TOLD;
        snprintf(buf, n, "That is wood enough. She will float. But she needs a sail. Buy a Sail Book at the book shop. The cloth is a wing: the great bat that roosts %s", where);
    } else if (pl->sail <= 0) {
        snprintf(buf, n, "The sail. The bat roosts %s Its wings, and a Sail Book from the book shop shows the rest.", where);
    } else if (!story_beaten(49)) {
        char sea[96];
        int fx = w.map->wharf_tip.x >= 0 ? w.map->wharf_tip.x : tx, fy = w.map->wharf_tip.x >= 0 ? w.map->wharf_tip.y : ty;
        story_lead(w.map, fx, fy, 49, sea, sizeof(sea));
        snprintf(buf, n, "She is ready at the end of the wharf. Out there something sinks boats. %s Go and see what it is.", sea);
    } else {
        snprintf(buf, n, "You came back. Nobody comes back from that. The sea is yours, boy.");
    }
}

// ── People ───────────────────────────────────────────────────────────────────

// Where a person stands: a room (arg = interior id, tx/ty its tile), or every
// village at once (by the well; one row, one speaker a village).
// SP_DEBUG: as SP_INTERIOR, in test mode only.
enum { SP_INTERIOR, SP_VILLAGE, SP_DEBUG, SP_TOWN };
struct StoryNpc {
    int place, arg;
    int town;             // the town whose door the player must have come in by, -1 any
    int tx, ty;
    int lead;             // the boss this one points at, -1 none
    const char* name;     // for the debug dialogue list
    // What it says: 0 the lead (the direction is appended), 1 the lead once
    // its boss is beaten, 2 after the turn, 3 the descent and after, 4 after
    // the swarm (amnesia).
    const char* lines[5];
    int skin = -1;              // story_npc_sprite
    const Shop* shop = nullptr; // a shopkeeper's stock (story_npc_shop)
    float px = -1, py = -1;     // in a room: the sprite's top left in pixels, in place of the tile
    int pace_ms = 0;            // walks on the spot, a beat this long; 0 stands
};
// Town 0's book shop: the books the boy starts out needing.
static const Item TOWN0_BOOK_STOCK[] = { ITEM_RAFT_BOOK, ITEM_KNIFE_BOOK, ITEM_BAND_AID_BOOK };
static const Shop TOWN0_BOOKS = {
    "Every craft starts with a book. Read one and your hands will know the rest.",
    TOWN0_BOOK_STOCK, 3 };
static const StoryNpc NPCS[] = {
    // The debug speaker, in the spawn house: a line long enough to page, for
    // working on the speech box
    { SP_DEBUG, 0, -1, 14, 8, -1, "DEBUG", {
        "Debug NPC. This is a test line for the speech box. It runs long on purpose, so that it wraps across several lines and scrolls. Commas breathe, full stops breathe longer... and so do these! Really? THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG. The quick brown fox jumps over the lazy dog. 0123456789 .,!?'-",
        "", "", "", "" } },
    // The town hall keeper, coastal town, until the hall has a room of its own
    { SP_INTERIOR, 3, 1, 12, 8, 6, "HALL KEEPER", {
        "Something has been tearing up the farms at night. Nobody here will go near it. Go and see what it is.",
        "You went out there? The farms have been quiet since. I did not think anyone would.",
        "You killed it. Why would you do that. It was meant to be there. Everything is.",
        "What comes is meant to come. It is written. Go home, boy.",
        "Do I know you? The farms? The farms are fine. They have always been fine." } },
    // The lighthouse keeper, coastal town, room 4 until the lighthouse has one:
    // the errand (keeper_line) in the first arc, these after
    { SP_INTERIOR, 4, 1, 12, 8, 49, "LIGHTHOUSE", {
        "",
        "",
        "You took my boat out and killed it. It was meant to sink us. Everything is meant.",
        "The light is out. What comes is meant to come. It is written. Go home, boy.",
        "A boat? I never had a boat. Who are you?" } },
    // The villager by the well, in every village: the first one asked gives the lead
    { SP_VILLAGE, 0, -1, 0, 0, 23, "VILLAGER", {
        "Something went under the sand last spring and the goats went with it. Nobody digs there now. Go and see what it is.",
        "The sand is still again. The goats are not coming back, but thank you.",
        "You dug it up and killed it. It was meant to be there. The goats were meant to go.",
        "What comes is meant to come. It is written. There is nothing for you here.",
        "Goats? We never kept goats. Who are you?" } },
    { SP_TOWN, 1, 0, 80, 74, -1, "FARMER", {
        "I like watching everyone pass through town.",
        "", "It has been awfully quiet today.", "Are you going out again?", "Hello! Are you new here?" }, 1 },
    { SP_TOWN, 2, 0, 87, 74, -1, "GLASSES", {
        "There is always something new to notice around here.",
        "", "Something about this place has changed.", "Look after yourself.", "I do not think we have met." }, 2 },
    // The book shop's owner (the elder), town 0, just behind his
    // counter, pacing on the spot slowly: talked to across it, he offers
    // SHOP / TALK / LEAVE.
    { SP_INTERIOR, 1, 0, 9, 7, -1, "BOOK SHOP", {
        "Welcome to the book shop! What can I do for you?",
        "", "Books. What is written is written. Buy, if you must.", "Still here? Buy something or go.",
        "Have we met? Welcome!" }, 0, &TOWN0_BOOKS, 293, 237, 400 },
};
static const int NPC_COUNT = (int)(sizeof(NPCS) / sizeof(NPCS[0]));

int story_npc_sprite(const StoryNpcPos& p) {
    return p.idx >= 0 && p.idx < NPC_COUNT ? NPCS[p.idx].skin : -1;
}

const Shop* story_npc_shop(const StoryNpcPos& p) {
    return p.idx >= 0 && p.idx < NPC_COUNT ? NPCS[p.idx].shop : nullptr;
}
static const StoryNpcConversation CLERK_CONVERSATION = {
    "Just restocking shelfs, need anything?",
    {"Why do I need books?", "Where am I?", "No"}
};
static const StoryNpcConversation GRANDMA_CONVERSATION = {
    "Good day deer, what do you need?",{"What's there to do in town?","Where am I?","No"}
};
const StoryNpcConversation* story_npc_conversation(const StoryNpcPos& p) {
    if(p.idx==SAILOR_FISHER_ID) {
        if(sailor_fisher_view().phase==SF_SLEEP||!sailor_fisher_line())return nullptr;
        static StoryNpcConversation sailor;
        sailor={sailor_fisher_line(),{"What's there to do in town?","Where am I?","No"}};
        return &sailor;
    }
    if(p.idx==GRANDMOTHER_ID)return &GRANDMA_CONVERSATION;
    return p.idx==BOOKSHOP_CLERK_ID ? &CLERK_CONVERSATION : nullptr;
}
const char* story_npc_answer(const StoryNpcPos& p,const StoryWhere& w,int choice) {
    if(!story_npc_conversation(p))return nullptr;
    if(choice==0) {
        if(p.idx==SAILOR_FISHER_ID)return "I usually spend a little time fishing by the river, then head home for a rest. But if you're looking for a little adventure, there's a small cave south of town and a graveyard to the northwest.";
        if(p.idx==GRANDMOTHER_ID)return "I usually pick out a good book from the library and go back home and read. But for a young one like yourself, there's a small cave south of town and a graveyard to the northwest, if you're looking for a little adventure.";
        return "Without these books you wouldn't be able to build anything or go anywhere. What's the point of these books is like asking what's the purpose of life.";
    }
    if(choice==1)return story_where_am_i(p,w);
    return nullptr;
}
void story_npc_resume(const StoryNpcPos& p) {
    if(p.idx==BOOKSHOP_CLERK_ID)bookshop_clerk_resume();
    if(p.idx==GRANDMOTHER_ID)grandmother_resume();
}
// Not while fading through a door.
bool story_npc_can_talk(const StoryNpcPos& p) {
    if(p.idx==SAILOR_FISHER_ID)return sailor_fisher_line()!=nullptr;
    if(p.idx==FISHER_ID)return fisher_line()!=nullptr;
    if(p.idx==GRANDMOTHER_ID)return grandmother_save().flash==0;
    if(p.idx==WOODCUTTER_ID)return woodcutter_save().flash==0;
    if(p.idx==MOTHER_ID)return mother_save().flash==0;
    return true;
}

void story_npc_talk_point(const StoryNpcPos& p, float* x, float* y) {
    *x = p.x + 14.0f;
    *y = p.y + 40.0f + (story_npc_shop(p) ? (float)IMAP_TILE : 0.0f);
}

static SDL_Texture* resident_art[3];

void story_people_free() {
    resident_art_free();
    for (SDL_Texture*& texture : resident_art) {
        SDL_DestroyTexture(texture);
        texture = nullptr;
    }
}

bool story_people_init(SDL_Renderer* renderer) {
    story_people_free();
    if (!resident_art_init(renderer)) return false;
    static const char* const paths[] = {
        "assets/npcs/elder.png", "assets/npcs/farmer.png", "assets/npcs/glasses.png"
    };
    for (int i = 0; i < 3; i++) {
        resident_art[i] = IMG_LoadTexture(renderer, paths[i]);
        if (!resident_art[i]) {
            fprintf(stderr, "Failed to load %s: %s\n", paths[i], IMG_GetError());
            story_people_free();
            return false;
        }
        SDL_SetTextureScaleMode(resident_art[i], SDL_ScaleModeNearest);
    }
    return true;
}

bool story_npc_draw(const StoryNpcPos& p, SDL_Renderer* renderer, const Camera* cam) {
    if (resident_draw(p, renderer, cam)) return true;
    int skin = story_npc_sprite(p);
    if (skin < 0 || !resident_art[skin]) return false;
    // Column 0 is standing; one who paces steps through the walk on the
    // world clock, so it stops when the world does.
    int facing = story_npc_facing(p), pace = p.idx >= 0 && p.idx < NPC_COUNT ? NPCS[p.idx].pace_ms : 0;
    int col = pace ? npc_walk_col(facing, (int)(world_ms() / (Uint32)pace)) : 0;
    SDL_Rect src = { col * 14, npc_sheet_row(facing) * 20, 14, 20 };
    SDL_Rect dst = { cam_screen_x(cam, p.x), cam_screen_y(cam, p.y),
                     (int)(28 * cam->zoom), (int)(40 * cam->zoom) };
    SDL_RenderCopy(renderer, resident_art[skin], &src, &dst);
    return true;
}

static int npc_facing[NPC_COUNT];   // 0 = FACE_DOWN, until spoken to

void story_npc_face(const StoryNpcPos& p, float dx, float dy) {
    int f = fabsf(dx) > fabsf(dy) ? (dx < 0 ? FACE_LEFT : FACE_RIGHT) : (dy < 0 ? FACE_UP : FACE_DOWN);
    if (p.idx == RESIDENT_STORY_ID) resident_face(f);
    else if (p.idx == BOOKSHOP_CLERK_ID) bookshop_clerk_face(f);
    else if (p.idx == GRANDMOTHER_ID) grandmother_face(f);
    else if (p.idx == WOODCUTTER_ID) woodcutter_face(f);
    else if (p.idx == MOTHER_ID) mother_face(f);
    else if (p.idx >= 0 && p.idx < NPC_COUNT) npc_facing[p.idx] = f;
}

// Nothing open: shopkeepers face forward again (they turn to the player
// only while being spoken to); the rest keep facing where they turned.
void story_npcs_idle() {
    for (int i = 0; i < NPC_COUNT; i++) if (NPCS[i].shop) npc_facing[i] = FACE_DOWN;
}

int story_npc_facing(const StoryNpcPos& p) {
    if(p.idx==SAILOR_FISHER_ID)return sailor_fisher_view().facing;
    if(p.idx==FISHER_ID)return fisher_view().facing;
    if(p.idx==BOOKSHOP_CLERK_ID)return bookshop_clerk_facing();
    if(p.idx==GRANDMOTHER_ID)return grandmother_facing();
    if(p.idx==WOODCUTTER_ID)return woodcutter_facing();
    if(p.idx==MOTHER_ID)return mother_facing();
    return p.idx >= 0 && p.idx < NPC_COUNT ? npc_facing[p.idx] : FACE_DOWN;
}

// Is door d (map->doors) inside town t's footprint.
static bool door_in_town(const Tilemap* map, int d, int t) {
    if (!map || d < 0 || d >= map->num_doors || t < 0 || t > 2 || map->towns[t].x < 0) return false;
    if (t == 1 && d == map->lighthouse_door) return true;   // on the wharf, outside the footprint
    const InteriorDoor& dr = map->doors[d];
    const TownPlacement& tp = map->towns[t];
    return dr.x >= tp.x && dr.x < tp.x + TOWN_W && dr.y >= tp.y && dr.y < tp.y + TOWN_H;
}

const char* story_world_name(){return "Vaalbara";}
const char* story_town_name(int town) {
    static const char* names[]={"Bloom",nullptr,nullptr};
    return town>=0&&town<3?names[town]:nullptr;
}
const char* story_where_am_i(const StoryNpcPos& p,const StoryWhere& w) {
    int town=-1;
    if(w.map)for(int i=0;i<3;i++) {
        if(w.state==STATE_INTERIOR) {
            if(door_in_town(w.map,w.door,i)){town=i;break;}
        } else if(w.state==STATE_OVERWORLD && w.map->towns[i].x>=0) {
            // NPC origins are world pixels outdoors. Normalize wrap at the map edge.
            int tx=((int)floorf((p.x+14)/TILE_SIZE)%MAP_WIDTH+MAP_WIDTH)%MAP_WIDTH;
            int ty=((int)floorf((p.y+40)/TILE_SIZE)%MAP_HEIGHT+MAP_HEIGHT)%MAP_HEIGHT;
            const auto& t=w.map->towns[i];
            if(tx>=t.x&&tx<t.x+TOWN_W&&ty>=t.y&&ty<t.y+TOWN_H){town=i;break;}
        }
    }
    static char line[256];
    const char* name=story_town_name(town);
    if(name)snprintf(line,sizeof(line),town==0 ?
        "You're in the town of %s, right in the heart of our world we call %s." :
        "You're in the town of %s, in our world, %s.",name,story_world_name());
    else snprintf(line,sizeof(line),"You're in our world, %s.",story_world_name());
    return line;
}

void story_village_npc_tile(const Tilemap* map, int village, int* tx, int* ty) {
    // the street's upper row (tilemap.cpp stamp_village: ly = ty + 18), a
    // tile right of the well's two columns (tx + 14, 15)
    *tx = map->villages[village].x + 16;
    *ty = map->villages[village].y + 18;
}

int story_npcs_here(const StoryWhere& w, StoryNpcPos out[], int max) {
    int n = 0;
    if (max > 0 && resident_here(w, &out[n])) ++n;
    if (n < max && sailor_fisher_here(w, &out[n])) ++n;
    if (n < max && fisher_here(w, &out[n])) ++n;
    if (n < max && bookshop_clerk_here(w, &out[n])) ++n;
    if (n < max && grandmother_here(w, &out[n])) ++n;
    if (n < max && woodcutter_here(w, &out[n])) ++n;
    if (n < max && mother_here(w, &out[n])) ++n;
    for (int i = 0; i < NPC_COUNT && n < max; i++) {
        const StoryNpc& p = NPCS[i];
        if (p.place == SP_INTERIOR || p.place == SP_DEBUG) {
            if (p.place == SP_DEBUG && !w.debug) continue;
            if (w.state != STATE_INTERIOR || w.room != p.arg) continue;
            if (p.town >= 0 && !door_in_town(w.map, w.door, p.town)) continue;
            // a player-sized frame (28x40) standing on the tile: feet on its bottom
            if (p.px >= 0) out[n++] = { i, p.px, p.py, -1 };
            else out[n++] = { i, p.tx * (float)IMAP_TILE + 2.0f, (p.ty + 1) * (float)IMAP_TILE - 40.0f, -1 };
        } else if (p.place == SP_TOWN) {
            if (w.state != STATE_OVERWORLD || w.map->towns[p.town].x < 0) continue;
            const TownPlacement& town = w.map->towns[p.town];
            int tx = town.x + p.tx, ty = town.y + p.ty;
            out[n++] = { i, tx * (float)TILE_SIZE + 2.0f, (ty + 1) * (float)TILE_SIZE - 40.0f, -1 };
        } else if (p.place == SP_VILLAGE) {
            if (w.state != STATE_OVERWORLD) continue;
            for (int v = 0; v < w.map->num_villages && n < max; v++) {
                int tx, ty;
                story_village_npc_tile(w.map, v, &tx, &ty);
                out[n++] = { i, tx * (float)TILE_SIZE + 2.0f, (ty + 1) * (float)TILE_SIZE - 40.0f, v };
            }
        }
    }
    for (int i = 0; i < n; i++) { out[i].x = art_snap(out[i].x); out[i].y = art_snap(out[i].y); }   // on the tiles' art grid
    return n;
}

// ── The hole ─────────────────────────────────────────────────────────────────

bool story_hole_tile(int tx, int ty) { return tx == DNG_FIXED_CAVE_X && ty == DNG_FIXED_CAVE_Y; }

bool story_hole_blocked() {
    StoryStage st = story_stage();
    return st == STORY_TURN || st == STORY_DESCENT;
}

void story_hole_apply(Tilemap* map) {
    if (story_stage() < STORY_TURN) return;
    for (int dy = -STORY_HOLE_R; dy <= STORY_HOLE_R; dy++)
        for (int dx = -STORY_HOLE_R; dx <= STORY_HOLE_R; dx++) {
            if (dx * dx + dy * dy > STORY_HOLE_R * STORY_HOLE_R || (dx == 0 && dy == 0)) continue;
            int x = DNG_FIXED_CAVE_X + dx, y = DNG_FIXED_CAVE_Y + dy;
            if (!in_world(&x, &y)) continue;
            int t = map->tiles[y][x];
            // ground only: the sea, ponds, cliffs and what is built stay
            if (t != TILE_GRASS && t != TILE_MEADOW && t != TILE_SAND && t != TILE_SNOW && t != TILE_PATH) continue;
            map->tiles[y][x]   = TILE_WASTELAND;
            map->overlay[y][x] = 0;
        }
}

// The hole's art, art/structures/hole/hole_design.py: sheet resolution,
// drawn at 2x like the tileset. The ring is 3x3 tiles with the mouth its
// middle cell, so drawn over the mouth it covers the ladder hole; the portal
// is its frames side by side; the page its two, flat and turning.
enum { HOLE_RING = 48, HOLE_PORTAL_W = 128, HOLE_PORTAL_H = 32, HOLE_PORTAL_FRAMES = 4,
       HOLE_PAGE_W = 6, HOLE_PAGE_H = 8, HOLE_PAGES = 40, HOLE_PORTAL_UP = 5 };
static SDL_Texture* hole_tex(SDL_Renderer* ren, int i) {     // loaded once each, as site_art is
    static const char* const PATH[3] = { "art/structures/hole/ring.png", "art/structures/hole/portal.png", "art/structures/hole/page.png" };
    static SDL_Texture* tex[3];
    static bool tried[3];
    if (!tried[i] && ren) { tried[i] = true; tex[i] = IMG_LoadTexture(ren, PATH[i]); }
    return tex[i];
}
// A piece of the art with its top left at a world point, 2x and the zoom.
static void hole_blit(SDL_Renderer* ren, const Camera* cam, SDL_Texture* t, SDL_Rect src, float wx, float wy) {
    float z = cam->zoom;
    SDL_Rect dst = { cam_screen_x(cam, wx), cam_screen_y(cam, wy), (int)(src.w * 2 * z), (int)(src.h * 2 * z) };
    SDL_RenderCopy(ren, t, &src, &dst);
}

void story_hole_draw(SDL_Renderer* ren, const Camera* cam, const Tilemap* map, bool air) {
    (void)map;
    if (story_stage() < STORY_TURN) return;
    float mx = (DNG_FIXED_CAVE_X + 0.5f) * TILE_SIZE, my = (DNG_FIXED_CAVE_Y + 0.5f) * TILE_SIZE;   // the mouth's middle
    if (!air) {
        if (SDL_Texture* t = hole_tex(ren, 0))
            hole_blit(ren, cam, t, { 0, 0, HOLE_RING, HOLE_RING }, mx - HOLE_RING, my - HOLE_RING);
        return;
    }
    if (!story_hole_blocked()) return;
    uint32_t ms = world_ms();
    float px = mx, py = my - HOLE_PORTAL_UP * TILE_SIZE;        // the portal's middle
    if (SDL_Texture* t = hole_tex(ren, 1)) {
        int f = (int)((ms / 120) % HOLE_PORTAL_FRAMES);
        hole_blit(ren, cam, t, { f * HOLE_PORTAL_W, 0, HOLE_PORTAL_W, HOLE_PORTAL_H }, px - HOLE_PORTAL_W, py - HOLE_PORTAL_H);
    }
    if (SDL_Texture* t = hole_tex(ren, 2)) {
        // Each page is a phase of its own drop, from under the portal to the
        // hole, drawn in toward the hole and fluttering on the way; the
        // phases come off the clock, so there is nothing to keep.
        float top = py + HOLE_PORTAL_H - 8.0f, bottom = my - 8.0f;
        for (int i = 0; i < HOLE_PAGES; i++) {
            float speed = 0.8f + 0.45f * ((i * 7) % 5) / 4.0f;              // drops a second
            float ph = fmodf(ms / 1000.0f * speed + i / (float)HOLE_PAGES, 1.0f);
            float x0 = px + ((i * 11) % 21 - 10) * 8.0f;                     // where it leaves the portal
            float x = x0 + (px - x0) * 0.6f * ph + 10.0f * sinf(ph * 9.0f + i);
            float y = top + (bottom - top) * ph;
            int frame = ((int)(ph * 8) + i) & 1;
            hole_blit(ren, cam, t, { frame * HOLE_PAGE_W, 0, HOLE_PAGE_W, HOLE_PAGE_H }, x - HOLE_PAGE_W, y - HOLE_PAGE_H);
        }
    }
}

// ── Notes ────────────────────────────────────────────────────────────────────
// Where a page lies: a room's tile (arg = interior id; town = the town whose
// door the player came in by, -1 any); a world tile off the starter cave's
// mouth (tx, ty the offset; the nearest walkable tile to it); the starter
// cave's floor by its first portal; the sea just east of the starter cave's
// mouth (tx tiles further out). A lead note names a tier-2 boss's direction
// from where it lay.
enum { NP_INTERIOR, NP_OVERWORLD, NP_CAVE, NP_WATER };
struct StoryNote { int place, arg, town, tx, ty; StoryStage min_stage; int min_kills; int lead; bool strike; const char* text; };
static const StoryNote NOTES[] = {
    { NP_CAVE,      0, -1,  2, 0, STORY_ARC1,    0, -1, false, "Scratch that." },
    // the turn: the three they sent, one page each, left where the boy has been
    { NP_INTERIOR,  1, -1,  9, 8, STORY_TURN,    0, 52, false, "We put the one that stares where it will find it." },
    { NP_INTERIOR,  0, -1, 10, 8, STORY_TURN,    0, 44, false, "The hand goes where it walks. It walks everywhere." },
    { NP_OVERWORLD, 0, -1,  3, 0, STORY_TURN,    0, 98, false, "The river snake, then. It goes to the water sooner or later." },
    // the writers to each other, washing up on the sea by the cave as the three fall
    { NP_WATER,     0, -1,  0, 0, STORY_TURN,    0, -1, false, "Where did it come from. It is not in the script. None of us wrote it. Check the earlier drafts." },
    { NP_WATER,     0, -1,  1, 0, STORY_TURN,    1, -1, false, "It killed the first one we sent. Send the others. Send everything at once." },
    { NP_WATER,     0, -1,  2, 0, STORY_TURN,    2, -1, false, "Two down. It does not tire and it does not read. We cannot write it out. It is not in here." },
    { NP_OVERWORLD, 0, -1, -3, 0, STORY_DESCENT, 0, -1, false, "Nothing left to send. One of ours goes down to stand in the door. If it reaches the centre we lose this world." },
    // a page of the script itself, in the hall: the keeper's line, crossed out at the turn, rewritten by the descent
    { NP_INTERIOR,  3,  1, 10, 10, STORY_TURN,   0, -1, true,  "Page 41. The keeper: Something has been tearing up the farms at night. Nobody here will go near it. Go and see what it is." },
    { NP_INTERIOR,  3,  1, 10, 10, STORY_DESCENT, 0, -1, false, "Page 41. The keeper: You killed it. Why would you do that. It was meant to be there. Everything is." },
};
static const int NOTE_COUNT = (int)(sizeof(NOTES) / sizeof(NOTES[0]));
static_assert(NOTE_COUNT <= 32, "StoryFlags::notes has a bit per note");
int story_note_count() { return NOTE_COUNT; }

static bool note_shown(int i) {
    const StoryNote& n = NOTES[i];
    return story_stage() >= n.min_stage && story_tier2_kills() >= n.min_kills && !((s_flags.notes >> i) & 1u);
}

// The nearest walkable tile to (x, y) within r, into x, y; false if none.
static bool nearest_walkable(const Tilemap* map, int* x, int* y, int r) {
    for (int d = 0; d <= r; d++)
        for (int dy = -d; dy <= d; dy++)
            for (int dx = -d; dx <= d; dx++) {
                if (abs(dx) != d && abs(dy) != d) continue;
                int nx = *x + dx, ny = *y + dy;
                if (in_world(&nx, &ny) && tilemap_is_walkable(map, nx, ny)) { *x = nx; *y = ny; return true; }
            }
    return false;
}

bool story_note_world_tile(const Tilemap* map, int idx, int* tx, int* ty) {
    const StoryNote& n = NOTES[idx];
    if (n.place == NP_OVERWORLD) {
        *tx = DNG_FIXED_CAVE_X + n.tx; *ty = DNG_FIXED_CAVE_Y + n.ty;
        return nearest_walkable(map, tx, ty, 4);
    }
    if (n.place == NP_WATER) {
        for (int x = DNG_FIXED_CAVE_X + 1; x < DNG_FIXED_CAVE_X + 80 && x < MAP_WIDTH; x++)
            if (map->tiles[DNG_FIXED_CAVE_Y][x] == TILE_WATER) { *tx = x + n.tx; *ty = DNG_FIXED_CAVE_Y; return *tx < MAP_WIDTH; }
    }
    return false;
}

int story_notes_here(const StoryWhere& w, const DungeonMap* dmap, StoryNotePos out[], int max) {
    int n = 0;
    for (int i = 0; i < NOTE_COUNT && n < max; i++) {
        const StoryNote& p = NOTES[i];
        if (!note_shown(i)) continue;
        if (p.place == NP_INTERIOR) {
            if (w.state != STATE_INTERIOR || w.room != p.arg) continue;
            if (p.town >= 0 && !door_in_town(w.map, w.door, p.town)) continue;
            out[n++] = { i, (p.tx + 0.5f) * IMAP_TILE, (p.ty + 0.5f) * IMAP_TILE, p.strike };
        } else if (p.place == NP_CAVE) {
            if (w.state != STATE_DUNGEON || !dmap || !dmap->starter || dmap->type != DUNGEON_ENT_CAVE || dmap->num_portals < 1) continue;
            int tx = dmap->portals[0].tx + p.tx, ty = dmap->portals[0].ty + p.ty, bx = -1, by = -1;
            for (int d = 0; d <= 4 && bx < 0; d++)   // the nearest floor to the spot
                for (int dy = -d; dy <= d && bx < 0; dy++)
                    for (int dx = -d; dx <= d && bx < 0; dx++) {
                        if (abs(dx) != d && abs(dy) != d) continue;
                        int cx = tx + dx, cy = ty + dy;
                        if (cx >= 0 && cy >= 0 && cx < DMAP_W && cy < DMAP_H && dmap->tiles[cy][cx] == DNG_FLOOR) { bx = cx; by = cy; }
                    }
            if (bx < 0) continue;
            out[n++] = { i, (bx + 0.5f) * DMAP_TILE, (by + 0.5f) * DMAP_TILE, p.strike };
        } else {
            if (w.state != STATE_OVERWORLD) continue;
            int tx, ty;
            if (!story_note_world_tile(w.map, i, &tx, &ty)) continue;
            out[n++] = { i, (tx + 0.5f) * TILE_SIZE, (ty + 0.5f) * TILE_SIZE, p.strike };
        }
    }
    return n;
}

const char* story_note_take(int idx, const StoryWhere& w) {
    static char buf[512];
    const StoryNote& p = NOTES[idx];
    s_flags.notes |= 1u << idx;
    if (p.lead < 0) { snprintf(buf, sizeof(buf), "%s", p.text); return buf; }
    // from where it lay: its own tile, or the door the room was entered by
    int tx = MAP_WIDTH / 2, ty = MAP_HEIGHT / 2;
    if (p.place == NP_INTERIOR) { if (w.door >= 0 && w.door < w.map->num_doors) { tx = w.map->doors[w.door].x; ty = w.map->doors[w.door].y; } }
    else story_note_world_tile(w.map, idx, &tx, &ty);
    char lead[96];
    story_lead(w.map, tx, ty, p.lead, lead, sizeof(lead));
    snprintf(buf, sizeof(buf), "%s %s", p.text, lead);
    return buf;
}

const char* story_npc_line(const StoryNpcPos& pos, const StoryWhere& w) {
    if(pos.idx==SAILOR_FISHER_ID)return sailor_fisher_line();
    if(pos.idx==FISHER_ID)return fisher_line();
    if (pos.idx == RESIDENT_STORY_ID) return resident_line();
    if (pos.idx == WOODCUTTER_ID) return woodcutter_line();
    if (pos.idx == MOTHER_ID) return mother_line();
    if (const auto* conversation=story_npc_conversation(pos))return conversation->prompt;
    static char buf[512];
    const StoryNpc& p = NPCS[pos.idx];
    StoryStage st = story_stage();
    // The first village the boy asks in is the one that sent him; the rest
    // know he has been told, and tell him again anyway, so no one is lost.
    bool told_elsewhere = false;
    if (p.place == SP_VILLAGE) {
        if (s_flags.first_village_plus1 == 0) s_flags.first_village_plus1 = (uint8_t)(pos.village + 1);
        told_elsewhere = s_flags.first_village_plus1 != pos.village + 1;
    }
    if (p.place == SP_DEBUG) return nullptr;   // the dialogue list instead
    if (st == STORY_ARC1 && p.lead == 49) { keeper_line(w, buf, sizeof(buf)); return buf; }
    if (st == STORY_ARC1) {
        if (p.lead >= 0 && !story_beaten(p.lead)) {
            // measured from the door the player came in by, or the villager's
            // own village; from the map's middle otherwise
            int tx = MAP_WIDTH / 2, ty = MAP_HEIGHT / 2;
            if (pos.village >= 0) story_village_npc_tile(w.map, pos.village, &tx, &ty);
            else if (w.door >= 0 && w.door < w.map->num_doors) { tx = w.map->doors[w.door].x; ty = w.map->doors[w.door].y; }
            char lead[96];
            story_lead(w.map, tx, ty, p.lead, lead, sizeof(lead));
            snprintf(buf, sizeof(buf), "%s %s", told_elsewhere ? "They told you already, did they. Well." : p.lines[0], lead);
        } else
            snprintf(buf, sizeof(buf), "%s", p.lines[p.lead >= 0 ? 1 : 0]);
    } else
        snprintf(buf, sizeof(buf), "%s", p.lines[st == STORY_TURN ? 2 : st == STORY_AMNESIA ? 4 : 3]);
    // After the turn the script speaks through them: each recites where one
    // of the writers' ambushes waits -- a tier-2 boss still standing, the
    // speakers sharing them out -- as a thing that is meant to be, from where
    // they stand. Hostile, and still a lead.
    if (st == STORY_TURN) {
        static const char* const EPITHET[STORY_TIER2] = { "the one that stares", "the hand", "the river snake" };   // 52 44 98
        int standing[STORY_TIER2], ns = 0;
        for (int i = 0; i < STORY_TIER2; i++)
            if (story_site_active(w.map, STORY_TIER1 + i)) standing[ns++] = i;
        if (ns > 0) {
            int k = standing[(pos.idx + (pos.village >= 0 ? pos.village : 0)) % ns];
            int tx = MAP_WIDTH / 2, ty = MAP_HEIGHT / 2;
            if (pos.village >= 0) story_village_npc_tile(w.map, pos.village, &tx, &ty);
            else if (w.door >= 0 && w.door < w.map->num_doors) { tx = w.map->doors[w.door].x; ty = w.map->doors[w.door].y; }
            char where[96];
            story_lead(w.map, tx, ty, STORY_BOSSES[STORY_TIER1 + k], where, sizeof(where));
            size_t len = strlen(buf);
            snprintf(buf + len, sizeof(buf) - len, " It is written that %s waits for you. %s", EPITHET[k], where);
        }
    }
    return buf;
}

// ── Debug: the dialogue list ─────────────────────────────────────────────────

// Every line the people and the notes can say, each as the situation that
// brings it on: a person (a = NPCS row) at a stage (b: 0 the lead, 1 the lead
// beaten, 2 the turn, 3 the descent, 4 amnesia), the keeper's errand at step
// b (in place of his stage 0), or note a.
enum { DLG_PERSON, DLG_ERRAND, DLG_NOTE };
struct DlgCase { int kind, a, b; };
static const char* const DLG_STAGE[5]   = { "ARC1", "ARC1 DONE", "TURN", "DESCENT", "AMNESIA" };
static const char* const DLG_STEP[4]    = { "BRING WOOD", "WOOD ENOUGH", "THE SAIL", "BOAT READY" };
enum { DLG_MAX = 64 };
static int dlg_cases(DlgCase out[DLG_MAX]) {
    int n = 0;
    auto add = [&](int k, int a, int b) { if (n < DLG_MAX) out[n++] = { k, a, b }; };
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].place == SP_DEBUG) { add(DLG_PERSON, i, 0); continue; }
        for (int v = 0; v < 5; v++) {
            if (v == 0 && NPCS[i].lead == 49) { for (int s = 0; s < 4; s++) add(DLG_ERRAND, i, s); continue; }
            add(DLG_PERSON, i, v);
        }
    }
    for (int i = 0; i < NOTE_COUNT; i++) add(DLG_NOTE, i, 0);
    return n;
}
static DlgCase s_dlg[DLG_MAX];
static const int s_dlg_n = dlg_cases(s_dlg);

int story_dialogue_count() { return s_dlg_n; }

const char* story_dialogue(int i, const StoryWhere& w, const char** label, bool* strike) {
    static char lbl[48];
    const DlgCase& c = s_dlg[i];
    *label  = lbl;
    *strike = false;
    // the real lines, with the flags and the player forced to the case and
    // put back after: taking the keeper's wood, a villager marking the first
    // village and a note's taken bit all undo
    StoryFlags keep_flags  = s_flags;
    Player     keep_player = *w.player;
    const char* text;
    if (c.kind == DLG_NOTE) {
        snprintf(lbl, sizeof(lbl), "NOTE %d", c.a);
        *strike = NOTES[c.a].strike;
        text = story_note_take(c.a, w);
    } else {
        const StoryNpc& p = NPCS[c.a];
        if (c.kind == DLG_ERRAND) {
            snprintf(lbl, sizeof(lbl), "%s %s", p.name, DLG_STEP[c.b]);
            story_set_stage(STORY_ARC1);
            s_flags.quest = c.b < 2 ? 0 : STORY_Q_BOAT_WOOD | STORY_Q_SAIL_TOLD;
            item_slot(w.player, ITEM_WOOD) = c.b == 1 ? KEEPER_WOOD : 0;
            w.player->sail = c.b == 3;
        } else {
            snprintf(lbl, sizeof(lbl), "%s %s", p.name, p.place == SP_DEBUG ? "PAGING" : DLG_STAGE[c.b]);
            story_set_stage(c.b <= 1 ? STORY_ARC1 : c.b == 2 ? STORY_TURN : c.b == 3 ? STORY_DESCENT : STORY_AMNESIA);
            if (c.b == 1) story_mark_beaten(p.lead);
        }
        StoryNpcPos pos = { c.a, 0.0f, 0.0f, p.place == SP_VILLAGE && w.map->num_villages > 0 ? 0 : -1 };
        text = p.place == SP_DEBUG ? p.lines[0] : story_npc_line(pos, w);
    }
    s_flags     = keep_flags;
    *w.player   = keep_player;
    return text;
}
