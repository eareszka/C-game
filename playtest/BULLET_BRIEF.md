# Bullet pattern work: brief

You own the bullet-hell patterns from here on. This brief gives you the state of things, what to fix first, and the rules that keep every pattern consistent. Read it fully before touching `src/enemies.cpp`.

## 1. Where things live
- **Patterns:** one C++ class per enemy in `src/enemies.cpp`, deriving from `Enemy` (`include/enemy.h`).
  - The factory is `enemy_build()`, called by `enemy_create()`.
  - The hooks are `fire_interval`/`fire`, `breathe`, `on_idle_frame`, `update`, `telegraphs` (lasers, with `hurt_w`), `parts` (with `hurt_r`), `contact_damage`, `pull`, `shove`, `blind`, `phase2_at`, `armor` and `catch_radius`.
- **Bullets:** `BulletSpawn` in `include/enemy.h`. Build them with the existing helpers (`mk`, `mkb`, `mksp`, `mkh`, `mkhsp`, `scratch_shots`, `shape_shots`) and use `ernd()` for randomness. Don't add a second RNG.
- **Phase 2:** use `ENRAGED` (hp < max_hp * `phase2_at()`). Always compare HP as a fraction of `max_hp`, never as an absolute number (see section 4).
- **Tiers:** `ENEMY_TIERS` in `include/enemy.h`. Don't change tiers; that's the user's decision.
- **Ready gate:** `include/ready.h`. Add an id there only after it passes the loop in section 6.

## 2. What the user's playtest found (2026-10-19, F4 difficulty run, one pass)
**Intended difficulty order, easiest first:** STARTER < LOW < MEDIUM < UPPER < HARD < SEVERE < BOSS1 < ELITE < BOSS2 (hardest of all).

**What was measured:** a human, a knife with that tier's gear, can't-die trials.

| Tier | Hits a minute (median) | Ratings |
|---|---|---|
| UPPER | 8 | mostly 3 |
| HARD | 3 | mostly 2 |
| BOSS1 | 6 | 1–3 |
| ELITE (Alber) | 0 | 1 |

The tiers come out inverted: UPPER plays harder than HARD, ELITE and most of BOSS1.

**Outliers, worked in this order:**
1. **07 Alber (ELITE):** 0 hits in 33 s, 7 grazes, rated 1. It needs to become a real elite, harder than every BOSS1.
2. **23 Olgoi-Khorkhoi (BOSS1):** 0 hits in 55 s, 2 grazes, rated 1. Its shots never come near the player. It needs real pressure between SEVERE and ELITE. Its 0.4× knife multiplier is intentional; don't fix difficulty through HP.
3. **HARD as a band:**
   - Tse'nagahi (33), Ajaju (39), Beast of Barrisdale (83) and Leucrocotta (86) each landed 1–2 hits and were rated 2. HARD should clearly beat UPPER's ~8 hits/min.
   - **Grootslang (27) is fine as it is (the user said so). Don't touch it,** even though it scored 0 hits.
4. **UPPER's top end:** Asp (21) 14.7/min, Opimachus (28) 13.0, Hidebehind (63) 12.9 and Hoga (77) 11.6 are above every HARD enemy.
   - **Ask the user before nerfing these.** The preferred fix is raising HARD/ELITE/BOSS1 above them, not lowering UPPER.
5. **Harder to hit than to dodge:** Roperite (61, 37% accuracy) and Leucrocotta (86, 59%). Note this for the user. Don't change it unless asked.
6. **Zero threat in UPPER:** Dungavenhooter (64), Loch Oich Monster (76) and Zankallala (78; not even a graze). Look at these after 1–4.

**Caveat:** this is one fight each, and one hit moves the rate by about 3 a minute. Only the outliers above are solid.

## 3. Battle design rules (the user)
These come before everything in section 4. If a pattern breaks one, fix that first.

### 3a. Every enemy has at least two bullet patterns
- **Two distinct attacks at minimum.** Distinct means a different dodge: a different shape, a different bullet type or a different way of moving. More bullets, a faster version or a mirrored copy of the same volley doesn't count as a second pattern.
- **Structure:**
  - The patterns take turns or overlap in phase 1.
  - Phase 2 must change how they combine, not only the numbers. For example, run both at once, add a third, or chain one into the other.
  - Say which is which in the class comment block, e.g. `Pattern A -- ...`, `Pattern B -- ...`, then what phase 2 does.
- **Known violation:** Dungavenhooter (64) is single-pattern on purpose ("ONE pattern (the user)" in its comment). That's an older call that this rule now overrides. Give it a second pattern and keep the slap. It's also a zero-threat outlier (section 2), so fixing both together is fine.
- **Audit:** before tuning any enemy, check that it has two patterns. Report every enemy that doesn't, ready or not, as a list, so the user can see the size of the job.

### 3b. Use the bullet types; they're the main tool for difficulty
The engine has many bullet behaviours (`BulletSpawn` in `include/enemy.h`, plus lasers and parts on `Enemy`). Pick the ones that fit the creature and make each pattern's dodge different from the other's. Don't fill every pattern with plain straight shots.

| Type | Fields | Good for |
|---|---|---|
| Ricochet shot | `bouncing` (3 wall hits, then gone) | filling the space behind the player, angles the player has to read off the walls |
| Ricochet laser | chained `TeleLine`s reflected off the arena edges (0..`ARENA_W`, 0..`ARENA_H`) | a beam that bounces round the arena and cuts off escape routes |
| Laser | `telegraphs()` with `hurt_w` | sweeps, cross beams, beams that lock off a lane |
| Mark | `TeleLine` stage 3 | warning where something is about to hit |
| Orb | `TeleLine.orb` | a growing glowing ball |
| Homing | `homing`, `homing_timer` | pressure that ends, so it can be dodged late |
| Mine | `delay`, `launch_speed`, `launch_off` | traps laid now that fire later, mixed with a second wave |
| Boomerang | `accel` < 0, `max_speed` | shots that come back through where the player dodged to |
| Slowing shot | `accel` < 0, `min_speed` | a wall that eases off and bunches up |
| Spawner | `spawner`, `spawn_interval` | a carrier that seeds shots along its path |
| Shedding | `shed_*` | eggs that hatch, logs that shed bark |
| Log | `half_len`, `ang`, `spin`, `max_tilt` | long rotating bars to slip past |
| Ring | `orbit_w`, `orbit_vx/vy`, `orbit_squash`, `orbit_about` | rings that spin as they spread, drifting suns, tornadoes |
| Orbit | `path_*` | shapes on ellipses, which can break off and aim (`path_aim`) |
| Zigzag | `zig`, `zig_every` | a twitching line |
| Wave | `wave`, `wave_w` | a shot that sways like water |
| Timed | `life`, `fade_out`, `flash_in` | short-lived walls, a cue as shots appear |
| Rain | `from`, `ox/oy`, `behind` | rain or weather from an edge, not from the enemy |
| Body | `parts()` with `hurt_r`, `contact_damage`, `pull`, `shove`, `blind`, `catch_radius` | heads that lunge, suction, knockback, gaze, catching the player's shots |
| Poison | `poison` (or `poisoned(out, n)` for a whole volley) | venom, spores, stingers: a hit costs its bar AND poisons the player |

**How to use them:**
- **Mix types inside a fight.** A good fight puts two kinds of dodge on screen together. For example:
  - a slow static or slowing wall plus an aimed or homing stream
  - ricochets filling the back of the arena while lasers lock the front
  - mines laid in phase 1 that launch during phase 2's main pattern
- **Ricochet lasers:**
  - Build them in `telegraphs()` as one `TeleLine` per segment, each reflected where the last one hits a wall.
  - Every segment shows as a stage 3 mark before it hurts, so the whole path can be read before it fires.
  - Cap them at 2 or 3 bounces so the beam stays readable.
  - The engine already hit-tests each `TeleLine` with `hurt_w`, so this is pattern code only and needs no engine change.
- **Find working examples** with `grep` before you write a new one: ricochets (around line 1195), boomerang, slowing shots (around 3913), reflected shots (around 5824), logs, tornadoes (around 1509). Copy the closest one and keep its conventions.
- **Poison shots** (the user, 2026-10-23; first used by Angont 32):
  - A hit costs its bar and sets the player's existing poison status: 1 HP a second, never below 1 HP, until an Antidote (exploration only) or a defeat. It lasts past the fight. In an F4 trial it drains only the trial's HP.
  - Drawn with a lavender core (the HUD's POISON colour) in place of the white one. What a poison shot sheds is poison too.
  - Keep them a minority, readable threat: slower or bigger shots the player learns to dodge first, one or two poison sources per pattern, never a screen of them. Never on lasers or body parts.
  - Only poisonous creatures get them (the poison-gland droppers: 5 21 25 32 35 56 69 74). Ask before adding them to an enemy the user already approved.
  - battlecensus tags poison hits `POISON` and reports whether the player ended up poisoned.
- **Fit the creature:** the bullet type should read as the creature's attack, like a tail slap's shockwave or a bird's feathers. If a type doesn't fit, don't force it in. Ask the user if you're unsure.
- **Within the rules:** the section 4 rules still apply to every type. That means telegraphed lasers, a gap the 3 px hitbox fits through, shots leaving from the sprite part that fires them, and the bullet budget.

## 4. Consistency rules for every pattern
- **Damage:** `damage = 5.0` (one bar) for normal shots. Lasers and parts always cost one bar. A bigger hit needs the user's say-so.
- **Origin:** bullets leave from the sprite part that fires them (mouth, claws, eye), not the sprite's centre. Match the animation by using `breathe`/`on_idle_frame` when a volley belongs to a pose.
- **Fair spawns:**
  - `SAFE_SPAWN` (24 px, `src/battle.cpp`) already drops shots spawned on top of the player. Don't design around it, and never aim spawns at the player's position.
  - Every laser must be telegraphed before it hurts.
  - Every dodge must have a gap the 3 px hitbox can fit through at focus speed (70 px/s).
- **Bullet budget:** stay under `MAX_ENEMY_BULLETS` (1024) with headroom. `battlecensus` reports peak bullets and frames at the cap; frames at the cap must be 0.
- **Readability over density:** difficulty should come from pattern structure (crossing streams, aimed volleys mixed with static walls, speed changes, phase-2 escalation). Don't get it from unreadable bullet soup or offscreen spawns.
- **Phase 2 must escalate:** each enemy's `phase2_at()` phase has to be visibly harder. The playtest log splits hits before and after phase 2; if after-phase-2 hits aren't higher, the enrage isn't doing its job.
- **HP:**
  - Leave each constructor's HP alone. It's tuning within the tier.
  - Tier-wide HP comes from `TIER_HP_MULT` in `enemy_create()` (multipliers measured 2026-10-19 so fight lengths grow by tier). Don't edit the table to fix difficulty; fix the pattern.
  - Any per-enemy HP logic must use fractions of `max_hp`, because the multiplier scales it (see Namungumi's regen).
- **Code style:** match the file. Each class has a short comment block saying what the pattern is, phase by phase, credits the user's calls with "(the user)", and puts named `static constexpr` constants at the top. No magic numbers in `fire()`.
- **Scope:** pattern code only. Don't change `src/battle.cpp` engine rules, i-frames, the player hitbox, tiers, gear or HP tables without asking.

## 5. Known engine bug (report it, don't fix it unasked)
When several bullets overlap the player in the same frame, each takes a bar despite i-frames (`_check_collisions`, `src/battle.cpp`). Cactus Cat's spine clusters took 10 bars in one frame against a still player. The user hasn't decided on a fix yet. Dense clusters are especially punishing until it's fixed.

## 6. The per-enemy loop
Every pattern change goes through all of these steps:
1. **Read:** read the class and its comment, and look at the sprite (`ENEMY_SHEETS` in `src/battle.cpp`).
2. **Change** the pattern.
3. **Build:** run `make` and `make battlecensus` from the repo root, with `C:\msys64\mingw64\bin` and `C:\msys64\usr\bin` on PATH and TMP/TEMP pointing at a writable folder.
4. **Bot check:** run `battlecensus.exe <id> 1 60`, plus a few more seeds. Check:
   - no point-blank spawns
   - frames at the cap = 0
   - hits only where the pattern means to threaten
   - for a pattern meant to be hard, the bot should take some hits
   - add a shot dir argument to get PNGs of each hit
5. **Hand it to the user** to play: `game.exe --debug`, then F4 (difficulty run, Up/Down jumps a tier) or F3 (pick one enemy).
6. **Report:** after the user's run, `python tools/playtest_report.py` ranks enemies and flags ABOVE/BELOW the tier medians in the difficulty order above. Target: each enemy within its tier's band and no FEEL mismatches.
7. **Ready gate:** add to `include/ready.h` only when the user approves. Then rerun `python tools/playtest_order.py` so the F4 run includes it.

## 7. How to report back to the user
For each enemy you touch, give:
- **What changed:** one line on the pattern before and after.
- **Bot numbers before and after:** `battlecensus` hits, peak bullets, tightest pass.
- **What to look for when playing it.**

Batch changes so the user can play them in one F4 block. Don't commit unless the user asks.
