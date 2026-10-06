#include "fc_palette.h"
#include "combat.h"
#include "battle.h"     // weapon_profile
#include "tilemap.h"
#include "dungeon.h"    // material_color
#include <SDL2/SDL_image.h>
#include <math.h>

// Seconds the knife, club and dagger take to swing across, and how far.
static const float SLASH_SECONDS = 0.16f;
static const float SLASH_SPAN    = 2.0943951f;   // 120 degrees, centred on facing

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

    ThrustProfile tp = weapon_thrust_profile(w);
    if (tp.half_width > 0.0f)
        return tp.cooldown_is_swing ? tp.seconds + tp.cooldown_recovery
                                    : rate_cd * tp.cooldown_scale;

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
                         const Camera* cam, bool attack_blocked, int cave_ore, HarvestResult* out)
{
    if (ws->tool_cd > 0.0f) ws->tool_cd -= dt;

    Weapon weapon = equipped_weapon(player);

    if (ws->tool_cd <= 0.0f && !attack_blocked
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
            t->dx     = cosf(ang);
            t->dy     = sinf(ang);
            t->weapon = weapon;
            t->seq    = ++ws->throw_seq;
            ws->tool_cd      = weapon_cooldown_seconds(weapon);
            ws->freeze_t     = weapon_freeze_seconds(weapon.type);
        } else if (weapon_thrusts(weapon.type)) {
            ThrustProfile tp = weapon_thrust_profile(weapon.type);
            float ang = facing_angle(player->facing);

            // Find the first thing in the corridor and drive that far plus the
            // overshoot. With nothing to bite on, the thrust still goes out to
            // its base reach rather than stopping dead.
            float first = resource_nodes_first_along(resources, hx, hy, ang,
                                                      tp.half_width, tp.base_reach);
            if (tiles) {
                float dt_ = tilemap_first_along(tiles, hx, hy, ang, tp.half_width, tp.base_reach);
                if (first < 0.0f || (dt_ >= 0.0f && dt_ < first)) first = dt_;
            }

            ws->swing_t      = 0.0f;
            ws->swing_angle  = ang;
            ws->swing_len    = (first >= 0.0f) ? first + tp.overshoot : tp.base_reach;
            ws->swing_weapon = weapon;
            ws->tool_cd = weapon_cooldown_seconds(weapon);
            ws->freeze_t = weapon_freeze_seconds(weapon.type);
        } else {
            // Show the swing, hit or miss; a held key swings again once it
            // has finished.
            if (ws->slash_t < 0.0f) {
                ws->slash_t      = 0.0f;
                ws->slash_angle  = facing_angle(player->facing);
                ws->swing_weapon = weapon;
            }
            int rn_hit = resource_nodes_try_hit(resources, hx, hy, 40, weapon, out);
            // Map tiles are only reached when no node was in range.
            if (rn_hit == 0 && tiles)
                tilemap_try_hit(tiles, hx, hy, 40, weapon, out);

            if (out->count > 0) {
                player->facing = facing_toward(out->hits[0].x - hx, out->hits[0].y - hy);
                player->facing_locked = 1;
                ws->tool_cd  = weapon_cooldown_seconds(weapon);
                // Only on a connected swing -- a whiff sets no cooldown either,
                // so rooting the player for one would be a free penalty.
                ws->freeze_t = weapon_freeze_seconds(weapon.type);
            }
        }
    }

    if (ws->slash_t >= 0.0f && (ws->slash_t += dt) > SLASH_SECONDS) ws->slash_t = -1.0f;

    // Advance a running sweep/thrust and strike whatever it covered this
    // frame. Driven by elapsed time rather than per-frame steps so it takes
    // the same path regardless of frame rate.
    if (ws->swing_t >= 0.0f) {
        if (weapon_sweeps(ws->swing_weapon.type)) {
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
        } else {
            // Thrust: the head travels out along the line, striking the slice of
            // the corridor it covered this frame.
            ThrustProfile tp = weapon_thrust_profile(ws->swing_weapon.type);

            float t0 = ws->swing_t / tp.seconds;
            ws->swing_t += dt;
            float t1 = ws->swing_t / tp.seconds;
            if (t1 > 1.0f) t1 = 1.0f;

            resource_nodes_thrust(resources, hx, hy, ws->swing_angle, tp.half_width,
                                  t0 * ws->swing_len, t1 * ws->swing_len, ws->swing_weapon, out);
            if (tiles)
                tilemap_thrust(tiles, hx, hy, ws->swing_angle, tp.half_width,
                              t0 * ws->swing_len, t1 * ws->swing_len, ws->swing_weapon, out);

            if (ws->swing_t >= tp.seconds) ws->swing_t = -1.0f;
        }
    }

    // Fly every thrown object. Each is retired by the first thing it can
    // harvest, or by leaving the view -- whichever comes first.
    for (ThrownObject& t : ws->thrown) {
        if (!t.live) continue;
        ThrowProfile tw = weapon_throw_profile(t.weapon.type);
        t.x += t.dx * tw.speed * dt;
        t.y += t.dy * tw.speed * dt;

        int struck = resource_nodes_strike_point(resources, t.x, t.y,
                                                 tw.radius, t.weapon, out);
        if (!struck && tiles)
            struck = tilemap_strike_point(tiles, t.x, t.y, t.weapon, out);
        if (struck) t.live = 0;

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
    // cave is that cave's ore.
    for (int i = 0; i < out->count; i++) {
        const HarvestHit& hit = out->hits[i];
        if (hit.resource < 0 || !hit.destroyed) continue;
        int n = harvest_yield(hit.resource);
        if (hit.resource == RESOURCE_ROCK && cave_ore >= 0)
            ore_count(player, (Material)cave_ore) += n;
        else
            player->inventory[hit.resource] += n;
    }
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

// A weapon in its ore at 2x art pixels and the camera's zoom, its grip at
// screen (gx, gy) and its point towards `ang` (radians, y down). The art is
// drawn grip low left, point high right -- -45 degrees -- so it turns by
// ang + 45 about the grip corner.
static void draw_weapon_at_grip(SDL_Renderer* ren, const Weapon& w, float gx, float gy,
                                float ang, float zoom) {
    SDL_Texture* tex = weapon_icons(ren);
    if (!tex) return;
    int size = (int)(WEAPON_ICON_CELL * 2 * zoom);
    SDL_Rect src = { (int)w.type * WEAPON_ICON_CELL, (int)w.material * WEAPON_ICON_CELL,
                     WEAPON_ICON_CELL, WEAPON_ICON_CELL };
    SDL_Rect dst = { (int)gx, (int)gy - size, size, size };
    SDL_Point grip = { 0, size };
    SDL_RenderCopyEx(ren, tex, &src, &dst, ang * 57.29578 + 45.0, &grip, SDL_FLIP_NONE);
}

// How long the weapon drawn grip to point, on screen.
static float weapon_length(float zoom) { return WEAPON_ICON_CELL * 2 * zoom * 1.41421f; }

void weapon_swing_draw(const WeaponSwingState* ws, float px, float py,
                       const Camera* cam, SDL_Renderer* ren)
{
    float z = cam->zoom;
    int cx = cam_screen_x(cam, px);
    int cy = cam_screen_y(cam, py);

    // Thrown objects: the weapon itself, tumbling end over end as it flies.
    for (const ThrownObject& t : ws->thrown) {
        if (!t.live) continue;
        SDL_Texture* tex = weapon_icons(ren);
        if (!tex) continue;
        int size = (int)(WEAPON_ICON_CELL * 2 * z);
        SDL_Rect src = { (int)t.weapon.type * WEAPON_ICON_CELL, (int)t.weapon.material * WEAPON_ICON_CELL,
                         WEAPON_ICON_CELL, WEAPON_ICON_CELL };
        SDL_Rect dst = { cam_screen_x(cam, t.x) - size / 2, cam_screen_y(cam, t.y) - size / 2, size, size };
        SDL_RenderCopyEx(ren, tex, &src, &dst, SDL_GetTicks() * 1.03, NULL, SDL_FLIP_NONE);
    }

    // Knife, club, dagger: a quick swing across the way the player faces.
    if (ws->slash_t >= 0.0f) {
        float prog = ws->slash_t / SLASH_SECONDS;
        if (prog > 1.0f) prog = 1.0f;
        float ang = ws->slash_angle - SLASH_SPAN * 0.5f + SLASH_SPAN * prog;
        draw_weapon_at_grip(ren, ws->swing_weapon, (float)cx, (float)cy, ang, z);
    }

    if (ws->swing_t < 0.0f) return;

    // Thrust: the weapon driving out point first, its point at the head of
    // the thrust.
    if (weapon_thrusts(ws->swing_weapon.type)) {
        ThrustProfile tp = weapon_thrust_profile(ws->swing_weapon.type);
        float prog = ws->swing_t / tp.seconds;
        if (prog > 1.0f) prog = 1.0f;
        float reach = ws->swing_len * prog * z;
        float len = weapon_length(z);
        if (reach < len) reach = len;   // never drawn back through the player
        float ca = cosf(ws->swing_angle), sa = sinf(ws->swing_angle);
        draw_weapon_at_grip(ren, ws->swing_weapon, cx + ca * (reach - len), cy + sa * (reach - len),
                            ws->swing_angle, z);
        return;
    }

    SweepProfile sp = weapon_sweep_profile(ws->swing_weapon.type);
    if (sp.span <= 0.0f) return;

    float r = sp.radius * z;
    float prog = ws->swing_t / sp.seconds;
    if (prog > 1.0f) prog = 1.0f;

    // Trail along the arc already cut, in the ore's base tone, brightest just
    // behind the blade so the direction of travel reads at a glance.
    SDL_Color base = material_color(ws->swing_weapon.material, ORE_BASE);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
    const int STEPS = 28;
    for (int i = 0; i < STEPS; i++) {
        float f0 = (float)i / STEPS;
        float f1 = (float)(i + 1) / STEPS;
        float a0 = ws->swing_angle + f0 * prog * sp.span;
        float a1 = ws->swing_angle + f1 * prog * sp.span;
        fc_draw_color(ren, base.r, base.g, base.b, (Uint8)(25.0f + 165.0f * f1));
        SDL_RenderDrawLine(ren,
            cx + (int)(cosf(a0) * r), cy + (int)(sinf(a0) * r),
            cx + (int)(cosf(a1) * r), cy + (int)(sinf(a1) * r));
    }
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);

    // The weapon itself, held from the player out along the blade's bearing.
    float cur = ws->swing_angle + prog * sp.span;
    draw_weapon_at_grip(ren, ws->swing_weapon, (float)cx, (float)cy, cur, z);
}
