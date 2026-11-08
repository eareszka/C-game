# 44 Itqiirpak: the grasp as an outline of the hand

From the story session, 2026-11-08. The user's words, after watching the intro's forced fight: **"instead of a simple ring it should be an outline of the hand"**.

## What to change
- 44's opening grasp (the unavoidable attack from `44_itqiirpak_bomb_opener.md`, repeating every 2.4 s until a bomb) is a closing **ring** of bullets today. Make it the **outline of a hand** instead: bullets laid along a hand's silhouette (palm, four fingers, thumb) around the boy, closing in on him as the ring does now, so it reads as the hand grabbing him.
- Keep everything else about it as it is: unavoidable, no gap to slip through, 1 bar a hit, repeating until a bomb, then 44's normal fight.
- The shape can come from 44's own sprite (`assets/enemies/redraws/44_itqiirpak.png`, the front view, frame 0) so the outline matches the hand on screen, or a simpler hand drawn in points. Your call within battle-pattern-rules; say what you chose.

## How it moves (the user, 2026-11-08, follow-up)
The user's words: "the bullets that form the outline start at the enemy's actual position, shrink and then grow to the outline, then slowly follow the player, increasing speed. Once the player is inside the middle of it they are guaranteed to have already taken a hit, and the outline shrinks its outline down to the player 2 more times, killing it."

Broken down, with the user's answers to two questions:
1. **Born at 44:** the outline's bullets start on 44 itself, at its actual position on screen.
2. **Shrink, then grow:** they draw in (shrink) and then grow out into the hand outline.
3. **Size:** the grown outline is **the same size as 44's sprite** on screen (its frame at battle scale, about 260x176).
4. **Follow:** the outline then follows the boy, slowly at first and speeding up.
5. **First hit:** by the time he's in the middle of it he must already have been hit: the outline's edge can't miss him on the way.
6. **Two more grabs:** after that first hit, the outline **grows back out round him and slowly shrinks down onto him**, twice more, each a grab of its own with a beat to read it. Each shrink hits once. With 3 bars and 1 bar a hit, the third hit kills him.
7. In the rematch (bombs), a bomb at any point clears it and 44's normal fight begins, as now.

## Where it shows
- The intro (story session's): the night's forced loss. 44 is drawn black there (`BattleScene::set_intro` sets `_silhouette`, which the story session added; leave it). The boy has 3 bars and no bombs.
- The rematch later in the game, with bombs.

## Preview
- `game.exe --battle 44 --intro` (3 bars, no bombs, the black hand): the user approves it there.
- `game.exe --battle 44`: the rematch version with bombs.
