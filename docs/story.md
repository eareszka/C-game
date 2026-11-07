# Story script: the lost dog

The user's decisions, 2026-11-07. This is the story's spine, from the opening to the ending. The lore underneath is unchanged (`src/story.cpp`, `include/story.h`): a civilization above writes this world's script and feeds it through the swarm at the planet's centre. The writers' pages fall into the world as notes. The boy is the one person outside the script.

## The reason to leave home
The writers take the boy's dog. He is the only one who remembers it, and he sets out to get it back.

## Intro: the foggy night
1. **The middle of a foggy night.** The boy and his dog wake up. The dog runs outside, goes to the water, and barks constantly at a fallen note.
2. **The note.** The player opens it: *"A young boy's dog goes missing and he's forced to find him."* When he finishes reading, the dog is still there.
3. **The hand.** A grand enemy covered in black emerges from the shadow. It is the **silhouette of the hand monster, 44 Itqiirpak**, drawn the same size as the real fight (its sheet filled solid black).
4. **The first battle: a forced loss.** The boy has **3 HP** and no bombs. The hand opens with an unavoidable attack and keeps repeating it until a bomb is used. He has none, so the third hit kills him.
5. **The next morning.** He wakes at home. The dog is gone, and so is everything that belonged to it.

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
