# The NES fit: redo enemies one at a time, on the user's say

Handed over on 2026-11-05. This file is for the session doing the work. It is not for the sprite agents, which still read only their job folder.

## What the user said

> "do one enemy at a time using the new stylistic fit. i will intruct which ones to fix."

Their complaints about the first round: "96's legs and back fin seemed to have merged into 1. 90's repeating pattern looks ai generated and copy pasted, 93's snake like underbelly and proportions are off and dont make sense, 34 looks too blocky. overall a majority look ai generated or that they copied the same feature/pattern throughout the design". They also said "i want to make it clear how the enemies should all have the nes style".

They say the look gets worse as size grows, though it also depends on the sprite.

## The new fit

The user chose the first three directly. The last three come from their complaints.

- **Big enemies:** big flat shapes and few lines, at the same 1 px pixels as the player. Plain areas are welcome.
- **Colours:** 4 to 5 plus black. Up to 8 only when a brief says the design needs it, such as 91's rainbow crystals.
- **Shading:** two flat tones per material, base and one shadow. No highlights or gradual shading.
- **No motif repeated identically:** scales, plates and bricks differ in size, spacing and shape, and some are left out.
- **Every part is its own part:** limbs, fins and tails are separate, and each can be traced from the body to its tip.
- **Proportions make sense** for that creature.

Some of the 26 picks use more colours or tones than this. They stay as they are. The rule should say the picks show the look, and where they differ the written limits win.

## Why the first round went wrong

- **The rule asks for filler.** `SPRITE_STYLE.md` says "Give them line work, plates, ridges, teeth and other pixel-level detail. Large plain smooth areas break the style." `PROMPT.md` step 4 repeats it, and `check_nes` warns "too smooth" under 4.5 colour patches per 100 px. So agents fill big bodies with texture.
- **The drawings are made by code.** 74 of 86 `draw.py` files use `for` loops, median 8 each, and loops make identical bricks and scales.
- **Repetition measures.** Share of detailed 5x5 blocks that repeat exactly elsewhere in the sprite, without overlapping: the 12 picks of 28 px or more have a median of 0.00, and only 21 is high at 0.26. The 86 new drawings have a median of 0.06, reaching 0.59 on 6. 93 is 0.26, 90 is 0.19, 34 is 0.12.
- **Anatomy is never checked.** 96 scores 0.02, so its problem isn't repetition. Nothing asks whether the body makes sense.
- **Passing the checker isn't approval.** All 86 passed, and the user rejected most of them.

## Set up once, before the first sprite

Nothing below has been done yet.

1. Copy `art/direction/SPRITE_STYLE.md` to `art/direction/approved_enemy_study/SPRITE_STYLE_nes_v1_2026-11-05.md`.
2. Rewrite `SPRITE_STYLE.md` to the fit above: the sentence "A big enemy is drawn the same way...", and the Shape, Colour and Line sections. Remove "Large plain smooth areas break the style". The inner-black figure of 8 to 15% no longer holds for big flat sprites.
3. Update `tools/sprite_agent/PROMPT.md`. Before drawing, the agent lists each body part and where it attaches, in a comment in `draw.py`. Step 4 drops "no long smooth curves or large plain areas" and asks: Can you trace every limb and fin to where it joins? Could this animal stand or move? Do any two patches look copy-pasted? Could this be on an NES, with flat shapes and few lines?
4. `tools/sprite_agent/new_job.py`: mark new jobs `"rule_version": 2` in `job.json`, because the `rule` key already holds a hash. Set colours to 5, or the brief's own `colours`, and show that in `BRIEF.md`.
5. `tools/sprite_agent/check.py`: on a rule 2 job, fail a `draw.py` containing `for`, `while` or comprehensions, parsed with `ast`.
6. `tools/enemy_style.py`, `check_nes`: add a strict mode for rule 2 only: no "too smooth" LOOK, no floor on inner black at big sizes, a repetition LOOK using the measure above, and tones limited to 2 as far as hue grouping can tell. `m['tones']` counts materials sharing a hue together, so treat it as a LOOK, not a FAIL.
7. `tools/sprite_agent/pix.py`: remove `tile` and its docstring line. `mirror` stays, since symmetry is normal in this style. `poly`, `oval`, `rect` and `dot` are enough even at 280 px when shapes are flat.

**The 86 finished jobs must keep the old checks.** Afterwards, `python -B tools/sprite_agent/run_tier.py TIER --list` must still show every tier as finished. Test that a rule 2 `draw.py` with a loop fails and one without passes, using a scratch copy, not a real job.

## Each sprite, only when the user names it

1. Add their note to `fixes` in `tools/sprite_agent/briefs.json`, in their words. Remove any wording that conflicts. For example, 34's note says "with the extra detail that size allows", and some looks ask for texture.
2. Run `python -B tools/sprite_agent/run.py ID`. It's one brand-new agent reading only its job, with no added context. The old job moves to `art/enemies/nes/_old/`. Don't use `run_tier.py` to draw, because it would redraw everything the new rule marks as unfinished.
3. Look at the result at game size against the complaint. Show old beside new and open it in Aseprite, using PowerShell `Start-Process` on the full path.
4. Say honestly if it still looks AI-made, and which part. Then wait. **Never start the next enemy unasked.**

If the fit keeps looking AI-made after a few sprites, say so plainly. The limit may be drawing through code at all, and the options then are the user drawing key sprites by hand, or a different tool for those.

## Limits

- Claude only. The user moved sprites off Codex. 29 and 94 are still Codex's until the user names them.
- Nothing installs in the game, and nothing commits.
- Sprites the user edited by hand are only redrawn if they name them: 38, 42, 47, 56, 57, 60, 65, 69 and 98 so far. A redraw replaces their edit, so warn them first.
- Don't start a batch or a queue. The complaints above are for reference, not a list to work through.

## Tools to know

- **Sheet:** `art/enemies/nes/_sheets/edit_sheet_03.aseprite`. `python -B tools/sprite_agent/edit_sheet.py update` brings saved edits in and puts new drawings on it. `open` opens it. The `watch` updater currently runs in the `sprite-edits-lore-sizing` session and stops with it.
- **Small changes:** `tools/sprite_agent/touch_up.py ID "note"` starts from the current sprite. It keeps the old checks unless you change that.
- **Audit:** https://claude.ai/artifact/EVMbnRYyQaVXmJuyjp8whu. Build with `python -B tools/enemy_audit/build_audit.py SCRATCHPAD`, then publish `enemy_style_audit.html` to that URL, reading the artifact first. The standing order is once per tier for drawings. For this work, ask the user how often they want it.
