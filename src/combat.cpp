#include "combat.h"
#include "battle.h"     // weapon_profile
#include "tilemap.h"
#include <math.h>

float weapon_cooldown_seconds(WeaponType w)
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
    if (facing >= 8) return 0.0f;           // right
    if (facing >= 6) return 3.1415927f;     // left
    if (facing >= 3) return -1.5707963f;    // up
    return 1.5707963f;                      // down
}

void weapon_swing_update(WeaponSwingState* ws, Player* player, const Input* in, float dt,
                         float hx, float hy, ResourceNodeList* resources, Tilemap* tiles,
                         const Camera* cam, bool attack_blocked, HarvestResult* out)
{
    if (ws->tool_cd > 0.0f) ws->tool_cd -= dt;

    WeaponType weapon = player->equipped_weapon;

    if (ws->tool_cd <= 0.0f && !attack_blocked
     && (input_down(in, SDL_SCANCODE_SPACE)
      || input_down(in, SDL_SCANCODE_Z)
      || input_down(in, SDL_SCANCODE_RETURN)))
    {
        if (weapon_sweeps(weapon)) {
            // Set the blade going; the strikes land below, as it travels.
            SweepProfile sp = weapon_sweep_profile(weapon);
            ws->swing_t      = 0.0f;
            ws->swing_angle  = facing_angle(player->facing) + sp.start_offset;
            ws->swing_weapon = weapon;
            ws->tool_cd = weapon_cooldown_seconds(weapon);
        } else if (weapon_throws(weapon)) {
            // Launch the object and step back -- it does the striking, not us.
            float ang = facing_angle(player->facing);
            ws->throw_live   = 1;
            ws->throw_x      = hx;
            ws->throw_y      = hy;
            ws->throw_dx     = cosf(ang);
            ws->throw_dy     = sinf(ang);
            ws->throw_weapon = weapon;
            ws->tool_cd      = weapon_cooldown_seconds(weapon);
            ws->freeze_t     = weapon_freeze_seconds(weapon);
        } else if (weapon_thrusts(weapon)) {
            ThrustProfile tp = weapon_thrust_profile(weapon);
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
            ws->freeze_t = weapon_freeze_seconds(weapon);
        } else {
            int rn_hit = resource_nodes_try_hit(resources, hx, hy, 40, weapon, out);
            // Map tiles are only reached when no node was in range.
            if (rn_hit == 0 && tiles)
                tilemap_try_hit(tiles, hx, hy, 40, weapon, out);

            if (out->count > 0) {
                float ddx = out->hits[0].x - hx;
                float ddy = out->hits[0].y - hy;
                if (ddx * ddx >= ddy * ddy)
                    player->facing = ddx >= 0.0f ? 8 : 6;
                else
                    player->facing = ddy >= 0.0f ? 0 : 3;
                player->facing_locked = 1;
                ws->tool_cd  = weapon_cooldown_seconds(weapon);
                // Only on a connected swing -- a whiff sets no cooldown either,
                // so rooting the player for one would be a free penalty.
                ws->freeze_t = weapon_freeze_seconds(weapon);
            }
        }
    }

    // Advance a running sweep/thrust and strike whatever it covered this
    // frame. Driven by elapsed time rather than per-frame steps so it takes
    // the same path regardless of frame rate.
    if (ws->swing_t >= 0.0f) {
        if (weapon_sweeps(ws->swing_weapon)) {
            SweepProfile sp = weapon_sweep_profile(ws->swing_weapon);

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
            ThrustProfile tp = weapon_thrust_profile(ws->swing_weapon);

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

    // Fly the thrown object. It is retired by the first thing it can harvest,
    // or by leaving the view -- whichever comes first.
    if (ws->throw_live) {
        ThrowProfile tw = weapon_throw_profile(ws->throw_weapon);
        ws->throw_x += ws->throw_dx * tw.speed * dt;
        ws->throw_y += ws->throw_dy * tw.speed * dt;

        int struck = resource_nodes_strike_point(resources, ws->throw_x, ws->throw_y,
                                                 tw.radius, ws->throw_weapon, out);
        if (!struck && tiles)
            struck = tilemap_strike_point(tiles, ws->throw_x, ws->throw_y, ws->throw_weapon, out);
        if (struck) ws->throw_live = 0;

        if (ws->throw_live && cam) {
            // The visible world rectangle; leaving it retires the object.
            float vw = cam->screen_w / cam->zoom;
            float vh = cam->screen_h / cam->zoom;
            if (ws->throw_x < cam->x - tw.radius || ws->throw_x > cam->x + vw + tw.radius ||
                ws->throw_y < cam->y - tw.radius || ws->throw_y > cam->y + vh + tw.radius)
                ws->throw_live = 0;
        }
    }

    for (int i = 0; i < out->count; i++)
        if (out->hits[i].resource >= 0)
            player->inventory[out->hits[i].resource]++;
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

void weapon_swing_draw(const WeaponSwingState* ws, float px, float py,
                       const Camera* cam, SDL_Renderer* ren)
{
    // Thrown object: a small blade tumbling end over end as it flies.
    if (ws->throw_live) {
        float z = cam->zoom;
        int cx = (int)((ws->throw_x - cam->x) * z);
        int cy = (int)((ws->throw_y - cam->y) * z);
        float r = weapon_throw_profile(ws->throw_weapon).radius * z;
        float spin = (float)SDL_GetTicks() * 0.018f;

        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
        // Two crossed bars, rotating -- reads as a tumbling axe head.
        for (int k = 0; k < 2; k++) {
            float a = spin + k * 1.5707963f;
            int ax = cx + (int)(cosf(a) * r), ay = cy + (int)(sinf(a) * r);
            int bx = cx - (int)(cosf(a) * r), by = cy - (int)(sinf(a) * r);
            SDL_SetRenderDrawColor(ren, k == 0 ? 235 : 170, k == 0 ? 235 : 130,
                                        k == 0 ? 245 : 80, 240);
            SDL_RenderDrawLine(ren, ax, ay, bx, by);
            SDL_RenderDrawLine(ren, ax, ay + 1, bx, by + 1);
        }
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
    }

    if (ws->swing_t < 0.0f) return;

    // Thrust: a shaft driving outward, with the head bright at its tip.
    if (weapon_thrusts(ws->swing_weapon)) {
        ThrustProfile tp = weapon_thrust_profile(ws->swing_weapon);
        float z  = cam->zoom;
        int cx = (int)((px - cam->x) * z);
        int cy = (int)((py - cam->y) * z);

        float prog = ws->swing_t / tp.seconds;
        if (prog > 1.0f) prog = 1.0f;
        float reach = ws->swing_len * prog * z;
        float ca = cosf(ws->swing_angle), sa = sinf(ws->swing_angle);
        int hxp = cx + (int)(ca * reach);
        int hyp = cy + (int)(sa * reach);

        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);

        // Shaft, thickened across the line of travel.
        SDL_SetRenderDrawColor(ren, 200, 215, 245, 190);
        for (int o = -1; o <= 1; o++) {
            int ox = (int)(-sa * o), oy = (int)(ca * o);
            SDL_RenderDrawLine(ren, cx + ox, cy + oy, hxp + ox, hyp + oy);
        }

        // Head: a short bar across the tip so the reach is easy to read.
        SDL_SetRenderDrawColor(ren, 255, 255, 255, 240);
        int wx = (int)(-sa * tp.half_width * z);
        int wy = (int)( ca * tp.half_width * z);
        SDL_RenderDrawLine(ren, hxp - wx, hyp - wy, hxp + wx, hyp + wy);

        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
        return;
    }

    SweepProfile sp = weapon_sweep_profile(ws->swing_weapon);
    if (sp.span <= 0.0f) return;

    float z = cam->zoom;
    int cx = (int)((px - cam->x) * z);
    int cy = (int)((py - cam->y) * z);
    float r = sp.radius * z;

    float prog = ws->swing_t / sp.seconds;
    if (prog > 1.0f) prog = 1.0f;

    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);

    // Trail along the arc already cut, brightest just behind the blade so the
    // direction of travel reads at a glance.
    const int STEPS = 28;
    for (int i = 0; i < STEPS; i++) {
        float f0 = (float)i / STEPS;
        float f1 = (float)(i + 1) / STEPS;
        float a0 = ws->swing_angle + f0 * prog * sp.span;
        float a1 = ws->swing_angle + f1 * prog * sp.span;
        SDL_SetRenderDrawColor(ren, 210, 225, 255, (Uint8)(25.0f + 165.0f * f1));
        SDL_RenderDrawLine(ren,
            cx + (int)(cosf(a0) * r), cy + (int)(sinf(a0) * r),
            cx + (int)(cosf(a1) * r), cy + (int)(sinf(a1) * r));
    }

    // The blade itself.
    float cur = ws->swing_angle + prog * sp.span;
    int bx = cx + (int)(cosf(cur) * r);
    int by = cy + (int)(sinf(cur) * r);
    SDL_SetRenderDrawColor(ren, 255, 255, 255, 235);
    SDL_RenderDrawLine(ren, cx, cy, bx, by);
    SDL_RenderDrawLine(ren, cx, cy + 1, bx, by + 1);

    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
}
