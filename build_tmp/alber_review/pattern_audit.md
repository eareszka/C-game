# Section 3 pattern audit ? 2026-10-19

Source: playtest/BULLET_BRIEF.md section 3; src/enemies.cpp factory IDs 0?100,
class attacks including fire, breathe, on_idle_frame, telegraphs and body mechanics.
This is a source-design audit, not a fairness or difficulty certification.
Density, cadence, mirroring and origin changes alone do not earn a second pattern.

## Alber
A: locked-aim crossing sweeps, requiring route reading/threading.
B: freshly aimed fans, requiring sidesteps while avoiding A.
Phase 1 overlaps A+B. Phase 2 adds C: moving shedding embers, whose delayed
radial rings overlap the following breath. This changes the combination.
Only its comment was changed for this audit, explicitly labeling A/B/C and
crediting the user. No gameplay values changed. Previous build/census results
remain applicable; zero dodge-bot hits means ELITE difficulty remains unproven.

## Only one distinct damaging bullet pattern across the fight: 21

| ID | Enemy | Existing pattern |
|---|---|---|
| 23 | Olgoi-Khorkhoi | Randomly rotated expanding rings; phase 2 increases count/speed/cadence |
| 32 | Angont | Aimed fan; phase 2 adds a faster shot on the same aim |
| 35 | Lomie | Aimed fan, widened and accelerated in phase 2 |
| 36 | Cu Sith | Aimed fan, widened and accelerated in phase 2 |
| 40 | Slide-Rock Bolter | Aimed fan; phase 2 adds two side shots |
| 51 | Aspidochelone | Expanding ring, no HP phase change |
| 64 | Dungavenhooter | Slap shockwave rings, accelerating with lost HP |
| 65 | Mice That Eat Iron | Unfinished aimed fan |
| 79 | Ugjuknarpak | Radial scratch volleys; roar increases directions, phase 2 curves/mirrors the scratches |
| 89 | Cuero | Unfinished aimed fan |
| 90 | Chipekwe | Unfinished aimed fan |
| 91 | Kurrea | Unfinished aimed fan |
| 92 | Siehnam | Unfinished aimed fan |
| 93 | Chipique | Unfinished aimed fan |
| 94 | Trochus | Unfinished aimed fan |
| 95 | Witkes | Unfinished aimed fan |
| 96 | Bregdi | Unfinished aimed fan |
| 97 | Ro | Unfinished aimed fan |
| 98 | Boiuna | Inherited Unfinished aimed fan, mouth origin |
| 99 | Fad Felen | Inherited Unfinished aimed fan, phase-2 art only |
| 100 | Flesh Planet | Unfinished aimed fan |

## Second pattern absent in phase 1: another 11

These have distinct attacks somewhere in the fight, but do not introduce two
in phase 1 as section 3a requires.

| ID | Enemy | Phase 1 only | Later second attack |
|---|---|---|---|
| 0 | Skvader | Aimed antler fan | Sweeping gust stream |
| 1 | Wolpertinger | Two-speed aimed fan | Landing ring and sweeping gust |
| 2 | Treesqueak | Gapped sound ring | Aimed acorn spread |
| 3 | Qique | Locked-line peck burst | Side feather arcs |
| 4 | Lili | Aimed fan | Closing pinch pairs |
| 9 | Questing Beast | Delayed aimed hoofprint mines | Traveling spots/rosettes |
| 13 | Beast of the Charred Forests | Aimed fan | Radial ring |
| 37 | Celestial Stag | Aimed fan with lateral shots | Radial ring |
| 45 | Kusa Kap | Aimed fan | Radial ring |
| 86 | Leucrocotta | Braided sound rings | Wall-origin sweeping fans |
| 88 | Amixsak | Repeated crossing seize streams | Surfacing explosion/contact/pull |

## Interpretation and other scope

52 Sannaja: one damaging bullet pattern (rings), plus a look-away blindness
mechanic. Counted as two mechanics under section 3b's explicit inclusion of
blindness/body mechanics; it still has no HP-dependent combination change.
If the minimum means two damaging projectile attacks even for gaze enemies,
add Sannaja to the one-bullet-pattern list (22 rather than 21).

Having two attacks does not certify the phase-2 combination rule. For example,
Myrmecoleon, Lusca and Moha-Moha retain fan+ring combinations while changing
numbers. They are not in the fewer-than-two list. Other density-only phase
escalations also need review when their individual tuning turn comes.

No enemy gameplay changed in this audit. Dungavenhooter retains its slap;
its second attack remains queued. No tiers, HP, gear, engine, ready gate or
commits changed.
