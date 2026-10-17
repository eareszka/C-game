# NPC routines — proposed design

The first test resident is implemented in `src/resident.cpp`, using the approved girl artwork. Home is Town 0's southwest cream/white kitchen (interior 4); the parents' house is the northeast dark-red-brick cottage (interior 3), using its left bed. The other three speaking residents retain their placements.

The persistent clock starts at day 1, 00:00; a full day takes 30 real minutes. It advances during active exploration, and pauses during dialogue, menus, maps, battles, and area/battle entry transitions, following `main.cpp`'s shared actor pause policy. Closing the game does not advance time. Save version 10 preserves the version-9 resident footer and appends a separate bookshop-worker footer. Versions 2–9 start only the new worker at their first shelf while retaining the existing migration behavior for the girl. Version 9 includes the clock, routine progress, kitchen waypoint, surface pause, and frozen doorway animation frame. Versions 6–8 migrate to the new appearance timing. Versions 6 and 7 migrate without a pause; activities already over the one-hour limit finish on the next tick. Version 6 preserves the clock/routine and starts with the stove as the next kitchen target; versions 2–5 start the girl's first kitchen activity.

## Bloom bookshop worker (implemented)

Vaalbara is the world; Bloom is central town 0. A new worker using the existing
`assets/npcs/glasses.png` stays in Bloom's specific bookshop instance (interior 1).
The outdoor glasses resident and elder shop owner remain separate people.

The repeating shelf route uses sprite origins `(235,196)` → `(371,196)` →
`(434,308)` → `(374,257)` → first stop. All four positions passed furniture
collision checks without adjustment. The worker faces up toward the books and
pauses 3, 4, 3, and 4 real seconds, respectively. Walking uses the same 90 px/s,
player-matched walking cadence, collision-sampled A*, and clear-segment smoothing
as the first resident. Each actor has independent route and activity state;
the shared clock advances once. The worker continues offscreen and through
hour skips. No inventory changes or new restocking art are implied.

TALK pauses the worker and turns them toward the player. Opening:
"Just restocking shelfs, need anything?" Choices: "Why do I need books?",
"Where am I?", "No". The books answer is the user's explanation about building,
travel and the purpose of life. Location answers use `story_where_am_i`, resolving
interiors by their entrance's town and outdoors by the speaker's position.
Bloom's answer identifies both Bloom and Vaalbara; unnamed places identify only
Vaalbara. Other NPCs can reuse this resolver without copying town strings.
Answers return to the choices with "Need anything?"; No, X, or Escape closes
the conversation and resumes the interrupted leg/pause and facing.

The version-10 worker footer preserves position, target stop, browsing phase,
remaining pause, facing and animation progress. Paths rebuild after loading.
`residentcheck` exercises three loops, rendering at each shelf and the shared
dialogue panel, dialogue pause/resume, isolated save/load, version-9 migration,
world-clock ownership, hour skip, and the original girl's full routine.

Press T during active overworld play to skip one game hour (75 real seconds of routine simulation). Each keypress advances walking, doors, and activity timers together and shows "1 HOUR LATER". Menus, dialogue, interiors, battles, and transitions do not accept this shortcut.

Test dialogue: cooking, "these new stoves scare me, i'm always afraid of a sudden gas leak"; from the kitchen to the door and on the outward journey, "heading over to my parents house right now, please leave me"; walking to the parents' bed, "time for bed *yawnnnnn*"; asleep, "zzzz"; leaving the parents' house, the walk home and back to the stove, "Sorry i'm busy at the moment".

The sections below retain the broader proposed design for expanding beyond this test. The implementation uses a kitchen walking loop (stove → one tile down → left → up to counter → down → right → up to stove), strict visible-trail navigation with narrow straight doorway approaches, player-obstruction waiting, and an existing sprite rotated into a sleeping pose. Doorway transfers share the battle enemy appearance renderer: alternating two-art-pixel horizontal strips fill in or dissolve in hard eighths over 0.6 seconds, in the original sprite colors. Facing and the current walking frame remain frozen across departure, location handoff, and arrival. A dedicated sleep drawing, multi-resident reservations, story overrides, and authoring/debug overlays remain future extensions.

## Player experience

Residents have purposes: visiting, working, resting, or watching the street. Some have dialogue; others simply carry on with their activities. Silence is independent of movement. Give residents different departure times, walking speeds, and meaningful pauses rather than making everyone move together.

An NPC remains the same person across outdoors and interiors. Entering a house, leaving town, or saving must not restart their routine. A player should be able to follow a resident through a doorway and find them continuing inside.

## First Town 0 routine

1. Begin inside the southwest white house at an authored, clear standing spot by the stove/countertop.
2. For one in-game hour, walk up to the stove, down one tile, left, and up to the countertop; pause for two real seconds facing each surface on arrival, return via the same aisle and repeat. After the hour, walk to the inside of the exit.
3. Cross the doorway into the matching outdoor entrance.
4. Follow authored trail junctions to the northeast red brick house.
5. Approach its door and enter that specific building.
6. Walk to the approach spot beside the first bed on the left.
7. Turn toward the bed, enter a sleeping state, and sleep for one in-game hour, timed from actually getting into bed.
8. Wake, get out at the bed's clear approach spot, and walk to the brick house exit.
9. Leave with the confirmed dissolve effect, retrace the trail to the southwest white house, and enter with the same transfer effect.
10. Return to the stove/countertop work spot and restart the one-hour activity. Repeat indefinitely.

Confirmed routine: stove/countertop walking loop (1 game hour) → outward journey → sleep in the first bed on the left (1 game hour) → return journey → repeat. Each one-hour activity lasts 75 real seconds (1 minute 15 seconds) while the world clock advances. The full cycle lasts 2 minutes 30 seconds plus both journeys and their doorway/bed transitions. Activity durations start on arrival; travel does not consume the next activity's one-hour allowance. This routine is duration-driven against the shared world clock rather than fixed departure hours, so its wall-clock departure time can drift as travel varies.

Use descriptive place names during authoring. Verify their building identities, stove/countertop work spot, and bed visually before assigning coordinates; compass descriptions alone do not establish which current house asset is intended.

## System structure

- **Resident definition:** stable identity, artwork, dialogue policy, routine, and any story conditions.
- **Resident state:** current location, position, facing, activity index, elapsed activity time, and occupied interaction target.
- **Location:** outdoors or a specific building instance. Include the entrance identity, not only the interior layout ID: the current story system already distinguishes shared rooms using their doors.
- **Named places:** door approaches, trail junctions, standing spots, and furniture targets. Resolve outdoor places relative to the town placement so world seeds do not break routes.
- **Activity sequence:** wait, walk, leave building, enter building, face target, use object, sleep. Activities finish through explicit conditions and can wait or fail safely.
- **Navigation:** authored trail waypoints can choose future routes; collision-aware local pathfinding currently follows the visible trail mask. Interior movement uses the room's walkable space. A shortest path alone would let residents cut across grass instead of following the trail.
- **Interaction targets:** each bed/chair/etc. has an identity, clear approach position, facing, occupied pose position, and reservation. Furniture graphics alone are insufficient to identify the leftmost bed reliably.

Keep movement and routine state separate from story dialogue. `story_npcs_here` currently returns fixed placements and should eventually read resident state for moving people. Drawing must use each resident's facing and walking/activity state, including inside houses. A silent resident must not produce an empty dialogue box or misleading TALK prompt.

## Persistent in-game clock

- Use one shared, continuously advancing game-world clock for all residents. Store elapsed world time with the save; derive the day number and time of day from it.
- Confirmed clock rate: one full 24-hour game day lasts 30 real minutes of advancing clock time. One real second advances 48 game seconds; one game hour lasts 75 real seconds.
- Entering/leaving houses, changing areas, and leaving town do not reset the clock or restart schedules. Offscreen residents use the same clock as visible ones.
- Schedule departures and activities against world time. Travel still takes actual movement time: a late resident completes the trip rather than teleporting to the next appointment. Define whether missed activities are skipped or performed late per routine.
- Starting hour and whether the clock advances during menus, dialogue, battles, and transitions remain to be chosen. Proposed default: advance during active play, including dialogue and battles; freeze during pause menus and loading/transitions. Closing the game does not advance world time.
- A clock does not require lighting/day-night visuals immediately. A visible HUD clock and lighting changes are separate presentation decisions.

## Continuity and interruptions

- Advance routines using the shared persistent clock, with one consistent policy for menus, dialogue, battles, and transitions.
- Residents continue logically while their location is not being drawn. Start with a small Town 0 population and advance the same activity state for visible and unseen residents; optimize later if needed.
- Crossing a door changes location once. Never draw the same resident both inside and outside or reset them when a room loads.
- Confirmed area-transfer effect: NPCs/actors use the same strip appearance/dissolve animation as an enemy appearing at battle start when leaving an area and when entering the destination area, including house doors. Reuse that effect's appearance and timing; transfer location once at its defined handoff. Routine walking resumes after the arrival appearance. This is attached to the actor's transfer, not a full-screen area fade or a flash whenever the player loads a room containing them.
- Save stable resident identities, building identities, activity progress, and the relevant clock. Do not rely on transient path nodes as saved identity. Rebuild routes and reservations after loading; give older saves a defined initial state.
- Let residents wait and retry when someone blocks a narrow route; do not push the player or teleport in view. Reserve narrow doors and furniture to avoid overlaps. If routing genuinely fails, remain in a safe state and report the failed destination in debug mode.
- Pause a speaking resident during conversation and resume afterward. Silent residents follow the chosen player-obstruction behavior without opening dialogue.
- Story overrides need explicit priority and a defined resume/replacement policy so a story change cannot strand a resident mid-doorway.

## Implementation order

1. Choose starting hour and pause policy; identify the resident and verify the exact buildings, stove/countertop work spot, and bed. The activity durations, return journey, and indefinite repetition are confirmed.
2. Author named door, trail, and bed targets for this route. Add debug route lines, activity labels, and target markers to inspect them.
3. Implement the shared clock and one persistent resident walking outdoors and indoors with correct facing, animation, collision, and doorway transfers using the battle-start appearance/dissolve effect.
4. Add bed approach, reservation, and a visible sleeping pose. Inventory available art first; sleeping artwork is not established by the existing walking sheets.
5. Add offscreen advancement and save/load continuity for the clock and resident before treating the routine as complete.
6. Validate the full journey, then reuse activities and targets for more residents with individual purposes and timing.

## Acceptance checks

- Follow the resident for the entire journey: they use the trail, correct doors, and specified bed without crossing solid furniture.
- Enter either house before, during, and after their transfer: one resident appears in the correct location with continuous progress.
- Leave and return, and save/load during walking and sleep: the routine continues without restarting or duplicating the resident.
- Block a door, occupy an approach, and give two residents the same bed: they wait/retry safely without overlapping or trapping the player.
- Pause/open menus/talk/start a battle: time follows the agreed policy.
- Check different world seeds, existing story dialogue, silent interaction behavior, depth ordering, and old saves.

## Decisions to confirm

1. What hour does a new game start, and which interruptions pause the clock? The full day length is confirmed as 30 real minutes. This resident departs after one hour at the stove/countertop, sleeps for one hour after reaching the bed, then returns and repeats.
2. Verify the stove/countertop facing targets and choose a natural turn cadence. No additional gestures or work animations have been specified.
3. Which resident performs this route? Keep the three current speakers in place unless reassigned; a new silent resident is also an option.

Suggested starting scope: one silent resident, one complete house-to-house trip, then expand once the player can follow that trip naturally.

## Bloom grandmother (implemented)

Grandmother starts seated on the green couch in the orange/brown, red-roof house south of town (interior 5). She rests for 30 in-game minutes, follows the visible trail to the bookshop (interior 1), searches an unoccupied freestanding shelf for five real seconds, visits the customer side of the front desk for five real seconds, and returns home to repeat. A shelf reservation keeps the glasses worker from browsing the same shelf while she approaches, searches, and clears the aisle. Walking, doorway effects, offscreen updates, conversation pauses, and the shared clock follow the existing resident conventions.

Her greeting is "Good day deer, what do you need?" Choices are "What's there to do in town?", "Where am I?", and "No". The activity answer is: "I usually pick out a good book from the library and go back home and read. But for a young one like yourself, there's a small cave south of town and a graveyard to the northwest, if you're looking for a little adventure." Location uses the shared world-position resolver. Answers return to the choices; closing resumes her routine.

Save version 11 appends her activity, position, timers, shelf and doorway state after the existing resident and worker records. Older saves start her on the couch. Headless resident checks cover complete journeys on seeds 387 and 2026, trail and furniture collision, timing, shelf reservations, dialogue, and save/load in every phase. Renderer captures are in build_tmp/npc_review/grandmother_phase_*.png.

Trail enforcement: outdoor pathfinding now recognizes Town 0's custom trail atlas cells (columns 0–15, rows 6–10) and checks the entire feet box against their drawn trail pixels at every sampled step. Only a 16-pixel-wide, short straight approach beneath each of the two house doors permits departure from that mask. Grass is excluded from the route, including transparent corners of trail tiles. The NPC waits/retries if no valid trail route exists.

Diagonal movement: A* permits eight directions in every area, including interiors with normalized travel cost, then merges visible waypoints into straight segments. Each complete segment must pass the same whole-feet trail and collision checks. Facing is chosen from the fixed segment direction so rounding cannot alternate up/right on a 45-degree run. Interior routes use the same straight-line smoothing with furniture collision checks. Kitchen activity waypoints still require the authored stove/aisle/counter stops, but movement between any stops can be diagonal where clear. Player input and enemy pursuit already use normalized continuous diagonal movement.
