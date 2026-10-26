# Project memory

- Ayotochtli installed for testing (2026-10-18): user requested installing the reviewed battle animations. `src/battle.cpp` now loads `assets/enemies/redraws/66_ayotochtli.png` and `66_ayotochtli_roll.png`, with matching Aseprite sources, all eight directions, 48x35 native frames, original standing/attack and rolling timing. Original assets and reviewed sources preserved. Both builds and a 12-second installed battle-render check passed with unchanged gameplay metrics. `tools/ayotochtli_install.py` recorded the installation and refreshed `enemy_rating.png`; 66 is now DONE, 48 drawn enemies remain. For testing: `run.bat`, F3, search AYOTOCHTLI, Enter (numbers in that list are ranks, not enemy IDs). Records in `assets/enemies/redraws/installation.json` and `build_tmp/ayotochtli_battle_review/installed/`.

- Current enemy (2026-10-18): user chose 66 Ayotochtli next, approved its cleaned 48x35 first frame, and requested rolling plus all battle frames. Source/review records are in `art/enemies/pixellab/66_ayotochtli/`; staged generation/packing uses `tools/ayotochtli_battle.py`. Preserve its three-frame standing/hunching layout, frame-1 attack, and four-frame ball roll at 70 ms, all eight directions. Review animations in Aseprite before installation; update the visible tracker with `--complete 66` when the fix is approved and installed.

- Ayotochtli animation review ready (2026-10-18): all eight standing/hunching and curled-ball rolling directions completed under `art/enemies/pixellab/66_ayotochtli/battle/`, matching `.aseprite` sources opened together. Three standing frames and four rolling frames per direction, 48x35, nine approved colors, binary alpha, original timing, exact Aseprite round trips. Staged 12-second battle test matched original gameplay metrics; logs/screenshots in `build_tmp/ayotochtli_battle_review/after/`. Additional cost 13 generations, balance 1956. Three interrupted jobs recovered by ID; final unsubmitted rear roll retried once. First-frame approved; animations awaiting review and installation. Original game assets unchanged and 66 not yet DONE; after approval/install immediately run the tracker completion command.

- Visible enemy tracker (user instruction, 2026-10-18): whenever a new enemy sprite fix is approved and installed, update `art/enemies/redraw_status.json` AND regenerate the visible `enemy_rating.png` immediately. Use `python tools/enemy_redraw_sheet.py --complete ID` after installation; do not mark unapproved drafts done. This art tracker is separate from `include/ready.h` and its gameplay-ready gate. The chart can run without the previous machine's external Bible checker; fallback labels say LOCAL and check only primary-sheet palette, binary alpha and layout, without claiming full visual style certification.

- Enemy art terminal workflow (2026-10-18): use PowerShell and Aseprite batch CLI, with no GUI launches. PixelLab CLI 0.7.0 installed; configure only PixelLab through its hidden prompt outside Git. See `docs/pixellab-terminal.md` for repeatable commands. Enemy 61 Roperite is unfinished: prepare only its native 98x65 first frame, preserve rope-snout lasso/rattle tail/pose/scale, dry-run and review cost before generation, and await design approval before animation or game installation. Preserve existing art direction and all original/completed assets.

- Roperite update (2026-10-18): user approved the first-frame design and requested running animations for its battle directions. Completed five unique view cycles plus mirrored left views in `art/enemies/pixellab/61_roperite/running/61_roperite_running.aseprite`, with a verified 8-direction runtime-layout PNG, 98x65 frames, five frames per direction at the existing 260 ms. Generation cost 6 total. A staged 12-second battle-render check matched the original gameplay metrics. Animation remains a separate review draft; installed assets and completion status unchanged. User explicitly requested Aseprite GUI review, overriding terminal-only preference for review launches.

- Roperite installed (2026-10-18): user approved the running animation and requested adding it to the game. `src/battle.cpp` now loads `assets/enemies/redraws/61_roperite.png`, with a matching tagged Aseprite source, and 61 is marked done. Five frames in all eight directions, native 98x65, 260 ms and frame-2 attack timing retained. Original assets and saved review preserved; the saved review's extra duplicate D frame was omitted only from the installed copy. Game build, exact Aseprite export round trip, and 12-second installed battle-render check passed, with identical gameplay metrics to the staged/original sheets. Records: `assets/enemies/redraws/installation.json`; screenshots/logs: `build_tmp/roperite_run_review/installed/`.

- Enemy 83 — Beast of Barrisdale: still needs a blocking animation during phase 2, when it hovers and catches player shots. The approved grounded idle and airborne animation are implemented; the blocking animation remains unfinished. (2026-10-11)


## Approved crafting stage (2026-10-15)

23 craftables; reusable recipe books bought with Gold in town book shops. Escape Charm, Band-Aid, Medkit, Antidote, Swift Boots and Diving Fins functionality are implemented; other new item effects remain deferred. Sleeping Bag retired. Escape Charm reusable; O2 Ring renamed O2 Charm. White Fur renamed Fur; Tripodero Legbone merged into Bone; Horn includes tusks.

### Recipes and book prices

- KNIFE: 2 WOOD + 3 ore; book 10 Gold; output 1.
- DAGGER: 2 WOOD + 3 ore; book 10 Gold; output 1.
- CLUB: 3 BONE + 3 ore; book 15 Gold; output 1.
- BAND-AID: 1 HIDE + 1 FLOWER; book 15 Gold; output 1.
- ANTIDOTE: 1 POISON GLAND + 1 FLOWER; book 20 Gold; output 1.
- RAFT: 10 WOOD + 3 VINE; book 30 Gold; output 1.
- CAMPFIRE: 6 WOOD + 4 STONE + 1 EVERLASTING EMBER; book 40 Gold; output 1.
- MEDKIT: 2 REGENERATIVE TISSUE + 2 HIDE + 2 VINE; book 60 Gold; output 1.
- BOMB: 2 BRONZE + 2 OILBLOOM + 1 EVERLASTING EMBER; book 70 Gold; output 1.
- SAIL: 6 WING SKIN + 4 VINE; book 80 Gold; output 1.
- AXE: 2 WOOD + 2 VINE + 3 ore; book 80 Gold; output 1.
- SMOKE BOMB: 4 WOOD + 2 HIDE + 2 ESSENCE; book 100 Gold; output 1.
- ESCAPE CHARM: 3 STONE + 4 VINE + 2 ENCHANTED WOOD; book 120 Gold; output 1.
- COLD-WEATHER GEAR: 6 WHITE FUR + 4 HIDE + 6 FEATHER; book 120 Gold; output 1.
- HALBERD: 2 WOOD + 3 ore + 1 OLD SPEARHEAD (first craft only); book 140 Gold; output 1.
- SPYGLASS: 1 EYE LENS + 3 BONE; book 160 Gold; output 1.
- DIVING FINS: 3 WING SKIN + 3 BONE + 4 GRIP SCALES; book 180 Gold; output 1.
- KATANA: 2 WOOD + 3 ore + 1 MOON STEEL (first craft only); book 180 Gold; output 1.
- SWIFT BOOTS: 6 HIDE + 4 WIND SINEW + 6 FEATHER + 6 GRIP SCALES; book 200 Gold; output 1.
- COMPASS: 4 BRONZE + 1 EYE LENS + 3 ESSENCE; book 250 Gold; output 1.
- O2 CHARM: 3 WATER RING + 10 GILLS; book 300 Gold; output 1.
- BINOCULARS: 2 EYE LENS + 2 HORN + 2 VINE; book 400 Gold; output 1.
- SCYTHE: 2 WOOD + 3 ore + 1 REAPERS EDGE (first craft only); book 500 Gold; output 1.

### Approved material sources (enemy IDs)

- HIDE: 00, 01, 09, 17, 50, 53, 55, 79, 86, 87.
- VINE: 02, 58, 61, 63.
- FEATHER: 03, 57, 67, 68, 75.
- FLOWER: 08, 22, 51, 70.
- OILBLOOM: 08, 22, 51, 70.
- FUR: 20, 28, 41, 48, 62.
- WING SKIN: 10, 12, 83.
- BONE: 38, 59, 62, 64, 66.
- EYE LENS: 06, 11, 52.
- HORN: 77, 84, 90.
- EVERLASTING EMBER: 07, 24, 73, 81, 97.
- WATER RING: 18, 49, 51.
- GILLS: 14, 15, 43, 46, 96.
- REGENERATIVE TISSUE: 60, 71, 89.
- POISON GLAND: 05, 21, 25, 32, 35, 56, 69, 74.
- SPIRIT ESSENCE: 29, 30, 34, 36, 37, 42, 44, 80, 88, 95.
- PLAGUE RESIDUE: 99.
- LAVA CHARM: 07, 13, 97.
- WIND SINEW: 16, 45.
- GRIP SCALES: 27, 39, 72, 85, 93, 98.
- ENCHANTED WOOD: 78.

Man-Eating Boulder (31) and Tse’nagahi (33): independent once-per-victory rolls, one each: Stone 100%, Bronze 40%, Emerald 20%, Veyrite 10%, Dravium 5%, Kharvite 2%, Reality Shard 0.5%. No other enemy uses ore rolls. All other assigned drops give one of each per victory. Bullet/laser cancellation gives at most 6 extra Wood/Stone combined, never more rare materials. Unassigned enemies give EXP and common bonuses only.

Unassigned: 04 Lili, 19 Skeljaskrimsli, 23 Olgoi-Khorkhoi, 26 Akhekh, 40 Slide-Rock Bolter, 47 Moha-Moha, 54 Billdad, 65 Mice That Eat Iron, 76 Loch Oich Monster, 82 Nadubi, 91 Kurrea, 92 Siehnam, 94 Trochus, 100 Flesh Planet.

### Deferred effects and rules

Band-Aid: implemented ITEMS > USE, restores exactly one health bar (5 HP), capped at max HP, consumes one. Exploration only, including pursuit; blocked during battles and battle/room transitions. Full health or defeated players cannot use it and spend nothing; Medkit: implemented ITEMS > USE, restores full HP and consumes one, exploration only with the same battle/transition restrictions as Band-Aids. Not consumed at full health and cannot revive; Antidote: implemented exploration-only USE, consumes one to clear poison and its timer. Not spent when healthy or defeated. Poison effect drains 1 HP/second in exploration (including interiors) and active battles, stopping at 1 HP; pauses with menus and transitions. Status persists until cured, including after healing and saving/loading. No attacks or bullets inflict poison yet (user explicitly deferred application mechanics). HUD shows purple HP and POISON; Campfire: consumed on placement, permanent warp point; Bomb: battle explosive; Smoke Bomb: break pursuit. Those six are consumables. Escape Charm: implemented reusable ITEMS > USE action, returning inside the actual entrance used this visit. Works during pursuit, blocked outside dungeons, in battle, or during battle/room transitions. Keeps dungeon progress and HP, clears motion/attacks and pursuit, and uses the existing fade-in with a one-second enemy pause. No cooldown or ingredient cost to use. Cold-weather Gear: prevents cold HP drain; entering cold without protection displays a warning. Swift Boots: implemented equip/unequip through ITEMS, WORN label when equipped, +50% walking and sprinting speed (120 to 180, 240 to 360), with matching walking animation. Applies on foot in overworld, interiors and land dungeons; crouching, swimming, raft/boat and battle speeds unchanged. No consumption; boost requires boots equipped and owned. Debug starts with boots equipped; normal crafting does not automatically equip them; Diving Fins: implemented +50% swimming speed in the oasis while equipped. One footwear slot shared with Swift Boots; equipping either takes off the other. Fins do not boost land, raft, boat or battle movement. ITEMS equip/unequip, WORN label, no consumption; O2 Charm: no oxygen loss underwater. Spyglass: see tier 2 on zoom-out; Binoculars: tier 1. Compass: reveal current dungeon map. Lava Charm: attach to raft for lava travel. Plague Residue: weapon poison coating, duration undecided. Spirit Essence retains More Shots upgrades (2, then 4); Oilbloom retains Faster upgrades. Exact gameplay effect tuning, equipment slots and regional book stock remain deferred.

### Stage implementation defaults

Book purchasing is included, through existing town book-shop counters, all 23 titles stocked. Scythe Book is most expensive at 500 Gold. All crafts spend materials and store outputs; no new gameplay effects in this stage. Existing weapons, raft and sail retain their behavior. Old free Raft/Sail book grants become shop purchases; existing owned books survive save migration. Books and permanent gear cap at one; resources and the six consumables cap at 999. Save version 5 stores poison and footwear equipment state and reads versions 2, 3 and 4. Version 4 boots owners migrate equipped to preserve their old speed boost.

31 named resources: Wood, Stone, Gold, Flower, Gravestone (legacy), Oilbloom, Hide, Bone, Spirit Essence, Bronze, Emerald, Veyrite, Dravium, Kharvite, Reality Shard, Vine, Feather, Fur, Wing Skin, Eye Lens, Horn, Everlasting Ember, Water Ring, Gills, Regenerative Tissue, Poison Gland, Plague Residue, Lava Charm, Wind Sinew, Grip Scales, Enchanted Wood.

Sail remains 6 Wing Skin + 4 Vine, intended around middle progression. Spyglass intended 3/5 and Binoculars 5/5; shared high-tier Eye Lens sources remain a balance consideration. Gathering and Gravestone removal are deferred. New effects, regional shop stock, equipment slots, heal amounts, movement bonuses, poison duration and crafting balance playtests remain future work.

### Debug functionality testing

User preference: whenever an item functionality is implemented for testing, automatically grant that item in the debug starting inventory. Maintain the test_items list in fresh_player in src/main.cpp. Escape Charm (one, reusable), Band-Aids (five), Medkits (five), Antidotes (five), Swift Boots (one), and Diving Fins (one) are currently granted; regular play inventory is unchanged.

Inventory display: show quantity labels for crafting materials and consumables only. Hide x1/count labels for permanent equipment, reusable items, books, and special weapon parts. Recipe ingredient have/need counts remain visible.

Debug starting health: 1 HP (max HP stays 60), to test healing items. Regular play starts at full health.

Debug poison testing: start poisoned at the existing 1/60 HP; heal with a Band-Aid or Medkit to observe drain, then cure with Antidote. Poison damage floor is 1 HP, not one full bar (latest user instruction).

Future Swift Boots battle effect (user confirmed): equipped Swift Boots should also increase movement speed in battle. Implement later; battle movement is currently unchanged. Battle boost amount is not yet specified.

Lagopus 67 art (2026-10-19): first-frame design approved. Full native 62x45 grounded (three poses, playback 0/1/0/2) and flight (four poses, 110 ms) review sheets for eight battle directions are under art/enemies/pixellab/67_lagopus/. Both *_review.aseprite animation files were opened together. Palette, alpha and exact Aseprite round trips passed; staged 12-second battle log matched the original. User responded positively ("looks amazing thank you"). Animation drafts are still separate from game assets; explicit installation remains pending. Total reported cost 19 generations. Do not mark 67 DONE until installed; update both tracker JSON and visible graph on installation. Repeatable commands and review details are in that folder's README.md and tools/lagopus_battle.py.

Footwear save layout: version 5 footwear integer uses 0=None, 1=Swift Boots, 2=Diving Fins, preserving existing version 5 boots saves without a size change. Debug starts with Swift Boots equipped and fins owned but unequipped.

World/place names (user confirmed): Vaalbara is the world; Bloom is the central starting town (town 0). Future NPC "Where am I?" questions must resolve the actual town from world position or an interior's entrance, using the shared story_where_am_i helper rather than duplicating town-specific dialogue.

Bloom bookshop worker: a new NPC using glasses.png, separate from the outdoor glasses resident and elder shop owner. Repeats shelf stops (235,196), (371,196), (434,308), (374,257), with quick 3/4/3/4-second pauses facing the books. Says "Just restocking shelfs, need anything?" with books-purpose, location, and No choices; answers return to choices. No/X/Escape resumes the interrupted routine. Save version 10 appends the worker's state after the unchanged girl-resident footer; versions 2–9 initialize only this new worker. See docs/npc-routines-plan.md.

Bloom grandmother: grandmother.png starts on the green couch in the southern orange/brown red-roof house (interior 5), rests 30 in-game minutes, follows the trail to the library/bookshop, searches a shelf free of the glasses worker for five real seconds, visits the front desk for five real seconds, then returns home and repeats. Greeting: "Good day deer, what do you need?" Choices: "What's there to do in town?", "Where am I?", "No". Activity answer mentions reading at home, a cave south and a graveyard northwest for adventure. Location uses the shared resolver. Save version 11 appends her state, preserving older resident/worker records; older saves initialize her on the couch.
