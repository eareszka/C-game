// Movement census: how often do the player's aimed shots land, enemy by
// enemy, with the battle's movement rule (BattleScene::_apply_move_rule) off
// and on -- and how fast each moves across the player's line.
//
//   movecensus.exe              every enemy, worst hit rate (rule off) first
//   movecensus.exe <id> [secs]  one enemy, one CSV line
//
// Runs the game's own BattleScene at 60 fps, the clock replaced as in
// tools/battlecensus.cpp. The player stands still at a spot, holds fire
// (auto-aimed, as in play) and can't be hurt; the enemy bleeds evenly over the
// fight so every phase plays, and the player's hits are counted but refunded,
// so both runs see the same fight length. Four players: standing at the
// bottom middle, the lower left, the lower right, and one strafing along the
// bottom at walking pace (enemies that follow the player's side only move
// for that one) -- the hit rate is their average.
// env MR_CAP, MR_BURST, MR_WIN (beat length, 0 none), MR_EVERY, MR_SCALE:
// the "on" run's MoveRule, to try other settings.
// One enemy a process (the enemy RNG can only be xored, never reset): the
// list mode runs itself once per enemy.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <string>
#include <vector>
#include <algorithm>
#include "entity.h"
#include "input.h"
#include "enemy.h"
#define private public
#include "battle.h"
#undef private

static Uint32 g_ms = 0;
extern "C" Uint32 SDL_GetTicks(void) { return g_ms; }
static const float DT = 1.0f / 60.0f;

struct Run { float hit = 0, lat_mean = 0, lat_p90 = 0, over = 0, speed_p90 = 0; };

static MoveRule g_on;   // the settings for the "on" runs

static Run fight(int id, bool rule, float secs, float px, float py, float strafe) {
    g_move_rule = g_on;
    g_move_rule.on = rule;
    float sdir = 1.0f;
    Player player = {0};
    player.level = 1;
    player.stats.max_hp = player.stats.hp = 100000;
    player.arsenal[player.equipped].type = (WeaponType)player.equipped;
    Input in; input_init(&in);
    in.keys[SDL_SCANCODE_Z] = KEY_HELD;
    g_ms = 1234;
    BattleScene bs(&player, id);
    static SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, ARENA_W, ARENA_H, 32, SDL_PIXELFORMAT_RGBA32);
    static SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    bs.draw(ren, nullptr);   // sizes the hitbox from the sheet, as in play
    Enemy* en = bs._enemy;
    while (bs._phase == BATTLE_PHASE_INTRO) { g_ms += 16; bs.update(&in, DT); }
    const float drain = en->max_hp / secs;
    std::vector<float> lats, speeds;
    float lx = en->x, ly = en->y, t = 0.0f;
    int frame = 0;
    bs._ts.shots = bs._ts.shots_hit = 0;
    while (en->is_alive() && t < secs * 1.5f) {
        if (strafe > 0.0f) {   // walk side to side between x 80 and 560
            px += sdir * strafe * DT;
            if ((px > 560.0f && sdir > 0) || (px < 80.0f && sdir < 0)) sdir = -sdir;
        }
        bs._bp.x = px; bs._bp.y = py;
        g_ms = 1234 + (Uint32)(t * 1000.0f);
        en->take_damage(drain * DT);
        bs._update_enemy(DT);
        bs._move_bullets(DT);
        bs._update_player_fire(&in, DT);
        float hp = en->hp;
        bs._check_collisions();
        en->hp = hp;                       // hits counted, not taken
        bs._bp.hp = player.stats.max_hp; bs._bp.iframes = 0.0f;
        if (bs._pierce_wait > 0.0f) bs._pierce_wait -= DT;
        if (bs._enemy_flash > 0.0f) bs._enemy_flash -= DT;
        if (bs._flash_gap   > 0.0f) bs._flash_gap   -= DT;
        if ((frame++ % 6) == 0) bs.draw(ren, nullptr);   // keeps a sprite hitbox's frame current
        float sx = en->x - lx, sy = en->y - ly, st = hypotf(sx, sy);
        if (st < 40.0f) {                  // not a teleport
            float rx = en->x - px, ry = en->y - py, r = hypotf(rx, ry);
            if (r > 1.0f) lats.push_back(fabsf(-sx * ry / r + sy * rx / r) / DT);
            speeds.push_back(st / DT);
        }
        lx = en->x; ly = en->y;
        t += DT;
    }
    Run out;
    out.hit = bs._ts.shots ? 100.0f * bs._ts.shots_hit / bs._ts.shots : 0.0f;
    if (!lats.empty()) {
        float sum = 0; int over = 0;
        for (float v : lats) { sum += v; over += v > g_on.lat_cap + 0.5f; }
        out.lat_mean = sum / lats.size();
        out.over = 100.0f * over / lats.size();
        std::sort(lats.begin(), lats.end());
        out.lat_p90 = lats[lats.size() * 9 / 10];
    }
    if (!speeds.empty()) { std::sort(speeds.begin(), speeds.end()); out.speed_p90 = speeds[speeds.size() * 9 / 10]; }
    return out;
}

static Run spots(int id, bool rule, float secs) {
    const float S[4][3] = { { ARENA_W * 0.5f, ARENA_H - 80.0f, 0.0f }, { 110.0f, ARENA_H - 140.0f, 0.0f },
                            { ARENA_W - 110.0f, ARENA_H - 140.0f, 0.0f }, { ARENA_W * 0.5f, ARENA_H - 80.0f, 160.0f } };
    Run sum;
    for (auto& s : S) {
        Run r = fight(id, rule, secs, s[0], s[1], s[2]);
        sum.hit += r.hit / 4; sum.lat_mean += r.lat_mean / 4; sum.lat_p90 += r.lat_p90 / 4;
        sum.over += r.over / 4; sum.speed_p90 += r.speed_p90 / 4;
    }
    return sum;
}

int main(int argc, char** argv) {
    SDL_SetMainReady();
    if (getenv("MR_CAP"))   g_on.lat_cap      = (float)atof(getenv("MR_CAP"));
    if (getenv("MR_BURST")) g_on.burst        = (float)atof(getenv("MR_BURST"));
    if (getenv("MR_WIN"))   g_on.window_len   = (float)atof(getenv("MR_WIN"));
    if (getenv("MR_EVERY")) g_on.window_every = (float)atof(getenv("MR_EVERY"));
    if (getenv("MR_SCALE")) g_on.window_scale = (float)atof(getenv("MR_SCALE"));
    if (argc >= 2) {
        if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
        IMG_Init(IMG_INIT_PNG);
        int id = atoi(argv[1]);
        float secs = argc > 2 ? (float)atof(argv[2]) : 40.0f;
        Run off = spots(id, false, secs), on = spots(id, true, secs);
        Enemy* e = enemy_create(id);
        printf("%d,%s,%.1f,%.1f,%.0f,%.0f,%.0f,%.0f,%.0f\n", id, e ? e->name() : "?",
               off.hit, on.hit, off.lat_mean, off.lat_p90, on.lat_p90, off.over, off.speed_p90);
        delete e;
        return 0;
    }
    // Every enemy, each in its own process.
    struct Row { int id; std::string name; float off, on, lm, lp, lpon, over, sp; };
    std::vector<Row> rows;
    for (int id = 0; id < ENEMY_COUNT; id++) {
        char cmd[512];
        snprintf(cmd, sizeof cmd, "\"%s\" %d", argv[0], id);
        FILE* p = popen(cmd, "r");
        if (!p) continue;
        char line[512] = {};
        bool got = false;
        while (fgets(line, sizeof line, p)) {
            Row r; char name[128] = {};
            if (sscanf(line, "%d,%127[^,],%f,%f,%f,%f,%f,%f,%f", &r.id, name, &r.off, &r.on, &r.lm, &r.lp, &r.lpon, &r.over, &r.sp) == 9) {
                r.name = name; rows.push_back(r); got = true;
            }
        }
        pclose(p);
        fprintf(stderr, "\r%d/%d%s", id + 1, ENEMY_COUNT, got ? "" : " (no result)");
    }
    fprintf(stderr, "\n");
    std::sort(rows.begin(), rows.end(), [](const Row& a, const Row& b) { return a.off < b.off; });
    printf("%3s  %-22s %7s %7s %6s  %9s %9s %9s %7s\n", "id", "enemy", "hit off", "hit on", "gain",
           "side mean", "side p90", "p90 on", "% over");
    float so = 0, sn = 0;
    for (const Row& r : rows) {
        printf("%3d  %-22s %6.1f%% %6.1f%% %+5.1f  %9.0f %9.0f %9.0f %6.0f%%\n", r.id, r.name.c_str(),
               r.off, r.on, r.on - r.off, r.lm, r.lp, r.lpon, r.over);
        so += r.off; sn += r.on;
    }
    printf("rule: cap %.0f px/s, burst %.0f px, beats %.2f s every %.1f s at %.2fx\n",
           g_on.lat_cap, g_on.burst, g_on.window_len, g_on.window_every, g_on.window_scale);
    if (!rows.empty()) printf("mean hit rate: %.1f%% off, %.1f%% on (%zu enemies)\n", so / rows.size(), sn / rows.size(), rows.size());
    return 0;
}
