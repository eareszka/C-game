# 44 Itqiirpak: the battle bomb and the hand's opening attack

From the story session, 2026-11-07. These are the user's decisions. Ask the user anything this brief doesn't settle; don't guess.

## Why
The game's intro: on a foggy night, a black silhouette of the hand monster (44 Itqiirpak) takes the boy's dog. That fight is a forced loss. Later in the game the boy meets the real 44, and this time he has bombs. The bomb is what tells the two fights apart.

## 1. The battle bomb (engine work, battle.cpp)
- **X uses a bomb.** Today X also cycles the weapon forward (`battle.cpp:646`, `E or X`). Take X out of that line, so only E cycles forward and Q back.
- **A bomb clears every enemy bullet on screen.** That's all it does: no damage, no invincibility unless the user asks.
- It uses one `ITEM_BOMB` from the player's inventory. If he has none, X does nothing (a small "no bombs" cue is fine).
- It needs some visible and audible feedback. Keep it within the SNES-like sound style (see sound-direction): synthesise it in `src/audio.cpp` or reuse an existing effect.
- Trials and debug fights (`_fixed_gear`): give them a few bombs so the bomb can be tested in `--battle 44`.
- The HUD should show the bomb count.

## 2. 44's opening attack: unavoidable until a bomb
- The fight opens with an attack that can't be dodged. It keeps repeating that attack until the player uses a bomb. After the bomb, 44's normal fight (its existing patterns) begins.
- What the attack looks like is up to you, within battle-pattern-rules and enemy-movement-rule. It should read as the hand closing in or grabbing, with no gap the player could slip through. Tie the shots to its frames (mouths in the palm, fingertips) the way its fire code already does.
- In the intro version the boy has **3 HP** and no bombs, so the repeating attack kills him on the third hit. Make the attack deal exactly 1 HP-bar's worth per hit, or whatever lands three clean hits from 3 HP. Say what you chose.
- The intro scene itself (the night, the silhouette art, the forced loss, waking at home) is the story session's job, not yours. Leave a way to start 44 in intro mode for testing: 3 HP, 0 bombs, and the silhouette later. Something like `game.exe --battle 44 --intro`.

## Preview
`game.exe --battle 44`: the user approves it there.
