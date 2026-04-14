#include <stdio.h>
#include <thread>
#include <SDL2/SDL_image.h>

#include "game_state.h"
#include "battle.h"
#include "dungeon.h"
#include "platform.h"
#include "core.h"
#include "input.h"
#include "overworld.h"
#include "camera.h"
#include "tilemap.h"
#include "resource_node.h"


int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;

    Platform plat;
    if (!platform_init(&plat, "Four Castle Chronicles", 640, 480)) {
        return 1;
    }

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    SDL_RenderSetLogicalSize(plat.renderer, 640, 480);

    if (!(IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG)) 
    {
        printf("SDL_image init failed: %s\n", IMG_GetError());
        platform_shutdown(&plat);
        return 1;
    }

    tilemap_init_tile_cache(plat.renderer);

    SDL_Texture* player_sprite = IMG_LoadTexture(plat.renderer, "assets/Sprite-0001.png");
    if (!player_sprite) {
        printf("Failed to load sprite: %s\n", IMG_GetError());
        tilemap_free_tile_cache();
        IMG_Quit();
        platform_shutdown(&plat);
        return 1;
    }

    GameState state = STATE_OVERWORLD;

    // Placeholder player stats — wire up to a real save/character system later
    Player player = {0};
    player.level             = 1;
    player.stats.max_hp      = 60;  player.stats.hp      = 60;
    player.stats.max_spd     = 10;  player.stats.spd     = 10;
    player.stats.max_attack  = 18;  player.stats.attack  = 18;
    player.stats.max_mag     = 12;  player.stats.mag     = 12;
    player.stats.max_luck    = 30;  player.stats.luck    = 30;
    player.stats.max_iq      = 8;   player.stats.iq      = 8;

    Battle battle;

    Overworld ow;

    float start_x = (MAP_WIDTH  / 2) * TILE_SIZE;
    float start_y = (MAP_HEIGHT / 2) * TILE_SIZE;
    overworld_init(&ow, &player, start_x, start_y);

    Tilemap* map = new Tilemap();
    unsigned int map_seed = (unsigned int)SDL_GetTicks();
    tilemap_build_overworld_phase1(map, map_seed);
    std::thread gen_thread(tilemap_build_overworld_phase2, map, map_seed);

    //initializes resources
    ResourceNodeList resources;
    resource_nodes_init(&resources);

    resource_nodes_add(&resources, RESOURCE_FLOWER, 320, 224);


    Input in = {0};

    // Zoom levels where TILE_SIZE(32) * zoom is always a whole number of pixels
    static const float zoom_levels[] = { 0.25f, 0.5f, 0.75f, 1.0f, 1.5f, 2.0f, 3.0f };
    static const int   zoom_count    = (int)(sizeof(zoom_levels) / sizeof(zoom_levels[0]));
    int zoom_idx = 3; // default: 1.0x

    Camera cam = {0};
    cam.screen_w = 640;
    cam.screen_h = 480;
    cam.zoom = zoom_levels[zoom_idx];

    bool running = true;

    DungeonMap    dmap    = {};
    DungeonPlayer dplayer = {};

    // Portal state: which overworld tiles DNG_ENTRY / DNG_EXIT map back to.
    // Set when entering a dungeon; both default to the entrance tile if there
    // is no connected partner dungeon.
    int dng_entry_portal_x = -1, dng_entry_portal_y = -1;
    int dng_exit_portal_x  = -1, dng_exit_portal_y  = -1;

    // Manual 60 fps frame cap — more consistent than SDL_RENDERER_PRESENTVSYNC on WSL2
    const Uint64 PERF_FREQ      = SDL_GetPerformanceFrequency();
    const Uint64 FRAME_TICKS    = PERF_FREQ / 60;
    Uint64       frame_deadline = SDL_GetPerformanceCounter() + FRAME_TICKS;

    while (running)
    {
        double dt_d = time_delta_seconds();
        if (dt_d > 0.05) dt_d = 0.05; // cap at 50 ms — prevents big jumps on stalled frames
        float dt = (float)dt_d;
        tilemap_update(dt);

        input_begin_frame(&in);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            input_handle_event(&in, &e);
        }
        if (in.quit) running = false;
        if (input_down(&in, SDL_SCANCODE_ESCAPE)) running = false;

        if (input_pressed(&in, SDL_SCANCODE_F11)) {
            Uint32 flags = SDL_GetWindowFlags(plat.window);
            SDL_SetWindowFullscreen(plat.window,
                (flags & SDL_WINDOW_FULLSCREEN_DESKTOP) ? 0 : SDL_WINDOW_FULLSCREEN_DESKTOP);
        }

        if (input_pressed(&in, SDL_SCANCODE_B) && state != STATE_BATTLE) {
            // Placeholder encounter — replace with encounter data from overworld
            Enemy enc = {0};
            enc.stats.max_hp    = 60; enc.stats.hp    = 60;
            enc.stats.max_spd   = 6;  enc.stats.spd   = 6;
            enc.stats.max_attack= 10; enc.stats.attack= 10;
            enc.stats.max_iq    = 5;  enc.stats.iq    = 5;
            enc.stats.max_luck  = 8;  enc.stats.luck  = 8;
            battle_start(&battle, &player, &enc, WEAPON_DAGGER);
            state = STATE_BATTLE;
        }

        // Mouse wheel steps through pixel-perfect zoom levels
        // scroll up (+y) = zoom in = higher index; scroll down = zoom out = lower index
        if (in.mouse_wheel != 0) {
            zoom_idx += in.mouse_wheel;
            if (zoom_idx < 0)           zoom_idx = 0;
            if (zoom_idx >= zoom_count) zoom_idx = zoom_count - 1;
            cam.zoom = zoom_levels[zoom_idx];
        }

        switch (state) {
            case STATE_TITLE:
                SDL_SetRenderDrawColor(plat.renderer, 0, 0, 0, 255);
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
                        if (e->type != DUNGEON_ENT_GRAVEYARD_SM &&
                            e->type != DUNGEON_ENT_GRAVEYARD_LG) continue;
                        if (e->gravestones_spawned) continue;
                        float ex = (float)(e->x * TILE_SIZE + TILE_SIZE / 2);
                        float ey = (float)(e->y * TILE_SIZE + TILE_SIZE / 2);
                        float ddx = px - ex, ddy = py - ey;
                        if (ddx*ddx + ddy*ddy < SPAWN_RANGE * SPAWN_RANGE) {
                            if (e->type == DUNGEON_ENT_GRAVEYARD_SM)
                                tilemap_spawn_graveyard_nodes(map, &resources, i, map_seed);
                            else
                                tilemap_spawn_graveyard_lg_nodes(map, &resources, i, map_seed);
                        }
                    }
                }

                overworld_update(&ow, &player, &in, dt, &resources, map);

                float player_cx = ow.x + player.width * 0.5f;
                float player_cy = ow.y + player.height * 0.5f;
                camera_center_on(&cam, player_cx, player_cy);

                SDL_SetRenderDrawColor(plat.renderer, 10, 10, 20, 255);
                SDL_RenderClear(plat.renderer);
                

                //draw order
                tilemap_draw(map, &cam, plat.renderer); //tiles
                resource_nodes_draw(&resources, &cam, plat.renderer); //resources
                player_draw(&player, ow.x, ow.y, &cam, plat.renderer, player_sprite);

                // --- 8-bit zoom slider (top-center) ---
                {
                    const int SL_W  = 140;
                    const int SL_X  = (640 - SL_W) / 2;
                    const int SL_Y  = 8;
                    const int TRK_H = 4;

                    // Track groove
                    SDL_SetRenderDrawColor(plat.renderer, 60, 60, 60, 255);
                    SDL_Rect track = { SL_X, SL_Y + 5, SL_W, TRK_H };
                    SDL_RenderFillRect(plat.renderer, &track);

                    // Filled portion (left of handle) in dim blue
                    int hx = SL_X + zoom_idx * SL_W / (zoom_count - 1);
                    SDL_SetRenderDrawColor(plat.renderer, 255, 255, 255, 255);
                    SDL_Rect fill = { SL_X, SL_Y + 5, hx - SL_X, TRK_H };
                    SDL_RenderFillRect(plat.renderer, &fill);

                    // Tick mark per zoom level
                    for (int i = 0; i < zoom_count; i++) {
                        int tx = SL_X + i * SL_W / (zoom_count - 1);
                        SDL_SetRenderDrawColor(plat.renderer, 140, 140, 140, 255);
                        SDL_Rect tick = { tx - 1, SL_Y + 3, 2, TRK_H + 4 };
                        SDL_RenderFillRect(plat.renderer, &tick);
                    }

                    // Handle knob (bright yellow, 8-bit chunky pixel)
                    SDL_SetRenderDrawColor(plat.renderer, 255, 220, 0, 255);
                    SDL_Rect knob = { hx - 4, SL_Y, 8, TRK_H + 14 };
                    SDL_RenderFillRect(plat.renderer, &knob);

                }

                // Dungeon entry — show name prompt when standing on an entrance.
                if (ow.at_dungeon_entrance) {
                    static const char* dungeon_names[] = {
                        "CAVE",
                        "RUINS",
                        "GRAVEYARD",
                        "GRAVEYARD",
                        "OASIS",
                        "PYRAMID",
                        "STONEHENGE",
                        "LARGE TREE",
                    };
                    int ci = (int)ow.dungeon_type;
                    if (ci < 0 || ci > 7) ci = 0;
                    const char* name = dungeon_names[ci];

                    // Dark bar at the bottom
                    SDL_SetRenderDrawColor(plat.renderer, 10, 10, 10, 220);
                    SDL_Rect bar = {0, 455, 640, 25};
                    SDL_RenderFillRect(plat.renderer, &bar);

                    // Dungeon name centred, white
                    int nx = (640 - text_width(name, 2)) / 2;
                    draw_text(plat.renderer, name, nx, 459, 2, 255, 255, 255);

                    // Difficulty indicator — thin bar below the text
                    SDL_SetRenderDrawColor(plat.renderer, 40, 40, 40, 255);
                    SDL_Rect diff_track = {0, 476, 640, 4};
                    SDL_RenderFillRect(plat.renderer, &diff_track);
                    SDL_SetRenderDrawColor(plat.renderer, 200, 200, 200, 255);
                    SDL_Rect diff_fill = {0, 476, (int)(640 * ow.dungeon_difficulty), 4};
                    SDL_RenderFillRect(plat.renderer, &diff_fill);

                    if (input_pressed(&in, SDL_SCANCODE_RETURN) ||
                        input_pressed(&in, SDL_SCANCODE_Z)      ||
                        input_pressed(&in, SDL_SCANCODE_SPACE)) {
                        int etx = (int)((ow.x + player.width  * 0.5f) / TILE_SIZE);
                        int ety = (int)((ow.y + player.height - 8.0f) / TILE_SIZE);

                        unsigned int dng_seed = map_seed
                            ^ ((unsigned int)etx * 73856093u)
                            ^ ((unsigned int)ety * 19349663u);

                        // Default: solo dungeon — both portals return to this entrance.
                        dng_entry_portal_x = etx; dng_entry_portal_y = ety;
                        dng_exit_portal_x  = etx; dng_exit_portal_y  = ety;
                        int from_exit = 0;
                        float connect_angle = NAN;

                        // Find the DungeonEntrance record we're standing on.
                        DungeonEntrance* cur_ent = nullptr;
                        for (int ci = 0; ci < map->num_dungeon_entrances; ci++) {
                            DungeonEntrance* ce = &map->dungeon_entrances[ci];
                            int stamp = (ce->size == 0) ? 1 : 2;
                            if (etx >= ce->x && etx < ce->x + stamp &&
                                ety >= ce->y && ety < ce->y + stamp) {
                                cur_ent = ce; break;
                            }
                        }

                        if (cur_ent && cur_ent->partner_idx >= 0) {
                            DungeonEntrance* partner = &map->dungeon_entrances[cur_ent->partner_idx];
                            int ax = cur_ent->x, ay = cur_ent->y;
                            int bx = partner->x, by = partner->y;

                            // Shared, order-independent seed.
                            int minx = ax < bx ? ax : bx, miny = ay < by ? ay : by;
                            int maxx = ax > bx ? ax : bx, maxy = ay > by ? ay : by;
                            dng_seed = map_seed
                                ^ ((unsigned int)minx * 73856093u)
                                ^ ((unsigned int)miny * 19349663u)
                                ^ ((unsigned int)maxx * 83492791u)
                                ^ ((unsigned int)maxy * 31729253u);

                            // Lexicographic order on stamp top-left: lower = DNG_ENTRY side.
                            bool we_are_primary = (ax < bx) || (ax == bx && ay < by);
                            if (we_are_primary) {
                                dng_entry_portal_x = ax;  dng_entry_portal_y = ay;
                                dng_exit_portal_x  = bx;  dng_exit_portal_y  = by;
                                from_exit     = 0;
                                connect_angle = atan2f((float)(by - ay), (float)(bx - ax));
                            } else {
                                dng_entry_portal_x = bx;  dng_entry_portal_y = by;
                                dng_exit_portal_x  = ax;  dng_exit_portal_y  = ay;
                                from_exit     = 1;
                                connect_angle = atan2f((float)(ay - by), (float)(ax - bx));
                            }
                        }

                        dungeon_generate(&dmap, ow.dungeon_type,
                                         ow.dungeon_difficulty, dng_seed);

                        if (!isnan(connect_angle)) {
                            // Connected: orient portals so the underground direction
                            // matches the overworld direction between the two entrances.
                            dungeon_orient_portals(&dmap, connect_angle);
                        } else {
                            // Solo: remove the exit tile; the entry tile is the only way out.
                            dmap.tiles[dmap.exit_y][dmap.exit_x] = DNG_FLOOR;
                        }

                        dungeon_player_init(&dplayer, &player, &dmap, from_exit);
                        state = STATE_DUNGEON;
                    }
                }

                if (input_down(&in, SDL_SCANCODE_TAB)) {
                    minimap_draw(map, plat.renderer, 640, 480, ow.x, ow.y);
                    if (in.mouse_left_pressed) {
                        // SDL_RenderWindowToLogical uses renderer output pixels, but mouse
                        // events are in window-point space (SDL_GetWindowSize). On WSL2 in
                        // fullscreen these can diverge, so compute the transform manually.
                        int win_w, win_h;
                        SDL_GetWindowSize(plat.window, &win_w, &win_h);
                        float scale = (win_w / 640.0f < win_h / 480.0f)
                                      ? win_w / 640.0f : win_h / 480.0f;
                        float vp_x = (win_w - 640.0f * scale) / 2.0f;
                        float vp_y = (win_h - 480.0f * scale) / 2.0f;
                        float lmx = (in.mouse_x - vp_x) / scale;
                        float lmy = (in.mouse_y - vp_y) / scale;
                        float wx, wy;
                        if (minimap_click_to_world(640, 480, (int)lmx, (int)lmy, &wx, &wy)) {
                            ow.x = wx;
                            ow.y = wy;
                        }
                    }
                }
                break;
            }

            case STATE_BATTLE:
                battle_update(&battle, &in, dt);
                battle_draw(&battle, plat.renderer, player_sprite);
                if (battle.phase == BATTLE_PHASE_VICTORY || battle.phase == BATTLE_PHASE_DEFEAT) {
                    if (input_pressed(&in, SDL_SCANCODE_RETURN) || input_pressed(&in, SDL_SCANCODE_Z))
                        state = STATE_OVERWORLD;
                }
                break;

            case STATE_DUNGEON: {
                dungeon_player_update(&dplayer, &player, &in, dt, &dmap);

                float dpcx = dplayer.x + player.width  * 0.5f;
                float dpcy = dplayer.y + player.height * 0.5f;
                camera_center_on(&cam, dpcx, dpcy);

                // Background matches wall colour so map edges blend in
                SDL_SetRenderDrawColor(plat.renderer, 5, 5, 8, 255);
                SDL_RenderClear(plat.renderer);

                dungeon_draw(&dmap, &cam, plat.renderer);
                player_draw(&player, dplayer.x, dplayer.y, &cam, plat.renderer, player_sprite);

                // DNG_ENTRY tile — exit back to the overworld entrance we came from.
                if (dplayer.at_entry) {
                    SDL_SetRenderDrawColor(plat.renderer, 40, 120, 40, 200);
                    SDL_Rect bar = {0, 460, 640, 20};
                    SDL_RenderFillRect(plat.renderer, &bar);
                    const char* lbl = "EXIT";
                    draw_text(plat.renderer, lbl,
                              (640 - text_width(lbl, 2)) / 2, 463, 2, 255, 255, 255);

                    if (input_pressed(&in, SDL_SCANCODE_RETURN) ||
                        input_pressed(&in, SDL_SCANCODE_Z)      ||
                        input_pressed(&in, SDL_SCANCODE_SPACE)) {
                        ow.x = (float)(dng_entry_portal_x * TILE_SIZE);
                        ow.y = (float)(dng_entry_portal_y * TILE_SIZE);
                        state = STATE_OVERWORLD;
                    }
                }

                // DNG_EXIT tile — exit to the connected overworld entrance (or back if none).
                if (dplayer.at_exit) {
                    SDL_SetRenderDrawColor(plat.renderer, 180, 50, 50, 200);
                    SDL_Rect bar = {0, 460, 640, 20};
                    SDL_RenderFillRect(plat.renderer, &bar);

                    if (input_pressed(&in, SDL_SCANCODE_RETURN) ||
                        input_pressed(&in, SDL_SCANCODE_Z)      ||
                        input_pressed(&in, SDL_SCANCODE_SPACE)) {
                        ow.x = (float)(dng_exit_portal_x * TILE_SIZE);
                        ow.y = (float)(dng_exit_portal_y * TILE_SIZE);
                        state = STATE_OVERWORLD;
                    }
                }

                if (input_pressed(&in, SDL_SCANCODE_ESCAPE))
                    state = STATE_OVERWORLD;
                break;
            }
        }

        draw_fps(plat.renderer, dt);
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

    gen_thread.join();
    delete map;

    //cleanups textures
    SDL_DestroyTexture(player_sprite);
    player_sprite = NULL;

    tilemap_free_tile_cache();
    IMG_Quit();
    platform_shutdown(&plat);

    return 0;
}
