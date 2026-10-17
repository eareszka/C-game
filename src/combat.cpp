#include "core.h"
#include "fc_palette.h"
#include "combat.h"
#include "battle.h"     // weapon_profile
#include "tilemap.h"
#include "dungeon.h"    // material_color
#include "collision.h"  // HB_*: where the feet are in the player's frame
#include "player_swing.inc"   // SWING_HAND: the hand in each swing frame
#include <SDL2/SDL_image.h>
#include <math.h>

// Seconds the knife, club and dagger take to swing.
static const float SLASH_SECONDS = 0.16f;

float weapon_cooldown_seconds(const Weapon& weapon)
{
    return weapon_shape_cooldown(weapon.type) * weapon_cooldown_mult(weapon);
}

// The cooldown the weapon's shape alone sets, before any oil.
float weapon_shape_cooldown(WeaponType w)
{
    float rate_cd = 1.0f / weapon_profile(w).fire_rate;

    SweepProfile sp = weapon_sweep_profile(w);
    if (sp.span > 0.0f)
        return sp.cooldown_is_sweep ? sp.seconds + sp.cooldown_recovery : rate_cd;

    ThrowProfile tw = weapon_throw_profile(w);
    if (tw.speed > 0.0f)
        return rate_cd * tw.cooldown_scale;

    return rate_cd;
}

float facing_angle(int facing) {
    const float Q = 0.78539816f;            // a quarter of a right angle
    switch (facing) {
    case FACE_RIGHT:      return 0.0f;
    case FACE_DOWN_RIGHT: return Q;
    case FACE_DOWN:       return 2 * Q;
    case FACE_DOWN_LEFT:  return 3 * Q;
    case FACE_LEFT:       return 4 * Q;
    case FACE_UP_LEFT:    return -3 * Q;
    case FACE_UP:         return -2 * Q;
    case FACE_UP_RIGHT:   return -Q;
    }
    return 2 * Q;
}

void weapon_swing_update(WeaponSwingState* ws, Player* player, const Input* in, float dt,
                         float hx, float hy, ResourceNodeList* resources, Tilemap* tiles,
                         const Camera* cam, int cave_ore, HarvestResult* out)
{
    if (ws->tool_cd > 0.0f) ws->tool_cd -= dt;

    Weapon weapon = equipped_weapon(player);

    if (ws->tool_cd <= 0.0f
     && (input_down(in, SDL_SCANCODE_SPACE)
      || input_down(in, SDL_SCANCODE_Z)
      || input_down(in, SDL_SCANCODE_RETURN)))
    {
        if (weapon_sweeps(weapon.type)) {
            // Set the blade going; the strikes land below, as it travels.
            SweepProfile sp = weapon_sweep_profile(weapon.type);
            ws->swing_t      = 0.0f;
            ws->swing_angle  = facing_angle(player->facing) + sp.start_offset;
            ws->swing_weapon = weapon;
            ws->tool_cd = weapon_cooldown_seconds(weapon);
        } else if (weapon_throws(weapon.type)) {
            // Launch the object and step back -- it does the striking, not us.
            // A free slot, or -- only if every one is flying -- the oldest.
            ThrownObject* t = &ws->thrown[0];
            for (ThrownObject& c : ws->thrown) {
                if (!c.live) { t = &c; break; }
                if (c.seq < t->seq) t = &c;
            }
            float ang = facing_angle(player->facing);
            t->live   = 1;
            t->x      = hx;
            t->y      = hy;
            t->ox     = hx;
            t->oy     = hy;
            t->flown  = 0.0f;
            t->dx     = cosf(ang);
            t->dy     = sinf(ang);
            t->weapon = weapon;
            t->seq    = ++ws->throw_seq;
            ws->tool_cd      = weapon_cooldown_seconds(weapon);
            ws->freeze_t     = weapon_freeze_seconds(weapon.type);
        } else {
            // Show the swing, hit or miss; a held key swings again once the
            // cooldown is out.
            if (ws->slash_t < 0.0f) {
                ws->slash_t      = 0.0f;
                ws->slash_angle  = facing_angle(player->facing);
                ws->swing_weapon = weapon;
            }
            int rn_hit = resource_nodes_try_hit(resources, hx, hy, 40, weapon, out);
            // Map tiles are only reached when no node was in range.
            if (rn_hit == 0 && tiles)
                tilemap_try_hit(tiles, hx, hy, 40, weapon, out);

            // The stab costs its cooldown whether or not it lands (the user,
            // 2026-10-12: stamina drains on a miss too), as every other
            // weapon's swing already does.
            ws->tool_cd = weapon_cooldown_seconds(weapon);

            if (out->count > 0) {
                player->facing = facing_toward(out->hits[0].x - hx, out->hits[0].y - hy);
                player->facing_locked = 1;
                // Only a connected swing roots the player: planting them for
                // a whiff would be a second penalty on top of the cooldown.
                ws->freeze_t = weapon_freeze_seconds(weapon.type);
            }
        }
    }

    if (ws->slash_t >= 0.0f && (ws->slash_t += dt) > SLASH_SECONDS) ws->slash_t = -1.0f;

    // Advance a running sweep and strike whatever it covered this frame.
    // Driven by elapsed time rather than per-frame steps so it takes the same
    // path regardless of frame rate.
    if (ws->swing_t >= 0.0f) {
        SweepProfile sp = weapon_sweep_profile(ws->swing_weapon.type);

        float t0 = ws->swing_t / sp.seconds;
        ws->swing_t += dt;
        float t1 = ws->swing_t / sp.seconds;
        if (t1 > 1.0f) t1 = 1.0f;

        resource_nodes_sweep(resources, hx, hy, sp.radius, ws->swing_angle,
                             t0 * sp.span, t1 * sp.span, ws->swing_weapon, out);
        if (tiles)
            tilemap_sweep(tiles, hx, hy, sp.radius, ws->swing_angle,
                          t0 * sp.span, t1 * sp.span, ws->swing_weapon, out);

        if (ws->swing_t >= sp.seconds) ws->swing_t = -1.0f;
    }

    // Fly every thrown object. Each is retired by the first thing it can
    // harvest -- unless it goes through them -- or by leaving the view,
    // whichever comes first. Nothing else ends one: another throw takes a
    // free slot.
    for (ThrownObject& t : ws->thrown) {
        if (!t.live) continue;
        ThrowProfile tw = weapon_throw_profile(t.weapon.type);
        float step = tw.speed * dt;
        t.x += t.dx * step;
        t.y += t.dy * step;

        if (tw.pierces) {
            // The slice of its corridor it covered this frame, measured from
            // where it was launched, so each thing in it is struck once.
            float ang = atan2f(t.dy, t.dx);
            resource_nodes_thrust(resources, t.ox, t.oy, ang, tw.radius,
                                  t.flown, t.flown + step, t.weapon, out);
            if (tiles)
                tilemap_thrust(tiles, t.ox, t.oy, ang, tw.radius,
                               t.flown, t.flown + step, t.weapon, out);
            t.flown += step;
        } else {
            int struck = resource_nodes_strike_point(resources, t.x, t.y,
                                                     tw.radius, t.weapon, out);
            if (!struck && tiles)
                struck = tilemap_strike_point(tiles, t.x, t.y, t.weapon, out);
            if (struck) t.live = 0;
        }

        if (t.live && cam) {
            // The visible world rectangle; leaving it retires the object.
            float vw = cam->screen_w / cam->zoom;
            float vh = cam->screen_h / cam->zoom;
            float rx = wrap_dpx(t.x - cam->x);
            float ry = wrap_dpy(t.y - cam->y);
            if (rx < -tw.radius || rx > vw + tw.radius ||
                ry < -tw.radius || ry > vh + tw.radius)
                t.live = 0;
        }
    }

    // Paid when a thing breaks, its whole yield at once. Rock broken in a
    // cave is that cave's ore. Every resource mined is also 1 EXP.
    for (int i = 0; i < out->count; i++) {
        const HarvestHit& hit = out->hits[i];
        if (hit.resource < 0 || !hit.destroyed) continue;
        int n = harvest_yield(hit.resource);
        if (hit.resource == RESOURCE_ROCK && cave_ore >= 0)
            ore_count(player, (Material)cave_ore) += n;
        else
            player->inventory[hit.resource] += n;
        player_gain_exp(player, n);
    }

    // The walk's phase as player_frame() reads it: step, standing, step, standing.
    static const int PHASE[4] = { 1, 0, 2, 0 };
    ws->body_frame = weapon_swing_body(ws, player->facing, weapon.type,
                                       player->is_moving ? PHASE[player->anim_step % 4] : 0);
}

bool weapon_swing_frozen_tick(WeaponSwingState* ws, Player* player, float dt) {
    if (ws->freeze_t <= 0.0f) return false;
    // Planted mid-swing. Skipping the input read is what roots the player: it
    // is also what sets facing, so the swing lands where it was aimed instead
    // of the player pivoting out from under it.
    ws->freeze_t -= dt;
    player->is_moving = 0;
    return true;
}

// The weapon pictures the menu shows (WEAPON_ICON_SHEET), loaded on the first
// draw: the renderer is not there before.
static SDL_Texture* weapon_icons(SDL_Renderer* ren) {
    static SDL_Texture* tex = nullptr;
    static bool tried = false;
    if (!tried) {
        tried = true;
        tex = IMG_LoadTexture(ren, WEAPON_ICON_SHEET);
        if (!tex) SDL_Log("weapon icons %s: %s", WEAPON_ICON_SHEET, IMG_GetError());
    }
    return tex;
}

// The eight ways a weapon is ever drawn on the map: step 0 points right, each
// step 45 degrees on, clockwise. The even ones are the weapon's held drawing
// pointing right and the odd ones the one pointing up and right (step 7),
// turned only by quarter turns -- so no pose is resampled (ITEM_STYLE.md).
static int pose_step(float ang) { return (int)lroundf(ang / 0.78539816f) & 7; }

// Which way round a swing goes for a player facing along `facing`: clockwise,
// or the other way when they face left, so that to either side the blade
// comes down from above -- the swing is the mirror of itself, as the player
// is. +1 or -1 pose steps.
static int swing_turn(float facing) { return cosf(facing) < -0.01f ? -1 : 1; }

// A sweep's blade: where its arc starts as it is drawn, the pose it starts in
// and the pose it has reached, as bearings. swing_angle is where the arc
// starts going clockwise; facing left it starts at the far end and comes back.
// ponytail: only the drawing is mirrored -- the strikes still land going
// clockwise (weapon_swing_update), over the same arc in the same time.
struct Blade { float facing; int turn; float first, cur; };
static Blade sweep_blade(const WeaponSwingState* ws, const SweepProfile& sp) {
    const float STEP = 0.78539816f;
    float prog = ws->swing_t / sp.seconds;
    if (prog > 1.0f) prog = 1.0f;
    Blade b;
    b.facing = ws->swing_angle - sp.start_offset;
    b.turn   = swing_turn(b.facing);
    float start = b.facing + b.turn * sp.start_offset;
    b.first = roundf(start / STEP) * STEP;
    b.cur   = roundf((start + b.turn * prog * sp.span) / STEP) * STEP;
    return b;
}

// A pose step's place among the swing frames' facings (SWING_FRAME0, entity.h:
// down, up, left, right, down-left, down-right, up-left, up-right).
static const int STEP_FACING[8] = { 3, 5, 0, 4, 2, 6, 1, 7 };

int weapon_swing_body(const WeaponSwingState* ws, int facing, WeaponType in_hand, int walk_phase) {
    enum { BACK, STRUCK, RAISED };
    int step, arm;
    if (ws->slash_t >= 0.0f) {
        step = pose_step(ws->slash_angle);
        arm = ws->swing_weapon.type == WEAPON_CLUB && ws->slash_t < SLASH_SECONDS * 0.5f ? BACK : STRUCK;
    } else if (ws->swing_t >= 0.0f) {
        SweepProfile sp = weapon_sweep_profile(ws->swing_weapon.type);
        Blade b = sweep_blade(ws, sp);
        step = pose_step(b.facing);
        // A full turn is whirled from a raised hand, the player facing as they
        // were (the user, 2026-10-12); a cut is drawn back, then struck.
        arm = sp.span > 6.0f ? RAISED : fabsf(b.cur - b.first) < 0.01f ? BACK : STRUCK;
    } else if (ws->freeze_t > 0.0f && weapon_throws(in_hand)) {
        step = pose_step(facing_angle(facing));
        arm = ws->freeze_t > weapon_freeze_seconds(in_hand) * 0.6f ? BACK : STRUCK;
    } else {
        return -1;
    }
    return SWING_FRAME0 + STEP_FACING[step] * 9 + walk_phase * 3 + arm;
}

// How long each weapon's held drawing is, grip to point, in its own pixels
// (WeaponType order; LENGTH of the drawings in weapons_design.py's HELD).
static const int HELD_LENGTH[WEAPON_COUNT] = { 9, 11, 11, 11, 16, 14, 14 };

// A weapon in its ore at 2x art pixels and the camera's zoom, its grip at
// screen (gx, gy), in pose `step`.
// ponytail: a turned pose carries its shading with it, so one pointing down
// and left is lit from below. Drawn poses per direction if that reads wrong.
static void draw_weapon_pose(SDL_Renderer* ren, const Weapon& w, float gx, float gy,
                             int step, float zoom) {
    SDL_Texture* tex = weapon_icons(ren);
    if (!tex) return;
    step &= 7;
    bool straight = !(step & 1);
    int size = (int)(WEAPON_ICON_CELL * 2 * zoom);
    SDL_Rect src = { (straight ? WEAPON_HELD_X : WEAPON_HELD_DIAG_X) + (int)w.type * WEAPON_ICON_CELL,
                     (int)w.material * WEAPON_ICON_CELL, WEAPON_ICON_CELL, WEAPON_ICON_CELL };
    // The grip: the straight drawing's left edge at its middle, the diagonal
    // one's bottom left corner.
    SDL_Point grip = { 0, straight ? size / 2 : size };
    SDL_Rect dst = { (int)gx, (int)gy - grip.y, size, size };
    SDL_RenderCopyEx(ren, tex, &src, &dst, (straight ? step : step - 7) * 45.0, &grip, SDL_FLIP_NONE);
}

// The weapon in the hand of the body's swing frame, in pose `step`; (cx, cy)
// is the middle of the feet on screen. Its butt end -- the end pixel of its
// outline -- goes on the hand's pixel (SWING_HAND), whichever way it is turned:
// CORNER is where that puts the drawing's grip corner, a pose each.
static void draw_weapon_in_hand(SDL_Renderer* ren, const WeaponSwingState* ws, int cx, int cy,
                                int step, float zoom) {
    static const SDL_Point CORNER[8] = { {0, 0}, {0, 0}, {1, 0}, {1, 0}, {1, 1}, {1, 1}, {0, 1}, {0, 1} };
    float gx = (float)cx, gy = (float)cy;
    step &= 7;
    if (ws->body_frame >= SWING_FRAME0) {
        const SDL_Point& h = SWING_HAND[ws->body_frame - SWING_FRAME0];
        // the frame's top left is the feet's middle less where the feet are in it
        gx = cx + ((h.x + CORNER[step].x) * 2 - (HB_X1 + HB_X2) * 0.5f) * zoom;
        gy = cy + ((h.y + CORNER[step].y) * 2 - (HB_Y1 + HB_Y2) * 0.5f) * zoom;
    }
    draw_weapon_pose(ren, ws->swing_weapon, gx, gy, step, zoom);
}

// The 45 degrees of a sweep's arc centred on `mid`, at reach r on screen, as
// solid squares of two art pixels in one palette colour; `dither` leaves out
// every other one. Stands in for a fading trail: nothing is blended. With a
// `crescent` (+1 or -1, the way the blade is turning) it is three squares deep
// at the blade's end tapering to one at its tail, the leading squares white:
// the scythe's.
static void draw_arc_step(SDL_Renderer* ren, int cx, int cy, float r, float mid, float zoom,
                          SDL_Color c, bool dither, int crescent = 0) {
    const float HALF = 0.39269908f;             // 22.5 degrees
    int b = (int)(4 * zoom);                    // two art pixels
    if (b < 1) b = 1;
    int n = (int)(r * 2 * HALF / b);
    int way = crescent ? crescent : 1;
    for (int i = 0; i <= n; i += dither ? 2 : 1) {
        float along = (float)i / n;             // 0 at the tail, 1 at the blade
        float a = mid + way * (-HALF + 2 * HALF * along);
        int deep = crescent ? 1 + (int)(2 * along + 0.5f) : 1;
        if (crescent && i >= n - 1) fc_draw_color(ren, 252, 252, 252, 255);
        else                        fc_draw_color(ren, c.r, c.g, c.b, 255);
        for (int k = 0; k < deep; k++) {
            float rr = r - k * b;
            SDL_Rect sq = { cx + (int)floorf(cosf(a) * rr / b) * b, cy + (int)floorf(sinf(a) * rr / b) * b, b, b };
            SDL_RenderFillRect(ren, &sq);
        }
    }
}

void weapon_swing_draw(const WeaponSwingState* ws, float px, float py,
                       const Camera* cam, SDL_Renderer* ren)
{
    const float STEP = 0.78539816f;             // 45 degrees
    float z = cam->zoom;
    int cx = cam_screen_x(cam, px);
    int cy = cam_screen_y(cam, py);

    // Thrown objects: the weapon itself about its middle -- one that goes
    // through flying point first, the rest tumbling end over end a pose at a
    // time.
    for (const ThrownObject& t : ws->thrown) {
        if (!t.live) continue;
        int step = weapon_throw_profile(t.weapon.type).pierces      ? pose_step(atan2f(t.dy, t.dx))
                                                                    : (int)(world_ms() / 60) & 7;
        float half = HELD_LENGTH[t.weapon.type] * z;       // half its length at 2x
        draw_weapon_pose(ren, t.weapon, cam_screen_x(cam, t.x) - cosf(step * STEP) * half,
                         cam_screen_y(cam, t.y) - sinf(step * STEP) * half, step, z);
    }

    // Knife and dagger: one pose, struck straight out the way the player
    // faces and held, as the first Zelda's sword is. The club is drawn back
    // 45 degrees to one side first (the user, 2026-10-12).
    if (ws->slash_t >= 0.0f) {
        int face = pose_step(ws->slash_angle);
        bool back = ws->swing_weapon.type == WEAPON_CLUB && ws->slash_t < SLASH_SECONDS * 0.5f;
        draw_weapon_in_hand(ren, ws, cx, cy, back ? face - swing_turn(ws->slash_angle) : face, z);
    }

    if (ws->swing_t < 0.0f) return;

    SweepProfile sp = weapon_sweep_profile(ws->swing_weapon.type);
    if (sp.span <= 0.0f) return;

    // The blade goes round a pose at a time: the bearing it has reached,
    // snapped to the nearest 45 degrees.
    Blade b = sweep_blade(ws, sp);

    // The arc it cuts, at its reach: the 45 degrees it is in solid in the
    // ore's lit tone, the 45 before -- once it has cut them -- dithered in
    // the base tone, so the direction of travel reads at a glance.
    float r = sp.radius * z;
    if (fabsf(b.cur - b.first) > 0.01f)
        draw_arc_step(ren, cx, cy, r, b.cur - b.turn * STEP, z, material_color(ws->swing_weapon.material, ORE_BASE), true);
    draw_arc_step(ren, cx, cy, r, b.cur, z, material_color(ws->swing_weapon.material, ORE_LIT), false,
                  sp.span > 6.0f ? b.turn : 0);

    draw_weapon_in_hand(ren, ws, cx, cy, pose_step(b.cur), z);
}
