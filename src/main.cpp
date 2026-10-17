#include <stdio.h>
#include <stdlib.h>   // strtoul, for the seed argument
#include <string.h>
#include <thread>
#include <unordered_map>
#include <vector>
#include <SDL2/SDL_image.h>

#include "fc_palette.h"
#include "game_state.h"
#include "battle.h"
#include "dungeon.h"
#include "dungeon_kinds.h"
#include "platform.h"
#include "core.h"
#include "input.h"
#include "overworld.h"
#include "interior.h"
#include "collision.h"
#include "camera.h"
#include "tilemap.h"
#include "resource_node.h"
#include "floattext.h"
#include "crafting.h"
#include "game_menu.h"
#include "save.h"
#include "story.h"
#include "resident.h"
#include "towns.h"      // TOWN1_HALL_DOOR_*: the debug warp to the hall


// How many whole pixels of frame there are to a logical pixel: as many as the
// window has room for. One is the floor, so a window smaller than the logical
// screen still gets a frame, just a downscaled one.
static int frame_scale_for(SDL_Renderer* renderer, int lw, int lh) {
    int ow = lw, oh = lh;
    SDL_GetRendererOutputSize(renderer, &ow, &oh);
    int s = ow / lw;
    if (oh / lh < s) s = oh / lh;
    return s < 1 ? 1 : s;
}

// Snap 0..1 to `levels` hard steps (rounding down; 1 stays 1), the way the
// NES fades and moves: a few distinct states, nothing in between.
static float nes_steps(float a, int levels) {
    if (a <= 0.0f) return 0.0f;
    if (a >= 1.0f) return 1.0f;
    return (float)(int)(a * levels) / levels;
}

#include "landmarks.inc"    // LANDMARK_KINDS: the ground each kind of landmark stands on

static const int CHEST_ICON_MAX = 4;

// What a landmark's cache holds, paid when it is struck open: 2 to 4 of the
// ore the caves about it hold -- so the farther out, the better -- 1 to 3 of
// a common drop by its ground, an essence or two, and in one cache in ten an
// oilbloom. Nothing here is found nowhere else. `roll` is the landmark's own:
// the same cache holds the same things whenever it is opened. Writes what
// it paid, for the chest's speech.
static void landmark_pay(Player* p, const LandmarkPlacement& l, unsigned roll,
                         Item* icons, int* counts, int* ni) {
    static const Item COMMON[] = { ITEM_VINE, ITEM_FEATHER, ITEM_BONE, ITEM_HIDE, ITEM_BONE, ITEM_VINE };   // by LandmarkGround
    auto next = [&]() { roll = roll * 1664525u + 1013904223u; return roll >> 16; };
    const Item ore = ore_item(material_for_difficulty(l.difficulty / 255.0f));
    const Item common = COMMON[LANDMARK_KINDS[l.kind].ground];
    const int ores = 2 + (int)(next() % 3), commons = 1 + (int)(next() % 3), essence = 1 + (int)(next() % 2);
    const bool bloom = next() % 10 == 0;
    item_slot(p, ore) += ores;
    item_slot(p, common) += commons;
    item_slot(p, ITEM_ESSENCE) += essence;
    if (bloom) item_slot(p, ITEM_OILBLOOM) += 1;
    *ni = 0;
    icons[(*ni)++] = ore;
    icons[(*ni)++] = common;
    icons[(*ni)++] = ITEM_ESSENCE;
    if (bloom) icons[(*ni)++] = ITEM_OILBLOOM;
    counts[0] = ores;
    counts[1] = commons;
    counts[2] = essence;
    if (bloom) counts[3] = 1;
}

// The door of map->doors the player last walked into, for the way back out.
static int entered_door = -1;

// Each enemy's own way of chasing on the map: its speed as a share of the
// chase pace (CHASER_SPEED, 1.5x the player's walk), t seconds into the chase
// (tools/minis.py chase_speed() draws each one). Walking away from one fails,
// running gets away.
static float chase_speed(int enemy_id, float t) {
    switch (enemy_id) {
        case 2:  return fmodf(t, 0.55f) < 0.3f ? 1.5f : 0.0f;    // Treesqueak darts: a scurry, a freeze
        case 7:  return fmodf(t, 0.9f) < 0.5f ? 1.3f : 0.4f;      // Alber swoops: a glide, then wingbeats
        case 8:  return fmodf(t, 0.6f) < 0.3f ? 1.7f : 0.2f;      // Snawfus bounds: a leap, a landing
        case 9:  return fmodf(t, 1.0f) < 0.5f ? 1.5f : 0.5f;      // the Questing Beast dashes straight at you, then a breath
        case 10: return fmodf(t, 0.6f) < 0.4f ? 1.6f : -0.3f;     // the Grand Goule surges, then draws back
        case 11: return fmodf(t, 0.85f) < 0.5f ? 0.0f : 2.3f;     // the Paoxiao lies in wait, then pounces
        case 12: return 1.2f;                                     // Ebigane jinks (chase_bend)
        case 13: return 1.1f;                                     // the Beast of the Charred Forests prowls (chase_bend)
        case 14: return fmodf(t, 0.55f) < 0.25f ? 2.4f : 0.0f;    // the Lodsilungur flops, then lies there
        case 15: return 1.0f + 0.5f * sinf(t * 6.2831853f / 0.9f);  // the Ofuguggi meanders, its pace rising and falling
        case 16: return fmodf(t, 0.8f) < 0.35f ? 2.0f : 0.6f;     // the Kamaitachi gusts at you, then whirls
        case 17: return 1.1f;                                     // the Qiqirn flees (chase_bend), a little slower than you run
        case 19: return 0.8f;                                     // the Skeljaskrimsli plods, slow and steady
        case 21: return fmodf(t, 0.5f) < 0.2f ? 1.7f : 0.5f;      // the Asp springs off its coils, then gathers
        default: return 1.0f;                                     // straight at the player
    }
}
// Which of its mini's two frames its chase shows, or -1 to step between them
// every 150 ms (tools/minis.py chase_frame()).
static int chase_frame(int enemy_id, float t) {
    switch (enemy_id) {
        case 8:  return fmodf(t, 0.6f) < 0.3f ? 0 : 1;            // Snawfus: stretched out in the leap, gathered landing
        case 11: return fmodf(t, 0.85f) < 0.5f ? 0 : 1;           // the Paoxiao: standing in the wait, in the air in the pounce
        case 14: return fmodf(t, 0.55f) < 0.25f ? 1 : 0;          // the Lodsilungur: in the air in the flop, lying between
        case 21: return fmodf(t, 0.5f) < 0.2f ? 1 : 0;            // the Asp: up in the air in the spring
        default: return -1;
    }
}
// How far its heading turns off the line to the player, radians (tools/minis.py chase_bend()).
static float chase_bend(int enemy_id, float t) {
    switch (enemy_id) {
        case 3:  return 0.9f * sinf(t * 6.2831853f / 0.7f);       // Qique zigzags, a weave every 0.7 s
        case 5:  return 0.6f * sinf(t * 6.2831853f / 0.35f);      // the Cobra wiggles, a quick slither
        case 12: return fmodf(t, 0.5f) < 0.25f ? 0.8f : -0.8f;    // Ebigane jinks, a bat's dart off one side then the other
        case 13: return 0.6f;                                     // the Beast prowls, circling in on you
        case 14: return fmodf(t, 1.1f) < 0.55f ? 0.7f : -0.7f;    // each of the Lodsilungur's flops veers the other way
        case 15: return 0.7f * sinf(t * 6.2831853f / 1.3f);       // the Ofuguggi meanders, curving one way then the other
        case 17: return 3.14159265f;                              // the Qiqirn, terrified of people, runs straight away from you
        case 16: {                                                // the Kamaitachi: a gust straight at you, then one loop round
            float u = fmodf(t, 0.8f);
            return u < 0.35f ? 0.0f : 6.2831853f * (u - 0.35f) / 0.45f;
        }
        default: return 0.0f;
    }
}

int main(int argc, char *argv[])
{
    // Two modes. Play, for players: a title screen, saving, none of the test
    // keys. Test (--debug): straight into the spawn house with the practice
    // enemy, and F1/F2/F3, B, R in battle and click-to-warp on the map.
    bool debug = false;
    const char* seed_arg = nullptr;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--debug") == 0) debug = true;
        else                                 seed_arg = argv[i];
    }
    BattleScene::debug_keys = debug;

    // One logical screen, drawn at one pixel to the pixel and scaled to the
    // window exactly once, at present time.
    static const int LOGICAL_W = 640, LOGICAL_H = 480;

    Platform plat;
    if (!platform_init(&plat, "Four Castle Chronicles", LOGICAL_W, LOGICAL_H)) {
        return 1;
    }

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    SDL_RenderSetLogicalSize(plat.renderer, LOGICAL_W, LOGICAL_H);

    // Everything the game draws goes here first, and this one finished picture
    // goes to the window.
    //
    // Drawing straight at the window sent every tile quad through the
    // logical-size scale -- 2.25 in a 1920x1080 window -- so a tile edge could
    // land on a half pixel. The outermost row of such a quad has its centre
    // exactly on the boundary of the source cell, and nearest rounding takes it
    // one texel into the neighbouring cell: tileset.png is packed sixteen to
    // the cell with no gutter, and what sits above the grass block is the tree
    // row, keyed background with two black pixels along the foot of a trunk.
    // That came out as a one-pixel dark dash along the top of the tile, walking
    // over the ground as the camera moved it in and out of the half-pixel
    // phase.
    //
    // Compositing first makes every quad edge whole, so no sample can reach a
    // cell boundary. That is a property of the frame rather than of any sheet,
    // tile or draw site, so it holds at every zoom and every window size, and
    // nothing downstream has to know about it.
    // The frame is a whole multiple of the logical screen rather than the
    // logical screen itself. At one to one a source texel gets
    // (int)(32*zoom)/16 pixels to live in, which is half a pixel at 0.25x and
    // one and a half at 0.75x: the first throws every other texel away and the
    // second lands them alternately one and two wide, and the window then
    // magnifies whichever it got. Drawing at the largest whole multiple the
    // window has room for gives those zooms their pixels back, and keeps the
    // scale inside the frame a whole number, which is the part that closes the
    // seam.
    SDL_Texture* frame_tex   = NULL;
    int          frame_scale = 0;
    const bool   can_target  = (SDL_RenderTargetSupported(plat.renderer) == SDL_TRUE);
    if (!can_target) printf("No render target: drawing straight at the window, seams and all.\n");

    if (!(IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG)) 
    {
        printf("SDL_image init failed: %s\n", IMG_GetError());
        platform_shutdown(&plat);
        return 1;
    }

    tilemap_init_tile_cache(plat.renderer);

    // The player, on the maps and in battle: 14x20 art pixels a frame
    // (assets/player_small.aseprite), drawn at 2x.
    SDL_Texture* player_sprite = IMG_LoadTexture(plat.renderer, "assets/player_small.png");
    if (!player_sprite) {
        printf("Failed to load sprite: %s\n", IMG_GetError());
        tilemap_free_tile_cache();
        IMG_Quit();
        platform_shutdown(&plat);
        return 1;
    }

    if (!story_people_init(plat.renderer)) {
        SDL_DestroyTexture(player_sprite);
        tilemap_free_tile_cache();
        IMG_Quit();
        platform_shutdown(&plat);
        return 1;
    }

    GameState state = STATE_OVERWORLD;

    // The player a new game starts with.
    Player player = {0};
    auto fresh_player = [&]() {
        player = Player{};
        player.level             = 1;
        player.stats.max_hp      = 60;  player.stats.hp      = 60;
        player.stats.max_spd     = 10;  player.stats.spd     = 10;
        player.stats.max_attack  = 18;  player.stats.attack  = 18;
        player.stats.max_mag     = 12;  player.stats.mag     = 12;
        player.stats.max_luck    = 30;  player.stats.luck    = 30;
        player.stats.max_iq      = 8;   player.stats.iq      = 8;
        // Keep items whose functionality is being tested ready in debug runs.
        if (debug) {
            player.stats.hp = 1; // Start injured for healing-item tests.
            player.poisoned = 1; // Debug-only status for testing poison and Antidotes.
            const Item test_items[] = { ITEM_ESCAPE_CHARM, ITEM_BAND_AID, ITEM_MEDKIT, ITEM_ANTIDOTE, ITEM_SWIFT_BOOTS, ITEM_DIVING_FINS };
            for (Item it : test_items) {
                item_slot(&player, it) = (it==ITEM_BAND_AID||it==ITEM_MEDKIT||it==ITEM_ANTIDOTE)?5:1;
                item_mark_found(&player, it);
            }
            item_equip_swift_boots(&player, true);
        }
    };
    fresh_player();

    BattleScene* battle_scene = nullptr;
    // The oasis's air: 1 full, 0 gone. It runs out over 16 s under water and
    // fills again at a surface; once gone, the swimmer drowns a bar of HP
    // every 2 s, never below 1 HP. A fight stops the clock (user).
    float oxygen = 1.0f, oxy_hurt_t = 0.0f;
    float drown_t = 9.0f;      // seconds since drowning last hurt: the fight's shake and red flash
    GameState    state_after_battle = STATE_OVERWORLD;
    int          battle_queue[3]             = {};
    int          battle_queue_chaser_idx[3] = { -1, -1, -1 };
    int          battle_queue_count = 0;
    int          battle_queue_idx   = 0;
    struct FlashEntry { float x, y; int id = -1, face = 0; };   // id, face: the chaser's mini, -1 for none
    FlashEntry   flash_entries[3]   = {};
    int          flash_count        = 0;
    float        pre_battle_timer   = -1.0f;  // -1 = inactive
    float        post_battle_t      = 0.0f;   // back on the map: fade-in, chasers hold
    // A door, stair or entrance taken: the screen fades to black as a battle
    // does, the room changes while it is black, and it fades back up.
    float        room_t             = -1.0f;  // seconds into that; -1 = inactive
    bool         room_swap          = false;  // the one frame it has gone black: change rooms now
    // Walking onto a door takes it, so the one you arrive on must not take you
    // straight back: it is live only once the player has stood off every door.
    bool         room_armed         = false;

    // The stair sound. ponytail: one device playing one clip; a mixer when a
    // second sound has to play over it.
    SDL_AudioSpec     stairs_spec;
    Uint8*            stairs_buf = nullptr;
    Uint32            stairs_len = 0;
    SDL_AudioDeviceID stairs_dev = 0;
    if (SDL_InitSubSystem(SDL_INIT_AUDIO) == 0 &&
        SDL_LoadWAV("assets/sound/40011_in.wav", &stairs_spec, &stairs_buf, &stairs_len)) {
        stairs_dev = SDL_OpenAudioDevice(NULL, 0, &stairs_spec, NULL, 0);
        SDL_PauseAudioDevice(stairs_dev, 0);
    } else {
        printf("No stair sound: %s\n", SDL_GetError());
    }
    // Test enemies in the spawn house: the enemy being tuned (swap in each new
    // one as its patterns are done; more entries fight as a pack). Armed
    // again once the player steps off them.
    // How near the middle of the player's frame comes to an actor to touch it.
    const float  ACTOR_TOUCH        = 22.0f;
    struct TestEnemy { int id; float x, y; };
    // The practice dummies stand on the starting house's floor (interior 0,
    // whose walkable floor starts at row 7), across the room from where the
    // player wakes, so they can be walked into but are not touched at once.
    TestEnemy    test_enemies[]     = {
        { 23, 10.0f * IMAP_TILE, 8.5f * IMAP_TILE },  // 23 Olgoi-Khorkhoi
    };
    const int    TEST_N             = debug ? (int)(sizeof(test_enemies) / sizeof(test_enemies[0])) : 0;   // none in play
    bool         debug_chest_opened = false;
    const int    DEBUG_CHEST_X = 12 * IMAP_TILE, DEBUG_CHEST_Y = 10 * IMAP_TILE;
    bool         test_armed         = true;
    bool         site_armed         = true;   // a boss site on the map: once per approach, as the dummies
    bool         boat_armed         = false;  // docking: only once the boy has sailed clear of the tip

    // Floating +N resource text — one active at a time above the last hit node.
    // Shared by the overworld and every dungeon (include/floattext.h).
    FloatText cur_float;

    Overworld ow;

    Tilemap* map = new Tilemap();
    // Print the seed, and take one on the command line. Worlds were seeded from
    // the clock and never recorded, so a world you noticed something wrong in
    // was gone the moment you closed the game and there was no way to get back
    // to it. Pass the number back in to regenerate that exact world.
    // In play the world is the save's, when there is one, so CONTINUE has
    // nothing to build; a seed on the command line is for testing.
    unsigned int map_seed = (unsigned int)SDL_GetTicks();
    Player saved_player = {0};
    float  saved_x = 0.0f, saved_y = 0.0f;
    bool   has_save = false;
    // Where the player has been, for their map (play mode); saved.
    static uint8_t explored[EXPLORE_H][EXPLORE_W] = {};
    // The open map's zoom, as pixels a tile: the game's own three steps,
    // 0.75x / 1x / 1.5x of 4 (128, 96 and 64 tiles across).
    static const int MAP_PX[] = { 3, 4, 6 };
    int map_zoom = 1;
    if (debug) {
        if (seed_arg) map_seed = (unsigned int)strtoul(seed_arg, nullptr, 10);
    } else {
        unsigned int s;
        has_save = save_read(&s, &saved_x, &saved_y, &saved_player, explored);
        if (has_save) map_seed = s;
    }
    printf("World seed: %u   (re-run with: game.exe %u)\n", map_seed, map_seed);
    fflush(stdout);
    tilemap_build_overworld_phase1(map, map_seed);

    // Spawn directly in front of the spawn house's front door. Phase 1 only
    // stamps town 0, and the stamp scans top-to-bottom, so the first
    // interior-0 door registered is the spawn house -- and stays the first
    // while the phase-2 thread appends doors from the other towns.
    auto place_at_start = [&]() {
        float start_x = 47916.0f;
        float start_y = 46528.0f;   // fallback if the door lookup fails
        for (int i = 0; i < map->num_doors; i++) {
            const InteriorDoor& d = map->doors[i];
            if (d.interior_id != 0) continue;
            // Feet centred under the door, one tile row below it; the -8 mirrors
            // the door-detection bias in overworld_update.
            start_x = (d.x + d.w * 0.5f) * TILE_SIZE - 8.0f - (HB_X1 + HB_X2) * 0.5f;
            start_y = (d.y + 1) * TILE_SIZE + TILE_SIZE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
            break;
        }
        overworld_init(&ow, &player, start_x, start_y);
    };
    place_at_start();

    std::thread gen_thread(tilemap_build_overworld_phase2, map, map_seed);

    //initializes resources
    ResourceNodeList resources;
    resource_nodes_init(&resources);

    resource_nodes_add(&resources, RESOURCE_FLOWER, 320, 224);
    bool oilbloom_done[OILBLOOM_SITES] = {};   // which of the world's sites are placed


    Input in = {0};

    // Zoom levels where TILE_SIZE(32) * zoom is always a whole number of pixels
    static const float zoom_levels[] = { 0.25f, 0.5f, 0.75f, 1.0f, 1.5f, 2.0f, 3.0f };
    static const int   zoom_count    = (int)(sizeof(zoom_levels) / sizeof(zoom_levels[0]));
    int zoom_idx = 3; // default: 1.0x
    // The game itself has three steps, 0.75x to 1.5x; the rest are for testing.
    const int zoom_min = debug ? 0 : 2, zoom_max = debug ? zoom_count - 1 : 4;

    Camera cam = {0};
    cam.screen_w = LOGICAL_W;
    cam.screen_h = LOGICAL_H;
    cam.zoom = zoom_levels[zoom_idx];

    bool running = true;

    // ── Debug menu ───────────────────────────────────────────────────────────
    static const char* DBG_TYPE_NAMES[] = {
        "CAVE", "RUINS", "GRAVEYARD", "GRAVEYARD LG",
        "OASIS", "PYRAMID", "STONEHENGE", "LARGE TREE", "CATACOMBS"
    };
    static const int DBG_TYPE_COUNT = DUNGEON_ENT_COUNT;

    // The warp list is "any cave" and then every kind of dungeon, commonest
    // first, straight from DUNGEON_KINDS (include/dungeon_kinds.h) -- the one
    // table the spawn rates come from, so the menu reads in the order the
    // world is populated in. A cave is one type but seven entries there: which
    // of MATERIALS (src/dungeon.cpp) a cave holds is picked from its
    // DungeonEntrance difficulty, and that material is the whole of the
    // difference, so it is what the menu has to name to warp you to a
    // particular kind of cave.
    //
    // Index layout: 0 = any cave, 1.. = DUNGEON_KINDS[index - 1].
    static const int DBG_TARGET_COUNT = 1 + DUNGEON_KIND_COUNT;
    auto dbg_target_type = [&](int i) -> DungeonEntranceType {
        return i == 0 ? DUNGEON_ENT_CAVE : DUNGEON_KINDS[i - 1].type;
    };
    // Which material this target insists on, or -1 for "whatever it holds".
    auto dbg_target_ore = [&](int i) {
        return i == 0 ? -1 : DUNGEON_KINDS[i - 1].material;
    };
    // Does this overworld entrance answer to the selected target?
    auto dbg_target_matches = [&](int i, const DungeonEntrance* e) {
        if (e->type != dbg_target_type(i)) return false;
        int ore = dbg_target_ore(i);
        return ore < 0 || (int)material_for_difficulty(e->difficulty) == ore;
    };
    // "CAVE", "CAVE: DRAVIUM", "RUINS", ... Material names come from
    // dungeon.cpp's table and are upper-cased here, because core.cpp's bitmap
    // font only carries ASCII 32-90 and draws lowercase as blanks.
    auto dbg_target_name = [&](int i, char* out, size_t n) {
        int ore = dbg_target_ore(i);
        if (ore < 0) {
            SDL_snprintf(out, n, "%s", DBG_TYPE_NAMES[dbg_target_type(i)]);
            return;
        }
        SDL_snprintf(out, n, "CAVE: %s", material_name((Material)ore));
        for (char* c = out; *c; c++)
            if (*c >= 'a' && *c <= 'z') *c = (char)(*c - 'a' + 'A');
    };
    // Every separate place the target could warp you to, as indices into
    // dungeon_entrances[], in array order. Every mouth of one mountain opens
    // the same cave and they all share its anchor, so a system contributes its
    // first mouth and no more -- otherwise a four-mouthed mountain is three
    // wasted steps of the tour and reads as four caves in the count.
    //
    // The row's count and the tour both walk this one list, so "12 FOUND" and
    // twelve presses of ENTER land on twelve different caves by construction.
    auto dbg_target_list = [&](int i, int* out, int max_out) {
        int n = 0;
        for (int a = 0; a < map->num_dungeon_entrances && n < max_out; a++) {
            const DungeonEntrance* e = &map->dungeon_entrances[a];
            if (!dbg_target_matches(i, e)) continue;
            bool listed = false;
            if (e->cave_anchor_x >= 0)
                for (int b = 0; b < a && !listed; b++)
                    listed = map->dungeon_entrances[b].cave_anchor_x == e->cave_anchor_x &&
                             map->dungeon_entrances[b].cave_anchor_y == e->cave_anchor_y;
            if (!listed) out[n++] = a;
        }
        return n;
    };
    // Scratch for the above, sized to the entrance array so no target can
    // overflow it. static rather than a local: 8KB is more than a stack frame
    // wants, and it is rebuilt from scratch on every call anyway.
    static int dbg_list[MAX_DUNGEON_ENTRANCES];
    // Where the tour has got to: index into dbg_list of the one you were last
    // put outside, or -1 before the first press.
    int  dbg_tour     = -1;

    bool dbg_open     = false;
    float ow_swap_t   = 99.0f;   // seconds since Q / E swapped weapons outside battle, for the weapon box
    bool dbg_readout  = false;   // F1: FPS, current-area coordinates and game time
    // 0=target, 1=enter, 2=regen, 3=noclip, 4=show all, 5=weapon, 6=grid, 7=seam
    static const int DBG_ROW_COUNT = 13;
    // The rows in two columns: the world (0-4, 6, 7) on the left, the player
    // (5, 8-10) on the right. dbg_sel is a row's id; UP/DOWN step through this
    // order, down the left column and on into the right.
    static const int DBG_ORDER[DBG_ROW_COUNT] = { 0, 1, 2, 3, 4, 6, 7,   5, 8, 9, 10, 11, 12 };
    static const int DBG_PLAYER_AT = 7;   // where the player column starts in DBG_ORDER
    auto dbg_pos = [&](int id) { int i = 0; while (DBG_ORDER[i] != id) i++; return i; };
    int  dbg_sel      = 0;
    int  dbg_target   = 0;
    int  dbg_story_go = 0;   // row 12: the story's places to warp to -- its boss sites, then the hall
    bool dbg_noclip   = false;
    bool dbg_show_all = false;
    bool dbg_grid     = false;
    GameMenu menu;            // the TAB menu: crafting and items
    // The speech box (draw_speech): what a person or a note says, typing out
    // part by part (dlg_part: the presses at its stops so far; dlg_t: seconds
    // into this part). While it is up the world sees no input, as with the
    // TAB menu; dlg_state is the box's own, set as it draws.
    const char* dlg_text   = nullptr;
    int         dlg_part   = 0;
    float       dlg_t      = 0.0f;
    SpeechState dlg_state  = SPEECH_TYPING;
    bool        dlg_strike = false;
    Item        dlg_icons[CHEST_ICON_MAX] = {};   // a chest's: the icon on speech line i + 1
    int         dlg_icon_n = 0;
    // Choices under a line (ask): once it has typed out, up/down pick one and
    // Z takes it -- dlg_pick(i) after the box closes; X is the last (LEAVE).
    const char* dlg_choices[4] = {};
    int         dlg_choice_n = 0, dlg_choice = 0;
    std::function<void(int)> dlg_pick;
    std::function<void()> dlg_after;
    auto say = [&](const char* text, bool strike = false) {
        dlg_text = text; dlg_part = 0; dlg_t = 0.0f; dlg_state = SPEECH_TYPING; dlg_strike = strike;
        dlg_icon_n = 0;   // chests set dlg_icons after say
        dlg_choice_n = 0;
        dlg_after = nullptr;
    };
    auto ask = [&](const char* text, std::initializer_list<const char*> choices, std::function<void(int)> pick) {
        say(text);
        for (const char* c : choices) if (dlg_choice_n < 4) dlg_choices[dlg_choice_n++] = c;
        dlg_choice = 0;
        dlg_pick = pick;
    };
    bool topic_active=false;
    StoryNpcPos topic_npc={};
    StoryWhere topic_where={};
    std::function<void(const char*)> topic_menu;
    topic_menu=[&](const char* prompt) {
        const auto* conversation=story_npc_conversation(topic_npc);
        if(!conversation)return;
        ask(prompt,{conversation->choices[0],conversation->choices[1],conversation->choices[2]},[&](int choice) {
            if(choice==2) {
                topic_active=false;story_npc_resume(topic_npc);return;
            }
            say(story_npc_answer(topic_npc,topic_where,choice));
            dlg_after=[&](){topic_menu("Need anything?");};
        });
    };
    // The debug speaker's list of every line (story_dialogue): -1 closed,
    // else the cursor. Each shows in the speech box; the list is back when
    // it closes. Its StoryWhere is the room's, kept from the talk.
    int        dlg_list  = -1;
    StoryWhere dlg_where = {};
    // The story's notes on whichever map (src/story.cpp): drawn where they lie
    // -- a white page with a fold, until they have a picture -- and TAKE NOTE
    // beside one, unless another prompt has the box. Call before the player
    // is drawn, with the feet's middle.
    auto notes_tick = [&](const StoryWhere& w, const DungeonMap* dm, const Camera* c, float fcx, float fcy, bool prompt_free, const Input* gin) {
        StoryNotePos ns[8];
        int n = story_notes_here(w, dm, ns, 8);
        for (int i = 0; i < n; i++) {
            float z = c->zoom;
            SDL_Rect page = { cam_px(c, ns[i].x) - (int)(6 * z), cam_py(c, ns[i].y) - (int)(5 * z), (int)(12 * z), (int)(10 * z) };
            fc_draw_color(plat.renderer, 40, 40, 40, 255);
            SDL_Rect shade = { page.x + 1, page.y + 1, page.w, page.h };
            SDL_RenderFillRect(plat.renderer, &shade);
            fc_draw_color(plat.renderer, 252, 252, 252, 255);
            SDL_RenderFillRect(plat.renderer, &page);
            fc_draw_color(plat.renderer, 160, 160, 160, 255);
            SDL_Rect fold = { page.x + (int)(2 * z), page.y + (int)(4 * z), page.w - (int)(4 * z), (int)(1 * z) > 0 ? (int)(1 * z) : 1 };
            SDL_RenderFillRect(plat.renderer, &fold);
        }
        if (!prompt_free || dlg_text) return;
        for (int i = 0; i < n; i++) {
            float ndx = fcx - ns[i].x, ndy = fcy - ns[i].y;
            if (w.state == STATE_OVERWORLD) { ndx = wrap_dpx(ndx); ndy = wrap_dpy(ndy); }
            if (ndx * ndx + ndy * ndy >= 40.0f * 40.0f) continue;
            draw_textbox(plat.renderer, "TAKE NOTE", 255, 255, 255);
            if (input_pressed(gin, SDL_SCANCODE_RETURN) ||
                input_pressed(gin, SDL_SCANCODE_Z)      ||
                input_pressed(gin, SDL_SCANCODE_SPACE)) {
                say(story_note_take(ns[i].idx, w), ns[i].strike);
                input_consume(&in, SDL_SCANCODE_Z);
                input_consume(&in, SDL_SCANCODE_RETURN);
                input_consume(&in, SDL_SCANCODE_SPACE);
            }
            break;
        }
    };
    // A line that answers a short pickup ("GOT RAFT BOOK"), and how long it stays.
    // Chest loot uses the speech box instead (say_chest).
    int  item_last[ITEM_COUNT] = {};   // last frame's item counts, for items_note_gains
    bool items_primed = false;
    const char* pickup_note   = nullptr;
    float       pickup_note_t = 0.0f;
    bool map_open         = false;
    bool battle_list_open = false;
    int  battle_list_sel  = 0;        // position in the filtered list
    char battle_query[24] = "";       // typed search: part of a name, or an id

    static const char* ENEMY_NAMES[] = {
        // Grassland 0–6
        "SKVADER", "WOLPERTINGER", "TREESQUEAK", "QIQUE", "LILI",
        "CROWING CRESTED COBRA", "WAKMANGGANCHI ARAGONDI",
        // Forest 7–13
        "ALBER", "SNAWFUS", "QUESTING BEAST", "GRAND'GOULE", "PAOXIAO",
        "EBIGANE", "BEAST OF THE CHARRED FORESTS",
        // Snow 14–20
        "LODSILUNGUR", "OFUGUGGI", "KAMAITACHI", "QIQIRN", "VATNAORMUR",
        "SKELJASKRIMSLI", "SERMILIK",
        // Desert 21–27
        "ASP", "CACTUS CAT", "OLGOI-KHORKHOI", "ZOUREG", "MYRMECOLEON",
        "AKHEKH", "GROOTSLANG",
        // Wasteland 28–34
        "OPIMACHUS", "KARNABO", "DAJNA", "MAN-EATING BOULDER", "ANGONT",
        "TSE'NAGAHI", "ANAYE",
        // Mountains 35–41
        "LOMIE", "CU SITH", "CELESTIAL STAG", "IGTUK", "AJAJU",
        "SLIDE-ROCK BOLTER", "SASNALKAHI",
        // Ocean 42–49
        "NYKUR", "SAZAE-ONI", "ITQIIRPAK", "KUSA KAP", "LUSCA",
        "MOHA-MOHA", "BJARNDYRAKONGUR", "PHYSETER",
        // Later cryptids, 50 on
        "TEAKETTLER", "ASPIDOCHELONE", "SANNAJA",
        "COME-AT-A-BODY", "BILLDAD", "WAPALOOSIE", "MOSKITTO", "DINGBAT", "AGROPELTER", "TRIPODERO", "RUMPTIFUSEL", "ROPERITE", "HUGAG", "HIDEBEHIND", "DUNGAVENHOOTER",
        // Folklore creatures, 65-99
        "MICE THAT EAT IRON", "AYOTOCHTLI", "LAGOPUS", "SHUYU", "BES CHEM",
        "TROLLGADDA", "NAMUNGUMI", "MAHWOT", "LIDERC", "BES RAP",
        "MAKALALA", "LOCH OICH MONSTER", "HOGA", "ZANKALLALA", "UGJUKNARPAK",
        "BES KOTAK", "IELTXU", "NADUBI", "BEAST OF BARRISDALE", "KIGUTILIK",
        "NANABOLELE", "LEUCROCOTTA", "COROCOTTA", "AMIXSAK", "CUERO",
        "CHIPEKWE", "KURREA", "SIEHNAM", "CHIPIQUE", "TROCHUS",
        "WITKES", "BREGDI", "RO", "BOIUNA", "FAD FELEN",
        // The final boss, 100
        "FLESH PLANET",
    };
    static_assert(sizeof(ENEMY_NAMES) / sizeof(ENEMY_NAMES[0]) == ENEMY_COUNT, "a name per enemy in the roster");

    // Static: the map is megabytes (its tiles, sight and the pyramid's art),
    // far past what main's stack holds.
    static DungeonMap dmap = {};
    DungeonPlayer dplayer = {};

    InteriorMap    imap    = {};
    InteriorPlayer iplayer = {};

    // A game begins inside the spawn house, standing mid-room on the floor,
    // by the bed. Exiting the doormat drops the player onto the overworld in
    // front of its door (place_at_start).
    auto wake_at_home = [&]() {
        debug_chest_opened = false;
        interior_load(&imap, 0);
        interior_player_init(&iplayer, &player, &imap);
        iplayer.x = IMAP_W * IMAP_TILE * 0.5f - (HB_X1 + HB_X2) * 0.5f;
        iplayer.y = 10 * IMAP_TILE + IMAP_TILE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
        player.facing = FACE_DOWN;  // toward the door
        state = STATE_INTERIOR;
    };
    wake_at_home();
    // The map minis (tools/minis.py): each chaser's own small sprite, cells of
    // 40x28 art px, 5 enemies a row, 8 cells each: D1 D2 U1 U2 L1 L2 R1 R2. An
    // enemy whose cells are empty is not confirmed yet and stays a square; one
    // with second frames steps between them as it moves, the rest hop.
    SDL_Texture* minis_tex = NULL, *minis_white = NULL;   // white: its hit flash (load_with_white)
    bool mini_done[100] = {}, mini_two[100] = {};
    if (SDL_Surface* ms = IMG_Load("assets/enemies/minis.png")) {
        if (SDL_Surface* m = SDL_ConvertSurfaceFormat(ms, SDL_PIXELFORMAT_RGBA32, 0)) {
            auto drawn = [m](int id, int cell) {
                for (int i = 0; i < 40 * 28; i++)
                    if (((Uint8*)m->pixels)[((id / 5) * 28 + i / 40) * m->pitch + (((id % 5) * 8 + cell) * 40 + i % 40) * 4 + 3]) return true;
                return false;
            };
            for (int id = 0; id < 100 && (id / 5 + 1) * 28 <= m->h; id++) {
                mini_done[id] = drawn(id, 0);
                mini_two[id]  = drawn(id, 1);
            }
            SDL_FreeSurface(m);
        }
        SDL_FreeSurface(ms);
        minis_tex = load_with_white(plat.renderer, "assets/enemies/minis.png", &minis_white);
    }
    // A mini too big for the sheet's cells has a strip of its own (minis_NN.png):
    // its 8 cells side by side, drawn at the same scale, feet where a chaser's are.
    SDL_Texture* mini_big[100] = {}, *mini_big_white[100] = {};
    int mini_big_w[100] = {}, mini_big_h[100] = {};
    for (int id = 0; id < 100; id++) {
        char path[40];
        SDL_snprintf(path, sizeof path, "assets/enemies/minis_%02d.png", id);
        if ((mini_big[id] = load_with_white(plat.renderer, path, &mini_big_white[id]))) {
            SDL_QueryTexture(mini_big[id], NULL, NULL, &mini_big_w[id], &mini_big_h[id]);
            mini_big_w[id] /= 8;
            mini_done[id] = mini_two[id] = true;
        }
    }

    if (!debug) state = STATE_TITLE;

    // face: its mini's view, 0-3 D U L R, and the way it ambles; t: how long it
    // has run at you; ax, ay: the middle of its amble; pause: a stop at a turn;
    // hx, hy: the leg it is on (one of 8 ways); poll: seconds to its next re-aim.
    struct DungeonChaser { float x, y; int enemy_id; bool active; bool chasing; float aggro_timer; int face; float t; float ax, ay, pause; float hx, hy, poll; };
    static const int MAX_CHASERS = 32;
    DungeonChaser chasers[MAX_CHASERS] = {};
    int num_chasers = 0;
    // The test house's enemies: drawn as chasers (draw_chaser), standing still
    // on their spots, facing down, in their first frame.
    DungeonChaser test_ch[sizeof(test_enemies) / sizeof(test_enemies[0])] = {};
    auto test_home = [&]() {
        for (int i = 0; i < TEST_N; i++)
            test_ch[i] = { test_enemies[i].x, test_enemies[i].y, test_enemies[i].id, true, false, 0.0f,
                           0, 0.0f, test_enemies[i].x, test_enemies[i].y, 1.0f, 0.0f, 0.0f, 0.0f };   // pause > 0: still
    };
    test_home();

    std::unordered_map<uint32_t, std::vector<uint8_t>> dungeon_explored_cache;
    char pickup_buf[128] = "";
    // A chest struck open: "chest was opened." in the speech box, then a
    // line for each thing in it, its icon beside it.
    auto say_chest = [&](const Item* items, const int* counts, int n) {
        SDL_strlcpy(pickup_buf, "chest was opened.", sizeof(pickup_buf));
        for (int i = 0; i < n; i++) {
            char ln[40];
            SDL_snprintf(ln, sizeof(ln), "\n%s x%d", item_name(items[i]), counts[i]);
            SDL_strlcat(pickup_buf, ln, sizeof(pickup_buf));
        }
        say(pickup_buf);
        dlg_icon_n = n;
        for (int i = 0; i < n; i++) dlg_icons[i] = items[i];
    };
    uint32_t current_dng_seed = 0;
    float dng_arrival_x = 0, dng_arrival_y = 0;
    bool dng_arrival_valid = false;

    // Portal state: which overworld tiles DNG_ENTRY / DNG_EXIT map back to.
    // Set when entering a dungeon; both default to the entrance tile if there
    // is no connected partner dungeon.
    int dng_entry_portal_x = -1, dng_entry_portal_y = -1;
    int dng_exit_portal_x  = -1, dng_exit_portal_y  = -1;

    float esc_hold_time = 0.f;

    // Throw the world away and grow another from seed: the debug menu's REGEN
    // MAP, and a new game started over a save's world.
    auto rebuild_world = [&](unsigned int seed) {
        dng_arrival_valid = false;
        tilemap_cancel_gen();
        gen_thread.join();
        tilemap_reset_gen_cancel();
        map_seed = seed;
        printf("World seed: %u   (re-run with: game.exe --debug %u)\n", map_seed, map_seed);
        fflush(stdout);
        delete map;
        map = new Tilemap();
        memset(tilemap_landmarks_opened(), 0, MAX_LANDMARKS / 8);   // another world: none of its landmarks opened
        memset(dungeon_chest_records(), 0, sizeof(DungeonChestRecord) * MAX_DUNGEON_CHEST_RECORDS);   // nor its dungeons' chests
        memset(story_flags(), 0, sizeof(StoryFlags));   // and its story not begun
        resident_reset();
        tilemap_build_overworld_phase1(map, map_seed);
        gen_thread = std::thread(tilemap_build_overworld_phase2, map, map_seed);
        resource_nodes_init(&resources);
        for (bool& b : oilbloom_done) b = false;
        dungeon_explored_cache.clear();
        dbg_tour = -1;   // new world, new set of entrances to tour
    };

    // The title screen (play mode only).
    enum { TITLE_NEW, TITLE_CONTINUE, TITLE_OPTIONS, TITLE_QUIT, TITLE_COUNT };
    enum { TPAGE_MAIN, TPAGE_OPTIONS, TPAGE_ERASE };
    int  title_sel     = has_save ? TITLE_CONTINUE : TITLE_NEW;
    int  title_page    = TPAGE_MAIN;
    bool title_erase   = false;   // ERASE SAVE? -- the cursor, on NO first
    bool title_loading = false, title_loading_drawn = false;   // LOADING goes up a frame before the new world is built

    // Shared actor pause rule. All movement, AI, encounter checks and future
    // actor updates must use this gate; UI keeps using real frame time.
    // Read it dynamically so dialogue opened mid-frame pauses later actors too.
    auto actors_paused = [&]() {
        return dbg_open || menu.open || map_open || battle_list_open || dlg_text || dlg_list >= 0;
    };

    // Manual 60 fps frame cap — more consistent than SDL_RENDERER_PRESENTVSYNC on WSL2
    const Uint64 PERF_FREQ      = SDL_GetPerformanceFrequency();
    const Uint64 FRAME_TICKS    = PERF_FREQ / 60;
    Uint64       frame_deadline = SDL_GetPerformanceCounter() + FRAME_TICKS;

    // ── Battle entry, shared by every map that starts fights ─────────────────
    // Each queued enemy flashes once in fight order, the screen blinks white,
    // and black stripes wipe the map away; the battle then fades up with
    // everyone in place. c is the map's camera.
    static const float FLASH_STEP = ACTOR_FLASH_STEP;
    static const float FLASH_ON   = ACTOR_FLASH_ON;
    static const float HOLD       = 0.24f; // the screen flashes, after the enemy flashes
    static const float FADE       = 0.24f; // stripe wipe to black
    auto pre_battle_tick = [&](float step, GameState back) {
        pre_battle_timer += step;
        if (pre_battle_timer < flash_count * FLASH_STEP + HOLD + FADE) return;
        pre_battle_timer = -1.0f;
        delete battle_scene;
        battle_scene = new BattleScene(&player, battle_queue[0]);
        battle_scene->set_more_after(battle_queue_count > 1);
        state_after_battle = back;
        state = STATE_BATTLE;
    };
    // Black over the screen in the NES's four steps, not a smooth ramp: its
    // fades are palette swaps, a few brightness levels and nothing between.
    auto veil = [&](float a) {
        if (a <= 0.0f) return;
        a = a >= 1.0f ? 1.0f : (float)(int)(a * 4.0f + 0.999f) / 4.0f;  // round up: starts fully black
        SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_BLEND);
        fc_draw_color(plat.renderer, 0, 0, 0, (Uint8)(255 * a));
        SDL_Rect r = { 0, 0, 640, 480 };
        SDL_RenderFillRect(plat.renderer, &r);
        SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_NONE);
    };
    auto chaser_rect = [&](const Camera* c, float wx, float wy) {
        int sz = (int)(14 * c->zoom);
        return SDL_Rect{ cam_px(c, wx) - sz / 2, cam_py(c, wy) - sz / 2, sz, sz };
    };
    // A chaser on the map: its mini at the player's scale, feet on the bottom of
    // its square; while it moves it steps to its second frame every other 150 ms
    // (or the one its chase picks), or hops a pixel if it has none. A square
    // until its mini is confirmed.
    auto draw_chaser = [&](const Camera* c, const DungeonChaser& ch, bool white = false) {
        int id = ch.enemy_id, face = ch.face;
        static const int SPIN[4] = { 0, 3, 1, 2 };                  // D R U L
        if (id == 16) face = SPIN[world_ms() / 120 % 4];        // the Kamaitachi spins, whichever way it goes
        float wx = ch.x, wy = ch.y;
        bool running = ch.chasing && ch.aggro_timer <= 0.0f;
        bool moving = ch.chasing ? running && chase_speed(id, ch.t) != 0.0f : ch.pause <= 0.0f;
        int frame = running ? chase_frame(id, ch.t) : -1;
        if (id < 0 || id >= 100 || !mini_done[id] || (!minis_tex && !mini_big[id])) {
            SDL_Rect cr = chaser_rect(c, wx, wy);
            fc_draw_color(plat.renderer, 200, 30, 30, 255);
            SDL_RenderFillRect(plat.renderer, &cr);
            fc_draw_color(plat.renderer, 255, 80, 80, 255);
            SDL_RenderDrawRect(plat.renderer, &cr);
            return;
        }
        float s = 2.0f * c->zoom;
        int step = moving && (world_ms() / 150) % 2;
        if (mini_two[id] && frame >= 0) step = frame;               // its chase picks the frame
        int hop = step && !mini_two[id] ? (int)s : 0;
        int cell = face * 2 + (step && mini_two[id]), cw = 40, chh = 28;
        SDL_Rect src = { ((id % 5) * 8 + cell) * 40, (id / 5) * 28, 40, 28 };
        if (mini_big[id]) { cw = mini_big_w[id]; chh = mini_big_h[id]; src = { cell * cw, 0, cw, chh }; }
        SDL_Rect dst = { cam_px(c, wx) - (int)(cw / 2 * s), cam_py(c, wy + 7.0f) - (int)(chh * s) - hop, (int)(cw * s), (int)(chh * s) };
        SDL_Texture* tex = mini_big[id] ? (white ? mini_big_white[id] : mini_big[id]) : (white ? minis_white : minis_tex);
        SDL_RenderCopy(plat.renderer, tex, &src, &dst);
    };
    // One chaser's turn, in a dungeon or the test house. Unseen, it ambles: one
    // way at random up to PATROL_R from the middle of its beat (ax, ay), a stop,
    // another way. Seen, it turns to look and holds 24 frames, then runs at
    // (cdx, cdy) its own way, re-aiming every 8 frames (EarthBound's): the line
    // to you, bent, snapped to one of 8 directions; between re-aims it keeps to
    // the leg, which is what a sidestep exploits. Returns its speed along
    // (hx, hy); fits(ch, wx, wy) says where it may stand.
    const float CHASER_SPEED = 1.5f * PLAYER_WALK_SPEED;   // walked away from, no; run from, yes
    auto chase_tick = [&](DungeonChaser& ch, bool seen, float cdx, float cdy, float dt, auto fits) -> float {
        const float NOTICE_T = 24.0f / 60.0f, POLL_T = 8.0f / 60.0f;  // EB's 24-frame hold, 8-frame re-aim
        if (!ch.chasing) {
            if (!seen) {
                const float PATROL_SPEED = 0.3f * PLAYER_RUN_SPEED, PATROL_R = 2.0f * DMAP_TILE;
                if (ch.pause > 0.0f) { ch.pause -= dt; return 0.0f; }
                static const float FX[4] = { 0, 0, -1, 1 }, FY[4] = { 1, -1, 0, 0 };
                float nx = ch.x + FX[ch.face] * PATROL_SPEED * dt, ny = ch.y + FY[ch.face] * PATROL_SPEED * dt;
                if (fabsf(nx - ch.ax) <= PATROL_R && fabsf(ny - ch.ay) <= PATROL_R && fits(ch, nx, ny)) {
                    ch.x = nx; ch.y = ny;
                } else {
                    ch.face  = rand() % 4;
                    ch.pause = 0.4f + (rand() % 100) * 0.01f;
                }
                return 0.0f;
            }
            ch.chasing = true;
            ch.aggro_timer = NOTICE_T;
            ch.t = 0.0f;
            ch.poll = 0.0f;
            ch.face = fabsf(cdx) > fabsf(cdy) ? (cdx < 0 ? 2 : 3) : (cdy < 0 ? 1 : 0);
        }
        if (ch.aggro_timer > 0.0f) { ch.aggro_timer -= dt; return 0.0f; }
        ch.t += dt;
        ch.poll -= dt;
        if (ch.poll <= 0.0f) {
            ch.poll += POLL_T;
            float dist = sqrtf(cdx * cdx + cdy * cdy);
            float mx = cdx / dist, my = cdy / dist;
            float bend = chase_bend(ch.enemy_id, ch.t), bc = cosf(bend), bs = sinf(bend);
            const float EIGHTH = 0.78539816f;   // pi / 4
            float a = roundf(atan2f(mx * bs + my * bc, mx * bc - my * bs) / EIGHTH) * EIGHTH;
            ch.hx = cosf(a); ch.hy = sinf(a);
            ch.face = fabsf(ch.hx) > fabsf(ch.hy) ? (ch.hx < 0 ? 2 : 3) : (ch.hy < 0 ? 1 : 0);   // it looks the way it runs
        }
        return CHASER_SPEED * chase_speed(ch.enemy_id, ch.t);
    };
    // Drawn over the map: the flashes and fade going in, the fade-in coming back.
    auto battle_veil_draw = [&](const Camera* c) {
        if (pre_battle_timer >= 0.0f) {
            int cur_step = (int)(pre_battle_timer / FLASH_STEP);
            float local_t = pre_battle_timer - cur_step * FLASH_STEP;
            for (int fi = 0; fi < flash_count; fi++) {
                const FlashEntry& fe = flash_entries[fi];
                if (fe.id >= 0 && fe.id < 100 && mini_done[fe.id]) {
                    // One with a mini flashes in it: solid white in its turn,
                    // as a fight's enemy flashes when hit; dim until then,
                    // itself after.
                    SDL_Texture* tex = mini_big[fe.id] ? mini_big[fe.id] : minis_tex;
                    DungeonChaser still = {};
                    still.x = fe.x; still.y = fe.y; still.enemy_id = fe.id; still.face = fe.face; still.pause = 1.0f;
                    if (fi > cur_step) SDL_SetTextureColorMod(tex, 110, 110, 110);
                    draw_chaser(c, still, fi == cur_step && local_t < FLASH_ON);
                    SDL_SetTextureColorMod(tex, 255, 255, 255);
                    continue;
                }
                SDL_Rect cr = chaser_rect(c, fe.x, fe.y);
                if (fi == cur_step && local_t < FLASH_ON) {
                    // Currently flashing — bright yellow
                    fc_draw_color(plat.renderer, 255, 220, 50, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    fc_draw_color(plat.renderer, 255, 255, 255, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                } else if (fi > cur_step) {
                    // Not yet reached — shown dim
                    fc_draw_color(plat.renderer, 80, 20, 20, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    fc_draw_color(plat.renderer, 120, 40, 40, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                } else {
                    // Flashed already: back to its own red, there until the wipe.
                    fc_draw_color(plat.renderer, 200, 30, 30, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    fc_draw_color(plat.renderer, 255, 80, 80, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                }
            }
            // After the flashes: the whole screen blinks white, the old
            // encounter flash, then black stripes slide in from alternate
            // sides a tile at a time until nothing is left.
            float flash_end = flash_count * FLASH_STEP;
            if (pre_battle_timer >= flash_end) {
                float t = pre_battle_timer - flash_end;
                if (t < HOLD) {
                    if ((int)(t / 0.04f) % 2 == 0) {
                        SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_BLEND);
                        fc_draw_color(plat.renderer, 255, 255, 255, 170);
                        SDL_Rect r = { 0, 0, 640, 480 };
                        SDL_RenderFillRect(plat.renderer, &r);
                        SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_NONE);
                    }
                } else {
                    float k = (t - HOLD) / FADE;
                    int cols = (int)(nes_steps(k > 1.0f ? 1.0f : k, 10) * 20.0f + 0.5f);  // of 20 32px tiles
                    fc_draw_color(plat.renderer, 0, 0, 0, 255);
                    for (int row = 0; row < 30; row++) {          // 16px stripes
                        int w = cols * 32;
                        SDL_Rect r = { row % 2 ? 640 - w : 0, row * 16, w, 16 };
                        SDL_RenderFillRect(plat.renderer, &r);
                    }
                }
            }
        }
        // Back from a fight: the map steps up out of black.
        if (post_battle_t > 0.6f) veil((post_battle_t - 0.6f) / 0.4f);
    };

    while (running)
    {
        double dt_d = time_delta_seconds();
        if (dt_d > 0.05) dt_d = 0.05; // cap at 50 ms — prevents big jumps on stalled frames
        float dt = (float)dt_d;
        room_swap = false;
        if (room_t >= 0.0f) {
            room_swap = room_t < BATTLE_FADE_T && room_t + dt >= BATTLE_FADE_T;
            room_t += dt;
            if (room_t >= 2.0f * BATTLE_FADE_T) room_t = -1.0f;
        }

        input_begin_frame(&in);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            input_handle_event(&in, &e);
        }
        if (in.quit) running = false;
        if (input_down(&in, SDL_SCANCODE_ESCAPE)) {
            esc_hold_time += dt;
            if (esc_hold_time >= 3.f) running = false;
        } else {
            esc_hold_time = 0.f;
        }

        // Bound before any state draws, so the RenderClear each of them opens
        // with clears the frame rather than the window. Sized here too, since
        // the window is resizable and F11 changes it out from under us.
        if (can_target) {
            int fs = frame_scale_for(plat.renderer, LOGICAL_W, LOGICAL_H);
            if (fs != frame_scale || !frame_tex) {
                if (frame_tex) SDL_DestroyTexture(frame_tex);
                frame_tex = SDL_CreateTexture(plat.renderer, SDL_PIXELFORMAT_RGBA8888,
                                              SDL_TEXTUREACCESS_TARGET,
                                              LOGICAL_W * fs, LOGICAL_H * fs);
                if (frame_tex) SDL_SetTextureBlendMode(frame_tex, SDL_BLENDMODE_NONE);
                frame_scale = fs;
            }
        }
        if (frame_tex) {
            SDL_SetRenderTarget(plat.renderer, frame_tex);
            // Explicit: binding a target resets the logical size, and this is
            // what makes the scale inside the frame exactly frame_scale.
            SDL_RenderSetLogicalSize(plat.renderer, LOGICAL_W, LOGICAL_H);
        }

        if (input_pressed(&in, SDL_SCANCODE_F1))
            dbg_readout = !dbg_readout;

        if (input_pressed(&in, SDL_SCANCODE_F11)) {
            Uint32 flags = SDL_GetWindowFlags(plat.window);
            SDL_SetWindowFullscreen(plat.window,
                (flags & SDL_WINDOW_FULLSCREEN_DESKTOP) ? 0 : SDL_WINDOW_FULLSCREEN_DESKTOP);
        }

        // ── Debug menu toggle / navigation ───────────────────────────────────
        if (debug && input_pressed(&in, SDL_SCANCODE_F2)) {
            dbg_open = !dbg_open;
            dbg_sel  = 0;
        }
        if (dbg_open) {
            // W/S up and down a column, wrapping; A/D across to the other
            // column, on the same line or its last. Q/E step the selected
            // row's value back and on, or flip it if it is on/off.
            {
                int pos   = dbg_pos(dbg_sel);
                int right = pos >= DBG_PLAYER_AT;
                int first = right ? DBG_PLAYER_AT : 0;
                int len   = right ? DBG_ROW_COUNT - DBG_PLAYER_AT : DBG_PLAYER_AT;
                int line  = pos - first;
                if (input_pressed(&in, SDL_SCANCODE_W)) line = (line + len - 1) % len;
                if (input_pressed(&in, SDL_SCANCODE_S)) line = (line + 1) % len;
                if (input_pressed(&in, SDL_SCANCODE_A) || input_pressed(&in, SDL_SCANCODE_D)) {
                    right = !right;
                    first = right ? DBG_PLAYER_AT : 0;
                    len   = right ? DBG_ROW_COUNT - DBG_PLAYER_AT : DBG_PLAYER_AT;
                    if (line >= len) line = len - 1;
                }
                dbg_sel = DBG_ORDER[first + line];
            }
            int  dbg_step   = input_pressed(&in, SDL_SCANCODE_E) - input_pressed(&in, SDL_SCANCODE_Q);
            bool dbg_toggle = input_pressed(&in, SDL_SCANCODE_E) || input_pressed(&in, SDL_SCANCODE_Q);

            if (dbg_sel == 0) {
                int was = dbg_target;
                dbg_target = (dbg_target + dbg_step + DBG_TARGET_COUNT) % DBG_TARGET_COUNT;
                // A different target is a different tour. Carrying the position
                // over would start the Dravium caves at the third one purely
                // because that is where the Kharvite tour had got to.
                if (dbg_target != was) dbg_tour = -1;
            }

            // Weapon: applied straight to the player so the change is visible
            // immediately — it drives both battle damage and the overworld tool
            // cooldown, with no confirm step to forget.
            // Row 8 does the same for the ore it is made of.
            {
                int step = dbg_step;
                if (dbg_sel == 5 && step) {
                    // Debug hands over the weapon outright: owned from here on.
                    player.equipped = (WeaponType)(((int)player.equipped + step + WEAPON_COUNT) % WEAPON_COUNT);
                    player.owned[player.equipped] = true;
                }
                Weapon& eq = equipped_weapon(&player);
                if (dbg_sel == 8)
                    eq.material = (Material)(((int)eq.material + step + MAT_COUNT) % MAT_COUNT);
                // Row 11: the story, as far as a stage (its beaten bits set to there)
                if (dbg_sel == 11 && step)
                    story_set_stage((StoryStage)((story_stage() + step + STORY_STAGE_COUNT) % STORY_STAGE_COUNT));
                if (dbg_sel == 12 && step)   // the sites, the hall, village 0, the lighthouse, the bat's tree, the wharf's tip
                    dbg_story_go = (dbg_story_go + step + STORY_BOSS_COUNT + 5) % (STORY_BOSS_COUNT + 5);
            }

            bool dbg_confirm = input_pressed(&in, SDL_SCANCODE_RETURN) ||
                               input_pressed(&in, SDL_SCANCODE_Z);
            bool dbg_flip    = dbg_confirm || dbg_toggle;   // the on/off rows take either

            if (dbg_sel == 1 && dbg_confirm) {
                // Step to the NEXT place answering the target, not the nearest:
                // pressing this repeatedly walks every one of them in turn,
                // which is how you find out where they all are. Array order, so
                // press number three always lands on the same cave.
                //
                // The menu deliberately stays open. Touring is the point, and
                // an F2 between every hop is three keys where one will do; the
                // world still draws around the panel, and the minimap (M) is
                // the thing you are reading anyway.
                int n = dbg_target_list(dbg_target, dbg_list, MAX_DUNGEON_ENTRANCES);
                if (n > 0) {
                    // Modulo, not ++: the gen thread is still appending
                    // entrances early on, so the list can grow or shrink under
                    // a tour already in progress.
                    dbg_tour = (dbg_tour + 1) % n;
                    // Feet in the middle of the entrance tile, the same way the
                    // spawn-door placement above does it. Landing the sprite
                    // origin on the tile instead puts the feet a tile south of
                    // the mouth, which is far enough off that the entrance
                    // prompt never appears and a key press mines the rock in
                    // front of you rather than taking you in.
                    const DungeonEntrance& e = map->dungeon_entrances[dbg_list[dbg_tour]];
                    ow.x  = e.x * TILE_SIZE + TILE_SIZE * 0.5f - (HB_X1 + HB_X2) * 0.5f;
                    ow.y  = e.y * TILE_SIZE + TILE_SIZE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
                    state = STATE_OVERWORLD;
                }
            }

            // Row 12: to a story place -- three tiles south of a boss's site, or
            // two below the coastal town's hall door -- so it is in view, not
            // underfoot.
            if (dbg_sel == 12 && dbg_confirm) {
                int tx = -1, ty = -1;
                if (dbg_story_go < STORY_BOSS_COUNT) {
                    tx = map->boss_sites[dbg_story_go].x; ty = map->boss_sites[dbg_story_go].y + 3;
                } else if (dbg_story_go == STORY_BOSS_COUNT) {
                    if (map->towns[1].x >= 0) { tx = map->towns[1].x + TOWN1_HALL_DOOR_X; ty = map->towns[1].y + TOWN1_HALL_DOOR_Y + 2; }
                } else if (dbg_story_go == STORY_BOSS_COUNT + 1) {
                    if (map->num_villages > 0) { story_village_npc_tile(map, 0, &tx, &ty); ty += 1; }   // the street's lower row, a step from the speaker
                } else if (dbg_story_go == STORY_BOSS_COUNT + 2) {
                    if (map->lighthouse_door >= 0)   // onto the lighthouse's door foot: it takes you in
                        { tx = map->doors[map->lighthouse_door].x; ty = map->doors[map->lighthouse_door].y; }
                } else if (dbg_story_go == STORY_BOSS_COUNT + 3) {
                    if (int t = story_quest_tree(map); t >= 0) { tx = map->dungeon_entrances[t].x; ty = map->dungeon_entrances[t].y + 2; }
                } else {
                    if (map->wharf_tip.x >= 0) { tx = map->wharf_tip.x; ty = map->wharf_tip.y; }
                }
                if (tx >= 0) {
                    ow.x  = tx * TILE_SIZE + TILE_SIZE * 0.5f - (HB_X1 + HB_X2) * 0.5f;
                    ow.y  = ty * TILE_SIZE + TILE_SIZE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
                    state = STATE_OVERWORLD;
                    dbg_open = false;
                }
            }

            if (dbg_sel == 2 && dbg_confirm) {
                // Regenerate the entire overworld with a new seed
                rebuild_world((unsigned int)SDL_GetTicks());
                ow.x = (MAP_WIDTH  / 2.0f) * TILE_SIZE;
                ow.y = (MAP_HEIGHT / 2.0f) * TILE_SIZE;
                state    = STATE_OVERWORLD;
                dbg_open = false;
            }

            if (dbg_sel == 3 && dbg_flip)
                dbg_noclip = !dbg_noclip;

            if (dbg_sel == 4 && dbg_flip)
                dbg_show_all = !dbg_show_all;

            if (dbg_sel == 6 && dbg_flip)
                dbg_grid = !dbg_grid;

            // Row 7: stand three tiles short of the seam, on the nearest
            // walkable tile to the middle of it, so the crossing can be tried
            // in seconds. The seam is the far edge of the wrap axis.
            // Row 9: ten of every material, and every book and special part,
            // to try every recipe. Never the raft (making it is the opening)
            // nor crafted equipment (its ingredients are here to make it).
            if (dbg_sel == 9 && dbg_confirm)
                for (int it = 0; it < ITEM_COUNT; it++) {
                    if (item_is_material((Item)it))      item_slot(&player, (Item)it) = ITEM_MAX;   // the most of every material (user: that is what GIVE ALL means)
                    else if ((item_is_book((Item)it) || (it >= ITEM_OLD_SPEARHEAD && it <= ITEM_REAPERS_EDGE)) && item_count(&player, (Item)it) == 0)   // made things are made
                        item_slot(&player, (Item)it) = 1;
                }

            // Row 10: every weapon held, as good as it gets -- the best ore,
            // FASTER and MORE SHOTS at their tops.
            if (dbg_sel == 10 && dbg_confirm)
                for (int w = 0; w < WEAPON_COUNT; w++) {
                    if (!player.owned[w]) continue;
                    player.arsenal[w].material = (Material)(MAT_COUNT - 1);
                    player.arsenal[w].oil      = WEAPON_OIL_MAX;
                    player.arsenal[w].echo     = WEAPON_ECHO_MAX;
                }

            if (dbg_sel == 7 && dbg_confirm && state == STATE_OVERWORLD) {
                int sx = MAP_WIDTH / 2, sy = MAP_HEIGHT / 2;
                if (map->wrap_axis == WRAP_X) sx = MAP_WIDTH  - 4;
                else                          sy = MAP_HEIGHT - 4;
                for (int d = 0; d < MAP_WIDTH / 2; d++) {
                    int ax = sx, ay = sy;
                    if (map->wrap_axis == WRAP_X) ay = MAP_HEIGHT / 2 + ((d & 1) ? d / 2 : -(d / 2));
                    else                          ax = MAP_WIDTH  / 2 + ((d & 1) ? d / 2 : -(d / 2));
                    if (!tilemap_is_walkable(map, ax, ay)) continue;
                    ow.x = ax * TILE_SIZE + TILE_SIZE * 0.5f - (HB_X1 + HB_X2) * 0.5f;
                    ow.y = ay * TILE_SIZE + TILE_SIZE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
                    break;
                }
                dbg_open = false;
            }

            if (input_pressed(&in, SDL_SCANCODE_ESCAPE))
                dbg_open = false;
        }

        // Whatever was gained since last frame now counts as found; the first
        // frame only takes stock, so what the game started with is not.
        items_note_gains(&player, item_last, !items_primed);
        items_primed = true;

        // ── The TAB menu (src/game_menu.cpp) ──────────────────────────────────
        // Opens anywhere but the title; in a battle it pauses the fight. Handled before anything else reads a key, so while it is open
        // the world sees none: game_in below is blank, and each raw key that
        // reaches into the world (zoom, map, leaving a room or dungeon, the
        // battle list) checks menu.open itself.
        {
            bool menu_ok  = state != STATE_TITLE && !dlg_text && dlg_list < 0;   // nor under the speech box
            // Pursuit remains available to future item restrictions.
            menu.chased = state == STATE_BATTLE;
            menu.save_block = debug ? "NOT IN DEBUG" : state == STATE_BATTLE ? "NOT IN A FIGHT" : nullptr;
            if (state == STATE_DUNGEON)
                for (int ci = 0; ci < num_chasers; ci++)
                    if (chasers[ci].active && chasers[ci].chasing) menu.chased = true;
            menu.escape_block = state == STATE_BATTLE ? "NOT IN A FIGHT"
                : state != STATE_DUNGEON || !dng_arrival_valid ? "ONLY IN A DUNGEON"
                : pre_battle_timer >= 0.0f ? "BATTLE IS STARTING"
                : room_t >= 0.0f ? "TRANSITION IN PROGRESS" : nullptr;
            menu.healing_block = state == STATE_BATTLE ? "EXPLORATION ONLY"
                : pre_battle_timer >= 0.0f ? "BATTLE IS STARTING"
                : room_t >= 0.0f ? "TRANSITION IN PROGRESS" : nullptr;
            bool was_open = menu.open;
            if (input_pressed(&in, SDL_SCANCODE_TAB) && !dbg_open && menu_ok) game_menu_toggle(&menu);
            else if (menu.open && menu_ok) game_menu_update(&menu, &player, &in, dt);
            if (menu.escape_request) {
                menu.escape_request = false;
                if (!menu.escape_block && item_count(&player, ITEM_ESCAPE_CHARM) > 0 &&
                    dungeon_escape_to(&dplayer, &player, &dmap, dng_arrival_x, dng_arrival_y)) {
                    menu.open = false;
                    map_open = false;
                    room_armed = false;
                    post_battle_t = 1.0f;
                    for (int ci = 0; ci < num_chasers; ci++) {
                        auto& ch = chasers[ci];
                        ch.chasing = false;
                        ch.aggro_timer = 0;
                        ch.ax = ch.x; ch.ay = ch.y;
                        ch.hx = ch.hy = ch.poll = 0;
                    }
                    camera_follow(&cam, dplayer.x, dplayer.y, (float)player.width, (float)player.height);
                    dungeon_frame_camera(&dmap, &cam);
                } else game_menu_say(&menu, menu.escape_block ? menu.escape_block : "CANNOT RETURN HERE");
            }
            // SAVE. The overworld spot is right wherever the player is: it
            // does not move while they are in a house or a dungeon, so a save
            // made inside loads outside that door, or at that dungeon's mouth.
            if (menu.save_request) {
                menu.save_request = false;
                bool ok = save_write(map_seed, ow.x, ow.y, player, explored);
                has_save = has_save || ok;
                game_menu_say(&menu, ok ? "SAVED" : "COULD NOT SAVE");
            }
            // The key that closed it (Z on CLOSE) is still held next frame;
            // without this it would swing at whatever stands in front.
            if (was_open && !menu.open) {
                input_consume(&in, SDL_SCANCODE_RETURN);
                input_consume(&in, SDL_SCANCODE_Z);
                input_consume(&in, SDL_SCANCODE_SPACE);
                if (state == STATE_BATTLE && battle_scene) battle_scene->sync_weapon();
            }
        }

        // ── The speech box ────────────────────────────────────────────────────
        // Z while it types shows the part whole; stopped, Z goes on; at the
        // end, Z closes it. The key is spent so nothing below acts on it (the
        // prompt that opened it would reopen it).
        if (dlg_text) dlg_t += dt;
        bool dlg_ok = input_pressed(&in, SDL_SCANCODE_Z) || input_pressed(&in, SDL_SCANCODE_RETURN) ||
                      input_pressed(&in, SDL_SCANCODE_SPACE);
        if(topic_active && (input_pressed(&in,SDL_SCANCODE_ESCAPE)||input_pressed(&in,SDL_SCANCODE_X))) {
            topic_active=false;dlg_text=nullptr;dlg_choice_n=0;dlg_after=nullptr;
            story_npc_resume(topic_npc);
            input_consume(&in,SDL_SCANCODE_ESCAPE);input_consume(&in,SDL_SCANCODE_X);
        }
        else if (dlg_text && dlg_choice_n && dlg_state == SPEECH_END) {
            if (input_pressed(&in, SDL_SCANCODE_UP)   || input_pressed(&in, SDL_SCANCODE_W)) dlg_choice = (dlg_choice + dlg_choice_n - 1) % dlg_choice_n;
            if (input_pressed(&in, SDL_SCANCODE_DOWN) || input_pressed(&in, SDL_SCANCODE_S)) dlg_choice = (dlg_choice + 1) % dlg_choice_n;
            bool leave = input_pressed(&in, SDL_SCANCODE_X);
            if (dlg_ok || leave) {
                int pick = leave ? dlg_choice_n - 1 : dlg_choice;
                dlg_text = nullptr; dlg_choice_n = 0;
                dlg_pick(pick);   // may say() or open the shop
            }
            input_consume(&in, SDL_SCANCODE_Z);
            input_consume(&in, SDL_SCANCODE_RETURN);
            input_consume(&in, SDL_SCANCODE_SPACE);
            input_consume(&in, SDL_SCANCODE_X);
        }
        else if (dlg_text && dlg_ok) {
            if (dlg_state == SPEECH_TYPING)    dlg_t = 1e9f;
            else if (dlg_state == SPEECH_WAIT) { dlg_part++; dlg_t = 0.0f; dlg_state = SPEECH_TYPING; }
            else {
                dlg_text = nullptr; dlg_icon_n = 0;
                auto after=std::move(dlg_after);dlg_after=nullptr;
                if(after)after();
            }
            input_consume(&in, SDL_SCANCODE_Z);
            input_consume(&in, SDL_SCANCODE_RETURN);
            input_consume(&in, SDL_SCANCODE_SPACE);
        }
        // The debug dialogue list, under the speech box: up/down, Z shows
        // one, ESC or X closes (spent, or ESC would leave the room too).
        else if (dlg_list >= 0 && !dlg_text) {
            int n = story_dialogue_count();
            if (input_pressed(&in, SDL_SCANCODE_UP)   || input_pressed(&in, SDL_SCANCODE_W)) dlg_list = (dlg_list + n - 1) % n;
            if (input_pressed(&in, SDL_SCANCODE_DOWN) || input_pressed(&in, SDL_SCANCODE_S)) dlg_list = (dlg_list + 1) % n;
            if (input_pressed(&in, SDL_SCANCODE_Z) || input_pressed(&in, SDL_SCANCODE_RETURN) ||
                input_pressed(&in, SDL_SCANCODE_SPACE)) {
                const char* lbl;
                bool strike;
                const char* t = story_dialogue(dlg_list, dlg_where, &lbl, &strike);
                say(t, strike);
            }
            if (input_pressed(&in, SDL_SCANCODE_ESCAPE) || input_pressed(&in, SDL_SCANCODE_X) || state != STATE_INTERIOR)
                dlg_list = -1;
            input_consume(&in, SDL_SCANCODE_Z);
            input_consume(&in, SDL_SCANCODE_RETURN);
            input_consume(&in, SDL_SCANCODE_SPACE);
            input_consume(&in, SDL_SCANCODE_ESCAPE);
            input_consume(&in, SDL_SCANCODE_X);
        }

        // ── Battle test list (F3) ─────────────────────────────────────────────
        if (debug && input_pressed(&in, SDL_SCANCODE_F3) && !dbg_open && !menu.open && state != STATE_BATTLE)
            battle_list_open = !battle_list_open;

        // The list runs easiest to hardest (the user): by tier, and within a
        // tier by id -- the same order the EXP climbs in (enemy_defeat_exp).
        // Its number is that rank, not the id. Filtered by what's typed:
        // letters match anywhere in the name, a number matches the rank (its
        // digits from the start).
        static int battle_order[ENEMY_COUNT], battle_rank[ENEMY_COUNT];
        static bool battle_ordered = false;
        if (!battle_ordered) {
            battle_ordered = true;
            int n = 0;
            for (int t = T_UNSET; t <= T_BOSS3; t++)
                for (int e = 0; e < ENEMY_COUNT; e++)
                    if (enemy_tier(e) == t) { battle_rank[e] = n; battle_order[n++] = e; }
        }
        int battle_hits[ENEMY_COUNT], battle_n = 0;
        for (int r = 0; r < ENEMY_COUNT; r++) {
            int e = battle_order[r];
            char id[8];
            SDL_snprintf(id, sizeof(id), "%02d", r);
            bool digits = battle_query[0] >= '0' && battle_query[0] <= '9';
            bool hit = digits ? (SDL_strncmp(id, battle_query, SDL_strlen(battle_query)) == 0 ||
                                 SDL_atoi(battle_query) == r)
                              : SDL_strstr(ENEMY_NAMES[e], battle_query) != nullptr;
            if (hit) battle_hits[battle_n++] = e;
        }
        if (battle_list_sel >= battle_n) battle_list_sel = battle_n > 0 ? battle_n - 1 : 0;

        if (battle_list_open) {
            // Typing: A-Z, 0-9, space, - and ' (names like COME-AT-A-BODY,
            // GRAND'GOULE); backspace takes one off. Enter fights.
            size_t ql = SDL_strlen(battle_query);
            auto type = [&](char c) {
                if (ql + 1 < sizeof(battle_query)) { battle_query[ql++] = c; battle_query[ql] = 0; battle_list_sel = 0; }
            };
            for (int k = 0; k < 26; k++)
                if (input_pressed(&in, (SDL_Scancode)(SDL_SCANCODE_A + k))) type((char)('A' + k));
            for (int k = 0; k < 10; k++)   // SDL lists 1..9 then 0
                if (input_pressed(&in, (SDL_Scancode)(SDL_SCANCODE_1 + k))) type((char)(k == 9 ? '0' : '1' + k));
            if (input_pressed(&in, SDL_SCANCODE_SPACE))      type(' ');
            if (input_pressed(&in, SDL_SCANCODE_MINUS))      type('-');
            if (input_pressed(&in, SDL_SCANCODE_APOSTROPHE)) type('\'');
            if (input_pressed(&in, SDL_SCANCODE_BACKSPACE) && ql > 0) { battle_query[--ql] = 0; battle_list_sel = 0; }

            if (battle_n > 0) {
                if (input_pressed(&in, SDL_SCANCODE_UP))
                    battle_list_sel = (battle_list_sel + battle_n - 1) % battle_n;
                if (input_pressed(&in, SDL_SCANCODE_DOWN))
                    battle_list_sel = (battle_list_sel + 1) % battle_n;
                if (input_pressed(&in, SDL_SCANCODE_RETURN)) {
                    delete battle_scene;
                    battle_scene = new BattleScene(&player, battle_hits[battle_list_sel]);
                    state = STATE_BATTLE;
                    battle_list_open = false;
                }
            }
            if (input_pressed(&in, SDL_SCANCODE_ESCAPE)) {
                if (ql > 0) { battle_query[0] = 0; battle_list_sel = 0; }   // first clears the search
                else battle_list_open = false;
            }
        }

        // Advance simulation only while no modal UI is open. UI animations
        // and dialogue typing continue to use dt independently.
        if (!actors_paused()) {
            if ((state == STATE_OVERWORLD || state == STATE_DUNGEON || state == STATE_INTERIOR) &&
                room_t < 0.0f && pre_battle_timer < 0.0f && post_battle_t <= 0.0f)
                player_poison_tick(&player, dt);
            world_advance(dt);
            if (post_battle_t > 0.0f) post_battle_t -= dt;
            drown_t += dt;
            if (state == STATE_DUNGEON && dmap.type == DUNGEON_ENT_OASIS) {
                if (dungeon_breathing(&dmap, &dplayer)) oxygen = SDL_min(1.0f, oxygen + dt * 1.5f);
                else oxygen = SDL_max(0.0f, oxygen - dt / 16.0f);
                if (oxygen > 0.0f) oxy_hurt_t = 0.0f;
                else if ((oxy_hurt_t += dt) >= 2.0f) {
                    oxy_hurt_t -= 2.0f;
                    player.stats.hp = SDL_max(1, player.stats.hp - HP_PER_BAR);
                    drown_t = 0.0f;
                }
            }
            tilemap_update(dt);
        }

        // Block input as well as actor updates while modal UI is open.
        Input in_blank = {0};
        const Input* game_in = (actors_paused() || room_t >= 0.0f)
                                ? &in_blank : &in;
        // Standing on a door, stair or entrance: called every frame the player
        // is on one. Stepping onto it starts the fade, and this is true once
        // the screen is black -- the caller changes rooms then. The player
        // stands still meanwhile, so they are still on it.
        bool on_room = false;
        auto room_taken = [&](bool stairs) {
            on_room = true;
            if (room_t < 0.0f && room_armed) {
                room_armed = false;
                room_t = 0.0f;
                if (stairs && stairs_dev) {
                    SDL_ClearQueuedAudio(stairs_dev);
                    SDL_QueueAudio(stairs_dev, stairs_buf, stairs_len);
                }
            }
            return room_swap;
        };


        // The debug grid's hitboxes. The ways in and out, green: every place
        // the feet's centre takes one and the feet can stand, an art pixel at
        // a time (nothing is finer). The player at (px, py), yellow: the feet box, which is what
        // meets the ground and the ways, and the middle of the frame, which is
        // what an actor is touched with.
        auto draw_hitboxes = [&](const Camera* c, float px, float py, auto way) {
            const float S = 2.0f;
            SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(plat.renderer, 0, 255, 0, 150);
            float xa = floorf(c->x / S) * S, xb = c->x + c->screen_w / c->zoom;
            float ya = floorf(c->y / S) * S, yb = c->y + c->screen_h / c->zoom;
            for (float y = ya; y < yb; y += S)
                for (float x = xa; x < xb; x += S) {
                    if (!way(x + 1, y + 1)) continue;
                    float e = x + S;
                    while (e < xb && way(e + 1, y + 1)) e += S;        // one rect a run
                    SDL_Rect r = { cam_px(c, x), cam_py(c, y), cam_px(c, e) - cam_px(c, x),
                                   cam_py(c, y + S) - cam_py(c, y) };
                    SDL_RenderFillRect(plat.renderer, &r);
                    x = e;
                }
            SDL_Rect feet = { cam_px(c, px + HB_X1), cam_py(c, py + HB_Y1),
                              cam_px(c, px + HB_X2) - cam_px(c, px + HB_X1),
                              cam_py(c, py + HB_Y2) - cam_py(c, py + HB_Y1) };
            SDL_SetRenderDrawColor(plat.renderer, 255, 255, 0, 255);
            SDL_RenderDrawRect(plat.renderer, &feet);
            int mx = cam_px(c, px + player.width * 0.5f), my = cam_py(c, py + player.height * 0.5f);
            SDL_RenderDrawLine(plat.renderer, mx - 3, my, mx + 3, my);
            SDL_RenderDrawLine(plat.renderer, mx, my - 3, mx, my + 3);
        };
        // An actor's, magenta: the ring ACTOR_TOUCH round it that the middle of
        // the player's frame has to come inside.
        auto draw_actor_hitbox = [&](const Camera* c, float ax, float ay) {
            SDL_SetRenderDrawColor(plat.renderer, 255, 0, 255, 255);
            SDL_Point ring[33];
            for (int i = 0; i <= 32; i++)
                ring[i] = { cam_px(c, ax + ACTOR_TOUCH * cosf(i * 6.2831853f / 32)),
                            cam_py(c, ay + ACTOR_TOUCH * sinf(i * 6.2831853f / 32)) };
            SDL_RenderDrawLines(plat.renderer, ring, 33);
        };

        if (debug && input_pressed(&in, SDL_SCANCODE_B) && !dbg_open && !menu.open && state != STATE_BATTLE) {
            delete battle_scene;
            battle_scene = new BattleScene(&player, 0);
            state = STATE_BATTLE;
        }

        // Mouse wheel steps through pixel-perfect zoom levels
        // scroll up (+y) = zoom in = higher index; scroll down = zoom out = lower index
        if (in.mouse_wheel != 0 && state != STATE_BATTLE && !menu.open && !(map_open && !debug)) {
            zoom_idx += in.mouse_wheel;
            if (zoom_idx < zoom_min) zoom_idx = zoom_min;
            if (zoom_idx > zoom_max) zoom_idx = zoom_max;
            cam.zoom = zoom_levels[zoom_idx];
        }

        // Q / E swap weapons on the map and in dungeons too (battle does its
        // own, in BattleScene::_cycle).
        ow_swap_t += dt;
        if ((state == STATE_OVERWORLD || state == STATE_DUNGEON) && !actors_paused())
            for (int dir : { -1, 1 })
                if (input_pressed(&in, dir < 0 ? SDL_SCANCODE_Q : SDL_SCANCODE_E)) {
                    player.equipped = owned_neighbour(&player, dir);
                    ow_swap_t = 0.0f;   // the box shows even with only one weapon
                }

        // Interactions keep their original input; movement/weapon updates get
        // a copy with attack keys removed whenever a prompt is in reach.
        Input world_input = *game_in;
        bool interaction_near = false;
        bool chest_prompt = false;
        if (state == STATE_OVERWORLD || state == STATE_DUNGEON || state == STATE_INTERIOR) {
            float px = state == STATE_OVERWORLD ? ow.x : state == STATE_DUNGEON ? dplayer.x : iplayer.x;
            float py = state == STATE_OVERWORLD ? ow.y : state == STATE_DUNGEON ? dplayer.y : iplayer.y;
            float fx = px + (HB_X1 + HB_X2) * 0.5f, fy = py + (HB_Y1 + HB_Y2) * 0.5f;
            auto near = [&](float x, float y, float radius) {
                float dx = fx - x, dy = fy - y;
                if (state == STATE_OVERWORLD) { dx = wrap_dpx(dx); dy = wrap_dpy(dy); }
                return dx * dx + dy * dy < radius * radius;
            };
            int town = state == STATE_INTERIOR ? entered_door : -1;
            StoryWhere where = { state, map, state == STATE_INTERIOR ? imap.id : -1, town, &player, debug };
            StoryNpcPos np[32]; int nn = story_npcs_here(where, np, 32);
            for (int i = 0; i < nn; i++)
            {
                if (!story_npc_can_talk(np[i])) continue;
                float tx, ty;
                story_npc_talk_point(np[i], &tx, &ty);
                interaction_near |= near(tx, ty, 40);
            }
            StoryNotePos ns[16]; int count = story_notes_here(where, state == STATE_DUNGEON ? &dmap : nullptr, ns, 16);
            for (int i = 0; i < count; i++) interaction_near |= near(ns[i].x, ns[i].y, 40);
            bool confirm = input_pressed(game_in, SDL_SCANCODE_Z) || input_pressed(game_in, SDL_SCANCODE_RETURN) || input_pressed(game_in, SDL_SCANCODE_SPACE);
            if (!interaction_near && game_in == &in && pre_battle_timer < 0.0f) {
                if (state == STATE_OVERWORLD) chest_prompt = tilemap_interact_chest(map, fx, fy, confirm);
                if (state == STATE_DUNGEON) {
                    for (int i = 0; i < dmap.num_loot; i++) {
                        auto& lo = dmap.loot[i];
                        if (lo.collected || lo.node < 0 || !near((lo.tx + 0.5f) * DMAP_TILE, (lo.ty + 0.5f) * DMAP_TILE, 48)) continue;
                        chest_prompt = true;
                        if (confirm) dmap.dungeon_rocks.nodes[lo.node].alive = 0;
                        break;
                    }
                }
                interaction_near |= chest_prompt;
                if (chest_prompt && confirm) {
                    input_consume(&in, SDL_SCANCODE_Z);
                    input_consume(&in, SDL_SCANCODE_RETURN);
                    input_consume(&in, SDL_SCANCODE_SPACE);
                }
            }
            if (state == STATE_OVERWORLD) {
                int bx, by;
                if (!player.at_sea && story_boat_spot(map, &bx, &by))
                    interaction_near |= near((map->wharf_tip.x + 0.5f) * TILE_SIZE, (map->wharf_tip.y + 0.5f) * TILE_SIZE, 40);
            }
        }
        interaction_near |= dlg_text != nullptr || room_t >= 0.0f;
        if (state == STATE_OVERWORLD) interaction_near |= ow.at_interior_door || ow.at_dungeon_entrance;
        if (state == STATE_DUNGEON) interaction_near |= dplayer.at_entry || dplayer.at_exit || dplayer.at_link >= 0;
        if (interaction_near) {
            world_input.keys[SDL_SCANCODE_Z] = KEY_UP;
            world_input.keys[SDL_SCANCODE_RETURN] = KEY_UP;
            world_input.keys[SDL_SCANCODE_SPACE] = KEY_UP;
            if (state == STATE_OVERWORLD) ow.swing = WeaponSwingState();
            if (state == STATE_DUNGEON) dplayer.swing = WeaponSwingState();
        }

        GameState state_before = state;

        // One persistent 30-minute world day, on the world clock: it stops
        // whenever the world does (actors_paused), and only the maps run it --
        // a battle freezes the day.
        if (!actors_paused() &&
            (state == STATE_OVERWORLD || state == STATE_DUNGEON || state == STATE_INTERIOR)) {
            if (state == STATE_OVERWORLD && post_battle_t <= 0.0f && input_pressed(&in, SDL_SCANCODE_T)) {
                resident_advance_hour(map);
                pickup_note = "1 HOUR LATER";
                pickup_note_t = 1.5f;
                input_consume(&in, SDL_SCANCODE_T);
            }
            resident_tick(map, dt);
        }

        switch (state) {
            case STATE_TITLE:
                fc_draw_color(plat.renderer, 0, 0, 0, 255);
                SDL_RenderClear(plat.renderer);
                break;

            case STATE_OVERWORLD: {
                // Lazy-spawn graveyard resource nodes when player gets within range.
                // Done here (main thread) so resource nodes are never touched by gen thread.
                {
                    const float SPAWN_RANGE = 1000.0f; // pixels
                    float px = ow.x + player.width  * 0.5f;
                    float py = ow.y + player.height * 0.5f;
                    for (int i = 0; i < map->num_dungeon_entrances; i++) {
                        DungeonEntrance* e = &map->dungeon_entrances[i];
                        if (!dungeon_is_graveyard(e->type)) continue;
                        if (e->gravestones_spawned) continue;
                        float ex = (float)(e->x * TILE_SIZE + TILE_SIZE / 2);
                        float ey = (float)(e->y * TILE_SIZE + TILE_SIZE / 2);
                        float ddx = wrap_dpx(px - ex), ddy = wrap_dpy(py - ey);
                        if (ddx*ddx + ddy*ddy < SPAWN_RANGE * SPAWN_RANGE) {
                            // SM hides its entrance under one of a scattered
                            // handful; the two larger scales lay theirs out in
                            // rows across a visible yard.
                            if (e->type == DUNGEON_ENT_GRAVEYARD_SM)
                                tilemap_spawn_graveyard_nodes(map, &resources, i, map_seed);
                            else
                                tilemap_spawn_graveyard_lg_nodes(map, &resources, i, map_seed);
                        }
                    }
                }

                // Oilblooms, on the same lazy rule as the graveyards.
                for (int s = 0; s < OILBLOOM_SITES; s++)
                    if (!oilbloom_done[s])
                        oilbloom_done[s] = tilemap_spawn_oilbloom(map, &resources, map_seed, s,
                            ow.x + player.width * 0.5f, ow.y + player.height * 0.5f);

                HarvestResult harvest = {};
                story_hole_apply(map);   // the ground round the island's cave, once the turn has come
                StoryWhere  ow_where = { STATE_OVERWORLD, map, -1, -1, &player };
                StoryNpcPos ow_npcs[32];
                int         ow_nn = 0, ow_talk = -1;   // who stands out here, and the one in reach
                const char* ow_prompt = nullptr;      // the boat's word, when beside it
                if (pre_battle_timer >= 0.0f) {
                    pre_battle_tick(actors_paused() ? 0.0f : dt, STATE_OVERWORLD);   // a boss site touched: the flashes, the wipe, the fight
                } else {
                    if (!actors_paused()) overworld_update(&ow, &player, &world_input, dt, &resources, map, &cam, dbg_noclip, &harvest);
                    // The story's people out of doors: standing by one, TALK.
                    ow_nn = story_npcs_here(ow_where, ow_npcs, 32);
                    {
                        float fcx = ow.x + (HB_X1 + HB_X2) * 0.5f, fcy = ow.y + (HB_Y1 + HB_Y2) * 0.5f;
                        for (int i = 0; i < ow_nn && !dlg_text; i++) {
                            if (!story_npc_can_talk(ow_npcs[i])) continue;
                            float tx, ty;
                            story_npc_talk_point(ow_npcs[i], &tx, &ty);
                            float ndx = wrap_dpx(fcx - tx), ndy = wrap_dpy(fcy - ty);
                            if (ndx * ndx + ndy * ndy >= 40.0f * 40.0f) continue;
                            ow_talk = i;
                            if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                                input_pressed(game_in, SDL_SCANCODE_Z)      ||
                                input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                                player.facing = facing_toward(-ndx, -ndy);   // the two turn to each other
                                story_npc_face(ow_npcs[i], ndx, ndy);
                                if(const auto* conversation=story_npc_conversation(ow_npcs[i])) {
                                    topic_active=true;topic_npc=ow_npcs[i];topic_where=ow_where;
                                    topic_menu(conversation->prompt);
                                } else say(story_npc_line(ow_npcs[i], ow_where));
                                input_consume(&in, SDL_SCANCODE_Z);
                                input_consume(&in, SDL_SCANCODE_RETURN);
                                input_consume(&in, SDL_SCANCODE_SPACE);
                            }
                            break;
                        }
                    }
                    // The boat at the wharf's tip: SET SAIL from beside it once it
                    // is sound and has a sail; at sea, coming back to the tip docks.
                    {
                        int btx, bty;
                        float fcx = ow.x + (HB_X1 + HB_X2) * 0.5f, fcy = ow.y + (HB_Y1 + HB_Y2) * 0.5f;
                        if (story_boat_spot(map, &btx, &bty)) {
                            float tipx = (map->wharf_tip.x + 0.5f) * TILE_SIZE, tipy = (map->wharf_tip.y + 0.5f) * TILE_SIZE;
                            float tdx = wrap_dpx(fcx - tipx), tdy = wrap_dpy(fcy - tipy), td2 = tdx * tdx + tdy * tdy;
                            if (player.at_sea) {
                                if (td2 > 96.0f * 96.0f) boat_armed = true;
                                else if (boat_armed && td2 < 48.0f * 48.0f && !dlg_text) {
                                    player.at_sea = 0;   // docked: feet on the tip
                                    ow.x = wrap_px(tipx - (HB_X1 + HB_X2) * 0.5f);
                                    ow.y = wrap_py(tipy - (HB_Y1 + HB_Y2) * 0.5f);
                                    pickup_note = "DOCKED"; pickup_note_t = 1.5f;
                                }
                            } else if (td2 < 40.0f * 40.0f && !dlg_text && ow_talk < 0) {
                                bool ready = story_boat_ready(&player);
                                ow_prompt = ready ? "SET SAIL" : (story_flags()->quest & STORY_Q_BOAT_WOOD) ? "NO SAIL" : "NOT SEAWORTHY";
                                if (ready && (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                                              input_pressed(game_in, SDL_SCANCODE_Z)      ||
                                              input_pressed(game_in, SDL_SCANCODE_SPACE))) {
                                    player.at_sea = 1;
                                    boat_armed = false;
                                    ow.x = wrap_px((btx + 0.5f) * TILE_SIZE - (HB_X1 + HB_X2) * 0.5f);
                                    ow.y = wrap_py((bty + 0.5f) * TILE_SIZE - (HB_Y1 + HB_Y2) * 0.5f);
                                    input_consume(&in, SDL_SCANCODE_Z);
                                    input_consume(&in, SDL_SCANCODE_RETURN);
                                    input_consume(&in, SDL_SCANCODE_SPACE);
                                }
                            }
                        }
                    }
                    // The story's bosses stand on the map (src/story.cpp): walk
                    // into one and it fights, once per approach as the dummies.
                    int hit = story_site_touch(map, ow.x + player.width * 0.5f, ow.y + player.height * 0.5f);
                    if (hit < 0) {
                        site_armed = true;
                    } else if (!actors_paused() && site_armed && post_battle_t <= 0.0f && room_t < 0.0f) {
                        site_armed = false;
                        float fx, fy;
                        story_site_flash_at(map, hit, &fx, &fy);
                        battle_queue[0]            = STORY_BOSSES[hit];
                        battle_queue_chaser_idx[0] = -1;
                        flash_entries[0]           = { fx, fy };
                        battle_queue_count = flash_count = 1;
                        battle_queue_idx   = 0;
                        pre_battle_timer   = 0.0f;
                    }
                }
                floattext_spawn_from_harvest(&cur_float, &harvest);
                // A landmark's cache struck open: speech box + menu icons.
                if (int lm = tilemap_take_opened_landmark(); lm >= 0 && lm < map->num_landmarks) {
                    Item icons[CHEST_ICON_MAX]; int counts[CHEST_ICON_MAX], ni = 0;
                    landmark_pay(&player, map->landmarks[lm], map_seed ^ (unsigned)lm * 2654435761u,
                                 icons, counts, &ni);
                    say_chest(icons, counts, ni);
                }

                camera_follow(&cam, ow.x, ow.y, (float)player.width, (float)player.height);

                fc_draw_color(plat.renderer, 10, 10, 20, 255);
                SDL_RenderClear(plat.renderer);
                

                tilemap_draw_base(map, &cam, plat.renderer);
                resource_nodes_draw(&resources, &cam, plat.renderer, tilemap_get_town_tex());
                // Afloat: the raft under the player's feet, the menu's own
                // picture of it at 2x, while their feet are on water.
                {
                    float fx = ow.x + (HB_X1 + HB_X2) * 0.5f, fy = ow.y + (HB_Y1 + HB_Y2) * 0.5f;
                    if (player.raft > 0 && !player.at_sea && tilemap_pixel_water(map, fx, fy)) {
                        int size = (int)(32 * cam.zoom);
                        game_menu_draw_item(&menu, plat.renderer, ITEM_RAFT,
                                            cam_screen_x(&cam, fx) - size / 2,
                                            cam_screen_y(&cam, fy) - size / 2, size);
                    }
                    // The boat: under the boy at sea, else moored off the wharf's
                    // tip. The raft's picture at half again, until a boat is drawn.
                    int btx, bty;
                    if (story_boat_spot(map, &btx, &bty)) {
                        float bx = player.at_sea ? fx : (btx + 0.5f) * TILE_SIZE, by = player.at_sea ? fy : (bty + 0.5f) * TILE_SIZE;
                        int size = (int)(48 * cam.zoom);
                        game_menu_draw_item(&menu, plat.renderer, ITEM_RAFT,
                                            cam_screen_x(&cam, bx) - size / 2,
                                            cam_screen_y(&cam, by) - size / 2, size);
                    }
                }
                story_hole_draw(plat.renderer, &cam, map, false);   // the hole's ring, on the ground
                story_sites_draw(plat.renderer, &cam, map);   // the story's bosses, where they were put
                notes_tick(ow_where, nullptr, &cam, ow.x + (HB_X1 + HB_X2) * 0.5f, ow.y + (HB_Y1 + HB_Y2) * 0.5f,
                           ow_talk < 0 && !ow_prompt && pre_battle_timer < 0.0f, game_in);
                // Town 0's approved residents; village speakers keep their placeholder.
                // The player walks through everyone: whoever's feet are lower is in front.
                auto draw_ow_npcs = [&](bool in_front) {
                    SDL_SetTextureColorMod(player_sprite, 255, 190, 110);
                    for (int i = 0; i < ow_nn; i++) {
                        if ((ow_npcs[i].y > ow.y) != in_front) continue;
                        if (!story_npc_draw(ow_npcs[i], plat.renderer, &cam))
                            player_draw(&player, ow_npcs[i].x, ow_npcs[i].y, &cam, plat.renderer, player_sprite,
                                        story_npc_facing(ow_npcs[i]));
                    }
                    SDL_SetTextureColorMod(player_sprite, 255, 255, 255);
                };
                draw_ow_npcs(false);
                player_draw(&player, ow.x, ow.y, &cam, plat.renderer, player_sprite, ow.swing.body_frame);
                draw_ow_npcs(true);
                for (int i = 0; i < ow_nn; i++)
                    tilemap_draw_over_player(map, &cam, plat.renderer, ow_npcs[i].x, ow_npcs[i].y,
                                             28, 40, ow_npcs[i].y + HB_Y2);
                overworld_draw_swing(&ow, &cam, plat.renderer);
                tilemap_draw_over_player(map, &cam, plat.renderer, ow.x, ow.y,
                                         (float)player.width, (float)player.height, ow.y + HB_Y2);
                resource_nodes_draw_over_player(&resources, &cam, plat.renderer, ow.x, ow.y,
                                                (float)player.width, (float)player.height, ow.y + HB_Y2);
                tilemap_draw_depth(map, &cam, plat.renderer);
                story_hole_draw(plat.renderer, &cam, map, true);    // the portal and its pages, in the air
                if (dbg_grid) {
                    tilemap_draw_debug_grid(map, &cam, plat.renderer);
                    draw_hitboxes(&cam, ow.x, ow.y,
                        [&](float x, float y) { return overworld_entrance_at(map, x, y) &&
                                                      can_occupy(map, x - (HB_X1 + HB_X2) * 0.5f, y - (HB_Y1 + HB_Y2) * 0.5f, tilemap_pixel_solid); });
                    // A house door's is a box of its own, taken when the feet box touches it.
                    SDL_SetRenderDrawColor(plat.renderer, 0, 255, 0, 150);
                    for (int i = 0; i < map->num_doors; i++) {
                        const InteriorDoor& d = map->doors[i];
                        float x0 = d.x * (float)TILE_SIZE, y1 = (d.y + 1) * (float)TILE_SIZE;
                        SDL_Rect r = { cam_screen_x(&cam, x0), cam_screen_y(&cam, y1 - DOOR_STEP),
                                       cam_screen_x(&cam, x0 + d.w * TILE_SIZE) - cam_screen_x(&cam, x0),
                                       cam_screen_y(&cam, y1) - cam_screen_y(&cam, y1 - DOOR_STEP) };
                        SDL_RenderFillRect(plat.renderer, &r);
                    }
                }

                // --- Weapon cooldown bar ---
                {
                    // Same source the swing uses, so the bar always spans the
                    // cooldown this weapon actually sets rather than its raw
                    // fire rate — which several weapons no longer go by.
                    float max_cd = weapon_cooldown_seconds(equipped_weapon(&player));
                    float ready  = (max_cd > 0.0f && ow.swing.tool_cd > 0.0f)
                                 ? 1.0f - ow.swing.tool_cd / max_cd : 1.0f;
                    if (ready < 0.0f) ready = 0.0f;
                    if (ready > 1.0f) ready = 1.0f;
                    const int BAR_W = 160, BAR_H = 5;
                    const int BAR_X = (640 - BAR_W) / 2, BAR_Y = 480 - 12;
                    fc_draw_color(plat.renderer, 40, 40, 40, 200);
                    SDL_Rect track = { BAR_X, BAR_Y, BAR_W, BAR_H };
                    SDL_RenderFillRect(plat.renderer, &track);
                    fc_draw_color(plat.renderer, 255, 220, 0, 255);
                    SDL_Rect fill = { BAR_X, BAR_Y, (int)(BAR_W * ready), BAR_H };
                    SDL_RenderFillRect(plat.renderer, &fill);
                }

                // --- Floating resource text ---
                floattext_update_draw(&cur_float, dt, &cam, plat.renderer);


                if (ow_talk >= 0 && !dlg_text) draw_textbox(plat.renderer, "TALK", 255, 255, 255);
                else if (ow_prompt && !dlg_text) draw_textbox(plat.renderer, ow_prompt, 255, 255, 255);
                battle_veil_draw(&cam);   // a boss site touched: the flashes and the wipe

                // The island's cave, while the pages pour into it: the boy is pushed
                // back off its mouth instead of going in (src/story.cpp).
                if (ow.at_dungeon_entrance && story_hole_blocked() &&
                    story_hole_tile(wrap_x((int)((ow.x + player.width * 0.5f) / TILE_SIZE)), wrap_y((int)((ow.y + player.height - 8.0f) / TILE_SIZE)))) {
                    ow.at_dungeon_entrance = 0;
                    ow.y = wrap_py(ow.y + 12.0f);
                    pickup_note   = "THE PAGES PUSH BACK";
                    pickup_note_t = 1.0f;
                }
                // Dungeon entry — walking onto an entrance goes in.
                if (ow.at_dungeon_entrance) {
                    if (room_taken(true)) {
                        int etx = wrap_x((int)((ow.x + player.width  * 0.5f) / TILE_SIZE));
                        int ety = wrap_y((int)((ow.y + player.height - 8.0f) / TILE_SIZE));

                        // Find the DungeonEntrance record we're standing on.
                        int cur_ent_idx = -1;
                        for (int ci = 0; ci < map->num_dungeon_entrances; ci++) {
                            DungeonEntrance* ce = &map->dungeon_entrances[ci];
                            int stamp = (ce->size == 0) ? 1 : 2;
                            if (etx >= ce->x && etx < ce->x + stamp &&
                                ety >= ce->y && ety < ce->y + stamp) {
                                cur_ent_idx = ci; break;
                            }
                        }

                        // Which dungeon this is, how hard, and where its stairs
                        // come out. One answer with its precedence written down,
                        // in dungeon.cpp where a tool can reach it -- as four
                        // last-writer-wins blocks out here, the partner rule
                        // silently beat the cave-system rule and a mountain
                        // could hide two different caves.
                        DungeonWiring w = dungeon_wiring_for(map, map_seed, cur_ent_idx);

                        dng_entry_portal_x = w.entry_ow_x; dng_entry_portal_y = w.entry_ow_y;
                        dng_exit_portal_x  = w.exit_ow_x;  dng_exit_portal_y  = w.exit_ow_y;
                        int   from_exit     = w.from_exit;
                        float connect_angle = w.connect_angle;
                        int   n_cave_mouth  = w.n_mouths;
                        int   my_mouth      = w.my_mouth;

                        dungeon_want(&dmap, &w);

                        dungeon_generate(&dmap, w.type, w.difficulty, w.seed);
                        current_dng_seed = w.seed;
                        // The lighthouse keeper's bat roosts in the tree it named (src/story.cpp)
                        if (dmap.num_spawners > 0 && story_quest_pin(map, map_seed, w.seed, &player))
                            dmap.spawners[0].enemy_id = 12;
                        // Once Anaye has fallen at its mouth, the island's cave leads to the
                        // swarm: nothing else is inside, only the planet's core (src/story.cpp).
                        if (dmap.num_spawners > 0 && dmap.starter && dmap.type == DUNGEON_ENT_CAVE &&
                            story_stage() >= STORY_OPEN && !story_beaten(100)) {
                            dmap.spawners[0].enemy_id = 100;
                            dmap.num_spawners = 1;
                        }
                        // A treasure is found once: every dungeon of its kind
                        // holds it until the player has picked one up anywhere.
                        for (int li = 0; li < dmap.num_loot; li++)
                            if (dmap.loot[li].item >= 0 && item_found(&player, (Item)dmap.loot[li].item)) {
                                dmap.loot[li].collected = true;        // its chest stands open
                                if (dmap.loot[li].node >= 0) { auto& node = dmap.dungeon_rocks.nodes[dmap.loot[li].node]; node.chest = 2; node.type = RESOURCE_TREE; node.hp = 3; }
                            }
                        {
                            auto exp_it = dungeon_explored_cache.find(current_dng_seed);
                            if (exp_it != dungeon_explored_cache.end())
                                SDL_memcpy(dmap.explored, exp_it->second.data(), DMAP_H * DMAP_W);
                        }

                        // Where the stairs let out. The three cases and the
                        // invariant they keep live in dungeon.cpp, next to the
                        // code that carved the stairs — out here they were
                        // somewhere tools/dngportals.cpp could not check them.
                        if (n_cave_mouth >= 2) {
                            dungeon_bind_cave_mouths(&dmap, w.mouth_ow_x, w.mouth_ow_y,
                                                     n_cave_mouth);
                        } else if (!isnan(connect_angle)) {
                            dungeon_bind_pair(&dmap, connect_angle,
                                              dng_entry_portal_x, dng_entry_portal_y, w.entry_type,
                                              dng_exit_portal_x,  dng_exit_portal_y,  w.exit_type);
                        } else {
                            dungeon_bind_solo(&dmap, dng_entry_portal_x, dng_entry_portal_y);
                        }

                        dungeon_player_init(&dplayer, &player, &dmap, from_exit);
                        // Come in by the mouth you actually used. Otherwise every
                        // way into a mountain drops you at the same chamber and
                        // the cave stops being a route through it.
                        if (n_cave_mouth >= 2 && my_mouth >= 0 &&
                            my_mouth < dmap.num_portals) {
                            dplayer.x = (float)(dmap.portals[my_mouth].tx * DMAP_TILE);
                            dplayer.y = (float)(dmap.portals[my_mouth].ty * DMAP_TILE
                                                + DMAP_TILE / 2 - 24);
                        }
                        dungeon_stand_before_way(&dmap, &dplayer);
                        dng_arrival_x = dplayer.x; dng_arrival_y = dplayer.y;
                        dng_arrival_valid = dungeon_player_fits(&dmap, &dplayer);
                        num_chasers = 0;
                        for (int si = 0; si < dmap.num_spawners && num_chasers < MAX_CHASERS; si++) {
                            DungeonSpawner& sp = dmap.spawners[si];
                            float cx = sp.tx * DMAP_TILE + DMAP_TILE * 0.5f, cy = sp.ty * DMAP_TILE + DMAP_TILE * 0.5f;
                            if (!enemy_flies(sp.enemy_id)) {   // a walker starts where its feet fit the drawn floor
                                float fx = cx - (HB_X1 + HB_X2) * 0.5f, fy = cy - (HB_Y1 + HB_Y2) * 0.5f;
                                unwedge_feet(&dmap, &fx, &fy, dungeon_solid_at);
                                cx = fx + (HB_X1 + HB_X2) * 0.5f; cy = fy + (HB_Y1 + HB_Y2) * 0.5f;
                            }
                            chasers[num_chasers++] = { cx, cy, sp.enemy_id, true, false, 0.0f,
                                                       si % 4, 0.0f, cx, cy, 0.0f, 0.0f, 0.0f, 0.0f };   // ambles set off different ways
                        }
                        state = STATE_DUNGEON;
                        oxygen = 1.0f; oxy_hurt_t = 0.0f;          // a breath at the top of the shaft
                        dplayer.vx = dplayer.vy = 0.0f;
                    }
                }
                // Building door — walking into it enters the interior.
                else if (ow.at_interior_door) {
                    if (room_taken(false)) {
                        const InteriorDoor& d = map->doors[ow.interior_door_idx];
                        entered_door = ow.interior_door_idx;
                        interior_load(&imap, d.interior_id);
                        interior_player_init(&iplayer, &player, &imap);
                        state = STATE_INTERIOR;
                    }
                }


                explore_mark(explored, ow.x, ow.y);
                if (input_pressed(&in, SDL_SCANCODE_M) && !dbg_open && !menu.open)
                    map_open = !map_open;

                if (map_open) {
                    // Test mode sees the whole world; a player sees the
                    // country round them, as far as they have explored it.
                    if (debug) minimap_draw(map, plat.renderer, 640, 480, ow.x, ow.y);
                    else {
                        // Locked on the player; the wheel, or up and down,
                        // zooms it (the world gets neither while it is open).
                        map_zoom += in.mouse_wheel
                                  + (input_pressed(&in, SDL_SCANCODE_UP)   || input_pressed(&in, SDL_SCANCODE_W))
                                  - (input_pressed(&in, SDL_SCANCODE_DOWN) || input_pressed(&in, SDL_SCANCODE_S));
                        if (map_zoom < 0) map_zoom = 0;
                        if (map_zoom > 2) map_zoom = 2;
                        minimap_draw_local(map, plat.renderer, 640, 480, ow.x, ow.y, MAP_PX[map_zoom], explored);
                    }

                    if (debug && in.mouse_left_pressed) {   // click to warp: testing only
                        float wx, wy;
                        if (minimap_click_to_world(640, 480, in.mouse_x, in.mouse_y, &wx, &wy)) {
                            ow.x = wx;
                            ow.y = wy;
                            map_open = false;
                        }
                    }
                }
                break;
            }

            case STATE_BATTLE:
                if (battle_scene) {
                    if (!actors_paused()) battle_scene->update(game_in, dt);
                    battle_scene->draw(plat.renderer, player_sprite);
                    if (battle_scene->is_done()) {
                        {
                            bool victory = battle_scene->get_phase() == BATTLE_PHASE_VICTORY;
                            if (victory) story_mark_beaten(battle_queue[battle_queue_idx]);   // a story boss down: the stage moves
                            float last_x = battle_scene->player_x(), last_y = battle_scene->player_y();
                            delete battle_scene;
                            battle_scene = nullptr;
                            if (victory && battle_queue_idx + 1 < battle_queue_count) {
                                battle_queue_idx++;
                                battle_scene = new BattleScene(&player, battle_queue[battle_queue_idx],
                                                               true, last_x, last_y);
                                battle_scene->set_more_after(battle_queue_idx + 1 < battle_queue_count);
                            } else {
                                post_battle_t = 1.0f;
                                // Re-activate any queued enemies that were never fought.
                                for (int qi = battle_queue_idx + 1; qi < battle_queue_count; qi++) {
                                    int cidx = battle_queue_chaser_idx[qi];
                                    if (cidx >= 0 && cidx < num_chasers)
                                        chasers[cidx].active = true;
                                }
                                battle_queue_count = 0;
                                battle_queue_idx   = 0;
                                state = state_after_battle;
                                state_after_battle = STATE_OVERWORLD;
                            }
                        }
                    }
                }
                break;

            case STATE_DUNGEON: {
                if (!actors_paused() && pre_battle_timer < 0.0f) {
                    HarvestResult dng_harvest = {};
                    dungeon_player_update(&dplayer, &player, &world_input, dt, &dmap, &cam, dbg_noclip, &dng_harvest);
                    floattext_spawn_from_harvest(&cur_float, &dng_harvest);
                    if (dplayer.picked_item >= 0 || dplayer.picked_gold > 0) {
                        Item it = dplayer.picked_item >= 0 ? (Item)dplayer.picked_item : ITEM_GOLD;
                        int  n  = dplayer.picked_item >= 0 ? 1 : dplayer.picked_gold;
                        say_chest(&it, &n, 1);
                    }
                }

                float dpcx = dplayer.x + player.width  * 0.5f;
                float dpcy = dplayer.y + player.height * 0.5f;
                cam.zoom = dmap.type == DUNGEON_ENT_OASIS ? 1.0f : zoom_levels[zoom_idx];   // the oasis is one screen tall
                camera_follow(&cam, dplayer.x, dplayer.y, (float)player.width, (float)player.height);
                dungeon_frame_camera(&dmap, &cam);

                if (pre_battle_timer >= 0.0f) {
                    pre_battle_tick(actors_paused() ? 0.0f : dt, STATE_DUNGEON);
                } else if (actors_paused() || post_battle_t > 0.0f || room_t >= 0.0f) {
                    // Just back from a fight, or on the stairs: everyone holds a beat, so the
                    // next battle can't start before the player can move.
                } else {
                    // Update chasers, EarthBound's way. One ambles until you are inside
                    // the shipped screen (1.0x: 320x240 px either way from you, whatever
                    // the test zoom shows), turns to look and holds 24 frames, then walks
                    // at you in 8 directions, re-aiming every 8 frames, and forgets you
                    // once you are a quarter screen past its edge. Touching any one,
                    // ambling or not, starts the fight.
                    const float TRIGGER_DIST2 = ACTOR_TOUCH * ACTOR_TOUCH;
                    const float SEE_W  = LOGICAL_W * 0.5f, SEE_H  = LOGICAL_H * 0.5f;
                    const float LOSE_W = SEE_W * 1.5f,     LOSE_H = SEE_H * 1.6f;   // EB forgets ~25% W / 30% H past the edge
                    // Chasers are drawn 14px wide; keep their centres this far
                    // apart so a pack never stacks into a single square.
                    const float CHASER_SEP    = 16.0f;

                    auto in_box = [&](const DungeonChaser& c, float w, float h) {
                        return fabsf(dpcx - c.x) <= w && fabsf(dpcy - c.y) <= h;
                    };
                    auto on_lit = [&](const DungeonChaser& c) {
                        int tx = (int)(c.x / DMAP_TILE), ty = (int)(c.y / DMAP_TILE);
                        return tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H && dmap.visible[ty][tx];
                    };
                    // Seen: on screen and in a lit region, so one behind the next
                    // room's wall never locks on.
                    auto sees = [&](const DungeonChaser& c) { return on_lit(c) && in_box(c, SEE_W, SEE_H); };
                    // Where a chaser may stand: a walker's feet are the player's box
                    // (its centre is the box's), asked of the same drawn ground; a
                    // flier only has to be on the map.
                    auto fits = [&](const DungeonChaser& c, float wx, float wy) {
                        if (enemy_flies(c.enemy_id))
                            return wx >= 0 && wx < DMAP_W * DMAP_TILE && wy >= 0 && wy < DMAP_H * DMAP_TILE;
                        return can_occupy(&dmap, wx - (HB_X1 + HB_X2) * 0.5f, wy - (HB_Y1 + HB_Y2) * 0.5f, dungeon_solid_at);
                    };
                    // A step of (dx, dy): a walker slides along walls as the player does.
                    auto step = [&](DungeonChaser& c, float dx, float dy) {
                        if (enemy_flies(c.enemy_id)) {
                            if (!fits(c, c.x + dx, c.y + dy)) return false;
                            c.x += dx; c.y += dy;
                            return true;
                        }
                        float fx = c.x - (HB_X1 + HB_X2) * 0.5f, fy = c.y - (HB_Y1 + HB_Y2) * 0.5f;
                        bool moved = move_feet(&dmap, &fx, &fy, dx, dy, dungeon_solid_at);
                        c.x = fx + (HB_X1 + HB_X2) * 0.5f; c.y = fy + (HB_Y1 + HB_Y2) * 0.5f;
                        return moved;
                    };

                    for (int ci = 0; ci < num_chasers; ci++) {
                        DungeonChaser& ch = chasers[ci];
                        if (!ch.active) continue;

                        // Lost you: it ambles where it stands.
                        if (ch.chasing && !(on_lit(ch) && in_box(ch, LOSE_W, LOSE_H))) {
                            ch.chasing = false;
                            ch.ax = ch.x; ch.ay = ch.y;
                        }

                        float cdx = dpcx - ch.x, cdy = dpcy - ch.y;
                        float dist2 = cdx*cdx + cdy*cdy;

                        if (dist2 < TRIGGER_DIST2) {
                            ch.active = false;

                            // Snapshot queue: touching enemy first, then up to 2 nearest
                            // other chasers that can see the player.
                            battle_queue_count = 0;
                            battle_queue_idx   = 0;
                            battle_queue_chaser_idx[0] = battle_queue_chaser_idx[1] = battle_queue_chaser_idx[2] = -1;
                            battle_queue[battle_queue_count++] = ch.enemy_id;
                            flash_entries[0] = { ch.x, ch.y, ch.enemy_id, ch.face };

                            struct { float d2; int enemy_id; int idx; } cands[MAX_CHASERS];
                            int nc = 0;
                            for (int cj = 0; cj < num_chasers; cj++) {
                                if (cj == ci) continue;
                                DungeonChaser& o = chasers[cj];
                                if (!o.active || !o.chasing || !sees(o)) continue;
                                float odx = dpcx - o.x, ody = dpcy - o.y;
                                cands[nc++] = { odx*odx + ody*ody, o.enemy_id, cj };
                            }
                            for (int a = 1; a < nc; a++) {
                                auto tmp = cands[a];
                                int b = a - 1;
                                while (b >= 0 && cands[b].d2 > tmp.d2) { cands[b+1] = cands[b]; b--; }
                                cands[b+1] = tmp;
                            }
                            for (int k = 0; k < nc && battle_queue_count < 3; k++) {
                                const DungeonChaser& o = chasers[cands[k].idx];
                                flash_entries[battle_queue_count] = { o.x, o.y, o.enemy_id, o.face };
                                battle_queue_chaser_idx[battle_queue_count] = cands[k].idx;
                                battle_queue[battle_queue_count++] = cands[k].enemy_id;
                                chasers[cands[k].idx].active = false;
                            }

                            // Clear every other active chaser that can see the player,
                            // not just the ones joining this fight, so finishing this
                            // encounter doesn't immediately chain into another one with
                            // whoever else was standing nearby.
                            for (int cj = 0; cj < num_chasers; cj++) {
                                if (cj == ci) continue;
                                DungeonChaser& o = chasers[cj];
                                if (o.active && sees(o)) o.active = false;
                            }

                            flash_count       = battle_queue_count;
                            pre_battle_timer  = 0.0f;
                            break;
                        }

                        float sp = chase_tick(ch, sees(ch), cdx, cdy, dt, fits);
                        if (!ch.chasing || ch.aggro_timer > 0.0f) continue;
                        // The leg, blended with a short-range push away from any other
                        // chaser it is crowding, so they flow around each other instead
                        // of merging.
                        float mvx = ch.hx, mvy = ch.hy;
                        for (int cj = 0; cj < num_chasers; cj++) {
                            if (cj == ci) continue;
                            const DungeonChaser& o = chasers[cj];
                            if (!o.active) continue;
                            float sx = ch.x - o.x, sy = ch.y - o.y;
                            float sd2 = sx*sx + sy*sy;
                            if (sd2 >= CHASER_SEP * CHASER_SEP) continue;
                            if (sd2 < 0.0001f) { sx = 1.0f; sy = 0.0f; sd2 = 1.0f; }
                            float sd = sqrtf(sd2);
                            float w  = (CHASER_SEP - sd) / CHASER_SEP;  // 1 when coincident
                            mvx += (sx / sd) * w * 1.5f;
                            mvy += (sy / sd) * w * 1.5f;
                        }
                        float mvl = sqrtf(mvx*mvx + mvy*mvy);
                        if (mvl > 0.0001f) { mvx /= mvl; mvy /= mvl; }

                        step(ch, mvx * sp * dt, mvy * sp * dt);
                    }

                    // Hard separation: push overlapping pairs apart until nothing
                    // overlaps, so what gets drawn this frame never shows two
                    // chasers merged. This is a relaxation, and one sweep only
                    // propagates a correction one link along a chain -- a pack
                    // crammed into a corridor needs many sweeps to spread out, so
                    // the cap is high and the loop exits as soon as it is clean.
                    // In the common case (nothing touching) that costs one sweep.
                    if (pre_battle_timer < 0.0f) {
                        // Slide per-axis, so a corridor wall blocking one
                        // component doesn't discard the whole correction.
                        auto shove = [&](DungeonChaser& C, float dx, float dy) {
                            if (fits(C, C.x + dx, C.y + dy)) {
                                C.x += dx; C.y += dy; return true;
                            }
                            bool moved = false;
                            if (dx != 0.0f && fits(C, C.x + dx, C.y)) { C.x += dx; moved = true; }
                            if (dy != 0.0f && fits(C, C.x, C.y + dy)) { C.y += dy; moved = true; }
                            return moved;
                        };

                        for (int pass = 0; pass < 32; pass++) {
                            bool overlapped = false;
                            for (int a = 0; a < num_chasers; a++) {
                                if (!chasers[a].active) continue;
                                for (int b = a + 1; b < num_chasers; b++) {
                                    if (!chasers[b].active) continue;
                                    DungeonChaser& A = chasers[a];
                                    DungeonChaser& B = chasers[b];
                                    float sx = B.x - A.x, sy = B.y - A.y;
                                    float d2 = sx*sx + sy*sy;
                                    if (d2 >= CHASER_SEP * CHASER_SEP) continue;
                                    overlapped = true;
                                    float d = sqrtf(d2);
                                    if (d < 0.0001f) {
                                        // Coincident: vary the direction by index so
                                        // a whole stack doesn't unfold along one axis.
                                        float ang = (float)((a * 7 + b) % 16) / 16.0f * 6.28318f;
                                        sx = cosf(ang); sy = sinf(ang); d = 1.0f;
                                    }
                                    float ux = sx / d, uy = sy / d;
                                    float half = (CHASER_SEP - d) * 0.5f;
                                    bool a_moved = shove(A, -ux * half, -uy * half);
                                    bool b_moved = shove(B,  ux * half,  uy * half);
                                    // Whatever one side couldn't take, give to the other.
                                    if (!a_moved) shove(B,  ux * half,  uy * half);
                                    if (!b_moved) shove(A, -ux * half, -uy * half);
                                }
                            }
                            if (!overlapped) break;
                        }
                    }
                }
                if (state == STATE_BATTLE) break;

                // Background matches wall colour so map edges blend in
                fc_draw_color(plat.renderer, 5, 5, 8, 255);
                SDL_RenderClear(plat.renderer);

                SDL_Rect drown_vp;
                hurt_shake_begin(plat.renderer, drown_t, &drown_vp);     // drowning: hurt as a fight shows it
                dungeon_draw(&dmap, &dplayer, &cam, plat.renderer);
                if (dbg_grid) {
                    dungeon_draw_debug_grid(&dmap, &cam, plat.renderer);
                    draw_hitboxes(&cam, dplayer.x, dplayer.y,
                        [&](float x, float y) { return dungeon_way_at(&dmap, x, y) >= 0 &&
                                                      can_occupy(&dmap, x - (HB_X1 + HB_X2) * 0.5f, y - (HB_Y1 + HB_Y2) * 0.5f, dungeon_solid_at); });
                    for (int ci = 0; ci < num_chasers; ci++)
                        if (chasers[ci].active) draw_actor_hitbox(&cam, chasers[ci].x, chasers[ci].y);
                }
                {
                    StoryWhere dw = { STATE_DUNGEON, map, -1, -1, &player };
                    notes_tick(dw, &dmap, &cam, dplayer.x + (HB_X1 + HB_X2) * 0.5f, dplayer.y + (HB_Y1 + HB_Y2) * 0.5f,
                               pre_battle_timer < 0.0f && post_battle_t <= 0.0f, game_in);
                }
                if (!dungeon_draw_swimmer(&dmap, &dplayer, &player, &cam, plat.renderer))
                    player_draw(&player, dplayer.x, dplayer.y, &cam, plat.renderer, player_sprite, dplayer.swing.body_frame);
                dungeon_draw_front(&dmap, &dplayer, &cam, plat.renderer);
                dungeon_draw_swing(&dplayer, &cam, plat.renderer);

                // --- Floating resource text ---
                floattext_update_draw(&cur_float, dt, &cam, plat.renderer);

                // Draw active chasers
                for (int ci = 0; ci < num_chasers; ci++) {
                    if (chasers[ci].active) draw_chaser(&cam, chasers[ci]);
                }
                hurt_shake_end(plat.renderer, &drown_vp);
                hurt_flash(plat.renderer, drown_t, 640, 480);

                battle_veil_draw(&cam);

                // The catacombs' holes and ladders, taken by walking onto them.
                if (dungeon_link_name(&dmap, &dplayer)) {
                    if (room_taken(true)) {
                        dungeon_take_link(&dmap, &dplayer);
                        camera_follow(&cam, dplayer.x, dplayer.y, (float)player.width, (float)player.height);
                    }
                }

                // DNG_ENTRY tile — exit back to the overworld entrance we came from.
                if (dplayer.at_entry) {
                    if (room_taken(true)) {
                        dungeon_explored_cache[current_dng_seed].assign(
                            &dmap.explored[0][0], &dmap.explored[0][0] + DMAP_H * DMAP_W);
                        // Leave by the portal walked into. A cave has one
                        // per mouth, so which one you are on is the whole question,
                        // and the old pair of destinations could only answer it for
                        // two. Falls back to the pair when a portal carries no
                        // destination of its own.
                        int land_x = dng_entry_portal_x, land_y = dng_entry_portal_y;
                        if (dplayer.at_way >= 0 && dmap.portals[dplayer.at_way].ow_x >= 0) {
                            land_x = dmap.portals[dplayer.at_way].ow_x;
                            land_y = dmap.portals[dplayer.at_way].ow_y;
                        }
                        overworld_stand_before_entrance(&ow, &player, map, land_x, land_y);
                        state = STATE_OVERWORLD;
                    }
                }

                // DNG_EXIT tile — exit to the connected overworld entrance (or back if none).
                if (dplayer.at_exit) {
                    if (room_taken(true)) {
                        dungeon_explored_cache[current_dng_seed].assign(
                            &dmap.explored[0][0], &dmap.explored[0][0] + DMAP_H * DMAP_W);
                        // Leave by the portal walked into. A cave has one
                        // per mouth, so which one you are on is the whole question,
                        // and the old pair of destinations could only answer it for
                        // two. Falls back to the pair when a portal carries no
                        // destination of its own.
                        int land_x = dng_exit_portal_x, land_y = dng_exit_portal_y;
                        if (dplayer.at_way >= 0 && dmap.portals[dplayer.at_way].ow_x >= 0) {
                            land_x = dmap.portals[dplayer.at_way].ow_x;
                            land_y = dmap.portals[dplayer.at_way].ow_y;
                        }
                        overworld_stand_before_entrance(&ow, &player, map, land_x, land_y);
                        state = STATE_OVERWORLD;
                    }
                }


                if (input_pressed(&in, SDL_SCANCODE_M) && !menu.open)
                    map_open = !map_open;

                if (map_open) {
                    dungeon_minimap_draw(&dmap, &dplayer, plat.renderer, 640, 480, dbg_show_all);

                    if (debug && in.mouse_left_pressed) {   // click to warp: testing only
                        float wx, wy;
                        if (dungeon_minimap_click_to_world(&dmap, 640, 480, in.mouse_x, in.mouse_y,
                                                           dbg_show_all, &wx, &wy)) {
                            dplayer.x = wx;
                            dplayer.y = wy;
                            map_open = false;
                        }
                    }
                }

                // ESC out of a dungeon or a house from anywhere: a test shortcut.
                if (debug && !dbg_open && !menu.open && input_pressed(&in, SDL_SCANCODE_ESCAPE)) {
                    dungeon_explored_cache[current_dng_seed].assign(
                        &dmap.explored[0][0], &dmap.explored[0][0] + DMAP_H * DMAP_W);
                    state = STATE_OVERWORLD;
                }
                break;
            }

            case STATE_INTERIOR: {
                // Interior fills the screen 1:1 — identity camera.
                Camera icam = {};
                icam.zoom = 1.0f;
                icam.screen_w = LOGICAL_W;
                icam.screen_h = LOGICAL_H;

                if (pre_battle_timer >= 0.0f) {
                    pre_battle_tick(actors_paused() ? 0.0f : dt, STATE_INTERIOR);
                    if (state == STATE_BATTLE) break;
                } else if (!actors_paused()) {
                    interior_player_update(&iplayer, &player, game_in, dt, &imap);
                    // Test enemies: they stand on their spots, facing you, each in
                    // its mini (the user: "dont have the enemies move in the
                    // house"). Walk into one and they all fight, as a dungeon pack
                    // does -- the one touched first, then by distance, each
                    // flashing in that order. Armed again once the player is off
                    // all of them.
                    float pcx = iplayer.x + player.width  * 0.5f;
                    float pcy = iplayer.y + player.height * 0.5f;
                    auto d2 = [&](const DungeonChaser& te) {
                        return (pcx - te.x) * (pcx - te.x) + (pcy - te.y) * (pcy - te.y);
                    };
                    int hit = -1;
                    for (int i = 0; i < TEST_N && imap.id == 0; i++)   // the starting house only
                        if (d2(test_ch[i]) < ACTOR_TOUCH * ACTOR_TOUCH) hit = i;
                    if (hit < 0) {
                        test_armed = true;
                    } else if (test_armed && post_battle_t <= 0.0f) {
                        test_armed = false;
                        int order[3] = { 0, 1, 2 };       // a pack is at most 3
                        int n = TEST_N < 3 ? TEST_N : 3;
                        for (int a = 0; a < n; a++)       // nearest first: the touched one leads
                            for (int b = a + 1; b < n; b++)
                                if (d2(test_ch[order[b]]) < d2(test_ch[order[a]]))
                                    { int t = order[a]; order[a] = order[b]; order[b] = t; }
                        for (int q = 0; q < n; q++) {
                            const DungeonChaser& te = test_ch[order[q]];
                            battle_queue[q]            = te.enemy_id;
                            battle_queue_chaser_idx[q] = -1;
                            flash_entries[q]           = { te.x, te.y, te.enemy_id, te.face };
                        }
                        battle_queue_count = flash_count = n;
                        battle_queue_idx   = 0;
                        pre_battle_timer   = 0.0f;
                    }
                }

                fc_draw_color(plat.renderer, 5, 5, 8, 255);
                SDL_RenderClear(plat.renderer);

                interior_draw(&imap, plat.renderer, tilemap_get_town_tex());
                // A debug-only reward chest beside the waking spot.
                if (debug && imap.id == 0) {
                    SDL_Rect src = { (CHEST_COL + (debug_chest_opened ? 1 : 0)) * 16, CHEST_ROW * 16, 16, 16 };
                    SDL_Rect dst = { DEBUG_CHEST_X, DEBUG_CHEST_Y, IMAP_TILE, IMAP_TILE };
                    if (SDL_Texture* sheet = tilemap_get_town_tex())
                        SDL_RenderCopy(plat.renderer, sheet, &src, &dst);
                    float dx = iplayer.x + (HB_X1 + HB_X2) * 0.5f - (DEBUG_CHEST_X + IMAP_TILE * 0.5f);
                    float dy = iplayer.y + (HB_Y1 + HB_Y2) * 0.5f - (DEBUG_CHEST_Y + IMAP_TILE * 0.5f);
                    if (!debug_chest_opened && !dlg_text && pre_battle_timer < 0.0f && dx * dx + dy * dy < 48.0f * 48.0f) {
                        draw_textbox(plat.renderer, "OPEN", 255, 255, 255);
                        if (input_pressed(game_in, SDL_SCANCODE_Z) || input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                            input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                            debug_chest_opened = true;
                            const Item items[] = { ITEM_VINE, ITEM_FEATHER, ITEM_ESSENCE, ITEM_OILBLOOM };
                            const int counts[] = { 3, 2, 1, 1 };
                            for (int i = 0; i < CHEST_ICON_MAX; i++) item_slot(&player, items[i]) += counts[i];
                            say_chest(items, counts, CHEST_ICON_MAX);
                            input_consume(&in, SDL_SCANCODE_Z);
                            input_consume(&in, SDL_SCANCODE_RETURN);
                            input_consume(&in, SDL_SCANCODE_SPACE);
                        }
                    }
                }


                // The story's people in this room (src/story.cpp): the player's
                // own sprite in another colour until they have faces of their own.
                StoryWhere  where = { STATE_INTERIOR, map, imap.id, entered_door, &player, debug };
                StoryNpcPos npcs[4];
                int         nn = story_npcs_here(where, npcs, 4);
                // The player walks through everyone: whoever's feet are lower is in front.
                auto draw_npcs = [&](bool in_front) {
                    SDL_SetTextureColorMod(player_sprite, 255, 190, 110);
                    for (int i = 0; i < nn; i++) {
                        if ((npcs[i].y > iplayer.y) != in_front) continue;
                        if (!story_npc_draw(npcs[i], plat.renderer, &icam))
                            player_draw(&player, npcs[i].x, npcs[i].y, &icam, plat.renderer, player_sprite,
                                        story_npc_facing(npcs[i]));
                        interior_draw_over_player(&imap, plat.renderer, npcs[i].x, npcs[i].y,
                                                  28, 40, npcs[i].y + HB_Y2);
                    }
                    SDL_SetTextureColorMod(player_sprite, 255, 255, 255);
                };
                draw_npcs(false);
                {
                    float nfx = iplayer.x + (HB_X1 + HB_X2) * 0.5f, nfy = iplayer.y + (HB_Y1 + HB_Y2) * 0.5f;
                    bool near_person = false;
                    for (int i = 0; i < nn; i++) {
                        if (!story_npc_can_talk(npcs[i])) continue;
                        float tx, ty;
                        story_npc_talk_point(npcs[i], &tx, &ty);
                        float ndx = nfx - tx, ndy = nfy - ty;
                        if (ndx * ndx + ndy * ndy < 40.0f * 40.0f) near_person = true;
                    }
                    notes_tick(where, nullptr, &icam, nfx, nfy, !near_person && !iplayer.at_exit && pre_battle_timer < 0.0f, game_in);
                }
                for (int i = 0; i < TEST_N && pre_battle_timer < 0.0f && imap.id == 0; i++)   // the flashes draw them; the starting house only
                    draw_chaser(&icam, test_ch[i]);
                player_draw(&player, iplayer.x, iplayer.y, &icam, plat.renderer, player_sprite);
                draw_npcs(true);
                interior_draw_over_player(&imap, plat.renderer, iplayer.x, iplayer.y,
                                          (float)player.width, (float)player.height, iplayer.y + HB_Y2);
                if (dbg_grid) {
                    draw_hitboxes(&icam, iplayer.x, iplayer.y,
                        [&](float x, float y) { return interior_at_exit(&imap, x, y); });   // the whole box, to the wall
                    for (int i = 0; i < TEST_N && imap.id == 0; i++)   // the starting house only
                        draw_actor_hitbox(&icam, test_ch[i].x, test_ch[i].y);
                }
                battle_veil_draw(&icam);

                // The door — out to the overworld, before the house's door.
                if (iplayer.at_exit) {
                    if (room_taken(false)) {
                        // out at the door walked in by: a room is shared by every
                        // village house that opens it, so the room cannot say which
                        if (entered_door >= 0) overworld_stand_before_door_idx(&ow, &player, map, entered_door);
                        else overworld_stand_before_door(&ow, &player, map, imap.id);
                        state = STATE_OVERWORLD;
                    }
                }

                float fcx = iplayer.x + (HB_X1 + HB_X2) * 0.5f;
                float fcy = iplayer.y + (HB_Y1 + HB_Y2) * 0.5f;
                // Standing by one of the story's people: TALK, and what they say
                // for the stage goes up in the speech box.
                for (int i = 0; i < nn && !dlg_text && !iplayer.at_exit; i++) {
                    if (!story_npc_can_talk(npcs[i])) continue;
                    float tx, ty;
                    story_npc_talk_point(npcs[i], &tx, &ty);
                    float ndx = fcx - tx, ndy = fcy - ty;
                    if (ndx * ndx + ndy * ndy >= 40.0f * 40.0f) continue;
                    draw_textbox(plat.renderer, "TALK", 255, 255, 255);
                    if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                        input_pressed(game_in, SDL_SCANCODE_Z)      ||
                        input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                        player.facing = facing_toward(-ndx, -ndy);   // the two turn to each other
                        story_npc_face(npcs[i], ndx, ndy);
                        const char* t = story_npc_line(npcs[i], where);
                        if(const auto* conversation=story_npc_conversation(npcs[i])) {
                            topic_active=true;topic_npc=npcs[i];topic_where=where;
                            topic_menu(conversation->prompt);
                        }
                        else if (const Shop* shop = story_npc_shop(npcs[i]))   // a shopkeeper: what will it be
                            ask(t, { "SHOP", "TALK", "LEAVE" }, [&, shop](int pick) {
                                if (pick == 0) game_menu_open_shop(&menu, shop->stock, shop->n);
                                if (pick == 1) say(shop->chat);
                            });
                        else if (t) say(t);
                        else { dlg_list = 0; dlg_where = where; }   // the debug speaker
                        input_consume(&in, SDL_SCANCODE_Z);
                        input_consume(&in, SDL_SCANCODE_RETURN);
                        input_consume(&in, SDL_SCANCODE_SPACE);
                    }
                    break;
                }

                if (debug && !dbg_open && !menu.open && input_pressed(&in, SDL_SCANCODE_ESCAPE))
                    state = STATE_OVERWORLD;
                break;
            }
        }

        if (chest_prompt && !dlg_text) draw_textbox(plat.renderer, "OPEN", 255, 255, 255);

        // Short pickup flash (docked, raft book, …). Chest loot uses speech below.
        if (pickup_note_t > 0.0f) {
            pickup_note_t -= dt;
            draw_textbox(plat.renderer, pickup_note, 255, 255, 80,
                         state == STATE_BATTLE && battle_scene && battle_scene->textbox_low());
        }
        SDL_Rect dlg_box = {};
        if (dlg_text)
            dlg_box = draw_speech(plat.renderer, dlg_text, dlg_part, dlg_t, &dlg_state, dlg_strike, 0,
                        [&](int line, int x, int y) {
                            if (line < 1 || line > dlg_icon_n) return 0;
                            game_menu_draw_item(&menu, plat.renderer, dlg_icons[line - 1], x, y - 4, 24);
                            return 32;
                        });
        // Its choices, once it has typed out: a panel on the box's top right,
        // the main menu's cursor and yellow.
        if (dlg_text && dlg_choice_n && dlg_state == SPEECH_END) {
            draw_speech_choices(plat.renderer,dlg_box,dlg_choices,dlg_choice_n,dlg_choice);
        }

        // A scene change consumes the key that caused it. The prompts confirm on
        // input_pressed, but the overworld tool swings on input_down, so without
        // this the key is still held on the next frame and the press that walked
        // you out of a dungeon or closed a battle also swings at whatever
        // resource happens to be standing next to the door.
        // Any arrival (a door, a battle ending, a debug warp) starts unarmed.
        if (state != state_before) room_armed = false;
        else if (!on_room)         room_armed = true;

        if (state != state_before) {
            input_consume(&in, SDL_SCANCODE_RETURN);
            input_consume(&in, SDL_SCANCODE_Z);
            input_consume(&in, SDL_SCANCODE_SPACE);
        }

        // ── Top HUD bar, every state ──────────────────────────────────────────
        // Left: health, the stamina meter (the weapon refilling after an
        // attack) and EXP. Right: the enemy's name and health in battle, the
        // zoom slider everywhere else. Drawn last, so it stays up through the
        // battle transitions too.
        {
            float hp = (float)player.stats.hp, max_hp = (float)player.stats.max_hp;
            float stamina = 1.0f;
            const Enemy* foe = nullptr;
            const WeaponSwingState* sw = state == STATE_OVERWORLD ? &ow.swing
                                       : state == STATE_DUNGEON   ? &dplayer.swing : nullptr;
            if (state == STATE_BATTLE && battle_scene) {
                hp      = battle_scene->hud_hp();
                max_hp  = battle_scene->hud_max_hp();
                stamina = battle_scene->hud_stamina();
                foe     = battle_scene->hud_enemy();
            } else if (sw) {
                float cd = weapon_cooldown_seconds(equipped_weapon(&player));
                stamina = cd > 0.0f ? 1.0f - sw->tool_cd / cd : 1.0f;
            }
            if (stamina < 0.0f) stamina = 0.0f;
            if (stamina > 1.0f) stamina = 1.0f;

            fc_draw_color(plat.renderer, 0, 0, 0, 255);
            SDL_Rect hud_bg = {0, 0, 640, ARENA_TOP};
            SDL_RenderFillRect(plat.renderer, &hud_bg);

            draw_text(plat.renderer, "HP", NES_PAD + 2, 7, 1, 255, 255, 255);
            // Health in segments, Zelda II style: one per HP_PER_BAR, green
            // while held, black once lost, in a white box.
            {
                int bars = (int)max_hp / HP_PER_BAR;
                int full = (int)ceilf(hp / HP_PER_BAR);
                fc_draw_color(plat.renderer, 255, 255, 255, 255);
                SDL_Rect box = { 27, 5, bars * 9 + 3, 10 };
                SDL_RenderDrawRect(plat.renderer, &box);
                for (int b = 0; b < bars; b++) {
                    if (b < full) {
                        if (player.poisoned) fc_draw_color(plat.renderer, 183, 74, 220, 255);
                        else fc_draw_color(plat.renderer, 78, 220, 74, 255);
                    }
                    else          fc_draw_color(plat.renderer, 0, 0, 0, 255);
                    SDL_Rect seg = { 29 + b * 9, 7, 8, 6 };
                    SDL_RenderFillRect(plat.renderer, &seg);
                }
            }
            draw_bar(plat.renderer, 28, 17, 110, 5, stamina, 1.0f, 255, 220, 0);
            if (player.poisoned) draw_text(plat.renderer, "POISON", 144, 20, 1, 183, 74, 220);
            char buf[24];
            // Level and EXP, just right of the HP box (it grows a bar a level).
            // In battle the score climbs live with this fight's hits and
            // grazes; levels are only applied when the fight is won.
            int exp_shown = player.stats.exp + ((state == STATE_BATTLE && battle_scene) ? battle_scene->hud_exp() : 0);
            SDL_snprintf(buf, sizeof(buf), "LV%d EXP:%d", player.level, exp_shown);
            draw_text(plat.renderer, buf, 27 + ((int)max_hp / HP_PER_BAR) * 9 + 12, 10, 1, 255, 255, 255);

            // The weapon in hand, in the item menu's own box and pictures: a
            // textbox hanging from the bar, the icon at 2x with ore and name
            // beside it as the menu writes them, and -- with more than one
            // owned -- the previous and next, dimmed, with the keys that reach
            // them in the menu's grey hint style. The outline blinks the menu's
            // selection yellow for a moment after a swap. Shown only then:
            // up for WEAPON_BOX_T after a swap (Q / E), then gone.
            const float WEAPON_BOX_T = 1.5f;
            float swap_t = (state == STATE_BATTLE && battle_scene) ? battle_scene->hud_swap_t() : ow_swap_t;
            if (swap_t < WEAPON_BOX_T) {
                const int WX = 245, WY = 2, WW = 150, WH = 40;
                const Weapon& eq = equipped_weapon(&player);
                if (swap_t < 0.3f && (int)(swap_t * 20.0f) % 2 == 0)
                    draw_nes_panel(plat.renderer, WX, WY, WW, WH, 255, 255, 80);
                else
                    draw_nes_panel(plat.renderer, WX, WY, WW, WH);
                game_menu_draw_weapon(&menu, plat.renderer, eq.type, eq.material, WX + 6, WY + 4, 32);
                draw_text(plat.renderer, weapon_name(eq.type), WX + 44, WY + 10, 1, 252, 252, 252);
                draw_text(plat.renderer, game_menu_ore_name(eq.material), WX + 44, WY + 22, 1, 120, 120, 120);

                int owned_n = 0;
                for (int w = 0; w < WEAPON_COUNT; w++) owned_n += player.owned[w];
                if (owned_n > 1) {
                    int pw = owned_neighbour(&player, -1), nw = owned_neighbour(&player, 1);
                    game_menu_draw_weapon(&menu, plat.renderer, (WeaponType)pw, player.arsenal[pw].material,
                                          WX - 20, WY + 6, 16, 110);
                    game_menu_draw_weapon(&menu, plat.renderer, (WeaponType)nw, player.arsenal[nw].material,
                                          WX + WW + 4, WY + 6, 16, 110);
                    draw_text(plat.renderer, "Q", WX - 16, WY + 26, 1, 120, 120, 120);
                    draw_text(plat.renderer, "E", WX + WW + 8, WY + 26, 1, 120, 120, 120);
                }
            }

            if (state == STATE_BATTLE) {
                if (foe) {
                    const char* nm = foe->name();
                    draw_text(plat.renderer, nm, 600 - text_width(nm, 1), 3, 1, 220, 220, 220);
                    draw_bar(plat.renderer, 420, 14, 180, 8, foe->hp, foe->max_hp, 220, 60, 60);
                }
            } else if (state == STATE_DUNGEON && dmap.type == DUNGEON_ENT_OASIS) {
                // In the oasis the zoom is held, and its air goes where the slider was
                dungeon_draw_oxygen(plat.renderer, oxygen, 452, 6);
            } else {
                // Zoom slider
                const int SL_W  = 120;
                const int SL_X  = 480 - SL_W / 2 + 40;
                const int TRK_Y = 12;
                const int TRK_H = 3;

                fc_draw_color(plat.renderer, 80, 80, 80, 255);
                SDL_Rect track = { SL_X, TRK_Y, SL_W, TRK_H };
                SDL_RenderFillRect(plat.renderer, &track);

                int hx = SL_X + (zoom_idx - zoom_min) * SL_W / (zoom_max - zoom_min);
                fc_draw_color(plat.renderer, 255, 255, 255, 255);
                SDL_Rect fill = { SL_X, TRK_Y, hx - SL_X, TRK_H };
                SDL_RenderFillRect(plat.renderer, &fill);

                for (int i = zoom_min; i <= zoom_max; i++) {
                    int tx = SL_X + (i - zoom_min) * SL_W / (zoom_max - zoom_min);
                    fc_draw_color(plat.renderer, 180, 180, 180, 255);
                    SDL_Rect tick = { tx - 1, TRK_Y - 2, 2, TRK_H + 4 };
                    SDL_RenderFillRect(plat.renderer, &tick);
                }

                fc_draw_color(plat.renderer, 255, 255, 255, 255);
                SDL_Rect knob = { hx - 3, 5, 6, 18 };
                SDL_RenderFillRect(plat.renderer, &knob);
                fc_draw_color(plat.renderer, 0, 0, 0, 255);
                SDL_Rect knob_inner = { hx - 1, 7, 2, 14 };
                SDL_RenderFillRect(plat.renderer, &knob_inner);
            }
        }

        // ── Crafting menu overlay ─────────────────────────────────────────────
        // ── The TAB menu (src/game_menu.cpp) ─────────────────────────────────
        game_menu_draw(&menu, &player, plat.renderer);

        // ── Title screen (play mode) ─────────────────────────────────────────
        if (state == STATE_TITLE) {
            SDL_Renderer* ren = plat.renderer;
            fc_draw_color(ren, 0, 0, 0, 255);
            SDL_Rect all = { 0, 0, 640, 480 };
            SDL_RenderFillRect(ren, &all);
            draw_text(ren, "FOUR CASTLE", (640 - text_width("FOUR CASTLE", 4)) / 2, 96, 4, 252, 252, 252);
            draw_text(ren, "CHRONICLES",  (640 - text_width("CHRONICLES", 4)) / 2, 136, 4, 252, 252, 252);

            bool up   = input_pressed(&in, SDL_SCANCODE_UP)   || input_pressed(&in, SDL_SCANCODE_W);
            bool down = input_pressed(&in, SDL_SCANCODE_DOWN) || input_pressed(&in, SDL_SCANCODE_S);
            bool ok   = input_pressed(&in, SDL_SCANCODE_Z) || input_pressed(&in, SDL_SCANCODE_RETURN) ||
                        input_pressed(&in, SDL_SCANCODE_SPACE);
            bool back = input_pressed(&in, SDL_SCANCODE_X);
            bool fullscreen = (SDL_GetWindowFlags(plat.window) & SDL_WINDOW_FULLSCREEN_DESKTOP) != 0;

            // A new game: the player as they start, at home. Over a save's
            // world it first grows a new one, a frame after LOADING is drawn.
            auto begin_new = [&]() {
                fresh_player();
                resident_reset();
                memset(explored, 0, sizeof(explored));
                place_at_start();
                wake_at_home();
                items_primed = false;
                input_consume(&in, SDL_SCANCODE_RETURN);
                input_consume(&in, SDL_SCANCODE_Z);
                input_consume(&in, SDL_SCANCODE_SPACE);
            };

            const int BX = 220, BY = 220, BW = 200, BH = 120;
            auto row = [&](int i, const char* label, bool on, bool grey) {
                int y = BY + 12 + i * 24;
                if (on) draw_text(ren, GLYPH_CURSOR, BX + 10, y, 2, 255, 255, 80);
                if (grey)    draw_text(ren, label, BX + 28, y, 2, 120, 120, 120);
                else if (on) draw_text(ren, label, BX + 28, y, 2, 255, 255, 80);
                else         draw_text(ren, label, BX + 28, y, 2, 252, 252, 252);
            };

            if (title_loading) {
                draw_text(ren, "LOADING", (640 - text_width("LOADING", 2)) / 2, 260, 2, 252, 252, 252);
                if (title_loading_drawn) {
                    rebuild_world((unsigned int)SDL_GetTicks());
                    title_loading = title_loading_drawn = false;
                    begin_new();
                } else {
                    title_loading_drawn = true;
                }
            } else if (title_page == TPAGE_MAIN) {
                static const char* NAMES[TITLE_COUNT] = { "NEW GAME", "CONTINUE", "OPTIONS", "QUIT" };
                draw_nes_panel(ren, BX, BY, BW, BH);
                for (int i = 0; i < TITLE_COUNT; i++)
                    row(i, NAMES[i], title_sel == i, i == TITLE_CONTINUE && !has_save);
                if (up)   title_sel = (title_sel + TITLE_COUNT - 1) % TITLE_COUNT;
                if (down) title_sel = (title_sel + 1) % TITLE_COUNT;
                if (ok && title_sel == TITLE_NEW) {
                    if (has_save) { title_page = TPAGE_ERASE; title_erase = false; }
                    else          begin_new();
                } else if (ok && title_sel == TITLE_CONTINUE && has_save) {
                    // The world is already the save's (built from its seed at
                    // launch); the player and where they stood come back.
                    player = saved_player;
                    ow.x = saved_x;
                    ow.y = saved_y;
                    items_primed = false;
                    state = STATE_OVERWORLD;
                    input_consume(&in, SDL_SCANCODE_RETURN);
                    input_consume(&in, SDL_SCANCODE_Z);
                    input_consume(&in, SDL_SCANCODE_SPACE);
                } else if (ok && title_sel == TITLE_OPTIONS) {
                    title_page = TPAGE_OPTIONS;
                } else if (ok && title_sel == TITLE_QUIT) {
                    running = false;
                }
            } else if (title_page == TPAGE_OPTIONS) {
                draw_nes_panel(ren, BX - 40, BY, BW + 80, 72);
                char buf[32];
                SDL_snprintf(buf, sizeof(buf), "FULLSCREEN: %s", fullscreen ? "ON" : "OFF");
                draw_text(ren, GLYPH_CURSOR, BX - 30, BY + 12, 2, 255, 255, 80);
                draw_text(ren, buf, BX - 12, BY + 12, 2, 255, 255, 80);
                draw_text(ren, "Z: CHANGE  X: BACK", BX - 12, BY + 44, 1, 120, 120, 120);
                if (ok) SDL_SetWindowFullscreen(plat.window, fullscreen ? 0 : SDL_WINDOW_FULLSCREEN_DESKTOP);
                if (back) title_page = TPAGE_MAIN;
            } else {   // TPAGE_ERASE
                // The save is only replaced by the new game's first SAVE.
                draw_nes_panel(ren, BX - 40, BY, BW + 80, 96);
                draw_text(ren, "START OVER?", BX - 12, BY + 12, 2, 252, 252, 252);
                for (int i = 0; i < 2; i++) {
                    bool on = title_erase == (i == 1);
                    if (on) draw_text(ren, GLYPH_CURSOR, BX - 30, BY + 40 + i * 24, 2, 255, 255, 80);
                    if (on) draw_text(ren, i ? "YES" : "NO", BX - 12, BY + 40 + i * 24, 2, 255, 255, 80);
                    else    draw_text(ren, i ? "YES" : "NO", BX - 12, BY + 40 + i * 24, 2, 252, 252, 252);
                }
                if (up || down) title_erase = !title_erase;
                if (back || (ok && !title_erase)) title_page = TPAGE_MAIN;
                else if (ok) { title_page = TPAGE_MAIN; title_loading = true; }
            }
        }

        // ── Debug menu overlay ───────────────────────────────────────────────
        if (dbg_open) {
            // The TAB menu's windows: the two groups, WORLD and PLAYER, in the
            // command window (A/D switches), the active group's rows in the
            // list, small font, and the keys in the preview box.
            int group = dbg_pos(dbg_sel) >= DBG_PLAYER_AT;
            draw_nes_panel(plat.renderer, CMD_X, CMD_Y, CMD_W, CMD_H);
            draw_nes_panel(plat.renderer, PRE_X, PRE_Y, PRE_W, PRE_H);
            draw_nes_panel(plat.renderer, LST_X, LST_Y, LST_W, LST_H);
            static const char* GROUPS[2] = { "WORLD", "PLAYER" };
            for (int i = 0; i < 2; i++) {
                int y = CMD_Y + 12 + i * 24;
                if (i == group) draw_text(plat.renderer, GLYPH_CURSOR, CMD_X + 10, y, 2, 255, 255, 80);
                if (i == group) draw_text(plat.renderer, GROUPS[i], CMD_X + 28, y, 2, 255, 255, 80);
                else            draw_text(plat.renderer, GROUPS[i], CMD_X + 28, y, 2, 252, 252, 252);
            }
            draw_text(plat.renderer, "DEBUG", CMD_X + 28, CMD_Y + 12 + 2 * 24, 2, 120, 120, 120);
            static const char* KEYS[4] = { "WASD: MOVE", "Q/E: CHANGE", "Z: SELECT", "F2: CLOSE" };
            for (int i = 0; i < 4; i++)
                draw_text(plat.renderer, KEYS[i], PRE_X + 14, PRE_Y + 16 + i * 18, 1, 180, 180, 180);
            draw_text(plat.renderer, GROUPS[group], LST_X + 12, LST_Y + 12, 2, 120, 120, 120);
            auto draw_row = [&](int row, const char* label, bool selected) {
                int pos = dbg_pos(row), right = pos >= DBG_PLAYER_AT;
                if (right != group) return;
                int rx  = LST_X;
                int ry  = LST_Y + 44 + (pos - right * DBG_PLAYER_AT) * 24;
                Uint8 r = selected ? 255 : 180;
                Uint8 g = selected ? 255 : 180;
                Uint8 b = selected ? 80  : 180;
                if (selected)
                    draw_text(plat.renderer, GLYPH_CURSOR, rx + 10, ry, 1, r, g, b);
                draw_text(plat.renderer, label, rx + 22, ry, 1, r, g, b);
            };

            // Row 0: warp target selector
            {
                char name[48], full[80];
                dbg_target_name(dbg_target, name, sizeof(name));
                SDL_snprintf(full, sizeof(full), "WARP: < %s >", name);
                draw_row(0, full, dbg_sel == 0);
            }

            // Row 1: the tour. Before the first press it reads how many of the
            // target this world holds -- a target as narrow as one ore band can
            // legitimately have none, and without that an empty result is
            // indistinguishable from a dead key. Once touring it reads which of
            // them you are standing outside, so you know when you have been
            // round them all.
            {
                char buf[48];
                int  n = dbg_target_list(dbg_target, dbg_list, MAX_DUNGEON_ENTRANCES);
                if (n <= 0)
                    SDL_snprintf(buf, sizeof(buf), "ENTER DUNGEON: NONE FOUND");
                else if (dbg_tour < 0)
                    SDL_snprintf(buf, sizeof(buf), "ENTER DUNGEON: %d FOUND", n);
                else
                    SDL_snprintf(buf, sizeof(buf), "ENTER DUNGEON: %d OF %d",
                                 (dbg_tour % n) + 1, n);
                draw_row(1, buf, dbg_sel == 1);
            }

            draw_row(2, "REGEN MAP", dbg_sel == 2);

            // Row 3: noclip toggle
            {
                const char* nc = dbg_noclip ? "NOCLIP: ON " : "NOCLIP: OFF";
                draw_row(3, nc, dbg_sel == 3);
            }

            // Row 4: show all tiles toggle
            {
                const char* sa = dbg_show_all ? "SHOW ALL: ON " : "SHOW ALL: OFF";
                draw_row(4, sa, dbg_sel == 4);
            }

            // Row 5: equipped weapon selector
            {
                char wbuf[64];
                SDL_snprintf(wbuf, sizeof(wbuf), "WEAPON: < %s >",
                             weapon_name(equipped_weapon(&player).type));
                draw_row(5, wbuf, dbg_sel == 5);
            }

            // Row 6: tile-grid overlay toggle
            {
                const char* gr = dbg_grid ? "GRID: ON " : "GRID: OFF";
                draw_row(6, gr, dbg_sel == 6);
            }

            // Row 7: warp to the seam, and which way the world wraps
            {
                static const char* SIDE[4] = { "W", "E", "N", "S" };
                char sb[64];
                SDL_snprintf(sb, sizeof(sb), "WARP TO SEAM (OCEAN %s, WRAP %s)",
                             SIDE[map->ocean_side & 3],
                             map->wrap_axis == WRAP_X ? "E-W" : "N-S");
                draw_row(7, sb, dbg_sel == 7);
            }

            // Row 8: what the equipped weapon is made of
            {
                char obuf[64];
                SDL_snprintf(obuf, sizeof(obuf), "ORE: < %s >",
                             material_name(equipped_weapon(&player).material));
                SDL_strupr(obuf);   // the menu font has capitals only
                draw_row(8, obuf, dbg_sel == 8);
            }

            // Row 9: give all
            draw_row(9, "GIVE ALL", dbg_sel == 9);
            draw_row(10, "MAX OUT WEAPONS", dbg_sel == 10);
            // Row 11: the story's stage
            {
                char sbuf[48];
                SDL_snprintf(sbuf, sizeof(sbuf), "STORY: < %s >", STORY_STAGE_NAMES[story_stage()]);
                draw_row(11, sbuf, dbg_sel == 11);
            }
            // Row 12: warp to a story place
            {
                char gbuf[64];
                if (dbg_story_go < STORY_BOSS_COUNT)
                    SDL_snprintf(gbuf, sizeof(gbuf), "GO: < BOSS %02d AT %d,%d >", STORY_BOSSES[dbg_story_go],
                                 map->boss_sites[dbg_story_go].x, map->boss_sites[dbg_story_go].y);
                else if (dbg_story_go == STORY_BOSS_COUNT)
                    SDL_snprintf(gbuf, sizeof(gbuf), "GO: < TOWN 1 HALL >");
                else if (dbg_story_go == STORY_BOSS_COUNT + 1)
                    SDL_snprintf(gbuf, sizeof(gbuf), "GO: < VILLAGE 0 >");
                else if (dbg_story_go == STORY_BOSS_COUNT + 2)
                    SDL_snprintf(gbuf, sizeof(gbuf), "GO: < TOWN 1 LIGHTHOUSE >");
                else if (dbg_story_go == STORY_BOSS_COUNT + 3)
                    SDL_snprintf(gbuf, sizeof(gbuf), "GO: < QUEST TREE >");
                else
                    SDL_snprintf(gbuf, sizeof(gbuf), "GO: < WHARF TIP >");
                draw_row(12, gbuf, dbg_sel == 12);
            }

        }

        // ── Debug dialogue list overlay ───────────────────────────────────────
        // As the battle test list; hidden while the line it shows is up.
        if (dlg_list >= 0 && !dlg_text) {
            const int ROW = 20, VIEW = (LST_H - 24) / ROW, n = story_dialogue_count();
            draw_nes_panel(plat.renderer, CMD_X, CMD_Y, CMD_W, CMD_H);
            draw_nes_panel(plat.renderer, PRE_X, PRE_Y, PRE_W, PRE_H);
            draw_nes_panel(plat.renderer, LST_X, LST_Y, LST_W, LST_H);
            draw_text(plat.renderer, "DIALOGUE TEST", CMD_X + 14, CMD_Y + 14, 1, 252, 252, 252);
            char count[24];
            SDL_snprintf(count, sizeof(count), "%d OF %d", dlg_list + 1, n);
            draw_text(plat.renderer, count, CMD_X + 14, CMD_Y + 40, 1, 255, 255, 80);
            static const char* KEYS[3] = { "UP/DN: SELECT", "Z: SHOW", "ESC: CLOSE" };
            for (int i = 0; i < 3; i++)
                draw_text(plat.renderer, KEYS[i], PRE_X + 14, PRE_Y + 16 + i * 18, 1, 180, 180, 180);
            int top = dlg_list - VIEW / 2;
            if (top > n - VIEW) top = n - VIEW;
            if (top < 0)        top = 0;
            for (int i = 0; i < VIEW && top + i < n; i++) {
                int  li  = top + i;
                bool sel = li == dlg_list;
                int  ry  = LST_Y + 12 + i * ROW;
                Uint8 cr = sel ? 255 : 180, cg = sel ? 255 : 180, cb = sel ? 80 : 180;
                if (sel) draw_text(plat.renderer, GLYPH_CURSOR, LST_X + 10, ry, 2, cr, cg, cb);
                const char* lbl;
                bool strike;
                story_dialogue(li, dlg_where, &lbl, &strike);
                int sc = text_width(lbl, 2) <= LST_W - 40 ? 2 : 1;
                draw_text(plat.renderer, lbl, LST_X + 28, ry + (2 - sc) * 4, sc, cr, cg, cb);
            }
        }

        // ── Battle test list overlay ──────────────────────────────────────────
        if (battle_list_open) {
            // The TAB menu's windows: title and search in the command window,
            // the list beside it, the keys in the preview box.
            const int ROW = 20, VIEW = (LST_H - 24) / ROW;
            draw_nes_panel(plat.renderer, CMD_X, CMD_Y, CMD_W, CMD_H);
            draw_nes_panel(plat.renderer, PRE_X, PRE_Y, PRE_W, PRE_H);
            draw_nes_panel(plat.renderer, LST_X, LST_Y, LST_W, LST_H);
            draw_text(plat.renderer, "BATTLE TEST", CMD_X + 14, CMD_Y + 14, 1, 252, 252, 252);

            // The search line, then the filtered list -- all ENEMY_COUNT of
            // them with nothing typed.
            char qline[40];
            SDL_snprintf(qline, sizeof(qline), "FIND:%s_", battle_query);
            draw_text(plat.renderer, qline, CMD_X + 14, CMD_Y + 40, 1, 255, 255, 80);
            static const char* KEYS[5] = { "TYPE: FIND", "UP/DN: SELECT", "ENTER: FIGHT", "ESC: CLEAR", "F3: CLOSE" };
            for (int i = 0; i < 5; i++)
                draw_text(plat.renderer, KEYS[i], PRE_X + 14, PRE_Y + 16 + i * 18, 1, 180, 180, 180);

            int top = battle_list_sel - VIEW / 2;
            if (top > battle_n - VIEW) top = battle_n - VIEW;
            if (top < 0)               top = 0;

            for (int i = 0; i < VIEW; i++) {
                int li = top + i;
                if (li >= battle_n) break;
                int idx = battle_hits[li];
                bool sel = (li == battle_list_sel);
                int ry = LST_Y + 12 + i * ROW;
                Uint8 cr = sel ? 255 : 180, cg = sel ? 255 : 180, cb = sel ? 80 : 180;
                if (sel) draw_text(plat.renderer, GLYPH_CURSOR, LST_X + 10, ry, 2, cr, cg, cb);
                char label[40];
                SDL_snprintf(label, sizeof(label), "%02d  %s", battle_rank[idx], ENEMY_NAMES[idx]);
                // The longest names only fit in the small font.
                int sc = text_width(label, 2) <= LST_W - 40 ? 2 : 1;
                draw_text(plat.renderer, label, LST_X + 28, ry + (2 - sc) * 4, sc, cr, cg, cb);
            }
            if (battle_n == 0)
                draw_text(plat.renderer, "NO MATCH", LST_X + 28, LST_Y + 12, 2, 180, 180, 180);
        }

        if (dbg_readout) {
            float dbg_px = state == STATE_INTERIOR ? iplayer.x : state == STATE_DUNGEON ? dplayer.x : ow.x;
            float dbg_py = state == STATE_INTERIOR ? iplayer.y : state == STATE_DUNGEON ? dplayer.y : ow.y;
            draw_fps(plat.renderer, dt, dbg_px, dbg_py);
            const unsigned long long seconds = (unsigned long long)resident_save().world_seconds;
            char clock[64];
            SDL_snprintf(clock, sizeof(clock), "DAY %llu %02d:%02d:%02d", seconds / 86400 + 1,
                         (int)(seconds / 3600 % 24), (int)(seconds / 60 % 60), (int)(seconds % 60));
            draw_text(plat.renderer, clock, 4, 40, 2, 255, 220, 0);
        }

        if (esc_hold_time > 0.f) {
            const int BAR_W = 80;
            const int BAR_H = 6;
            const int BX = 4, BY = 34;
            draw_text(plat.renderer, "HOLD ESC TO QUIT", BX, BY - 12, 1, 255, 255, 80);
            fc_draw_color(plat.renderer, 60, 60, 60, 255);
            SDL_Rect track = { BX, BY, BAR_W, BAR_H };
            SDL_RenderFillRect(plat.renderer, &track);
            int fill_w = (int)(esc_hold_time / 3.f * BAR_W);
            if (fill_w > BAR_W) fill_w = BAR_W;
            fc_draw_color(plat.renderer, 255, 80, 80, 255);
            SDL_Rect fill = { BX, BY, fill_w, BAR_H };
            SDL_RenderFillRect(plat.renderer, &fill);
        }

        // A door or stair: black over everything, down and back up.
        if (room_t >= 0.0f)
            veil(room_t < BATTLE_FADE_T ? room_t / BATTLE_FADE_T : 2.0f - room_t / BATTLE_FADE_T);

        // The one place the window scale is applied. RenderClear ignores the
        // viewport, so this paints the letterbox bars as well.
        if (frame_tex) {
            SDL_SetRenderTarget(plat.renderer, NULL);
            SDL_RenderSetLogicalSize(plat.renderer, LOGICAL_W, LOGICAL_H);
            fc_draw_color(plat.renderer, 10, 10, 20, 255);
            SDL_RenderClear(plat.renderer);
            SDL_RenderCopy(plat.renderer, frame_tex, NULL, NULL);
        }
        SDL_RenderPresent(plat.renderer);

        // Precise frame cap: sleep most of the wait, spin the last ~1 ms
        {
            Uint64 now = SDL_GetPerformanceCounter();
            if (now < frame_deadline) {
                Uint32 sleep_ms = (Uint32)((frame_deadline - now) * 1000 / PERF_FREQ);
                if (sleep_ms > 1) SDL_Delay(sleep_ms - 1);
                while (SDL_GetPerformanceCounter() < frame_deadline) {}
            }
            frame_deadline += FRAME_TICKS; // next frame target (self-correcting)
        }
    }

    tilemap_cancel_gen();
    game_menu_free(&menu);
    gen_thread.join();
    delete battle_scene;
    delete map;

    //cleanups textures
    story_people_free();
    SDL_DestroyTexture(player_sprite);
    player_sprite = NULL;
    for (SDL_Texture* t : { minis_tex, minis_white }) if (t) SDL_DestroyTexture(t);
    for (SDL_Texture* t : mini_big) if (t) SDL_DestroyTexture(t);
    for (SDL_Texture* t : mini_big_white) if (t) SDL_DestroyTexture(t);

    if (frame_tex) SDL_DestroyTexture(frame_tex);
    frame_tex = NULL;

    tilemap_free_tile_cache();
    if (stairs_dev) SDL_CloseAudioDevice(stairs_dev);
    SDL_FreeWAV(stairs_buf);
    IMG_Quit();
    platform_shutdown(&plat);

    return 0;
}
