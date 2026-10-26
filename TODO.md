# TODO: Four Castle Chronicles to 1.0

The master to-do list, checked against the code on 2026-10-18 (HEAD a0d6754). It replaces the stage list in PRODUCTION_PLAN.pdf (2026-10-10), which is out of date. Tick items off as they land.

## Where the game stands (HEAD a0d6754)
| Area | State |
|---|---|
| World, 9 dungeon types, battle engine, crafting (23 recipes) | Done |
| Title screen, save/load (v17, migrates back to v2), play vs `--debug` | Done |
| Story arc ARC1→TURN→DESCENT→OPEN→AMNESIA, leads, 10 notes | Done in code, but there is no ending |
| NPCs | 9 with routines; table NPCs; one shop (3 books) |
| Boss sites + beaten flags | Done for 6/23/30/52/44/98. 49 is reached by boat, 34 guards the cave mouth, **100 can't be reached** |
| Enemy patterns | 67 of 101 bespoke. 14 placeholders (65, 89–100), 20 old prototypes |
| Enemy sprites | Only 65 is missing; 84–95 are roughs |
| Settlements | Town 0 is done. Town 1 has a layout but no collision, depth or interiors. Town 2 is blank. Villages are procedural with no interiors. The 3 castles are checkerboards |
| Death | **Broken**: defeat leaves you walking around at 0 HP |
| Audio, packaging, version, stage cards, ending, credits, rebinding | Missing |

---

## Decisions only you can make (these block P3 and P4)
1. **The ending.** The PDF says "7 flags → walk home as the world dissolves → Flesh Planet → true world → credits". The code says "beat Anaye (34) → go down the starter cave → swarm (100) → AMNESIA". Pick one, or merge them (e.g. the cave descent *is* the walk home).
2. **The castles.** What are the 3 placed castles (ocean, mountain, lava) and the unplaced 4th for? The game's title depends on the answer. The PDF assumed the castles hold the tier-2 bosses, but the code puts those bosses at overworld sites.
3. **The boss roster.** The code uses {6,23,49,30 | 52,44,98 | 34 | 100}, and the PDF used a different list. I will treat the code as the source of truth unless you say otherwise.
4. **The true world.** Is it a reskin of the existing world or new content? This is the biggest unknown in the schedule.
5. **Music.** Will you compose it, commission it, or license it?

---

## Prioritised to-do list

### P0: a stranger can play it without breaking it (Beta 0.1) — about 4–6 days
- [x] **Death/respawn**: on defeat, wake at home with full HP and clear poison (`battle.cpp:604`, `main.cpp:1964`)
- [x] Gate the cheats left open in play mode: T = instant battle win (`battle.cpp:587`), T = +1 hour (`main.cpp:1546`), F1 readout (`main.cpp:986`)
- [x] Debug chest in the spawn house: already debug-only (`main.cpp:2355`)
- [x] **Ready gate** (`include/ready.h`; boss sites too): one list of finished enemy ids; `dungeon_pick_enemy` (`dungeon.cpp:2429`) only picks ready ones; `enemy_tier_sheet.py` reads the same list
- [ ] Don't stamp unbuilt settlements (no magenta or checker blocks): town 2, castles
- [x] Chasers with no mini draw their shrunk battle sprite, not a red square (`main.cpp` draw_chaser). Hand-made minis are still an art job
- [x] **Packaging script** (`dist.bat` → `tools/package.sh`): `dist.bat` builds a zip with the exe, the SDL DLLs and `assets/`; test it on a PC without MSYS2
- [x] Version string on the title screen, `CHANGELOG.md`, itch.io note on the title and in `packaging/README.txt`
- [ ] Create the itch.io page (restricted) and upload the zip
- [x] Enemies 00–02: bullets leave from the head/mouth; battlecensus clean
- [ ] Play-test 00–02 and boss 23 at its new 1200 HP
- [x] Starter HP: Skvader 180, Treesqueak 240
- [x] Raft worn/unworn like the boots (save v18)
- [x] Permanent harvests and kills, saved (`include/persist.h`; checked by `killcheck`)
- [ ] Play-test permanence: cut, kill, save, CONTINUE; lose a pack fight after one win; raft unequip on land vs water
- [ ] Ship **Beta 0.1** to friends: does it start, save, and survive dying?

### P1: the first region and the first boss feel complete (Beta 0.2) — about 18–22 days
- [x] Audio: a built-in mixer (`src/audio.cpp`, synthesized clips, WAV overrides in `assets/sound/`; SDL_mixer isn't needed), MASTER/SOUND volumes in OPTIONS kept in `settings.txt`, effects for shots, hits, grazes, pickups, menus, speech, harvesting, chests, level-ups and stairs. Music is still P2
- [ ] Add a speaker name to the dialogue box (`core.cpp:140`)
- [ ] Give routine NPCs lines that change with the story stage (today they only have the "what to do / where am I" lines)
- [ ] An opening beat: a short intro for a new game (today you just wake up in the spawn house)
- [ ] Stage name cards between queued battle stages (`main.cpp:1959`)
- [ ] Shop: stock more than 3 books (the plan says all 23, with regional stock decided later)
- [ ] Boss 06: final art, check the pattern and HP; fix **boss 23's HP (165)**
- [x] Boss 23 lead-up (`src/story.cpp` worm errand): the sand village nearest the site asks for 3 asp glands (asps pinned in the nearest oasis/pyramid), then the herder's 3-clue trail, then the bell rung on the soft sand raises the worm. The site stays hidden until then; checked by `storycheck`
- [ ] Play-test the worm errand in the real game; draw the clues (they use the white note page) and a soft-sand mark at the hidden site
- [ ] LOW and MEDIUM bands through the per-enemy loop (art → bullet origin → pattern → `battlecensus` → playtest → ready list); includes **65's sprite and pattern**
- [ ] Move centre-firing patterns to firing from the sprite part (0–5, 8–12, 14, 15, 17, 50, 53, 56, 59, 66, 79, 80, 82)
- [ ] Ship **Beta 0.2**: can a new player find and beat a boss from town talk alone?

### P2: public demo (all of ARC1: bosses 6, 23, 49, 30) — about 24–32 days
- [ ] UPPER and HARD bands through the loop, plus 89's pattern
- [ ] **Boss 49 (Physeter)**: real HP (it is set to 1M as a test), a bespoke pattern, a check of the boat → sea fight route
- [ ] Boss 30: lead from an NPC (there is none today), polish
- [ ] Village interiors, or at least villager sprites (placeholder today, `main.cpp:1722`)
- [ ] **Town 1** collision and depth layers, houses and interiors (`towns.h:1537,1701`)
- [ ] Music: title, overworld, town, dungeon, battle, boss
- [ ] Pause screen with quit (today you hold ESC for 3 seconds), key rebinding
- [ ] Draw the boat (today it is the raft scaled up, `main.cpp:1708`)
- [ ] A "demo ends here" card after ARC1; everything later stays behind the ready gate
- [ ] Ship the **public demo** (itch.io, and a Steam demo if you want one)

### P3: mid-game (TURN and DESCENT: bosses 52, 44, 98, 34) — about 36–42 days
- [ ] Resolve decision 2 (castles), then build castle blueprints and interiors or arenas (`castles.h:24`)
- [ ] **Travel gates that currently do nothing**: cold damage plus Cold-Weather Gear (snow), Lava Charm on the raft over the lava moat, O2 Charm. Snow and wasteland are one country each now, so a gate on the border means something
- [ ] After the one-blob biomes: re-measure `TIER_CUTS` (`dungeon.cpp`), the cave material cut points (`tools/oreprof.cpp`; kharvite caves appeared in 2 of 8 census worlds against 5 of 8 before) and the dungeon kind targets (`dungeon_kinds.cpp`) with `make dngcensus`; each far biome's dungeons now sit in one difficulty band
- [ ] Redraw the roughs (84–95 and the one-pose redraws); SEVERE and ELITE bands through the loop
- [ ] Rewrite the 20 old prototype patterns (13, 25, 29, 31, 32, 34–38, 40, 41, 44–49, 51, 52)
- [ ] Bosses 52, 44, 98 (Boiuna is a placeholder), 34 Anaye: patterns, HP, leads
- [ ] Town 2 authored and named (towns 1 and 2 have no names)
- [ ] Hook up the remaining item effects: Campfire warp, Bomb, Smoke Bomb, Compass, Spyglass/Binoculars zoom, attacks that poison
- [ ] Music for the farlands and the tier-2 bosses
- [ ] Ship **Beta 0.5**

### P4: the ending — about 16–25 days (depends on decisions 1 and 4)
- [ ] Make the swarm (100) reachable: place it in the cave during the OPEN stage (it is unreachable today)
- [ ] Support more than 2 phases: turn `ENRAGED` (`enemies.cpp:116`) into a list of thresholds
- [ ] Flesh Planet: sprite pass, a multi-phase pattern, drops
- [ ] The finale sequence (the walk home / dissolving, per decision 1)
- [ ] The true world (per decision 4)
- [ ] AMNESIA epilogue, credits screen, "both worlds reachable afterwards"
- [ ] Ship to closed testers only (no spoilers)

### P5: release 1.0 — about 15–20 days
- [ ] Balance pass with `spawncensus` plus tester reports: EXP, ore bands, gold prices, recipe costs. **Enemies, ore and EXP are now finite** (nothing respawns): check the curve can be climbed without grinding
- [ ] Swift Boots speed in battle (you've confirmed you want this, but the amount isn't decided)
- [ ] Clean up loose ends: Beast of Barrisdale (83) blocking animation, oilbloom art (`resource_node.cpp:78`), tail-swing TODO (`enemies.cpp:1808`), dead `#if 0` (`tilemap.cpp:4927`), rooms without layouts (`interior.cpp:135,180`)
- [ ] Remaining music and a final sound pass
- [ ] Update `CPP_GUIDE.md` §5 (it is stale)
- [ ] A full playthrough from a fresh save on the packaged build, then **1.0**

**Total: about 115–145 working days.** With your current bursty schedule, expect the demo around early 2027 and release around mid-to-late 2027.

---

## How to work through it
- Three lanes that rarely collide: **Enemy** (one enemy per session, through the per-enemy loop), **Systems** (one outer-game item at a time), **World** (blueprints, towns, castles).
- A stage is done when the packaged zip runs from a new save to the end of that stage's content with debug keys off, every ready enemy has passed `battlecensus` and your playtest, and `spawncensus`, `craftcheck` and `dngportals` all exit clean.

