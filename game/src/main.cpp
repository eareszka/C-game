#include <stdio.h>
#include <thread>
#include <SDL2/SDL_image.h>

#include "game_state.h"
#include "battle.h"
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

    //SDL_SetWindowFullscreen(plat.window, SDL_WINDOW_FULLSCREEN_DESKTOP);
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    SDL_RenderSetLogicalSize(plat.renderer, 640, 480);

    if (!(IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG)) 
    {
        printf("SDL_image init failed: %s\n", IMG_GetError());
        platform_shutdown(&plat);
        return 1;
    }

    SDL_Texture* player_sprite = IMG_LoadTexture(plat.renderer, "assets/Sprite-0001.png");
    if (!player_sprite) {
        printf("Failed to load sprite: %s\n", IMG_GetError());
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
    float player_spd = 150.0f;
    overworld_init(&ow, start_x, start_y, player_spd, 32, 48);

    Tilemap* map = new Tilemap();
    unsigned int map_seed = (unsigned int)SDL_GetTicks();
    tilemap_build_overworld_phase1(map, map_seed);
    std::thread gen_thread(tilemap_build_overworld_phase2, map, map_seed);

    //initializes resources
    ResourceNodeList resources;
    resource_nodes_init(&resources);

    resource_nodes_add(&resources, RESOURCE_TREE, 160, 160);
    resource_nodes_add(&resources, RESOURCE_ROCK, 256, 128);
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


    while (running) 
    {
        double dt_d = time_delta_seconds();
        float dt = (float)dt_d;

        input_begin_frame(&in);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            input_handle_event(&in, &e);
        }
        if (in.quit) running = false;
        if (input_down(&in, SDL_SCANCODE_ESCAPE)) running = false;

        if (input_pressed(&in, SDL_SCANCODE_B) && state != STATE_BATTLE) {
            // Placeholder encounter — replace with encounter data from overworld
            Enemy enc[2] = {0};
            enc[0].enemy_id        = 0;
            enc[0].stats.max_hp    = 30; enc[0].stats.hp    = 30;
            enc[0].stats.max_spd   = 8;  enc[0].stats.spd   = 8;
            enc[0].stats.max_attack= 10; enc[0].stats.attack= 10;
            enc[0].stats.max_iq    = 4;  enc[0].stats.iq    = 4;
            enc[0].stats.max_luck  = 10; enc[0].stats.luck  = 10;
            enc[1].enemy_id        = 1;
            enc[1].stats.max_hp    = 20; enc[1].stats.hp    = 20;
            enc[1].stats.max_spd   = 12; enc[1].stats.spd   = 12;
            enc[1].stats.max_attack= 7;  enc[1].stats.attack= 7;
            enc[1].stats.max_iq    = 2;  enc[1].stats.iq    = 2;
            enc[1].stats.max_luck  = 15; enc[1].stats.luck  = 15;
            battle_start(&battle, &player, enc, 2);
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
                overworld_update(&ow, &in, dt, &resources);

                float player_cx = ow.x + ow.width * 0.5f;
                float player_cy = ow.y + ow.height * 0.5f;
                camera_center_on(&cam, player_cx, player_cy);

                SDL_SetRenderDrawColor(plat.renderer, 10, 10, 20, 255);
                SDL_RenderClear(plat.renderer);
                

                //draw order
                tilemap_draw(map, &cam, plat.renderer); //tiles
                resource_nodes_draw(&resources, &cam, plat.renderer); //resources
                overworld_draw(&ow, &cam, plat.renderer, player_sprite); //player

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

                if (input_down(&in, SDL_SCANCODE_TAB)) {
                    minimap_draw(map, plat.renderer, 640, 480, ow.x, ow.y);
                    if (in.mouse_left_pressed) {
                        float wx, wy;
                        if (minimap_click_to_world(640, 480, in.mouse_x, in.mouse_y, &wx, &wy)) {
                            ow.x = wx;
                            ow.y = wy;
                        }
                    }
                }
                break;
            }

            case STATE_BATTLE:
                battle_update(&battle, &in, dt);
                battle_draw(&battle, plat.renderer);
                if (battle.phase == BATTLE_PHASE_VICTORY || battle.phase == BATTLE_PHASE_DEFEAT) {
                    if (input_pressed(&in, SDL_SCANCODE_RETURN) || input_pressed(&in, SDL_SCANCODE_Z))
                        state = STATE_OVERWORLD;
                }
                break;
        }

        SDL_RenderPresent(plat.renderer);
    }

    gen_thread.join();
    delete map;

    //cleanups textures
    SDL_DestroyTexture(player_sprite);
    player_sprite = NULL;

    IMG_Quit();
    platform_shutdown(&plat);

    return 0;
}
