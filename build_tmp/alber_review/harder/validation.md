# Alber: stronger electric fire ? 2026-10-19

Alber alone changed; verified source outside its class/comment is byte-for-byte
identical after newline normalization to enemies_before.cpp from this turn.
Sprite, mouth tracking, constructor HP/multipliers, tiers, engine and ready gate preserved.

## Attacks

- A: crossing sweeps. Slow flame decelerates from 190 to 85 px/s, creating
  lingering lanes. Every third fast spark ricochets (three engine wall hits,
  six-second lifetime). Others fly straight. Crossing duplicate guard retained.
- B: three sparks 0.38 radians apart at 185 px/s, homing for 1.2 seconds then
  committing. Fresh aim every 0.4 seconds; late sidesteps interact with A's lanes.
- Phase 2: ember rings retained. Every second phase-2 breath ends in a
  mouth-fired lightning beam with exactly two wall reflections. The whole path
  blinks for 0.35 s, glows harmlessly for another 0.60 s, hurts for 0.55 s,
  then fades harmlessly for 0.20 s. No retargeting once marked. It hovers and
  holds facing while channeling, keeping wingbeats. The next breath resumes
  sweeps/homing during the beam, with ember rings persisting too.
- Normal bullets and ember children remain 5 damage. Own mouth-distance guard
  suppresses bullet launches/beam starts within 64 px; engine shedding guard
  still suppresses ring emission within 40 px. No reliance on SAFE_SPAWN.
- Settings remain latched per breath/rest cycle; no mid-cycle phase reset.

## Verification

Both make all and make battlecensus passed with MSYS paths and TMP/TEMP/TMPDIR
pointing at the writable workspace tmp directory. Final build in build.txt.
Focused C++ check passed: five aim scenarios, finite fixed reflection geometry,
segment continuity and reflection angles, shared mark/charge/hot lifecycle,
bounded writes including zero capacity, phase gate, continuous movement,
finite homing, origin clearance and 5 damage. Source: check.cpp; result check.txt.

60-second seeds 1?5 (deterministic, so identical seeds are expected):

| Bot | Before hits | After hits | Before peak | After peak | Before tightest | After tightest |
|---|---:|---:|---:|---:|---:|---:|
| Default | 0 | 1 | 79/1024 | 119/1024 | 7.9 px | -0.1 px |
| 70 px/s | 0 | 9 | 91/1024 | 125/1024 | 1.5 px | -4.3 px |

All final seeds: zero frames at cap, zero spawns below 40 px. Closest
spawn 237.1 px (default), 263.3 px (focus). Both bots have zero phase-1
hits; all their hits occur in phase 2. Default hit at 44.80 s is a committed
homing spark with active lightning and other lanes on screen. Focus hits
include sparks, a crossing lightning contact, a fast sweep and an ember child.
Census prints a line for each frame touching a laser but its summary groups
contiguous laser contact; use summary hits, not raw HIT line counts.

Additional focus checks: higher home (320,360) completes with zero hits and
1.4 px minimum clearance, peak 130/1024; home (160,400) takes two hits;
1.5-second lookahead takes six. Routes therefore exist for the 3 px hitbox at
70 px/s; these tests do not prove every situation safe. Worst observed peak
130/1024 leaves 87.3% headroom. No close spawns or cap frames in these runs.

Inspected actual hit PNGs plus warning/hot transition renders. Final traces and
seeds are under final/, including separate focus screenshots. Initial tuning
artifacts outside final/ are not final metrics. The bot initially ignored
stage-3 marks; adding a harmless bright charge stage made warning recognition
possible. That clear warning is retained in the final version.

## Human handoff

game.exe --debug; F3, type ALBER, Enter. Watch for slow flame lanes, hollow
ricochet sparks returning from walls, sparks ceasing to track after their
initial turn, and the full marked lightning path. In phase 2, move out of the
marked path before charging completes while reading the following breath.
Human validation against BOSS1 remains pending; bot hits do not certify ELITE.
After the user's recorded run, run python tools/playtest_report.py.
No ready gate, tier, HP/gear, engine or commit changes.
