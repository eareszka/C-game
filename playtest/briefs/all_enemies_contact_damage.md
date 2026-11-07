# Battle task: EVERY enemy's body hurts to touch

From the user (2026-11-06), via the animation session, after Lodsilungur: "just make sure the enemy is a
hitbox that damages the player. make sure this is the case for ALL".

- Today `Enemy::contact_damage()` defaults to 0 (include/enemy.h:228) and only some enemies override it (8 in
  src/enemies.cpp, some only in one phase -- e.g. "ENRAGED ? 5 : 0", "rolling ? 5 : 0"). Battle reads it in src/battle.cpp
  (~line 1451: `float touch = _enemy->contact_damage();`).
- Make touching ANY enemy's body cost the player, in every phase, for every enemy (bosses, placeholders /
  `Unfinished`, spawner-havers, all). Simplest: a non-zero default (the bar the others use, 5.0) and drop the
  phase/state conditions that turn it off -- but check each override: some may deliberately turn it off
  (e.g. while it is off-screen, sunk/hidden, "GONE" states, or a grace at the fight's start) -- keep a zero
  only where the body genuinely isn't there to touch, and list those for the user.
- The hit shape is the drawn sprite (`_on_sprite`, sprite-shaped, uses whichever sheet is drawn), so it
  follows the new animations; check it also holds for the flap/alt sheets and for four-view enemies
  (`four_views()` -> `facing_toward4` in _on_sprite too, src/battle.cpp ~line 955 -- please confirm it uses
  the same facing the draw uses).
- Fairness: the player must still be able to get clear -- e.g. a fight that starts with the player inside or
  right under the enemy shouldn't hit them before they can move (a short grace), and enemies that charge
  straight at the player are already balanced around it.
Build, run the dodge-bot checks you use, and report which enemies changed and any you left at zero and why.
