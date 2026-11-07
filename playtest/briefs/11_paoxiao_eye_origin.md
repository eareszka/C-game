# Bullet task: Paoxiao (11) -- the eye volley leaves from the eye

From the user (2026-11-06), via the animation session: "have the eye bullet cluster spawn from the eye
opening exactly at its position".

- The cry's eye-of-bullets (`Paoxiao::breathe`) now leaves from the enemy's middle (x, y). Make every
  bullet of it start at the flank eye's opening (`from = true; ox, oy`), keeping the shape/drift as now.
- New sheet (animation session, PixelLab): 56x52 frame drawn 2x about its middle; `four_views()` is on,
  so the view is `facing_toward4(px - x, py - y)` (or `move_facing()` when it isn't -1). The cry fires on
  idle frame 2. The eye's middle on that frame, in frame px, measured from the installed sheet:
    down  (facing the player below it): (36.8, 26.6)
    right:                              (27.5, 26.8)
    left (the right view mirrored):     (27.5, 26.8)
    up    (its back -- no eye drawn):   use (27.5, 26.8) too
  Screen: ox = x + (fx + 0.5 - 28) * 2, oy = y + (fy + 0.5 - 26) * 2.
  (Phase 2's eye shot in the wind-up can leave from the same spot if you like.)
Preview `game.exe --battle 11` (`C:\msys64\mingw64\bin` first on PATH); the user approves there.

## From the user (2026-11-06): the eye expands in place
"the whole eye should expand from the point of the eye and not follow the player"
- The eye of bullets GROWS outward from the flank eye's point (its lids/iris/pupil spreading in its shape)
  with NO shared drift toward the player -- drop the `dx, dy` drift at the player. It just expands from
  where the eye is.

## From the user (2026-11-06): faster
"have those bullets expand out way faster" -- the eye of bullets grows out from the eye WAY faster (a big
jump in its spread speeds, not a nudge).

## From the user (2026-11-06): exact at every angle; no fading bullets
"the eye pattern still is slightly off the middle of the eye it needs to be perfect at all angles. no fading
bullets for this fight"
1. The eye MOVES between idle frames, and my first numbers were the white pixels' centroid (the down view
   was 0.7 frame px off the opening's middle). Use this table: the eye opening's middle, frame px, measured
   on the installed sheets (playtest/briefs/_eye_table_11.txt, regenerate it if the sheets change):
     idle 11_paoxiao.png (5 frames)        f0          f1           f2 (cry)     f3           f4
       down                              (38.0,27.0)* (38.0,27.5)  (37.5,26.5)  (38.0,26.5)  (38.0,27.0)*
       right                             (27.5,27.5)* (27.5,28.0)  (27.5,27.0)  (27.5,27.0)  (27.5,28.0)
       left (measured, use as is)        (27.5,27.5)* (27.5,28.0)  (27.5,27.0)  (27.5,27.0)  (27.5,28.0)
       up (its back, no eye drawn)       (27.5,27.0)* on every frame
     warning, 11_paoxiao_leap.png frames 4-5 (state AIM; frame = 4 + (int)(st / 0.13f) % 2):
       down (38.5,25.5) (37.0,26.5)   right (28.5,27.0) (26.5,28.0)   left (26.5,27.0) (28.5,28.0)
       up (27.5,27.0)*
   (* = the eye isn't open on that frame; nearest sensible spot.)
   - The left view's numbers are measured -- use them directly, don't negate the right's offset.
   - Know the idle frame on screen: keep the last frame from `on_idle_frame(frame, ...)` (called each time
     the idle turns), so the 0.9 s eye shot uses the right row; the cry is always frame 2.
   - Screen: ox = x + (fx + 0.5 - 28) * 2, oy = y + (fy + 0.5 - 26) * 2 (frame drawn 2x about the enemy;
     checked against BattleScene::_draw_enemy).
   - The view: `move_facing()` if >= 0, else `facing_toward4(px - x, py - y)` -- as now.
2. NO FADING BULLETS anywhere in Paoxiao's fight (no fade/alpha/ghost bullets).
Note: the animation session changed the leap sheet to 6 frames (0-3 a sprint, 4-5 the warning) and
updated `flap_phase()` itself; don't change that.
