# Story script: the lost dog

The user's decisions, 2026-11-07. This is the story's spine, from the opening to the ending. The lore underneath is unchanged (`src/story.cpp`, `include/story.h`): a civilization above writes this world's script and feeds it through the swarm at the planet's centre. The writers' pages fall into the world as notes. The boy is the one person outside the script.

## The reason to leave home
The writers take the boy's dog. He is the only one who remembers it, and he sets out to get it back.

## Intro: the foggy night
1. **The middle of a foggy night.** The boy and his dog wake up. The dog runs outside, goes to the water, and barks constantly at a fallen note.
2. **The note.** The player opens it: *"Tonight the last pet is taken. Tomorrow something new takes its place."* (final, 2026-11-08: the last pet taken; new creatures, the cryptids, made to replace them, not pets turned into them) When he finishes reading, the dog is still there.
3. **The hand.** A grand enemy covered in black emerges from the shadow. It is the **silhouette of the hand monster, 44 Itqiirpak**, drawn the same size as the real fight (its sheet filled solid black).
4. **The first battle: a forced loss.** The boy has **3 HP** and no bombs. The hand opens with an unavoidable attack and keeps repeating it until a bomb is used. He has none, so the third hit kills him.
5. **The next morning.** He wakes at home. The dog is gone, and so is everything that belonged to it.

### What the intro needs (2026-11-07)
- **The area:** only the northern half of the starting island. A **wall of fog** closes off every tree and keeps the player on the path. The user is drawing the outline on `art/story/intro/island_outline.aseprite`. One pixel there is a quarter of a tile, and the top-left is world tile 1400,1400 (town 0 is a fixed stamp, the same in every world).
- **Night:** one night filter over the whole frame, so every sprite, tile and NPC turns to night at once.
- **Built (2026-11-07), `src/intro.cpp`:** the night tint (outdoors and in rooms), the dithered fog wall over everything outside `assets/story/intro_area.png`, and the boy kept inside it (he slides along the fog). Try it with `run.bat --intro`. Set `INTRO_OUTSIDE=1` to start at the house door instead of in the room. It isn't saved and NEW GAME doesn't start it yet; that waits until the whole night is built.
- **The dog (approved 2026-11-08):** a small dark brown French bulldog, 4 views, drawn by hand at game size from a PixelLab design (`art/story/intro/dog/dog_design.py` → `assets/story/dog.png`). The walk bounces like the boy's: the side walk's motion is PixelLab's, cleaned to the confirmed design; front and back squash 1 px a stride. Idle: panting, or a tail wag from behind. In the game it follows the boy along his own footsteps, in the room and outdoors (`intro_dog_*` in `src/intro.cpp`). PixelLab has 0.5 generations left.
- **The spawn house (room 0), built 2026-11-08:** on the night, the dog's bed stands where the plant is and its bowl beside it, where the opening chest is; the chest of drawers is there both times (`art/interiors_nes/house0_intro_design.py` → `assets/interiors/room_0_intro.*`, loaded as room 0 while the intro runs). The morning after, the plant and the opening chest are back, as if they'd always been there.
- **The day stands still** for the whole intro: the townspeople's clock (`resident_tick`) doesn't run, so no one walks to the house.
- **On foot:** no bicycle on the night, even in a debug run.
- **The opening, staged (built 2026-11-08, the user's direction):**
  1. The boy asleep in his bed (`assets/story/boy_sleep.png`, his own side frames, drawn as the townspeople sleep) and the dog asleep in its own, Z's off both. He can't move.
  2. After 2 s the dog wakes with a start, a "!" over it, looks west, east, west, east, runs for the door and leaves as a townsperson does: to the room's entry spot (`resident_entry`), fading there (`draw_actor_appearance`) on the step and facing it arrived with, and appearing on that same frame outside the house's door (`resident_outside`).
  3. A second later the boy wakes: he stirs in the covers (the Z's stop), then hops out onto the floor in front of the bed (sprite origin 403,217, clear of the bed so none of him is hidden), facing down. Then the house's lights come up, easing in over 1.6 s: the night tint is off indoors from here, still on outside.
  4. When he steps out, the dog is already well on its way: west of the house and north of the door (the user's spot, sprite origin 47958,46271), running north, about to leave the top of the screen. It holds there while the screen is still black from the door, then runs on.
  5. Near the north shore it stops at the user's spot (sprite origin 48150,45565 by the debug readout, kept relative to town 0) and stands facing north, barking at nothing: two yips and a breath, louder as he nears (`SFX_BARK`, synthesized).
  6. When he comes within 7 tiles, a page floats down out of the air (the hole's page art), swaying, and lands right north of the dog, in front of its nose. Then the dog goes round it barking: left of it, in front, right of it, in front again, and on, facing it from each (two rounds of barks at each). Only now: TAKE NOTE, *"Tonight the last pet is taken. Tomorrow something new takes its place."*
  7. A breath after he reads it, the hand rises out of the sea north of the dog (built 2026-11-08): 44 Itqiirpak's front view at the fight's own size, black (8,6,12), cut off at the waterline as it comes up over 3 s, breathing (frames 0-1), then every mouth wide (frame 2). The dog turns to the sea and barks at it; the boy can't move. Fitting: 44 comes out of the water in its lore.
  8. The fight: 44 in intro mode (`BattleScene::set_intro`: 3 bars, no bombs, drawn black). Its grasp kills him on the third hit. The grasp is to become an outline of the hand instead of a ring (the user; brief to the pattern session, `playtest/briefs/44_grasp_hand_outline.md`).
  9. However the fight ends, the night is over: back on the map he lies out cold where he stood (no Z's) while the hand reaches down over the shore, takes the dog and carries it off north, the dog kicking and barking fainter. The screen goes black, "THE NEXT MORNING" on the black, and he wakes in bed in the everyday room 0 (plant and chest back, no bed or bowl, no dog), lights on, and gets up. The curtains are shut on the night and stay shut in the morning until he has been out and the day has come (`assets/interiors/room_0_morning.*`, from `house0_intro_design.py`).
  10. His first step outside, he stands still while the night lifts to day and the fog thins away to nothing; then the intro is over. Test start: `INTRO_OUTSIDE=taken game.exe --intro`.
  - Test starts: `INTRO_OUTSIDE=1` (at the door, the dog already out), `INTRO_OUTSIDE=note` (three tiles south of where the page lands), `INTRO_OUTSIDE=hand` (there, the page already read: the hand rises).
- **The opening chest (2026-11-08):** the boy now starts with no weapon. The chest by the plant holds the knife's makings, 2 wood, 3 stone and the knife book, with the line "Someone left these out for you." It opens once a game (`StoryFlags::home`, the old padding byte, so saves keep their layout). With no weapon he can't swing or shoot.

## Looking for the dog
- **"Where's my dog?"** becomes a talk option with everyone.
- **On the island (Bloom):** people are shocked and say they never knew he had a dog. The writers erased this dog from their memory.
- **After leaving the island:** people answer with some version of *"Why would you ever want one? They're so dangerous."* On the mainland, dogs are known only as monsters: **17 Qiqirn** and **36 Cu Sith** are the dogs people know. (The user rejected "What's a dog?" because those two enemies make it a plot hole.)
- Draft mainland lines, not yet approved: "Keep your voice down. If one hears you, it'll come." / "Lost one? Good. Don't go looking for it." / "You *kept* one? In your house? Are you mad?"

## The bomb and the rematch
- **The battle bomb:** X uses one crafted `ITEM_BOMB` and clears every enemy bullet on screen. X no longer switches weapons; Q and E do.
- **The rematch with 44** (tier 2, after the TURN): the same unavoidable opening attack. Now the boy has bombs, drops one, escapes, and the real fight begins.
- The writers' note already in the game fits it: *"The hand goes where it walks. It walks everywhere."*
- The pattern session is building it from `playtest/briefs/44_itqiirpak_bomb_opener.md`, previewed with `game.exe --battle 44`.
- **Still open:** make sure the boy can get a bomb before 44 appears, or a fight he can't win blocks the game.

## The ending
The boy defeats the hive (the swarm, 100, at the planet's centre) and **writes a note of his own to bring his dog back**. Everything in the world is reset.

The game opens with a page that takes the dog and ends with a page the boy writes himself.

**Still open:**
- What the reset restores: the world as it was before the foggy night, or a fresh one.
- Whether the boy remembers what happened.
- The last shot. A suggestion: a clear morning, the dog runs to the water, and there is no note.
- Whether the reset leads to a New Game+.

## How the old stages fit
ARC1 → TURN → DESCENT → OPEN → AMNESIA still read off the beaten bosses. The dog story runs over the top of them:
- The intro happens before ARC1.
- The 44 rematch falls in the TURN.
- The ending replaces the old "walk home / Flesh Planet / true world" plan (TODO.md decision 1).
- AMNESIA is now the people's forgetting, which the intro already shows on a small scale.
