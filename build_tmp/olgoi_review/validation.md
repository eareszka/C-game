# Olgoi-Khorkhoi ? three phases, 2026-10-19

User direction: next enemy after Alber; specifically requested three phases.
Baseline source copied to enemies_before.cpp. Verified all source outside
Olgoi-Khorkhoi and its comment is unchanged, including Alber. HP 1200 and
weapon multipliers (including intentional 0.4 knife) retained. No tier, gear,
engine, ready gate, asset or commit changes.

## Fight

1. Above/equal 66% HP: a 1.2-second venom breath in each 3.2-second cycle,
   followed by blade bars. Venom fans wave and slow into lanes. Bars leave the
   two drawn blade tips, spin, slow, turn before the arena edge, and return.
2. Below 66%: the existing spinning-head sheet starts. Venom becomes continuous,
   with the centre drop homing for 0.8 s then committing; the returning blades
   overlap it every 1.8 s. Mouth-fired acid globules shed an 18-shot ring after
   1.4 s, every 2.8 s.
3. Below 33%: these attacks continue while a three-pronged electrical fork
   charges every 3.6 s. All beams mark for 0.3 s, charge harmlessly for another
   0.6 s (turn already visible), then hurt for 1.1 s and fade harmlessly for
   0.25 s. Aim is sampled once; no retargeting. Sweep is 0.13 radians/s,
   directed toward the farther horizontal side from the original target,
   including targets above the mouth.

Origins follow the existing mouth and blade measurements. Idle mouth dip
(frames 4?5) is now tracked; blade tips follow the 30-degree-per-frame spin
sheet. Mouth launches require 70 px clearance. Longer blade bars require
100 px, so a focus-speed sidestep has time to clear the full rotating capsule.
Normal shots and shed children deal 5.0 damage. Existing engine shedding
suppression within 40 px is unchanged; no direct spawns target the player.

## Verification

make all battlecensus passed with MSYS paths and workspace TMP/TEMP/TMPDIR.
check.cpp passed with 12 player positions through all three HP bands:
bounded bullet and telegraph writes (including zero capacity), distinct
phase-1 attacks, rings restricted to phases 2/3, electric fork restricted to
phase 3, harmless full warnings, 5 damage, own launch guards, finite homing,
and analytical blade turn points inside the arena. All source outside the
class/comment compared equal to this turn's snapshot.

Focus-speed geometry: at the farthest playable point from the mouth, the
0.13 rad/s sweep moves under 59 px/s. At the 70 px start guard the 0.32 radian
beam spacing exceeds 22 px, versus 12 px needed for adjacent 3 px beam widths
and the 3 px player core. The blade's 100 px launch guard provides more than
18 px of focus movement before its full 18 px capsule/player clearance reaches
the initial target. These are component checks; combined routes still need a
human playtest.

60-second seeds 1?5, final source (no RNG, identical runs expected):

| Bot | Hits | Peak / 1024 | Cap frames | Spawns <40 px | Tightest pass |
|---|---:|---:|---:|---:|---:|
| Baseline default | 0 each | 36 | 0 | 0 | 23.7?23.8 px |
| Final default | 9 each | 73 | 0 | 0 | -2.2 px |
| Final focus, max 70 px/s | 8 each | 80 | 0 | 0 | -1.7 px |

Closest final spawn: 113.2 px default, 155.5 px focus. Peak 80 uses 7.8% of
budget. Both final bots took zero hits in phases 1 and 2, all hits in phase 3.
Phase 2 changes structure/volume but its human escalation is not yet validated.
Default bot's first six hits occur when it chooses the top edge during the
fork, where fresh venom arrives; later hits are venom and a blade bar. Focus
hits are returning/turning bars and lingering venom, while the fork restricts
routes. Higher home at (320,360), still limited to 70 px/s, takes two hits
instead of eight. No cap or close-spawn frames there either.

Inspected rendered venom/blades, fork charge/hot images and actual hit PNGs.
Artifacts: final/ logs and PNGs, traces/ transition frames, check.cpp/check.txt,
build.txt. Tuning files outside final/ are not final metrics.

## Handoff

Launch game.exe --debug, F3, type OLGOI, Enter. Check the venom/blade alternation,
head spin and overlapping attacks below 66%, then follow the marked fork's
moving gaps below 33% while watching the returning bars.
Human BOSS1 difficulty and placement below Alber remain pending. Bot hit counts
alone do not rank the two fights. Run tools/playtest_report.py after the user's
recorded playtest; leave ready.h unchanged until user approval.
