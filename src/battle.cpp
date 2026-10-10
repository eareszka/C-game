#include "fc_palette.h"
#include "battle.h"
#include "core.h"
#include "dungeon.h"   // material_color
#include "crafting.h"  // Item, item_slot, part_item
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <filesystem>
#include <string>

static const float PI  = 3.14159265f;
static const float TAU = 6.28318530f;

static const float ENEMY_FLASH_T   = 0.07f;  // seconds the enemy flashes white after a hit
// At most one flash this often: a full-oil weapon lands a hit every few
// frames, and flashing on each would hold the enemy solid white.
static const float ENEMY_FLASH_GAP = 0.2f;
// A piercing shot still inside the enemy strikes again after this long.
static const float PIERCE_REHIT_T  = 0.07f;
// Every shot flies at one speed: the one that crosses the gap the fight opens
// at (player 400, enemy ~160) in BULLET_TRAVEL_T. Fixed, so a shot's pace
// never depends on where it was fired from.
static const float BULLET_TRAVEL_T = 0.48f;

// See battle.h. A halberd at 0.6 a second goes 0.6, 0.83, 1.1 ... 11, 15;
// a dagger at 2.2 a second, 2.4 ... 15 -- each its own same step.
float faster_fire_rate(float base_rate, int level) {
    return base_rate * powf(TOUHOU_FIRE_RATE / base_rate, (float)level / WEAPON_OIL_MAX);
}

// rate x damage = base rate x base damage x FASTER_DPS_AT_MAX ^ (level/max),
// so the damage takes whatever the rate does not.
float faster_damage(float base_rate, float base_damage, int level) {
    return base_damage * powf(FASTER_DPS_AT_MAX * base_rate / TOUHOU_FIRE_RATE,
                              (float)level / WEAPON_OIL_MAX);
}
static const float BULLET_SPEED    = 240.0f / BULLET_TRAVEL_T;
static const float SHOT_FADE       = 0.4f;   // fade-out stretch, as a share of the sprite's reach   // seconds from firing to reaching the enemy



// ── Weapon profiles ───────────────────────────────────────────────────────────

ProjectileProfile weapon_profile(WeaponType type) {
    // {damage, fire_rate, count, spread_deg, radius, pierces}
    // One shot a volley for every weapon; more come from upgrades (not built
    // yet), which fan them across the weapon's spread.
    switch (type) {
        case WEAPON_KNIFE:   return {  8.0f, 1.8f, 1,  0.0f, 3.0f };
        case WEAPON_CLUB:    return { 14.0f, 0.8f, 1,  0.0f, 7.0f };
        case WEAPON_DAGGER:  return {  6.0f, 2.2f, 1,  0.0f, 3.0f };
        case WEAPON_AXE:     return { 18.0f, 0.7f, 1, 60.0f, 5.0f };
        case WEAPON_HALBERD: return { 16.0f, 0.6f, 1,  0.0f, 4.0f, true };
        case WEAPON_KATANA:  return { 13.0f, 1.4f, 1, 15.0f, 4.0f };
        case WEAPON_SCYTHE:  return { 24.0f, 0.9f, 1, 30.0f, 4.0f, true };   // the strongest, by a clear step
        default:             return {  6.0f, 2.2f, 1,  0.0f, 3.0f };
    }
}

const char* weapon_name(WeaponType type) {
    switch (type) {
        case WEAPON_KNIFE:   return "KNIFE";
        case WEAPON_CLUB:    return "CLUB";
        case WEAPON_DAGGER:  return "DAGGER";
        case WEAPON_AXE:     return "AXE";
        case WEAPON_HALBERD: return "HALBERD";
        case WEAPON_KATANA:  return "KATANA";
        case WEAPON_SCYTHE:  return "SCYTHE";
        default:             return "UNKNOWN";
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

// A sheet as plain RGBA32 bytes, for the copies below that edit its pixels;
// null if it will not load.
static SDL_Surface* load_rgba(const char* path) {
    SDL_Surface* raw = IMG_Load(path);
    if (!raw) return nullptr;
    SDL_Surface* s = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_RGBA32, 0);
    SDL_FreeSurface(raw);
    return s;
}

// An .aseprite saved after its PNG is exported first (tools/enemy_sheet.py),
// so art edited in Aseprite shows in the next battle. Only where the tools
// are: a shipped game has neither the .aseprite nor the script.
static void export_if_edited(const char* png) {
    namespace fs = std::filesystem;
    std::error_code ec;
    fs::path ase = fs::path(png).replace_extension(".aseprite");
    if (!fs::exists(ase, ec) || !fs::exists("tools/enemy_sheet.py", ec)) return;
    if (fs::exists(png, ec) && fs::last_write_time(ase, ec) <= fs::last_write_time(png, ec)) return;
    std::string cmd = "python tools/enemy_sheet.py export \"" + ase.string() + "\"";
    if (system(cmd.c_str()) != 0) SDL_Log("enemy sheet %s: could not export its .aseprite", png);
}

// Load a sheet, and the same sheet as a solid white silhouette in *white:
// every opaque pixel turned the palette's white, alpha kept. SDL can only
// darken a texture with a colour mod, so the flash needs its own copy.
static SDL_Texture* load_with_white(SDL_Renderer* ren, const char* path, SDL_Texture** white) {
    *white = nullptr;
    export_if_edited(path);
    SDL_Surface* s = load_rgba(path);
    if (!s) return nullptr;
    SDL_Texture* tex = SDL_CreateTextureFromSurface(ren, s);
    for (int y = 0; y < s->h; y++) {
        Uint8* p = (Uint8*)s->pixels + y * s->pitch;
        for (int x = 0; x < s->w; x++, p += 4)
            p[0] = p[1] = p[2] = 252;
    }
    *white = SDL_CreateTextureFromSurface(ren, s);
    SDL_FreeSurface(s);
    return tex;
}

// Load a sheet, and in fade[i] the same sheet keeping only the pixels whose
// fc_bayer() rank is below 12, 8 and 4: a fade as an ordered dither, the way
// the game does every fade, so no pixel is ever a blend off the palette.
static SDL_Texture* load_with_fades(SDL_Renderer* ren, const char* path, SDL_Texture* fade[3]) {
    SDL_Surface* s = load_rgba(path);
    if (!s) return nullptr;
    SDL_Texture* tex = SDL_CreateTextureFromSurface(ren, s);
    for (int i = 0; i < 3; i++) {
        int keep = 12 - 4 * i;
        for (int y = 0; y < s->h; y++) {
            Uint8* p = (Uint8*)s->pixels + y * s->pitch;
            for (int x = 0; x < s->w; x++, p += 4)
                if (fc_bayer(x, y) >= keep) p[3] = 0;
        }
        fade[i] = SDL_CreateTextureFromSurface(ren, s);   // each step thins the last
    }
    SDL_FreeSurface(s);
    return tex;
}

static bool circles_overlap(float ax, float ay, float ar,
                             float bx, float by, float br) {
    float dx = ax - bx, dy = ay - by, rsum = ar + br;
    return dx*dx + dy*dy < rsum*rsum;
}

// The point of a shot's middle nearest (x, y): its centre, or for a log the
// nearest point of the line it lies along.
static void bullet_nearest(const Bullet& bl, float x, float y, float* nx, float* ny) {
    *nx = bl.x; *ny = bl.y;
    if (bl.half_len <= 0.0f) return;
    float ux = cosf(bl.ang), uy = sinf(bl.ang);
    float t = fminf(fmaxf((x - bl.x) * ux + (y - bl.y) * uy, -bl.half_len), bl.half_len);
    *nx = bl.x + ux * t; *ny = bl.y + uy * t;
}

// An enemy shot touching a circle: round shots as circles, logs as capsules.
static bool bullet_touches(const Bullet& bl, float x, float y, float r) {
    float nx, ny;
    bullet_nearest(bl, x, y, &nx, &ny);
    return circles_overlap(nx, ny, bl.radius, x, y, r);
}

// ── Enemy sprites ─────────────────────────────────────────────────────────────

// Sheets built by tools/build_enemy.py: one row, 8 directions
// (D DR R UR U UL L DL) x `frames` idle frames each. Three frames play in
// `loop` order; more (big creatures, smoother motion) play straight through
// as a cycle, STEP_MS each -- the same timings as the preview GIFs. Enemies past the end of the table have no
// sprite yet and draw as a box.
// flap: an optional sheet played while the enemy moves (Enemy::flap_phase) --
// Qique's wingbeat, the cobra's slither -- laid out like a one-row sheet with
// FLAP_FRAMES frames a direction.
struct EnemySheet { const char* path; Uint8 loop[4]; int frames = 3; bool rows = false;   // rows: one row per direction
                    const char* flap = nullptr;
                    const char* alt  = nullptr;      // alt: the idle in another pose (Enemy::alt_pose), same layout
                    const char* log  = nullptr;      // log: its log bullet, drawn lying flat (BulletSpawn::half_len) --
                    int log_frames   = 1;            // a row of this many frames, rolling, LOG_MS each
                    int log_rows     = 1;            // 3: rows flat / right end up / right end down, stepped 0 1 0 2 to rock
                    const char* marks = nullptr; };  // ground marks (footprints): a row of frames, Enemy::marks picks one
static const int FLAP_FRAMES = 4;   // wings up, mid, down, mid
static const EnemySheet ENEMY_SHEETS[] = {
    { "assets/enemies/00_skvader.png",                {0, 1, 0, 2} },
    { "assets/enemies/01_wolpertinger.png",           {0, 1, 0, 2} },
    { "assets/enemies/02_treesqueak.png",             {0, 1, 0, 2} },
    { "assets/enemies/03_qique.png",                  {0, 1, 0, 2}, 3, false, "assets/enemies/03_qique_flap.png" },
    { "assets/enemies/04_lili.png",                   {0, 1, 2, 1} },  // legs splay out
    { "assets/enemies/05_crowing_crested_cobra.png",  {0, 1, 0, 2}, 3, false, "assets/enemies/05_crowing_crested_cobra_slither.png" },
    { "assets/enemies/06_wakmangganchi_aragondi.png", {0, 1, 0, 2} },
    { "assets/enemies/07_alber.png",                  {0, 1, 0, 2} },
    { "assets/enemies/08_snawfus.png",                {0, 1, 0, 2} },
    { "assets/enemies/09_questing_beast.png",         {0, 1, 0, 2}, 3, false, "assets/enemies/09_questing_beast_walk.png" },
    { "assets/enemies/10_grand_goule.png",            {0, 1, 0, 2} },
    { "assets/enemies/11_paoxiao.png",                {0, 1, 0, 2}, 3, false,
      "assets/enemies/11_paoxiao_leap.png", "assets/enemies/11_paoxiao_closed.png" },
    { "assets/enemies/12_ebigane.png",                {0, 1, 0, 2}, 3, false, "assets/enemies/12_ebigane_fly.png" },
    { "assets/enemies/13_beast_of_the_charred_forests.png", {0, 1, 0, 2} },
    { "assets/enemies/14_lodsilungur.png",            {0, 1, 0, 2} },
    { "assets/enemies/15_ofuguggi.png",               {0, 1, 0, 2}, 3, false, "assets/enemies/15_ofuguggi_swim.png" },  // swim = backwards, tail first
    { "assets/enemies/16_kamaitachi.png",             {0, 1, 0, 2} },
    { "assets/enemies/17_qiqirn.png",                 {0, 1, 0, 2}, 3, false, "assets/enemies/17_qiqirn_run.png" },  // run = its frightened gallop round the edge
    { "assets/enemies/18_vatnaormur.png",             {}, 5 },
    { "assets/enemies/19_skeljaskrimsli.png",         {}, 5 },
    { "assets/enemies/20_sermilik.png",               {}, 5 },
    { "assets/enemies/21_asp.png",                    {0, 1, 0, 2} },
    { "assets/enemies/22_cactus_cat.png",             {0, 1, 0, 2} },
    { "assets/enemies/23_olgoi_khorkhoi.png",         {}, 8 },
    { "assets/enemies/24_zoureg.png",                 {0, 1, 0, 2}, 3, false, nullptr, "assets/enemies/24_zoureg_three.png" },  // alt: head split into three needle heads (phase 2 lasers; its frame is 60x35)
    { "assets/enemies/25_myrmecoleon.png",            {}, 5 },
    { "assets/enemies/26_akhekh.png",                 {0, 1, 0, 2} },
    { "assets/enemies/27_grootslang.png",             {}, 5 },
    { "assets/enemies/28_opimachus.png",              {0, 1, 0, 2} },
    { "assets/enemies/29_karnabo.png",                {0, 1, 0, 2} },
    { "assets/enemies/30_dajna.png",                  {}, 8, true },   // fills the top of the arena: one row per direction
    { "assets/enemies/31_man_eating_boulder.png",     {0, 1, 0, 2} },
    { "assets/enemies/32_angont.png",                 {}, 5 },
    { "assets/enemies/33_tsenagahi.png",              {0, 1, 0, 2} },
    { "assets/enemies/34_anaye.png",                  {}, 8, true },   // giant: one row per direction
    { "assets/enemies/35_lomie.png",                  {0, 1, 0, 2} },
    { "assets/enemies/36_cu_sith.png",                {0, 1, 0, 2} },
    { "assets/enemies/37_celestial_stag.png",         {0, 1, 0, 2} },
    { "assets/enemies/38_igtuk.png",                  {0, 1, 0, 2} },
    { "assets/enemies/39_ajaju.png",                  {0, 1, 0, 2} },
    { "assets/enemies/40_slide_rock_bolter.png",      {}, 5 },
    { "assets/enemies/41_sasnalkahi.png",             {}, 5 },
    { "assets/enemies/42_nykur.png",                  {0, 1, 0, 2} },
    { "assets/enemies/43_sazae_oni.png",              {0, 1, 0, 2} },
    { "assets/enemies/44_itqiirpak.png",              {}, 8, true },   // giant: one row per direction
    { "assets/enemies/45_kusa_kap.png",               {0, 1, 0, 2} },
    { "assets/enemies/46_lusca.png",                  {0, 1, 0, 2} },
    { "assets/enemies/47_moha_moha.png",              {}, 5 },
    { "assets/enemies/48_bjarndyrakongur.png",        {0, 1, 0, 2} },
    { "assets/enemies/49_physeter.png",               {}, 8, true },   // fills the top of the arena: one row per direction
    { "assets/enemies/50_teakettler.png",             {0, 1, 0, 2}, 3, false, "assets/enemies/50_teakettler_walk.png" },  // frame 1: the whistle; walk = backwards
    { "assets/enemies/51_aspidochelone.png",                 {}, 8, true },  // giant, 8 dirs: colossal island turtle, palms and a campfire on its back; frames 3-4 head raised, jaws wide
    { "assets/enemies/52_sannaja.png",                       {}, 8, true },  // biggest enemy (352x224 frames, too big to see whole), 8 dirs: colossal shelled six-legged beast, red spider head, two staring eyes; frames 3-4 the killing gaze
    { "assets/enemies/53_come_at_a_body.png",         {0, 1, 0, 2}, 3, false, "assets/enemies/53_come_at_a_body_dash.png" },  // frame 1: it spits; dash = rush and flight
    { "assets/enemies/54_billdad.png",                {0, 1, 0, 2}, 3, false, "assets/enemies/54_billdad_slap.png" },  // frame 1: the spring; slap (phase 2) = tail hammer, already turned to show its back
    { "assets/enemies/55_wapaloosie.png",             {0, 1, 0, 2}, 3, false, nullptr,
      "assets/enemies/55_wapaloosie_up.png", "assets/enemies/55_wapaloosie_log.png", 8, 3 },                         // frame 1: the inchworm hump; alt: reared up on its back legs
    { "assets/enemies/56_moskitto.png",               {}, 5, false, "assets/enemies/56_moskitto_grab.png" },  // big: always aloft; grab = lunging to snatch
    { "assets/enemies/57_dingbat.png",                {}, 5, false, "assets/enemies/57_dingbat_stare.png", "assets/enemies/57_dingbat_catch.png" },  // big, 6 dirs; alt = catching pose (perched); flap = the stare's wingbeat
    { "assets/enemies/58_agropelter.png",             {}, 5 },         // big: squatting, its long skinny arms flailing
    { "assets/enemies/59_tripodero.png",              {0, 1, 0, 2}, 3, false, "assets/enemies/59_tripodero_walk.png" },  // frame 1: fires a clay slug; walk = big steps left then right
    { "assets/enemies/60_rumptifusel.png",            {}, 5 },         // big: a huge fur pelt, the hood arching; frame 2 reared highest, purple belly bared
    { "assets/enemies/61_roperite.png",               {}, 5 },         // big, 8 dirs: always dashing, rope-snout lasso, rattle tail; frame 2 the lasso flicked out
    { "assets/enemies/62_hugag.png",                  {}, 5, false, "assets/enemies/62_hugag_stomp.png" },  // big, 8 dirs: stilt-legged shaggy beast; frame 2 bellow; flap = big stomping steps, frames 1 and 3 the slams
    { "assets/enemies/63_hidebehind.png",             {0, 1, 0, 2} },  // big, front only (drawn flat to SPRITE_STYLE.md): faceless shaggy fur cone, a fan of hooked claws raised at each side
    { "assets/enemies/64_dungavenhooter.png",         {}, 8 },         // big, 8 dirs, 8 frames: one tail slap looped; frame 6 the impact (dust crown at the club)
    { nullptr },                                                       // 65 Mice That Eat Iron: skipped for now
    { "assets/enemies/66_ayotochtli.png",             {0, 1, 0, 2}, 3, false, "assets/enemies/66_ayotochtli_roll.png" },  // frame 1: hunched into its shell; flap = curled in a ball, rolling
    { "assets/enemies/67_lagopus.png",                {0, 1, 0, 2}, 3, false, "assets/enemies/67_lagopus_fly.png" },  // 6 dirs; idle: wings spread, rippling; flap = flying, all 8 dirs
    { "assets/enemies/68_shuyu.png",                  {0, 1, 0, 2}, 3, false, "assets/enemies/68_shuyu_flap.png" },  // frames 1, 2: heads plucking the air; flap (phase 2) = wings beating
    { "assets/enemies/69_bes_chem.png",               {0, 1, 0, 2} },  // frame 1: the fanged mouth gapes wide
    { "assets/enemies/70_trollgadda.png",             {}, 5 },         // big, 6 dirs: angry mossy pike, a massive tree wedged in its jaws; frame 2 jaws strained widest
    { "assets/enemies/71_namungumi.png",              {}, 5 },         // big, 6 dirs: veined black cloak over a red skirt, glowing eye, fang comb; frame 2 reared highest
    { "assets/enemies/72_mahwot.png",                 {}, 5, false, nullptr, "assets/enemies/72_mahwot_roar.png" },  // big, 8 dirs: swimming mini-Godzilla; alt: reared roar, jaws wide, plates glowing (atomic breath)
    { "assets/enemies/73_liderc.png",                 {}, 5, false, nullptr, nullptr, nullptr, 1, 1, "assets/enemies/73_liderc_prints.png" },  // big, 8 dirs: creepy ghost hen of fire; frame 2 flare-up; fades in only as the player nears; prints: human + goose foot
    { "assets/enemies/74_bes_rap.png",                {}, 5 },         // big, 8 dirs: skinny pink pig ghoul, toothy grin; frame 2 lunges and sprays foamy spit
    { "assets/enemies/75_makalala.png",               {}, 5, false, "assets/enemies/75_makalala_fly.png" },  // big, 8 dirs: giant slate ground bird, ivory club on its head; frame 2 the scream; flap = flying, the club glowing
    { "assets/enemies/76_loch_oich_monster.png",      {}, 5 },         // big, 8 dirs: dog-headed slippery lake serpent, two fins; frame 2 a bark
    { "assets/enemies/77_hoga.png",                   {}, 5 },         // big, 8 dirs: ox-headed lake fish, curved horns; frame 2 a bellow
    { "assets/enemies/78_zankallala.png",             {0, 1, 0, 2}, 3, false, "assets/enemies/78_zankallala_run.png" },  // medium, 8 dirs: tiny trickster riding a jerboa; frame 1 boast; flap = very fast run
    { "assets/enemies/79_ugjuknarpak.png",            {}, 5 },         // big, 8 dirs: giant tusked bearded seal reared on its hind legs, clawing the air; frame 2 widest roar
    { "assets/enemies/80_bes_kotak.png",              {}, 5 },         // big, 8 dirs: blocky floating box spirit; frame 2 lid lifts, mouth slot gapes
    { "assets/enemies/81_ieltxu.png",                 {0, 1, 0, 2}, 3, false, nullptr, "assets/enemies/81_ieltxu_fire.png" },  // medium, 8 dirs: near-black night bird, dark; alt = lit up breathing fire (frame 1 the jet)
    { "assets/enemies/82_nadubi.png",                 {}, 5, false, "assets/enemies/82_nadubi_crawl.png", "assets/enemies/82_nadubi_scratch.png" },  // big, 8 dirs: barbed spirit on all fours; flap = spider crawl; alt = reared, raking claws
    { "assets/enemies/83_beast_of_barrisdale.png",    {}, 5, false, "assets/enemies/83_beast_of_barrisdale_fly.png" },  // big, 8 dirs: massive three-legged bat-winged beast; frame 2 rears and roars; flap = flying, legs swept back
    { "assets/enemies/84_kigutilik.png",              {}, 5 },  // big, 8 dirs: violet stilt-legged beast, walrus head, cup on its head; frame 2 jaws open
    { "assets/enemies/85_nanabolele.png",                    {}, 5 },  // big, 8 dirs: glowing-scaled river dragon; frame 2 jaws gape, lights blaze
    { "assets/enemies/86_leucrocotta.png",                   {}, 5 },  // big, 8 dirs: stag-legged lion-hyena, badger head; frame 2 calls, ear-to-ear bone mouth gaping
    { "assets/enemies/87_corocotta.png",                     {}, 5 },  // big, 8 dirs: grey hyena-wolf, bristling mane, colour-shifting eyes; frame 2 jaws wide
    { "assets/enemies/88_amixsak.png",                       {}, 5 },  // big, 8 dirs: risen empty walrus hide, floating; frame 2 flippers flung high to seize
    { "assets/enemies/89_cuero.png",                         {}, 5 },  // big, 8 dirs: living stretched cowhide, rim of eyes and hooked claws; frame 2 heaves up, claws flared
    { "assets/enemies/90_chipekwe.png",                      {}, 5 },  // big, 8 dirs: massive dark rhino-reptile, one ivory horn; frame 2 head down, horn thrust to gore
    { "assets/enemies/91_kurrea.png",                        {}, 5 },  // big, 8 dirs: huge lagoon serpent reared from its coils; frame 2 drawn back, jaws open to strike
    { "assets/enemies/92_siehnam.png",                       {}, 5 },  // big, 8 dirs: gaunt night deer, huge bone antlers, bloodied muzzle; frame 2 antlers levelled to stab
    { "assets/enemies/93_chipique.png",                      {}, 5 },  // big, 8 dirs: black river serpent looping through white water, small grey head; frame 2 head darts, jaws open
    { "assets/enemies/94_trochus.png",                       {}, 5 },  // big, 8 dirs: great spined sea wheel half sunk in white water; frame 2 spins hard, spines drawn in
    { "assets/enemies/95_witkes.png",                        {}, 5 },  // big, 8 dirs: half-shaped water spirit rising from a whirlpool, offering tea; frame 2 arms spread, pool surging
    { "assets/enemies/96_bregdi.png",                        {}, 8, true },  // giant, 8 dirs: dark sea beast surfacing, two huge wing-fins; frames 3-4 fins wrap round in front, jaws open
    { "assets/enemies/97_ro.png",                            {}, 8, true },  // giant, 8 dirs: reared dark-red dragon, great wings, long tail; frames 3-4 wings high, howling
    { "assets/enemies/98_boiuna.png",                        {}, 8, true },  // giant, 8 dirs: colossal black river snake, searchlight eyes, horn fangs, V wake; frames 3-4 reared, jaws gaping
    { "assets/enemies/99_fad_felen.png",                     {}, 5 },  // big, 8 dirs: pillar of yellow plague cloud, hag face, misty claws; frame 2 arms flung wide, mouth gaping
    { "assets/enemies/100_flesh_planet.png",          {}, 8, true },   // giant: the final boss's ball (final_boss_views, one row a direction, all alike) -- the rest of its fight later
};
static const int ENEMY_SHEET_COUNT = sizeof(ENEMY_SHEETS) / sizeof(ENEMY_SHEETS[0]);

// A log whose sheet has tilt rows rocks by stepping them -- flat, right end
// up, flat, right end down -- ROCK_STEP s each, from its own age; its hitbox
// tilts with the row (LOG_TILT: the drawn rows lean ~10 degrees).
static const float ROCK_STEP = 0.25f;
static const float LOG_TILT  = 0.18f;   // radians
static int log_row(const Bullet& bl, const EnemySheet& es) {
    static const int STEPS[4] = { 0, 1, 0, 2 };
    return es.log_rows > 1 ? STEPS[(int)(bl.age / ROCK_STEP) % 4] : 0;
}
static const Uint32 LOOP_MS[4] = { 400, 250, 400, 250 };
static const Uint32 STEP_MS = 260;

// The idle frame an enemy sheet shows right now: three frames in `loop`
// order at LOOP_MS, more straight through at STEP_MS. Drawing and the breath
// hook (Enemy::breathe) both read it, so a volley leaves on the frame shown.
static int idle_frame_now(const EnemySheet& es, Uint32 ms) {
    if (es.frames != 3) return (ms / STEP_MS) % es.frames;
    Uint32 t = ms % (LOOP_MS[0] + LOOP_MS[1] + LOOP_MS[2] + LOOP_MS[3]);
    int step = 0;
    while (t >= LOOP_MS[step]) t -= LOOP_MS[step++];
    return es.loop[step];
}

// Sheet row for a FACE_* direction.
static int sheet_dir(int facing) {
    switch (facing) {
        case FACE_DOWN:       return 0;
        case FACE_DOWN_RIGHT: return 1;
        case FACE_RIGHT:      return 2;
        case FACE_UP_RIGHT:   return 3;
        case FACE_UP:         return 4;
        case FACE_UP_LEFT:    return 5;
        case FACE_LEFT:       return 6;
        default:              return 7;   // FACE_DOWN_LEFT
    }
}

// ── BattleScene ───────────────────────────────────────────────────────────────

// The fade up from black at the start and down to black at the end, in seconds.
static const float FADE_T  = 0.4f;
// A pack's next fight: the player's glide back and the enemy's drop, in seconds.
static const float CHAIN_T = 0.6f;

BattleScene::BattleScene(Player* player, int enemy_id, bool chained, float from_x, float from_y) {
    _chained = chained;
    _from_x  = from_x;
    _from_y  = from_y;
    memset(_player_bullets, 0, sizeof(_player_bullets));
    memset(_enemy_bullets,  0, sizeof(_enemy_bullets));
    memset(_pickups,        0, sizeof(_pickups));

    _phase       = BATTLE_PHASE_INTRO;
    _player_ref  = player;
    _weapon_type = equipped_weapon(player).type;

    _bp = {};
    _bp.x      = ARENA_W * 0.5f;
    _bp.y      = ARENA_H - 80.0f;
    _bp.hp     = (float)player->stats.hp;
    _bp.max_hp = (float)player->stats.max_hp;
    _equip(_weapon_type);

    seed_enemy_rng((unsigned int)SDL_GetTicks());
    _enemy    = enemy_create(enemy_id);
    _enemy_id = enemy_id;
}

// Firing as weapon w: its shape's profile, sped up by its oil, hitting as
// hard as its ore, with a shot a volley more per echo -- and the shot hitbox,
// the opaque bounds of its cell in the shot sheet. At the start of a fight
// and on every swap.
void BattleScene::_equip(WeaponType w) {
    _weapon_type = w;
    _bp.weapon = weapon_profile(_weapon_type);
    // What the weapon is made of and what has been bought for it: ore sets
    // the damage, oil the cooldown, echo the shots a volley.
    const Weapon& held = _player_ref->arsenal[w];
    float base_rate = _bp.weapon.fire_rate;
    _bp.weapon.fire_rate  = faster_fire_rate(base_rate, held.oil);
    _bp.weapon.damage     = faster_damage(base_rate, _bp.weapon.damage, held.oil)
                          * material_power(held.material)
                          * level_damage_mult(_player_ref->level);
    _bp.weapon.count     += held.echo;

    // The hitbox is the sprite: the opaque bounds of this weapon's cell, about
    // its centre, at the 2x it is drawn. Every ore row is the same shape.
    float r = _bp.weapon.radius;
    _shot_x0 = _shot_y0 = -r;
    _shot_x1 = _shot_y1 =  r;
    {
        const int CELL = PLAYER_SHOT_CELL;
        SDL_Surface* s = load_rgba(PLAYER_SHOT_SHEET);
        if (s) {
            int cx = (int)_weapon_type * CELL, x0 = CELL, y0 = CELL, x1 = -1, y1 = -1;
            for (int y = 0; y < CELL && y < s->h; y++)
                for (int x = 0; x < CELL && cx + x < s->w; x++)
                    if (((Uint8*)s->pixels)[y * s->pitch + (cx + x) * 4 + 3]) {
                        if (x < x0) x0 = x;
                        if (x > x1) x1 = x;
                        if (y < y0) y0 = y;
                        if (y > y1) y1 = y;
                    }
            if (x1 >= 0) {
                const int c = CELL / 2;
                _shot_x0 = (x0 - c) * 2.0f;  _shot_x1 = (x1 + 1 - c) * 2.0f;
                _shot_y0 = (y0 - c) * 2.0f;  _shot_y1 = (y1 + 1 - c) * 2.0f;
            }
            SDL_FreeSurface(s);
        }
    }
    float ex = fmaxf(-_shot_x0, _shot_x1), ey = fmaxf(-_shot_y0, _shot_y1);
    _shot_reach = sqrtf(ex * ex + ey * ey);
}

// Swap to the next or previous weapon the player owns, in arsenal order,
// wrapping. The choice is the player's equipped weapon from then on, so it
// carries out of the fight. The new weapon's cooldown starts at a quarter
// second at least: a swap is never a free extra volley.
// The TAB menu paused the fight and may have equipped or re-forged a weapon:
// fire as whatever is equipped now, with a swap's cooldown floor.
void BattleScene::sync_weapon() {
    _equip(_player_ref->equipped);
    _bp.fire_timer = fmaxf(_bp.fire_timer, 0.25f);
}

void BattleScene::_cycle(int dir) {
    WeaponType w = owned_neighbour(_player_ref, dir);
    _swap_t = 0.0f;                                  // the box shows even with only one weapon
    if (w == _player_ref->equipped) return;
    _player_ref->equipped = w;
    _equip(w);
    _bp.fire_timer = fmaxf(_bp.fire_timer, 0.25f);
    _swap_t = 0.0f;
}

BattleScene::~BattleScene() {
    delete _enemy;
    if (_sheet) SDL_DestroyTexture(_sheet);
    if (_flap)  SDL_DestroyTexture(_flap);
    if (_alt)   SDL_DestroyTexture(_alt);
    if (_log)   SDL_DestroyTexture(_log);
    if (_marks) SDL_DestroyTexture(_marks);
    if (_alt_white) SDL_DestroyTexture(_alt_white);
    if (_sheet_white) SDL_DestroyTexture(_sheet_white);
    if (_flap_white)  SDL_DestroyTexture(_flap_white);
    if (_bullets) SDL_DestroyTexture(_bullets);
    if (_item_icons) SDL_DestroyTexture(_item_icons);
    for (SDL_Texture* t : _bullets_fade) if (t) SDL_DestroyTexture(t);
}

// ── update ────────────────────────────────────────────────────────────────────

// Eased progress of a chained intro: quick off the mark, soft landing.
float BattleScene::_chain_in() const {
    if (!_chained || _phase != BATTLE_PHASE_INTRO) return 1.0f;
    float k = _t / CHAIN_T;
    if (k >= 1.0f) return 1.0f;
    float u = 1.0f - k;
    return 1.0f - u * u * u;
}

// How dark the screen is, 0..1: up from black in the intro, down to black
// once the end panel is dismissed.
float BattleScene::_darkness() const {
    if (_phase == BATTLE_PHASE_INTRO) return _chained ? 0.0f : 1.0f - _t / FADE_T;
    if (_outro_t > 0.0f)              return _outro_t / FADE_T;
    return 0.0f;
}

// Being hit: the whole fight freezes for HITSTOP, the screen flashes white
// then red, and shakes for SHAKE_T -- a hit costs whole bars now, so it has to
// land like one.
static const float HITSTOP = 0.12f;
static const float SHAKE_T = 0.30f;
static const float FLASH_T = 0.40f;

void hurt_shake_begin(SDL_Renderer* ren, float t, SDL_Rect* saved) {
    SDL_RenderGetViewport(ren, saved);
    if (t < SHAKE_T) {
        int amp = 2 * (int)(3.0f * (1.0f - t / SHAKE_T) + 0.5f);   // 6, 4, 2 px
        SDL_Rect shaken = *saved;
        shaken.x += ((int)(t * 30.0f) % 2) ? amp : -amp;
        SDL_RenderSetViewport(ren, &shaken);
    }
}

void hurt_shake_end(SDL_Renderer* ren, const SDL_Rect* saved) {
    SDL_RenderSetViewport(ren, saved);
}

// White over the first HITSTOP, then red fading out in hard steps, NES
// palette-flash style.
void hurt_flash(SDL_Renderer* ren, float t, int w, int h) {
    if (t >= FLASH_T) return;
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
    SDL_Rect all = { 0, 0, w, h };
    if (t < HITSTOP) fc_draw_color(ren, 252, 252, 252, 150);
    else {
        float k = 1.0f - (t - HITSTOP) / (FLASH_T - HITSTOP);
        fc_draw_color(ren, 183, 0, 0, (Uint8)(110 * ((int)(k * 3.0f + 0.999f) / 3.0f)));
    }
    SDL_RenderFillRect(ren, &all);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
}

void BattleScene::update(const Input* in, float dt) {
    if (_hit_t < HITSTOP) { _hit_t += dt; return; }
    _hit_t += dt;
    _t += dt;
    bool confirm = input_pressed(in, SDL_SCANCODE_RETURN) || input_pressed(in, SDL_SCANCODE_Z);

    switch (_phase) {
        case BATTLE_PHASE_INTRO:
            if (_t >= (_chained ? CHAIN_T : FADE_T)) {
                _phase = BATTLE_PHASE_FIGHTING;
                _t = 0.0f;
                // A beat to move before the first volley: control returns
                // before danger does.
                _enemy->fire_timer = 0.5f;
                _fire_iv = _enemy->fire_interval();
            }
            return;
        case BATTLE_PHASE_VICTORY:
            _update_pickups(dt);
            // The wait keeps a held fire key (Z) from skipping the panel.
            if (confirm && _t > 0.6f) _confirmed = true;
            if (_confirmed && (_more_after || (_outro_t += dt) >= FADE_T)) _done = true;
            return;
        case BATTLE_PHASE_DEFEAT:
            if (confirm && _t > 0.6f) _confirmed = true;
            if (_confirmed && (_outro_t += dt) >= FADE_T) _done = true;
            return;
        default:
            break;
    }

    // Swap weapons on the fly: Q back, E or X on.
    if (input_pressed(in, SDL_SCANCODE_Q)) _cycle(-1);
    if (input_pressed(in, SDL_SCANCODE_E) || input_pressed(in, SDL_SCANCODE_X)) _cycle(1);
    _swap_t += dt;

    // Debug: drop the enemy to its next stage -- just under its own phase
    // line (Enemy::phase2_at, which differs per enemy); past it, to 1 HP.
    if (input_pressed(in, SDL_SCANCODE_R)) {
        float line = _enemy->max_hp * _enemy->phase2_at();
        _enemy->hp = _enemy->hp >= line ? line - 1.0f : 1.0f;
    }

    // Debug: instantly win the current battle.
    if (input_pressed(in, SDL_SCANCODE_T))
        _enemy->take_damage(_enemy->hp);

    _update_movement(in, dt);
    _update_player_fire(in, dt);
    _update_enemy(dt);
    _move_bullets(dt);
    _check_collisions();

    if (_bp.iframes > 0.0f) _bp.iframes -= dt;
    if (_enemy_flash > 0.0f) _enemy_flash -= dt;
    if (_flash_gap   > 0.0f) _flash_gap   -= dt;
    if (_pierce_wait > 0.0f) _pierce_wait -= dt;

    if (!_enemy->is_alive()) {
        _win();
    } else if (_bp.hp <= 0.0f) {
        _player_ref->stats.hp = 0;
        _phase = BATTLE_PHASE_DEFEAT;
        _t = 0.0f;
    }
}

// Bullet cancel: every enemy bullet still in the air becomes a pickup that
// flies to the player, and a denser screen pays more of the enemy's part.
// What a cancelled bullet turns into: mostly the common stuff of the world,
// and one in PART_SHARE the part this enemy drops -- the vine off a
// Treesqueak, the hide off a hare. The enemy itself always gives one part,
// so even a clean win with nothing in the air pays it.
static const Item COMMON_DROPS[] = { ITEM_WOOD, ITEM_STONE };
static const int  PART_SHARE     = 4;
static_assert(ITEM_COUNT <= 32, "BattleScene::_won holds a count per Item");

// Anything not from the common pool is rare: the part an enemy is hunted for.
static bool is_common_drop(int it) {
    for (Item c : COMMON_DROPS) if (c == it) return true;
    return false;
}

void BattleScene::_win() {
    _player_ref->stats.hp = (int)_bp.hp;
    _phase = BATTLE_PHASE_VICTORY;
    _t = 0.0f;
    for (int& n : _won) n = 0;

    Item part = part_item(enemy_part(_enemy_id));
    unsigned rng = SDL_GetTicks() * 2654435761u + (unsigned)_enemy_id;
    int n = 0;
    // The enemy's own part, from where it stood.
    _pickups[n++] = { _enemy->x, _enemy->y, 0.0f, -120.0f, true, part };
    for (int i = 0; i < MAX_ENEMY_BULLETS && n < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        bl.active = false;
        rng = rng * 1664525u + 1013904223u;
        int roll = (int)((rng >> 16) % (PART_SHARE * 64));
        Item it = roll < 64 ? part : COMMON_DROPS[roll % (int)(sizeof(COMMON_DROPS) / sizeof(COMMON_DROPS[0]))];
        // Pop back the way it came, then get pulled in.
        _pickups[n++] = { bl.x, bl.y, -bl.vx * 0.4f, -bl.vy * 0.4f, true, it };
    }
    // Its lasers too (the user): each breaks into a string of pickups along
    // the part of it that's on screen, a step apart, popping out sideways.
    // Its warning marks and its glowing balls aren't lasers: left out.
    Enemy::TeleLine tl[64];
    int nt = _enemy->telegraphs(tl, 64);
    for (int k = 0; k < nt; k++) {
        const Enemy::TeleLine& L = tl[k];
        if (L.stage == 3 || L.orb > 0.0f) continue;
        float dx = L.x1 - L.x0, dy = L.y1 - L.y0, len = sqrtf(dx * dx + dy * dy);
        if (len < 1.0f) continue;
        float ux = dx / len, uy = dy / len;
        for (float d = 12.0f; d < len && n < MAX_ENEMY_BULLETS; d += 24.0f) {
            float x = L.x0 + ux * d, y = L.y0 + uy * d;
            if (x < 0.0f || x > ARENA_W || y < ARENA_TOP || y > ARENA_H) continue;
            rng = rng * 1664525u + 1013904223u;
            int roll = (int)((rng >> 16) % (PART_SHARE * 64));
            Item it = roll < 64 ? part : COMMON_DROPS[roll % (int)(sizeof(COMMON_DROPS) / sizeof(COMMON_DROPS[0]))];
            float side = (rng >> 8) & 1 ? 1.0f : -1.0f;
            _pickups[n++] = { x, y, -uy * side * 40.0f, ux * side * 40.0f, true, it };
        }
    }
    // ponytail: credited now, not as pickups land -- the scene can be dismissed
    // before they arrive, so the flight is only for show.
    _won_new = 0;
    for (int i = 0; i < n; i++)
        if (!item_found(_player_ref, (Item)_pickups[i].item)) _won_new |= 1u << _pickups[i].item;
    for (int i = 0; i < n; i++) item_mark_found(_player_ref, (Item)_pickups[i].item);
    for (int i = 0; i < n; i++) {
        item_slot(_player_ref, (Item)_pickups[i].item) += 1;
        _won[_pickups[i].item]++;
    }
    // The score: hits + grazes + the defeat bonus (enemy_defeat_exp: a
    // common's grows with its rank, a boss pays far more). A level-up heals:
    // the battle's own HP follows.
    _exp_gain = _hits + _grazes + enemy_defeat_exp(_enemy_id);
    _levels   = player_gain_exp(_player_ref, _exp_gain);
    if (_levels > 0) {
        _bp.max_hp = (float)_player_ref->stats.max_hp;
        _bp.hp     = (float)_player_ref->stats.hp;
    }
}

void BattleScene::_update_pickups(float dt) {
    const float PULL = 2200.0f, DRAG = 4.0f;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Pickup& p = _pickups[i];
        if (!p.active) continue;
        float dx = _bp.x - p.x, dy = _bp.y - p.y;
        float d = sqrtf(dx*dx + dy*dy);
        if (d < 10.0f) { p.active = false; continue; }
        // Drag bleeds off the pop and any sideways drift, so nothing orbits.
        float keep = 1.0f - DRAG * dt;
        if (keep < 0.0f) keep = 0.0f;
        p.vx = p.vx * keep + dx / d * PULL * dt;
        p.vy = p.vy * keep + dy / d * PULL * dt;
        p.x += p.vx * dt;
        p.y += p.vy * dt;
    }
}

void BattleScene::_update_movement(const Input* in, float dt) {
    // The map's keys: crouch (ctrl) is focus -- slow and precise -- and
    // shift sprints.
    bool focus  = _bp.focus = player_crouching(in);
    bool sprint = player_sprinting(in);
    // Focus dims the sprite a tier at a time (lit, dark 1, dark 2) and brightens
    // it back the same way on release: one tier per DIM_STEP seconds.
    const float DIM_STEP = 0.08f;
    _bp.dim = fminf(fmaxf(_bp.dim + (focus ? dt : -dt) / DIM_STEP, 0.0f), 2.0f);
    const float PSPEED     = focus ? 70.0f : sprint ? 250.0f : 160.0f;
    const float MARGIN     = 16.0f;
    const float ANIM_SPEED = focus ? 0.30f : sprint ? 0.10f : 0.20f;

    float mx, my;
    player_read_input(_player_ref, in, &mx, &my);
    _bp.x += mx * PSPEED * dt;
    _bp.y += my * PSPEED * dt;

    if (_bp.x < MARGIN)           _bp.x = MARGIN;
    if (_bp.x > ARENA_W - MARGIN) _bp.x = ARENA_W - MARGIN;
    if (_bp.y < ARENA_TOP + MARGIN) _bp.y = ARENA_TOP + MARGIN;
    if (_bp.y > ARENA_H - MARGIN) _bp.y = ARENA_H - MARGIN;

    player_animate(_player_ref, dt, ANIM_SPEED);
}

void BattleScene::_update_player_fire(const Input* in, float dt) {
    _bp.fire_timer -= dt;
    // An enemy that can't be seen doesn't hold the player's facing: let it
    // follow their movement at once (a facing locked toward where it was
    // last seen sent blind shots the wrong way -- the tester).
    // It can't be seen -- a ghost drawn at zero opacity (the same quarter
    // steps the draw uses), or gone off the arena (the user) -- so nothing
    // tracks it.
    bool hidden = _enemy->opacity(_bp.x, _bp.y) < 0.25f
               || _enemy->x < 0.0f || _enemy->x > ARENA_W || _enemy->y < ARENA_TOP || _enemy->y > ARENA_H;
    if (hidden) _player_ref->facing_locked = 0;
    bool pressed = input_down(in, SDL_SCANCODE_SPACE) ||
                   input_down(in, SDL_SCANCODE_Z);

    if (pressed && _bp.fire_timer <= 0.0f) {
        // Shots aim themselves at the enemy -- unless it can't be seen:
        // then they go the way the player is facing (the user).
        float base;
        if (hidden) base = facing_angle(_player_ref->facing);   // movement steers it (unlocked below)
        else {
            _player_ref->facing = facing_toward(_enemy->x - _bp.x, _enemy->y - _bp.y);
            _player_ref->facing_locked = 1;
            base = atan2f(_enemy->y - _bp.y, _enemy->x - _bp.x);
        }

        const ProjectileProfile& wp = _bp.weapon;
        float step  = (wp.count > 1) ? (wp.spread * PI / 180.0f) / (wp.count - 1) : 0.0f;
        float start = base - step * (wp.count - 1) * 0.5f;
        for (int i = 0; i < wp.count; i++)
            _spawn_player_bullet(start + i * step);
        _bp.fire_timer = 1.0f / wp.fire_rate;
    }
}

void BattleScene::_update_enemy(float dt) {
    _enemy->update(dt, _bp.x, _bp.y);
    // A pull: the player drawn toward it (they walk against it), kept in the arena.
    if (float pull = _enemy->pull()) {
        float dx = _enemy->x - _bp.x, dy = _enemy->y - _bp.y, d = sqrtf(dx * dx + dy * dy);
        if (d > 1.0f) {
            float st = fminf(pull * dt, d);
            _bp.x = fminf(fmaxf(_bp.x + dx / d * st, 16.0f), ARENA_W - 16.0f);
            _bp.y = fminf(fmaxf(_bp.y + dy / d * st, ARENA_TOP + 16.0f), ARENA_H - 16.0f);
        }
    }
    _anim_ms += dt * 1000.0f * _enemy->anim_speed();
    BulletSpawn spawns[256];   // the most one volley may fire (Dingbat's ring wall is 160)
    // When its rate speeds up mid-fight -- a phase change, say -- the wait shrinks to
    // the new rate at once instead of running out the old, slower one. Only
    // on a speed-up, so the opening grace stays whole.
    float iv = _enemy->fire_interval();
    if (iv < _fire_iv) _enemy->fire_timer = fminf(_enemy->fire_timer, iv);
    _fire_iv = iv;
    _enemy->fire_timer -= dt;
    if (_enemy->fire_timer <= 0.0f) {
        int count = _enemy->fire(_bp.x, _bp.y, spawns, 256);
        for (int i = 0; i < count; i++)
            _spawn_enemy_bullet(spawns[i]);
        _enemy->fire_timer = _enemy->fire_interval();
    }
    // The breath frame: the moment the idle animation turns to it.
    if (_enemy_id >= 0 && _enemy_id < ENEMY_SHEET_COUNT) {
        int f = idle_frame_now(ENEMY_SHEETS[_enemy_id], (Uint32)_anim_ms), bf = _enemy->breath_frame();
        if (f == bf && _idle_frame != bf) {
            int count = _enemy->breathe(_bp.x, _bp.y, spawns, 256);
            for (int i = 0; i < count; i++)
                _spawn_enemy_bullet(spawns[i]);
        }
        if (f != _idle_frame) {
            int count = _enemy->on_idle_frame(f, _bp.x, _bp.y, spawns, 256);
            for (int i = 0; i < count; i++)
                _spawn_enemy_bullet(spawns[i]);
        }
        _idle_frame = f;
    }
}

void BattleScene::_move_bullets(float dt) {
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        bl.age += dt;
        bl.x += bl.vx * dt;
        bl.y += bl.vy * dt;
        // Gone when its centre reaches the edge: by then it has dithered
        // away (see _shot_edge_gap), so nothing is cut off.
        if (_shot_edge_gap(bl) <= 0.0f) bl.active = false;
    }

    // Collect orb spawn positions so we don't modify the array while iterating.
    struct OrbSpawn { float x, y; };
    OrbSpawn orb_pending[32];
    int n_orb = 0;
    struct Shed { float x, y, heading, spread, speed, damage; int n; float spin; };
    Shed shed_pending[32];
    int n_shed = 0;

    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        bl.age += dt;   // from its spawn, waiting or not
        if (bl.life > 0.0f && bl.age >= bl.life) { bl.active = false; continue; }

        // A boomerang slows along its heading, stops, and flies back; once
        // it is returning and reaches the enemy, the enemy swallows it.
        if (bl.accel != 0.0f && bl.min_speed > 0.0f && bl.ow != 0.0f) {
            bl.ovr = fmaxf(bl.ovr + bl.accel * dt, bl.min_speed);   // orbiting: it's the speed outward that eases
        } else if (bl.accel != 0.0f && bl.min_speed > 0.0f) {
            // Easing off: slows along the way it is going now (a ricochet
            // turns it), never below min_speed.
            float cur = sqrtf(bl.vx * bl.vx + bl.vy * bl.vy);
            float sp  = fmaxf(cur + bl.accel * dt, bl.min_speed);
            if (cur > 0.0f) { bl.vx = bl.vx / cur * sp; bl.vy = bl.vy / cur * sp; }
        } else if (bl.accel != 0.0f) {
            bl.vx += bl.ux * bl.accel * dt;
            bl.vy += bl.uy * bl.accel * dt;
            if (bl.max_speed > 0.0f) {                  // coming back no faster than this
                float sp = sqrtf(bl.vx * bl.vx + bl.vy * bl.vy);
                if (sp > bl.max_speed) { bl.vx *= bl.max_speed / sp; bl.vy *= bl.max_speed / sp; }
            }
            float ddx = bl.x - _enemy->x, ddy = bl.y - _enemy->y;
            if (bl.vx * bl.ux + bl.vy * bl.uy < 0.0f && ddx * ddx + ddy * ddy < 24.0f * 24.0f) {
                bl.active = false;
                continue;
            }
        }

        // A mine waits where it was dropped, then launches at the player --
        // an orbiting one keeps orbiting (a ring forming round the enemy)
        // until it launches, then flies straight.
        if (bl.delay > 0.0f) {
            bl.delay -= dt;
            if (bl.delay > 0.0f) { if (bl.ow == 0.0f) continue; }
            else {
                float la = atan2f(_bp.y - bl.y, _bp.x - bl.x) + bl.launch_off;
                bl.vx = cosf(la) * bl.launch_speed;
                bl.vy = sinf(la) * bl.launch_speed;
                bl.ow = 0.0f;
                bl.accel = 0.0f; bl.min_speed = 0.0f;   // its orbit's easing is done: left set it braked the launch to a dead stop
            }
        }

        if (bl.homing && bl.homing_timer > 0.0f) {
            bl.homing_timer -= dt;
            if (bl.homing_timer <= 0.0f) bl.homing = false;
        }

        if (bl.homing && bl.ow != 0.0f) {
            // A formation homing: its drifting centre turns toward the player
            // (every shot of it alike, so the shape holds).
            const float TURN = 2.2f;
            float dx = _bp.x - bl.ocx, dy = _bp.y - bl.ocy, dist = sqrtf(dx * dx + dy * dy);
            float spd = sqrtf(bl.ocvx * bl.ocvx + bl.ocvy * bl.ocvy);
            if (dist < 70.0f) bl.homing = false;           // this close it commits and flies on past: a sidestep beats it (the tester)
            else if (spd > 0.0f) {
                float nx = bl.ocvx / spd + dx / dist * TURN * dt, ny = bl.ocvy / spd + dy / dist * TURN * dt;
                float len = sqrtf(nx * nx + ny * ny);
                bl.ocvx = nx / len * spd; bl.ocvy = ny / len * spd;
            }
        } else if (bl.homing) {
            // Turn rate: fast for bullets, slow for orbs so the ring still matters
            const float TURN = bl.spawner ? 0.9f : 2.2f;
            float dx = _bp.x - bl.x, dy = _bp.y - bl.y;
            float dist = sqrtf(dx*dx + dy*dy);
            if (dist > 1.0f) {
                float spd = sqrtf(bl.vx*bl.vx + bl.vy*bl.vy);
                if (spd > 0.0f) {
                    float nx = bl.vx/spd + dx/dist * TURN * dt;
                    float ny = bl.vy/spd + dy/dist * TURN * dt;
                    float len = sqrtf(nx*nx + ny*ny);
                    bl.vx = nx/len * spd;
                    bl.vy = ny/len * spd;
                }
            }
        }

        if (bl.ow != 0.0f) {
            // Orbiting: straight out from its centre while turning round it.
            bl.orad += bl.ovr * dt;
            bl.oang += bl.ow * dt;
            if (bl.pa > 0.0f) {
                // The centre on its path: an ellipse (or squarer, pround < 1),
                // tilted, about (pcx, pcy). Its heading, the way it's going.
                auto at = [&](float phi, float* px, float* py) {
                    float c = cosf(phi), s = sinf(phi), e = bl.pround;
                    float ex = bl.pa * (e == 1.0f ? c : copysignf(powf(fabsf(c), e), c));
                    float ey = bl.pb * (e == 1.0f ? s : copysignf(powf(fabsf(s), e), s));
                    float ct = cosf(bl.ptilt), st = sinf(bl.ptilt);
                    *px = bl.pcx + ex * ct - ey * st; *py = bl.pcy + ex * st + ey * ct;
                };
                float x0, y0, x1, y1;
                at(bl.pphi, &x0, &y0);
                if (bl.peven) {                            // px/s along it: step the angle by how far it reaches
                    at(bl.pphi + 0.01f, &x1, &y1);
                    float ds = hypotf(x1 - x0, y1 - y0) / 0.01f;
                    bl.pphi += ds > 0.0f ? bl.pw * dt / ds : 0.0f;
                } else bl.pphi += bl.pw * dt;
                at(bl.pphi, &x1, &y1);
                if (bl.pfor > 0.0f && (bl.pfor -= dt) <= 0.0f) {
                    // Its orbit done: on straight the way it was going.
                    if (dt > 0.0f) { bl.ocvx = (x1 - x0) / dt; bl.ocvy = (y1 - y0) / dt; }
                    if (bl.paim) {                         // ...or turned for the player, at the same pace
                        float tx = _bp.x, ty = _bp.y;
                        if (bl.paim_slot >= 0) _enemy->aim_slot(bl.paim_slot, _bp.x, _bp.y, &tx, &ty);
                        float sp = hypotf(bl.ocvx, bl.ocvy), dx = tx - x1, dy = ty - y1, d = hypotf(dx, dy);
                        if (d > 0.0f) { bl.ocvx = dx / d * sp; bl.ocvy = dy / d * sp; }
                    }
                    if (bl.pface && (bl.ocvx != 0.0f || bl.ocvy != 0.0f)) bl.oang = bl.obase + atan2f(bl.ocvy, bl.ocvx);   // still facing its way
                    bl.pa = 0.0f;
                } else {
                    bl.ocx = x1; bl.ocy = y1;
                    if (bl.pface && (x1 != x0 || y1 != y0))      // turned along the way it's going
                        bl.oang = bl.obase + atan2f(y1 - y0, x1 - x0);   // (in place of the turn above)
                }
            }
            if (bl.octurn != 0.0f) {                       // the drift arching round
                if (bl.octurn_t > 0.0f && (bl.octurn_t -= dt) <= 0.0f) bl.octurn = 0.0f;   // the arch done: on straight
                float c = cosf(bl.octurn * dt), sn = sinf(bl.octurn * dt), vx = bl.ocvx;
                bl.ocvx = vx * c - bl.ocvy * sn; bl.ocvy = vx * sn + bl.ocvy * c;
            }
            bl.ocx += bl.ocvx * dt; bl.ocy += bl.ocvy * dt;
            float nx = bl.ocx + cosf(bl.oang) * bl.orad, ny = bl.ocy + sinf(bl.oang) * bl.orad * (bl.osq > 0.0f ? bl.osq : 1.0f);
            if (dt > 0.0f) { bl.vx = (nx - bl.x) / dt; bl.vy = (ny - bl.y) / dt; }
            bl.x = nx; bl.y = ny;
        } else {
            if (bl.zig_every > 0.0f && (bl.zig_t -= dt) <= 0.0f) {
                // Swing across its course to the other side.
                bl.zig_t += bl.zig_every;
                float r = -2.0f * bl.zig * bl.zig_s, c = cosf(r), sn = sinf(r), vx = bl.vx, vy = bl.vy;
                bl.vx = vx * c - vy * sn; bl.vy = vx * sn + vy * c;
                bl.zig_s = -bl.zig_s;
            }
            if (bl.wave != 0.0f) {
                // Roll on along its wave: turn by how far the swing moved.
                float r = bl.wave * (sinf(bl.wave_w * (bl.wave_t + dt)) - sinf(bl.wave_w * bl.wave_t)), c = cosf(r), sn = sinf(r), vx = bl.vx, vy = bl.vy;
                bl.vx = vx * c - vy * sn; bl.vy = vx * sn + vy * c;
                bl.wave_t += dt;
            }
            bl.x += bl.vx * dt;
            bl.y += bl.vy * dt;
        }
        if (bl.shed_every > 0.0f && bl.shed_left != 0 && (bl.shed_t -= dt) <= 0.0f) {
            bl.shed_t += bl.shed_every;
            if (bl.shed_left > 0) bl.shed_left--;
            bool still = bl.vx == 0.0f && bl.vy == 0.0f;     // a sitting egg sheds from its middle
            if (n_shed < 32)
                shed_pending[n_shed++] = { bl.x, still ? bl.y : bl.y + bl.radius, atan2f(bl.vy, bl.vx),
                                           bl.shed_spread, bl.shed_speed, bl.damage, bl.shed_n, bl.shed_spin };
            if (bl.shed_left == 0 && bl.shed_dies) { bl.active = false; continue; }
        }
        bl.ang += bl.spin * dt;   // a log turns -- or rocks, turning back at its tilt
        if (bl.half_len > 0.0f && _enemy_id >= 0 && _enemy_id < ENEMY_SHEET_COUNT
            && ENEMY_SHEETS[_enemy_id].log_rows > 1) {
            int row = log_row(bl, ENEMY_SHEETS[_enemy_id]);   // the hitbox leans with the drawn row
            bl.ang = row == 1 ? -LOG_TILT : row == 2 ? LOG_TILT : 0.0f;
        }
        if (bl.max_tilt > 0.0f && fabsf(bl.ang) > bl.max_tilt) {
            bl.ang  = copysignf(bl.max_tilt, bl.ang);
            bl.spin = -bl.spin;
        }

        if (bl.spawner) {
            bl.spawn_timer -= dt;
            if (bl.spawn_timer <= 0.0f && n_orb < 32) {
                orb_pending[n_orb++] = { bl.x, bl.y };
                bl.spawn_timer = bl.spawn_interval;
            }
            if (bl.x < -20 || bl.x > ARENA_W + 20 ||
                bl.y < ARENA_TOP - 20 || bl.y > ARENA_H + 20)
                bl.active = false;
        } else if (bl.bouncing) {
            float r = bl.radius;
            if (bl.x - r < 0)       { bl.x = r;           bl.vx =  fabsf(bl.vx); bl.bounces++; }
            if (bl.x + r > ARENA_W) { bl.x = ARENA_W - r; bl.vx = -fabsf(bl.vx); bl.bounces++; }
            if (bl.y - r < ARENA_TOP) { bl.y = ARENA_TOP + r; bl.vy = fabsf(bl.vy); bl.bounces++; }
            if (bl.y + r > ARENA_H) { bl.y = ARENA_H - r; bl.vy = -fabsf(bl.vy); bl.bounces++; }
            if (bl.bounces >= 3) bl.active = false;
        } else {
            // Gone once its centre leaves the arena -- for a log, once all of
            // it has (m: its reach), so one can enter from out of sight
            // above (spawned up to m over the top) and leave the same way.
            // Outside and heading further out, it's gone. A shot coming IN
            // from outside -- a line sliding in from beyond the wall -- is
            // left to arrive.
            float m = bl.half_len > 0.0f ? bl.half_len + bl.radius : 0.0f;
            // A shot PARKED on an orbit -- circling a fixed centre at a fixed
            // radius (a hurricane's band, a shield) -- goes off screen and comes
            // back round: kept.
            bool parked = (bl.ow != 0.0f && bl.ovr < 1.0f && bl.ocvx == 0.0f && bl.ocvy == 0.0f)
                       || bl.pa > 0.0f;                    // ...or riding a path, which comes back round
            if (!parked && ((bl.x < -m && bl.vx <= 0.0f) || (bl.x > ARENA_W + m && bl.vx >= 0.0f) ||
                (bl.y < ARENA_TOP - 2.0f * m && bl.vy <= 0.0f) || (bl.y > ARENA_H + m && bl.vy >= 0.0f)))
                bl.active = false;
        }
    }

    // Emit 8-way ring from each orb that ticked.
    // Minimum distance: at d < 50px the ring gaps (39px) are too small for the
    // player circle (r=12) to fit through, making the hit unavoidable.
    for (int p = 0; p < n_shed; p++) {
        const Shed& s = shed_pending[p];
        float dx = s.x - _bp.x, dy = s.y - _bp.y;
        if (dx*dx + dy*dy < 40.0f*40.0f) continue;   // never point-blank
        for (int k = 0; k < s.n; k++) {
            float a = s.heading + (s.n > 1 ? (k / (float)(s.n - 1) - 0.5f) * s.spread : 0.0f);
            BulletSpawn chip = { cosf(a) * s.speed, sinf(a) * s.speed, 2.5f, s.damage };
            chip.orbit_w = s.spin;
            _spawn_bullet_at(s.x, s.y, chip);
        }
    }
    for (int p = 0; p < n_orb; p++) {
        float dx = orb_pending[p].x - _bp.x;
        float dy = orb_pending[p].y - _bp.y;
        if (dx*dx + dy*dy < 50.0f*50.0f) continue;
        for (int i = 0; i < 8; i++) {
            float a = i * (TAU / 8.0f);
            BulletSpawn sub;
            sub.vx = cosf(a) * 130.0f;
            sub.vy = sinf(a) * 130.0f;
            sub.radius = 3.5f;
            sub.damage = 1.0f;
            _spawn_bullet_at(orb_pending[p].x, orb_pending[p].y, sub);
        }
    }
}

// The axe and club tumble; everything else points the way it flies.
double BattleScene::_shot_angle(const Bullet& bl) const {
    if (bl.weapon == WEAPON_AXE || bl.weapon == WEAPON_CLUB)
        return SDL_GetTicks() * 1.03;   // ~1000 deg/sec, as the overworld throw
    return atan2f(bl.vy, bl.vx) * (180.0 / PI);
}

// How far the shot's centre is from the edge it is flying toward -- the
// nearer of the two it heads for -- so a shot leaving past the HUD fades out
// below it, where it can be seen, and a shot just fired near the bottom edge
// it is flying away from does not fade at all.
float BattleScene::_shot_edge_gap(const Bullet& bl) const {
    float gx = bl.vx > 0.0f ? ARENA_W - bl.x : bl.vx < 0.0f ? bl.x : 1e9f;
    float gy = bl.vy > 0.0f ? ARENA_H - bl.y : bl.vy < 0.0f ? bl.y - ARENA_TOP : 1e9f;
    return fminf(gx, gy);
}

// The scythe's slash leaves at the katana's size -- half its own -- and opens
// to full width over BULLET_TRAVEL_T -- at the enemy, from the opening gap. Everything else is drawn
// at the sprite's size throughout.
float BattleScene::_shot_scale(const Bullet& bl) const {
    if (bl.weapon != WEAPON_SCYTHE) return 1.0f;
    float k = bl.age / BULLET_TRAVEL_T;
    return 0.5f + 0.5f * (k < 1.0f ? k : 1.0f);
}

void BattleScene::_check_collisions() {
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        // A piercing shot inside the enemy strikes again only every
        // PIERCE_REHIT_T, however long it takes to pass through.
        if (bl.pierces && _pierce_wait > 0.0f) continue;
        if (float cr = _enemy->catch_radius()) {      // caught out of the air: no hit
            float cdx = bl.x - _enemy->x, cdy = bl.y - _enemy->y;
            if (cdx * cdx + cdy * cdy < cr * cr) { bl.active = false; _enemy->catch_shot(bl.x, bl.y); continue; }
        }
        // The enemy's centre in the shot's own frame, then its distance to
        // the nearest point of the shot's box -- grown with it -- against the
        // enemy's radius.
        // ponytail: one box for all shots, the weapon in hand's -- a shot
        // still in flight from before a swap borrows the new one's until it
        // leaves; per-shot boxes if that is ever noticed.
        float a = (float)(_shot_angle(bl) * (PI / 180.0));
        float k = _shot_scale(bl);
        float dx = _enemy->x - bl.x, dy = _enemy->y - bl.y;
        float lx =  dx * cosf(a) + dy * sinf(a);
        float ly = -dx * sinf(a) + dy * cosf(a);
        float x0 = _shot_x0 * k, x1 = _shot_x1 * k, y0 = _shot_y0 * k, y1 = _shot_y1 * k;
        float qx = lx < x0 ? x0 : lx > x1 ? x1 : lx;
        float qy = ly < y0 ? y0 : ly > y1 ? y1 : ly;
        if ((lx - qx) * (lx - qx) + (ly - qy) * (ly - qy) < _hit_r * _hit_r) {
            _enemy->take_damage(bl.damage * _enemy->damage_mult((WeaponType)bl.weapon) * _enemy->armor());
            _hits++;
            _pierce_wait = PIERCE_REHIT_T;
            if (_flash_gap <= 0.0f) { _enemy_flash = ENEMY_FLASH_T; _flash_gap = ENEMY_FLASH_GAP; }
            if (!bl.pierces) bl.active = false;
        }
    }
    float px = _bp.x, py = _bp.y;
    // Graze: an enemy shot passing within GRAZE_MARGIN of the hitbox without
    // touching it -- the reward for dodging close. Once per bullet, so a
    // slow one sitting beside the player can't be farmed.
    const float GRAZE_MARGIN = 10.0f;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active || bl.grazed) continue;
        if (bullet_touches(bl, px, py, PLAYER_R + GRAZE_MARGIN) &&
            !bullet_touches(bl, px, py, PLAYER_R)) {
            bl.grazed = true;
            _grazes++;
        }
    }
    if (_bp.iframes > 0.0f) return;
    // Whole bars, at least one: every hit is a visible chunk.
    auto hurt = [&](float damage) {
        _hit_bars = (int)ceilf(damage / HP_PER_BAR);
        _hit_t    = 0.0f;
        _bp.hp -= _hit_bars * HP_PER_BAR;
        if (_bp.hp < 0.0f) _bp.hp = 0.0f;
        _bp.iframes = 1.5f;
    };
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        if (bullet_touches(bl, px, py, PLAYER_R)) {
            hurt(bl.damage);
            bl.active = false;
        }
    }
    // Its lasers: a beam that hurts (hurt_w > 0) costs a bar to touch -- the
    // player's hitbox within hurt_w of the beam's line.
    if (_bp.iframes <= 0.0f) {
        Enemy::TeleLine tl[64];
        int nt = _enemy->telegraphs(tl, 64);
        for (int k = 0; k < nt; k++) {
            const Enemy::TeleLine& L = tl[k];
            if (L.hurt_w <= 0.0f) continue;
            float dx = L.x1 - L.x0, dy = L.y1 - L.y0, l2 = dx * dx + dy * dy;
            float t = l2 > 0.0f ? fminf(fmaxf(((px - L.x0) * dx + (py - L.y0) * dy) / l2, 0.0f), 1.0f) : 0.0f;
            if (circles_overlap(L.x0 + dx * t, L.y0 + dy * t, L.hurt_w, px, py, PLAYER_R)) { hurt(HP_PER_BAR); break; }
        }
    }
    // Its body, for an enemy that hurts to touch: the same circle shots hit.
    float touch = _enemy->contact_damage();
    if (touch > 0.0f && _bp.iframes <= 0.0f && circles_overlap(_enemy->x, _enemy->y, _hit_r, px, py, PLAYER_R))
        hurt(touch);
}

void BattleScene::_spawn_player_bullet(float angle) {
    const ProjectileProfile& wp = _bp.weapon;
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (bl.active) continue;
        bl.x = _bp.x; bl.y = _bp.y;
        bl.vx = cosf(angle) * BULLET_SPEED;
        bl.vy = sinf(angle) * BULLET_SPEED;
        bl.radius = wp.radius;
        bl.damage = wp.damage;
        bl.age = 0.0f;
        bl.weapon   = (int)_weapon_type;
        bl.material = (int)_player_ref->arsenal[_weapon_type].material;
        bl.pierces  = wp.pierces;
        bl.active = true;
        return;
    }
}

void BattleScene::_spawn_bullet_at(float ox, float oy, const BulletSpawn& bs) {
    // A mine placed outside the arena is left out: it would launch inward
    // from out of sight (they used to be culled before launching).
    if (bs.delay > 0.0f && (ox < 0.0f || ox > ARENA_W || oy < ARENA_TOP || oy > ARENA_H)) return;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (bl.active) continue;
        bl.x = ox; bl.y = oy;
        bl.vx = bs.vx; bl.vy = bs.vy;
        bl.radius = bs.radius;
        bl.damage = bs.damage;
        bl.bouncing       = bs.bouncing;
        bl.bounces        = 0;
        bl.spawner        = bs.spawner;
        bl.spawn_interval = bs.spawn_interval;
        bl.spawn_timer    = bs.spawn_interval;
        bl.homing         = bs.homing;
        bl.homing_timer   = bs.homing_timer;
        bl.delay          = bs.delay;
        bl.launch_speed   = bs.launch_speed;
        bl.launch_off     = bs.launch_off;
        bl.accel          = bs.accel;
        bl.min_speed      = bs.min_speed;
        bl.max_speed      = bs.max_speed;
        bl.age            = 0.0f;
        bl.half_len       = bs.half_len;
        bl.ang            = bs.ang;
        bl.spin           = bs.spin;
        bl.max_tilt       = bs.max_tilt;
        bl.shed_every     = bs.shed_every;
        bl.shed_t         = bs.shed_first;
        bl.shed_n         = bs.shed_n;
        bl.shed_spread    = bs.shed_spread;
        bl.shed_speed     = bs.shed_speed;
        bl.shed_left      = bs.shed_times > 0 ? bs.shed_times : -1;
        bl.shed_dies      = bs.shed_dies;
        bl.shed_spin      = bs.shed_spin;
        bl.ow             = bs.orbit_w;
        bl.zig = bs.zig; bl.zig_every = bs.zig_every; bl.zig_t = bs.zig_every * 0.5f; bl.zig_s = 1;
        bl.wave = bs.wave; bl.wave_w = bs.wave_w; bl.wave_t = 0.0f;
        bl.life = bs.life;
        if (bs.zig != 0.0f) {                         // it starts on one side of its course
            float c = cosf(bs.zig), sn = sinf(bs.zig), vx = bl.vx, vy = bl.vy;
            bl.vx = vx * c - vy * sn; bl.vy = vx * sn + vy * c;
        }
        bl.ocx = ox; bl.ocy = oy; bl.orad = 0.0f;
        bl.ocvx = bs.orbit_vx; bl.ocvy = bs.orbit_vy;
        bl.octurn = bs.drift_turn; bl.octurn_t = bs.drift_turn_for;
        bl.pa = bs.path_a; bl.pb = bs.path_b; bl.ptilt = bs.path_tilt; bl.pw = bs.path_w; bl.pphi = bs.path_phase;
        bl.pcx = bs.path_cx; bl.pcy = bs.path_cy;
        bl.pface = bs.path_face; bl.pfor = bs.path_for; bl.pround = bs.path_round; bl.peven = bs.path_even; bl.paim = bs.path_aim; bl.paim_slot = bs.path_aim_slot;
        bl.osq  = bs.orbit_squash;
        bl.oang = atan2f(bs.vy, bs.vx);
        bl.ovr  = sqrtf(bs.vx * bs.vx + bs.vy * bs.vy);
        bl.obase = bl.oang;
        if (bs.orbit_about) {                         // turning round a given middle from where it's put
            float dx = ox - bs.orbit_cx, dy = oy - bs.orbit_cy;
            bl.ocx = bs.orbit_cx; bl.ocy = bs.orbit_cy;
            bl.orad = hypotf(dx, dy); bl.oang = atan2f(dy, dx);   // (ovr stays its speed: a ring that spreads as it turns)
        }
        bl.flash_in       = bs.flash_in;
        bl.grazed         = false;
        {
            float sp = sqrtf(bs.vx * bs.vx + bs.vy * bs.vy);
            bl.ux = sp > 0.0f ? bs.vx / sp : 0.0f;
            bl.uy = sp > 0.0f ? bs.vy / sp : 0.0f;
        }
        if (bs.delay > 0.0f) bl.vx = bl.vy = 0.0f;   // a mine sits until it launches
        bl.active         = true;
        return;
    }
}

// No enemy shot is ever made on top of the player: one whose start is within
// SAFE_SPAWN (plus its own size) of the hitbox is left out. One rule for every
// enemy -- hugging a body, standing under a rain, a muzzle off to one side --
// instead of a guard in each pattern (the pattern tester's finding).
static const float SAFE_SPAWN = 24.0f;

void BattleScene::_spawn_enemy_bullet(const BulletSpawn& bs) {
    float ox = bs.from ? bs.ox : _enemy->x, oy = bs.from ? bs.oy : _enemy->y;
    float reach = SAFE_SPAWN + bs.radius + bs.half_len;
    float dx = ox - _bp.x, dy = oy - _bp.y;
    if (dx * dx + dy * dy < reach * reach) return;
    _spawn_bullet_at(ox, oy, bs);
}

// ── Drawing helpers ───────────────────────────────────────────────────────────

void BattleScene::_fill_rect(SDL_Renderer* ren, int x, int y, int w, int h,
                               Uint8 r, Uint8 g, Uint8 b, Uint8 a) {
    fc_draw_color(ren, r, g, b, a);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(ren, &rect);
}

void BattleScene::_draw_rect_outline(SDL_Renderer* ren, int x, int y, int w, int h,
                                      Uint8 r, Uint8 g, Uint8 b) {
    fc_draw_color(ren, r, g, b, 255);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderDrawRect(ren, &rect);
}

float BattleScene::hud_stamina() const {
    float max_cd = 1.0f / _bp.weapon.fire_rate;
    return 1.0f - (_bp.fire_timer > 0.0f ? _bp.fire_timer / max_cd : 0.0f);
}

// ── draw ──────────────────────────────────────────────────────────────────────

// The enemy faces the player and plays its idle loop, drawn at the player's 2x
// and centred on its hitbox; enemies without a sheet yet draw as a box. On a
// win it blinks out.
void BattleScene::_draw_enemy(SDL_Renderer* ren) const {
    if (_phase == BATTLE_PHASE_VICTORY && (_t > 0.4f || (int)(_t * 20.0f) % 2)) return;
    float k = _chain_in();
    int ex = (int)_enemy->x;
    int ey = (int)(-60.0f + (_enemy->y + 60.0f) * k);
    if (!_sheet_tried) {
        _sheet_tried = true;
        if (_enemy_id >= 0 && _enemy_id < ENEMY_SHEET_COUNT && ENEMY_SHEETS[_enemy_id].path) {
            _sheet = load_with_white(ren, ENEMY_SHEETS[_enemy_id].path, &_sheet_white);
            if (!_sheet) SDL_Log("enemy sheet %s: %s", ENEMY_SHEETS[_enemy_id].path, IMG_GetError());
            if (const char* fp = ENEMY_SHEETS[_enemy_id].flap) {
                _flap = load_with_white(ren, fp, &_flap_white);
                if (!_flap) SDL_Log("enemy flap sheet %s: %s", fp, IMG_GetError());
            }
            if (const char* ap = ENEMY_SHEETS[_enemy_id].alt) {
                _alt = load_with_white(ren, ap, &_alt_white);
                if (!_alt) SDL_Log("enemy alt sheet %s: %s", ap, IMG_GetError());
            }
            if (const char* lp = ENEMY_SHEETS[_enemy_id].log) {
                _log = IMG_LoadTexture(ren, lp);
                if (!_log) SDL_Log("enemy log sprite %s: %s", lp, IMG_GetError());
            }
            if (const char* mp = ENEMY_SHEETS[_enemy_id].marks) {
                _marks = IMG_LoadTexture(ren, mp);   // missing (not drawn yet): no marks drawn
                if (_marks) SDL_SetTextureBlendMode(_marks, SDL_BLENDMODE_BLEND);
            }
        }
        if (_sheet) {
            // Hitbox scales with the creature: 40% of the drawn frame's
            // smaller side, so a hare is a small target and a boar a big one.
            int sw, sh;
            SDL_QueryTexture(_sheet, NULL, NULL, &sw, &sh);
            const EnemySheet& es = ENEMY_SHEETS[_enemy_id];
            int fw = es.rows ? sw / es.frames : sw / (8 * es.frames), fh = es.rows ? sh / 8 : sh;
            _hit_r = 0.4f * 2.0f * (fw < fh ? fw : fh);
        }
    }

    if (_sheet) {
        int sw, sh;
        SDL_QueryTexture(_sheet, NULL, NULL, &sw, &sh);
        const EnemySheet& es = ENEMY_SHEETS[_enemy_id];
        int fw = es.rows ? sw / es.frames : sw / (8 * es.frames), fh = es.rows ? sh / 8 : sh;
        int frame = _enemy->anim_frame() >= 0 ? _enemy->anim_frame() : idle_frame_now(es, (Uint32)_anim_ms);
        int mf  = _enemy->move_facing();   // running somewhere: face that way, not the player
        int dir = sheet_dir(mf >= 0 ? mf : facing_toward(_bp.x - _enemy->x, _bp.y - _enemy->y));
        SDL_Rect src = es.rows ? SDL_Rect{ frame * fw, dir * fh, fw, fh }
                               : SDL_Rect{ (dir * es.frames + frame) * fw, 0, fw, fh };
        // Moving, the flap sheet: a wingbeat across a flight, a slither wave.
        SDL_Texture* tex = _sheet;
        float flap = _enemy->flap_phase();
        if (flap >= 0.0f && _flap) {
            int f = (int)(flap * FLAP_FRAMES) % FLAP_FRAMES;
            src = SDL_Rect{ (dir * FLAP_FRAMES + f) * fw, 0, fw, fh };
            tex = _flap;
        }
        int foot = ey + fh;   // the frame's bottom row: an alt of another size stands on the same ground
        if (!(flap >= 0.0f && _flap) && _alt && _enemy->alt_pose()) {
            // The other pose, same frame -- its own frame size, which may be
            // bigger than the idle's (Zoureg's three heads): centred, feet down.
            int aw, ah;
            SDL_QueryTexture(_alt, NULL, NULL, &aw, &ah);
            fw = es.rows ? aw / es.frames : aw / (8 * es.frames); fh = es.rows ? ah / 8 : ah;
            src = es.rows ? SDL_Rect{ frame * fw, dir * fh, fw, fh } : SDL_Rect{ (dir * es.frames + frame) * fw, 0, fw, fh };
            tex = _alt;
        }
        // Hit: the frame in solid white for a few frames.
        if (_enemy_flash > 0.0f) {
            SDL_Texture* w = tex == _flap ? _flap_white : tex == _alt ? _alt_white : _sheet_white;
            if (w) tex = w;
        }
        // Its marks on the ground (footprints), under it: seen however far,
        // fading in hard quarter steps as they age, turned in 90-degree steps.
        if (_marks) {
            Enemy::Mark mk_[48];
            int nm = _enemy->marks(mk_, 48);
            int mw, mh;
            SDL_QueryTexture(_marks, NULL, NULL, &mw, &mh);
            const int frames = 2;                    // a row of two: human foot, goose foot
            int cw = mw / frames;
            for (int i = 0; i < nm; i++) {
                const Enemy::Mark& m = mk_[i];
                // never brighter than 3/4, so a fresh print can't be read as a shot
                Uint8 a = (Uint8)(255 * (float)(int)((1.0f - fminf(fmaxf(m.age, 0.0f), 1.0f)) * 3.0f + 0.999f) / 4.0f);
                if (!a) continue;
                SDL_SetTextureAlphaMod(_marks, a);
                SDL_Rect msrc = { (m.kind % frames) * cw, 0, cw, mh };
                SDL_Rect mdst = { ((int)m.x & ~1) - cw, ((int)m.y & ~1) - mh, cw * 2, mh * 2 };
                SDL_RenderCopyEx(ren, _marks, &msrc, &mdst, (m.dir & 3) * 90.0, NULL, SDL_FLIP_NONE);
            }
            SDL_SetTextureAlphaMod(_marks, 255);
        }
        SDL_Rect dst = { ex - fw, foot - fh * 2, fw * 2, fh * 2 };
        // A ghost's opacity, by the player's distance, in hard quarter steps.
        float op = _enemy->opacity(_bp.x, _bp.y);
        Uint8 alpha = (Uint8)(255 * (float)(int)(fminf(fmaxf(op, 0.0f), 1.0f) * 4.0f + 0.001f) / 4.0f);
        if (_enemy_flash > 0.0f) alpha = 255;   // a hit always flashes it, white and whole, however unseen (the user)
        SDL_SetTextureAlphaMod(tex, alpha);
        if (k >= 1.0f) {
            SDL_RenderCopy(ren, tex, &src, &dst);
            SDL_SetTextureAlphaMod(tex, 255);
        } else {
            // Phasing in, the map's stripe wipe in reverse: bands two art
            // pixels tall fill in from alternate sides, in hard eighths.
            float fill = (float)(int)((_t / CHAIN_T) * 8.0f) / 8.0f + 0.125f;
            int sw = (int)(fw * (fill > 1.0f ? 1.0f : fill));
            for (int row = 0, band = 0; row < fh; row += 2, band++) {
                int rh = fh - row < 2 ? fh - row : 2;
                int sx = band % 2 ? fw - sw : 0;
                SDL_Rect bs = { src.x + sx, src.y + row, sw, rh };
                SDL_Rect bd = { dst.x + sx * 2, dst.y + row * 2, sw * 2, rh * 2 };
                SDL_RenderCopy(ren, tex, &bs, &bd);
            }
            SDL_SetTextureAlphaMod(tex, 255);
        }
    } else {
        int hw = ENEMY_R + 4;
        Uint8 pulse = (_phase == BATTLE_PHASE_FIGHTING) ? 200 : 80;
        _fill_rect(ren, ex - hw, ey - hw, hw*2, hw*2, 40, pulse, 40, 255);
        _draw_rect_outline(ren, ex - hw, ey - hw, hw*2, hw*2, 80, 255, 80);
    }
}

void BattleScene::draw(SDL_Renderer* ren, SDL_Texture* player_sprite) const {
    _fill_rect(ren, 0, 0, ARENA_W, ARENA_H, 0, 0, 0, 255);

    // Hit shake: the arena jumps side to side on the 2px art grid, dying
    // away over SHAKE_T. The HUD, drawn after, stays still.
    SDL_Rect vp;
    hurt_shake_begin(ren, _hit_t, &vp);


    _draw_enemy(ren);

    // Player bullets: the weapon's own shape in its ore's metal -- row is the
    // material, column the weapon, each cell drawn pointing right and turned
    // to the way it flies (the axe and club spin instead). Same 2x art pixels as the
    // enemy, and the hitbox is the same box (see the constructor). Without the
    // sheet, a square in the ore's lit tone with a white core.
    if (!_bullets_tried) {
        _bullets_tried = true;
        _bullets = load_with_fades(ren, PLAYER_SHOT_SHEET, _bullets_fade);
        if (!_bullets) SDL_Log("player bullets: %s", IMG_GetError());
    }
    const int BCELL = PLAYER_SHOT_CELL;
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        const Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        // Each shot in its own weapon and ore: one fired before a swap keeps them.
        SDL_Rect bsrc = { bl.weapon * BCELL, bl.material * BCELL, BCELL, BCELL };
        SDL_Color ore = material_color((Material)bl.material, ORE_LIT);
        if (_bullets) {
            double deg = _shot_angle(bl);
            int half = (int)(BCELL * _shot_scale(bl));
            SDL_Rect dst = { (int)bl.x - half, (int)bl.y - half, half * 2, half * 2 };
            // Leaving: over the last stretch before the edge -- a share of
            // the sprite's reach -- it dithers out in three steps, so it is
            // gone by the time its centre arrives and _move_bullets retires it.
            float m = SHOT_FADE * _shot_reach * _shot_scale(bl);
            float gap = _shot_edge_gap(bl);
            SDL_Texture* tex = _bullets;
            if (gap < m) {
                int step = (int)((1.0f - gap / m) * 3.0f);
                tex = _bullets_fade[step < 2 ? step : 2];
            }
            if (tex) SDL_RenderCopyEx(ren, tex, &bsrc, &dst, deg, NULL, SDL_FLIP_NONE);
            continue;
        }
        int r = (int)bl.radius;
        _fill_rect(ren, (int)bl.x - r, (int)bl.y - r, r*2, r*2, ore.r, ore.g, ore.b, 255);
        _fill_rect(ren, (int)bl.x - 1, (int)bl.y - 1, 2, 2, 252, 252, 252, 255);
    }

    // Player sprite (flickers during iframes). Focused (ctrl) it goes under
    // the enemy's shots -- only the hitbox dot stays over them -- so you see
    // exactly what is about to touch the dot; otherwise over them as before.
    auto draw_player = [&]() {
        bool visible = _bp.iframes <= 0.0f ||
                       ((int)(_bp.iframes * 10.0f) % 2 == 0);
        if (visible) {
            float k = _chain_in();
            float px = _from_x + (_bp.x - _from_x) * k;
            float py = _from_y + (_bp.y - _from_y) * k;
            if (player_sprite) {
                // The map's sheet at the map's 2x. The art is 11x15 at the
                // bottom middle of a 14x20 frame, so the body's centre -- where
                // the hitbox is -- sits 15 across and 25 down the 28x40 frame.
                int frame = player_frame(_player_ref);

                SDL_Rect src = { frame * 14, 0, 14, 20 };
                // 29 down rather than the body's centre at 25: the hitbox sits
                // two art pixels lower on the body, at the chest.
                SDL_Rect dst = { (int)px - 15, (int)py - 29, 28, 40 };
                // Focus (ctrl): see-through and darker so the hitbox dot reads --
                // hard quarter steps (lit, dark 1, dark 2), like the Liderc's (73) fading.
                int tier = (int)_bp.dim;
                if (tier > 0) {
                    Uint8 v = (Uint8)(255 - 64 * tier);
                    SDL_SetTextureAlphaMod(player_sprite, v);
                    SDL_SetTextureColorMod(player_sprite, v, v, v);
                }
                SDL_RenderCopy(ren, player_sprite, &src, &dst);
                SDL_SetTextureAlphaMod(player_sprite, 255);
                SDL_SetTextureColorMod(player_sprite, 255, 255, 255);
            } else {
                _fill_rect(ren, (int)px - 6, (int)py - 6, 12, 12, 220, 220, 255, 255);
            }
        }
    };
    if (_bp.focus) draw_player();

    // Enemy bullets, in the colour of the enemy firing them (exact palette
    // colours, bright enough to pop off the black). The kind shows by shape,
    // NES style: plain is solid with a white core, homing flickers white,
    // bouncing is a hollow ring until its last bounce, a spawner orb has a
    // yellow core.
    //
    // Drawn chunkier than they hit, like NES shots: a ball on the 2px art
    // grid, half-size 2*ceil((radius+1)/2) -- a 2.5 bullet draws 8x8, a 4
    // acorn 12x12 -- corners cut so it reads round. The hit stays bl.radius,
    // so the art is a size up and the dodging is unchanged.
    SDL_Color c = enemy_bullet_color(_enemy_id);
    // Warning lasers, drawn in the game's own terms -- palette colours, the
    // 2px grid, hard steps instead of fades: an outer band of the enemy's
    // colour, a lighter band, a white core. Shooting out it has a white
    // flare at its tip and at the muzzle; charged, its band pulses a step
    // wider and back; dissipating, it thins a step at a time and breaks into
    // dashes that open from the enemy outward until it's gone.
    if (_phase != BATTLE_PHASE_VICTORY) {   // won: its lasers have broken up into pickups (_win)
        Enemy::TeleLine tl[64];
        int nt = _enemy->telegraphs(tl, 64);
        Uint32 now = SDL_GetTicks();
        // bands: a darker shade of the enemy's colour outside (contrast --
        // a pale colour lightened again just snapped back to itself), its
        // own colour inside that, a white core always lit
        Uint8 dr = (Uint8)(c.r * 45 / 100), dg = (Uint8)(c.g * 45 / 100), db = (Uint8)(c.b * 45 / 100);
        Uint8 mr = c.r, mg = c.g, mb = c.b;
        for (int k = 0; k < nt; k++) {
            const Enemy::TeleLine& L = tl[k];
            float dx = L.x1 - L.x0, dy = L.y1 - L.y0, len = sqrtf(dx * dx + dy * dy);
            if (L.orb > 0.0f) {                                             // a ball: the same bands, filled round
                int pulse = (now / 70) % 2 ? 2 : 0;
                float rr[3] = { L.orb + pulse, L.orb - 4.0f, L.orb * 0.5f };
                Uint8 cr[3] = { dr, mr, 252 }, cg[3] = { dg, mg, 252 }, cb[3] = { db, mb, 252 };
                int cx = (int)L.x0 & ~1, cy = (int)L.y0 & ~1;
                for (int pass = 0; pass < 3; pass++) {
                    float r = rr[pass];
                    if (r <= 0.0f) continue;
                    for (int yy = -(int)r & ~1; yy <= (int)r; yy += 2) {
                        int half = ((int)sqrtf(fmaxf(r * r - (float)(yy * yy), 0.0f))) & ~1;
                        if (half > 0) _fill_rect(ren, cx - half, cy + yy, half * 2, 2, cr[pass], cg[pass], cb[pass], 255);
                    }
                }
                continue;
            }
            if (L.stage == 3) {                                             // a mark: thin, its own colour, blinking
                if ((now / 120) % 2) continue;
                for (int s = 0, n = (int)(len / 2.0f); s <= n; s++) {
                    float f = n ? s / (float)n : 0.0f;
                    _fill_rect(ren, ((int)(L.x0 + dx * f) & ~1) - 1, ((int)(L.y0 + dy * f) & ~1) - 1, 2, 2, mr, mg, mb, 255);
                }
                continue;
            }
            // half-widths of the three bands, in 2px steps
            int ho = 4, hm = 2, hc = 1;
            if (L.stage == 1 && (now / 70) % 2) { ho = 5; hm = 3; }          // charged: the pulse
            if (L.stage == 2) {                                             // dissipating: thinning a step at a time
                int st = (int)(L.fade * 3.99f);
                ho = 4 - st; hm = st >= 2 ? 1 : 2; hc = st >= 3 ? 0 : 1;
            }
            int steps = (int)(len / 2.0f) + 1;
            // How much of it is on screen: the dissipation runs along that
            // part, not the whole beam (most of a long one is off screen).
            int vis = 0;
            for (int s = 0; s <= steps; s++) {
                float f = steps ? s / (float)steps : 0.0f;
                float lx = L.x0 + dx * f, ly = L.y0 + dy * f;
                if (lx >= 0.0f && lx <= ARENA_W && ly >= ARENA_TOP && ly <= ARENA_H) vis = s;
            }
            // Three passes -- the dark band all along, then the colour band,
            // then the core -- so no step's outer band covers the last one's core.
            for (int pass = 0; pass < 3; pass++) {
                int hw = pass == 0 ? ho : pass == 1 ? hm : hc;
                if (!hw) continue;
                Uint8 r = pass == 0 ? dr : pass == 1 ? mr : 252, g = pass == 0 ? dg : pass == 1 ? mg : 252, bb = pass == 0 ? db : pass == 1 ? mb : 252;
                for (int s = 0; s <= vis; s++) {
                    if (L.stage == 2) {                                     // breaking up, from the enemy out
                        float f = vis ? s / (float)vis : 0.0f;
                        int gap = (int)(L.fade * 4.0f);
                        if (f < L.fade * 0.8f || (gap && (s / 3) % (gap + 1) != 0)) continue;
                    }
                    float f = steps ? s / (float)steps : 0.0f;
                    int lx = (int)(L.x0 + dx * f) & ~1, ly = (int)(L.y0 + dy * f) & ~1;
                    _fill_rect(ren, lx - hw, ly - hw, hw * 2, hw * 2, r, g, bb, 255);
                }
            }
            if (L.stage == 0) {                                             // the tip flare and the muzzle
                int tx = (int)L.x1 & ~1, ty = (int)L.y1 & ~1, mx = (int)L.x0 & ~1, my = (int)L.y0 & ~1;
                int fl = (now / 50) % 2 ? 10 : 8;                           // a cross flare, flickering a step
                _fill_rect(ren, tx - fl, ty - 2, fl * 2, 4, 252, 252, 252, 255);
                _fill_rect(ren, tx - 2, ty - fl, 4, fl * 2, 252, 252, 252, 255);
                _fill_rect(ren, tx - 4, ty - 4, 8, 8, mr, mg, mb, 255);
                _fill_rect(ren, tx - 2, ty - 2, 4, 4, 252, 252, 252, 255);
                _fill_rect(ren, mx - 6, my - 6, 12, 12, dr, dg, db, 255);    // the muzzle glow
                _fill_rect(ren, mx - 4, my - 4, 8, 8, mr, mg, mb, 255);
                _fill_rect(ren, mx - 2, my - 2, 4, 4, 252, 252, 252, 255);
            }
        }
    }
    bool flash = (SDL_GetTicks() / 100) % 2 == 0;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        const Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        if (bl.half_len > 0.0f && _log) {
            // A log: the enemy's log sprite at 2x, centred, turned to lie
            // at its angle, its frames rolling -- each log a few frames out
            // of step with the last, so they don't roll in unison.
            // A sheet with tilt rows rocks by its rows (drawn on the grid,
            // log_row) and is never turned by the engine.
            const Uint32 LOG_MS = 90;
            const EnemySheet& es = ENEMY_SHEETS[_enemy_id];
            int nf = es.log_frames, sw, sh;
            SDL_QueryTexture(_log, NULL, NULL, &sw, &sh);
            // The roll runs off the log's own age, so what it sheds (BulletSpawn
            // shed_*) can leave on a frame of the roll -- the stub at the bottom.
            int lw = sw / nf, lh = sh / es.log_rows, f = (int)(bl.age * 1000.0f / LOG_MS) % nf;
            SDL_Rect src = { f * lw, log_row(bl, es) * lh, lw, lh };
            SDL_Rect dst = { (int)bl.x - lw, (int)bl.y - lh, lw * 2, lh * 2 };
            if (es.log_rows > 1) SDL_RenderCopy(ren, _log, &src, &dst);
            else SDL_RenderCopyEx(ren, _log, &src, &dst, bl.ang * (180.0 / PI), NULL, SDL_FLIP_NONE);
            continue;
        }
        if (bl.half_len > 0.0f) {
            // A log without a sprite, on the 2px grid: in the enemy's bullet colour
            // like any of its shots, with the white core along its middle.
            // A capsule is convex, so each 2px row is one run.
            float reach = bl.half_len + bl.radius + 2.0f;
            int y0 = ((int)(bl.y - reach)) & ~1, y1 = (int)(bl.y + reach);
            int x0 = ((int)(bl.x - reach)) & ~1, x1 = (int)(bl.x + reach);
            for (int yy = y0; yy <= y1; yy += 2) {
                for (int pass = 0; pass < 2; pass++) {
                    float lim = pass ? 1.5f : bl.radius + 1.0f;   // body, then core
                    int xa = x1 + 2, xb = x0 - 2;
                    for (int xx = x0; xx <= x1; xx += 2) {
                        float nx, ny;
                        bullet_nearest(bl, xx + 1.0f, yy + 1.0f, &nx, &ny);
                        float dx = xx + 1.0f - nx, dy = yy + 1.0f - ny;
                        if (dx * dx + dy * dy <= lim * lim) { if (xx < xa) xa = xx; xb = xx; }
                    }
                    if (xa > xb) continue;
                    if (pass) _fill_rect(ren, xa, yy, xb - xa + 2, 2, 252, 252, 252, 255);
                    else      _fill_rect(ren, xa, yy, xb - xa + 2, 2, c.r, c.g, c.b, 255);
                }
            }
            continue;
        }
        int h  = 2 * (int)ceilf((bl.radius + 1.0f) / 2.0f);
        int cx = (int)bl.x & ~1, cy = (int)bl.y & ~1;
        // Homing shots flicker white; a flash_in shot flickers as it appears
        // -- and, if it has a life, again before it goes (FLASH_OUT s).
        const float FLASH_IN = 0.25f, FLASH_OUT = 0.6f;
        bool going = bl.flash_in && bl.life > 0.0f && bl.age > bl.life - FLASH_OUT;
        bool white = (bl.homing && flash) || (bl.flash_in && (bl.age < FLASH_IN || going) && (int)(bl.age * 20.0f) % 2 == 0);
        Uint8 r = white ? 252 : c.r, g = white ? 252 : c.g, b = white ? 252 : c.b;
        _fill_rect(ren, cx - h + 2, cy - h, 2*h - 4, 2*h, r, g, b, 255);
        _fill_rect(ren, cx - h, cy - h + 2, 2*h, 2*h - 4, r, g, b, 255);
        int k = h >= 6 ? 4 : 2;   // core: two art pixels across on the big ones
        if (bl.bouncing && bl.bounces < 2)
            _fill_rect(ren, cx - h + 2, cy - h + 2, 2*h - 4, 2*h - 4, 0, 0, 0, 255);   // hollow
        else if (bl.spawner)
            _fill_rect(ren, cx - k, cy - k, 2*k, 2*k, 240, 188, 60, 255);
        else if (bl.delay <= 0.0f)   // a waiting mine has no white core: it lights when it launches
            _fill_rect(ren, cx - k/2 - 1, cy - k/2 - 1, k + 2, k + 2, 252, 252, 252, 255);
    }

    if (!_bp.focus) draw_player();

    // Cancelled bullets flying in, each as the item it pays -- the menu's own
    // picture of it, at 1x.
    if (!_item_icons_tried) {
        _item_icons_tried = true;
        _item_icons = IMG_LoadTexture(ren, "assets/items.png");
    }
    bool flying = false;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        const Pickup& p = _pickups[i];
        if (!p.active) continue;
        flying = true;
        if (_item_icons) {
            SDL_Rect src = { p.item * 16, 0, 16, 16 }, dst = { (int)p.x - 8, (int)p.y - 8, 16, 16 };
            SDL_RenderCopy(ren, _item_icons, &src, &dst);
        } else {
            _fill_rect(ren, (int)p.x - 2, (int)p.y - 2, 4, 4, 252, 252, 252, 255);
        }
    }

    // Hitbox marker: the hitbox itself, a white dot -- the roundest shape the
    // art grid allows at this size, a 3x3 art-pixel circle -- with a black
    // outline so it stands off the sprite and any bullet. Always shown in a
    // fight, drawn over everything, and blinking for its first second so the
    // player sees that this dot is what gets hit.
    bool intro_blink = _t < 1.0f && (int)(_t * 8.0f) % 2;
    if (_phase == BATTLE_PHASE_FIGHTING && !intro_blink) {
        int cx = (int)_bp.x, cy = (int)_bp.y;
        const int BX[5] = { -3, 1, -1, -1, -1 }, BY[5] = { -1, -1, -3, 1, -1 };
        for (int i = 0; i < 5; i++)
            _fill_rect(ren, cx + BX[i] - 2, cy + BY[i] - 2, 6, 6, 0, 0, 0, 255);
        for (int i = 0; i < 5; i++)
            _fill_rect(ren, cx + BX[i], cy + BY[i], 2, 2, 252, 252, 252, 255);
    }

    // Victory / defeat overlay
    // The win panel waits for the pickups to land and goes as the fade out starts.
    if (_phase == BATTLE_PHASE_VICTORY && !_confirmed && (!flying || _t > 1.2f)) {
        draw_nes_panel(ren, 160, 172, 320, 148);
        draw_text(ren, "VICTORY",
                  160 + (320 - text_width("VICTORY", 2)) / 2, 186, 2, 255, 255, 255);
        // Everything it paid, as the item's picture and how many, side by
        // side: the rare ones first, their count in gold, then the common
        // stuff in white. Under anything never held before, NEW, flashing
        // gently.
        int order[ITEM_COUNT], no = 0;
        for (int pass = 0; pass < 2; pass++)
            for (int it = 0; it < ITEM_COUNT; it++)
                if (_won[it] && is_common_drop(it) == (pass == 1)) order[no++] = it;
        const int GAP = 20;
        int total = 0;
        char cnt[ITEM_COUNT][8];
        for (int i = 0; i < no; i++) {
            SDL_snprintf(cnt[i], sizeof(cnt[i]), "%d", _won[order[i]]);
            total += 32 + 6 + text_width(cnt[i], 2) + (i ? GAP : 0);
        }
        int x = 320 - total / 2;
        for (int i = 0; i < no; i++) {
            bool rare = !is_common_drop(order[i]);
            if (_item_icons) {
                SDL_Rect src = { order[i] * 16, 0, 16, 16 }, dst = { x, 214, 32, 32 };
                SDL_RenderCopy(ren, _item_icons, &src, &dst);
            }
            int w = text_width(cnt[i], 2);
            draw_text(ren, cnt[i], x + 38, 222, 2, 255, rare ? 220 : 255, rare ? 40 : 255);
            if (((_won_new >> order[i]) & 1u) && (SDL_GetTicks() / 400) % 2 == 0)
                draw_text(ren, "NEW", x + (38 + w - text_width("NEW", 1)) / 2, 252, 1, 255, 220, 40);
            x += 32 + 6 + w + GAP;
        }
        // The score under the haul: what earned it, the total, and a level-up.
        {
            char line[48];
            SDL_snprintf(line, sizeof(line), "HITS %d  GRAZE %d  DEFEAT %d", _hits, _grazes, enemy_defeat_exp(_enemy_id));
            draw_text(ren, line, 320 - text_width(line, 1) / 2, 266, 1, 200, 200, 200);
            SDL_snprintf(line, sizeof(line), "+%d EXP", _exp_gain);
            draw_text(ren, line, 320 - text_width(line, 2) / 2, 280, 2, 252, 252, 252);
            if (_levels > 0 && (SDL_GetTicks() / 400) % 2 == 0) {
                SDL_snprintf(line, sizeof(line), "LEVEL UP!  LV %d", _player_ref->level);
                draw_text(ren, line, 320 - text_width(line, 1) / 2, 302, 1, 255, 255, 80);
            }
        }
    } else if (_phase == BATTLE_PHASE_DEFEAT && !_confirmed) {
        draw_nes_panel(ren, 160, 180, 320, 70);
        draw_text(ren, "GAME OVER",
                  160 + (320 - text_width("GAME OVER", 2)) / 2, 206, 2, 255, 255, 255);
    }


    // Hit flash: white over the freeze, then red fading out in hard steps.
    hurt_flash(ren, _hit_t, ARENA_W, ARENA_H);

    // Fading in or out: black over everything in the NES's four hard steps.
    float dark = _darkness();
    if (dark > 0.0f) {
        dark = dark >= 1.0f ? 1.0f : (float)(int)(dark * 4.0f + 0.999f) / 4.0f;
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
        _fill_rect(ren, 0, 0, ARENA_W, ARENA_H, 0, 0, 0, (Uint8)(255 * dark));
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
    }

    hurt_shake_end(ren, &vp);
}
