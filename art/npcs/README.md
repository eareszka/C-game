# Approved villagers

Sleeping NPCs (girl, fisher, sailor fisher and woodcutter) now use exact edits
of their approved side sprites, with the eyes hidden and two breathing cels
per profile. `*_sleep_simple.aseprite` sources export to
`assets/npcs/*_sleep_simple.png`; `tools/create_sleep_simple.lua` makes the
local Aseprite edits without any paid generation, and
`tools/verify_sleep_simple.py` checks both profiles against the original art.
`include/npc_sleep.h` lays them face-up across the mattress at the same 2x
pixel scale as standing NPCs. Only the chest moves, once every 900 ms; three
staggered pixel Zs drift upward and fade. Both effects follow the saved world
clock, so dialogue and other world pauses freeze them together. Walking sheets
are unchanged. Earlier generated sleeping drafts are retained for reference.

The northeast yellow-house fisher uses `fisher.png` and the new two-frame
`fisher_fishing.png` while fishing east at the water ring. The animation's
editable source is `art/npcs/fisher_fishing.aseprite`, created/exported with the
existing local pixel-plugin and verified pixel for pixel. Its four original
colors and walking sheet are preserved. See `docs/fisher-routine.md`.

Bloom (central town 0) also has a new shelf-restocking worker inside its bookshop,
using the existing `assets/npcs/glasses.png` without changing its pixels. This is
a separate NPC from the glasses resident outdoors and the elder shop owner.
Their four-stop shelf route, conversations, and saved routine are documented in
`docs/npc-routines-plan.md`. The world is named Vaalbara.

The additional 30-NPC cast is under review. Its latest corrected files are
in `cast30_corrected/`: clean side-view eyes and solid black profile lenses.
`cast30/` preserves the first version for comparison.

The approved character sources are `01_farmer_walk_3frame.aseprite`,
`02_apron_villager_walk_3frame.aseprite`, `03_elder_walk_3frame.aseprite`, and
`04_spectacled_villager_walk_3frame.aseprite`, with matching PNG/JSON exports.
Earlier draft, sidefix, matched, and fullstep files are retained references.

Each character has a 14x20 canvas. The 42x80 PNG has rows down, up, left,
right. Down and up have three drawings: standing, step A, step B. Side rows
retain the approved two drawings; their third atlas cell is transparent.

Front/back playback matches `src/entity.cpp::player_frame`:
step A, standing, step B, standing; 200 milliseconds per beat at normal walking
speed, 800 milliseconds per cycle. Stop on standing. These are three unique
drawings with four playback beats. Use the JSON playback sequences rather
than looping the three stored frames in order. `villagers_player_cadence_review.aseprite`
is the verified four-beat animated front/back preview made through the pixel plugin.

Town 0 uses `assets/npcs/elder.png`, `farmer.png`, and `glasses.png`, copied
without pixel changes from the approved sheets. Their JSON files describe
the atlas and playback. `src/story.cpp` places them on clear ground at local
tiles (73,74), (80,74), (87,74). They are stationary, front-facing residents
with the existing TALK interaction; roaming has not been assigned. The girl
(apron villager) is approved artwork and supplies the first roaming test resident
through `assets/npcs/girl.png`; the farmer stands in her old spot. The player
walks through every NPC, drawn in front of whoever's feet are higher. The resident starts in the southwest kitchen, walks
between stove and counter via the aisle one tile below them for one game hour, pausing two seconds at each surface, follows the trail to the northeast
red-brick house's left bed, sleeps for one hour, and returns to repeat.
The clock and resident persist through saves; `docs/npc-routines-plan.md` records
the behavior and dialogue. The three stationary residents retain their placements.

Validation: all 40 source cels reopened and checked, runtime PNGs equal their
approved sources, game/storycheck builds pass, town-0 placement and dialogue
checks pass on seeds 387 and 2026. `build_tmp/npc_review/town0_residents.png`
uses the game's renderer and has no off-palette pixels.

`assets/npcs/` also holds the 30 cast sheets from `cast30_corrected/`, copied
without pixel changes and with the number prefix dropped (`05_baker.png` ->
`baker.png`), so all 34 runtime sheets sit together; only the four above are
placed in the game. `build_tmp/npc_review/all_npcs.png` shows all 34.

Grandmother now uses the existing `assets/npcs/grandmother.png` walking sheet for
her Bloom house/library routine. `grandmother_seated.aseprite` is the separate
14x20 couch pose, exported to `assets/npcs/grandmother_seated.png` through the
pixel art plugin with the original four opaque colors and transparent background.
The walking sheet remains unchanged. Runtime couch, shelf and desk captures live
in `build_tmp/npc_review/grandmother_phase_*.png`.

The woodcutter now uses `assets/npcs/woodcutter_chop.png` for his actual axe
swing instead of walking in place. Four 200 ms cels (ready, raised, impact,
recovery) are supplied for down/up/left/right, 40x40 each, with the original
sprite origin at (12,12). The bronze axe uses his existing four opaque colors;
feet stay planted and the impact cel triggers the tree shake once per swing.
`art/npcs/woodcutter_chop_v2.aseprite` is the editable source, drawn/exported
through the local pixel-plugin and verified pixel for pixel. The first
`woodcutter_chop.aseprite` is retained as a draft; `woodcutter.png` is unchanged.
`chopcheck` validates all sixteen rendered cels, stationary feet and the runtime
loop. Preview: `build_tmp/npc_review/woodcutter_chop_preview.png`; actual tree
captures: `build_tmp/npc_review/woodcutter_chop_world_*.png`.
