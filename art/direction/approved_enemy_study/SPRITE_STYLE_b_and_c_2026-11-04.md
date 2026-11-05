# Enemy sprite style

**The rule changed on 2026-11-04 (the user): NES style at every size, with enemies growing larger as their tier and difficulty rise, and upper-tier bosses very large. It replaces styles B and C.** The rest of this file still describes B and C until it is rewritten, so don't draw to it yet.

The rules every enemy battle sprite follows, new ones and redraws. They are not
chosen: they are measured from the sprites the user is happy with, and anything
else is held to them. `tools/enemy_style.py` holds the measurable half. Read
this before drawing or generating an enemy.

The one-palette rule of `ART_DIRECTION.md` still holds underneath. Its four
colours a 16px cell is for the tile sheet, not for battle sprites.

![the style board PixelLab gets](approved_enemy_study/style_bc_native_512.png)

## The style

**Every enemy is a combination of styles B and C** (the user, 2026-11-04: "ALL
enemies from here on out will be a combination of B and C"). The names come
from the style audit of 2026-11-04; `STYLE_B` and `STYLE_C` in
`tools/enemy_style.py` list who is in each.

- **From C, shaded naturals:** real animal proportions and weight, and shading
  in clear steps.
- **From B, flat cartoons:** hard flat fills, clean black lines and strong
  shapes that read at a glance.

Tone is free. A goofy Bes Rap and a horrible Siehnam belong in the same game as
long as they are drawn the same way.

This replaces the old bible, which lived on a branch that no longer exists, and
two rules that had drifted apart: chibi anatomy with a dark, mid and light ramp,
and one colour plus one shade.

## The reference

**B:** 29 Karnabo, 77 Hoga, 93 Chipique. **C:** 87 Corocotta, 92 Siehnam,
45 Kusa Kap.

When a rule here is unclear, the answer is whatever these six do. They replace
the old anchors 0, 1, 3 and 8, which were about 20 px wide and could not show
how to shade a large body.

## Form

- A real animal has its real proportions and weight.
- A monster or folklore creature has a clear, expressive shape, and the head or
  face is easy to find.
- One coherent silhouette, composed for its view. No stacked cutout pieces.
- Not chibi, not an icon, not a diagram or an emblem. Not smooth vector curves,
  and not dense rendered modelling.

## Fill and shade

- **Flat, hard-edged fills.** No gradients, soft shading, dithering, hatching,
  speckle, scale lattices, fur noise or antialiasing.
- **At most 3 tones per material** (the user, 2026-11-04), matching the three
  tones the overworld's stone, wood and foliage use. Most materials want a main
  colour and one shade. Add the third only where the form needs it.
- **Shade shapes follow the body.** They should explain where a limb turns or
  a mass ends. A flat sprite whose patches don't follow its anatomy still fails:
  compare 38 Igtuk with 29 Karnabo.
- **Clear steps.** Neighbouring tones differ enough to read as separate shapes.
- **Light from the upper left**, as everywhere else in the game.
- **Small patches merge.** A patch of 6 px or fewer takes the colour around it,
  except eyes and teeth (`flat()` in `art/enemies/pixellab/36_cu_sith/views.py`).

## Line

- One pixel of black for the outline and for the lines between parts. No
  doubled outlines.
- About 5 to 15% of the drawn pixels are interior black. Much less reads as a
  cut-out, much more breaks the sprite into shards on the black arena.

## Colour

- Only colours from `game_palette.gpl`, and at most 8 plus black.
- Prefer the colours the world already uses (`OVERWORLD_STYLE.md`, `MATERIALS`):
  it ties the enemies to the towns. 7 Alber's reds are the coastal town's red
  paint, and 70 Trollgadda's greens are the overworld's grass and stems.
- Most B and C bodies sit around saturation 12 to 41 and lightness 36 to 66.
  A grey wolf or a dark eagle can sit outside that. Nothing goes darker on
  average than lightness 25, apart from the exceptions below.

## The black arena

The battle draws on pure black (`src/battle.cpp`, `BattleScene::draw`), so the
player never sees a black outline.

- **No part may be drawn only in black.** It vanishes: 16 Kamaitachi's ears,
  43 Sazae-Oni's shell tip, 84 Kigutilik's cup top, 12 Ebigane's tail tip.
- **No body may be mostly close to black.** 91 Kurrea's plates float because its
  serpent body is almost arena black.
- **Look at every sprite on black and on grey.** Black is what the player gets.

## Eyes

Each eye is one solid mark of 1 to 2 px: black on lit skin, or one accent colour
on dark hide, with at most a black brow or socket line beside it. Never a ring,
an iris with a pupil, or a white glint (the user, 2026-10-29). X eyes and skull
sockets are allowed as character features, as on 25, 57 and 99.

## Size

The game draws every sprite at 2x. Never scale art; one art pixel is one art
pixel.

Drawn height by tier, from what B and C sprites already are:

| Tier | Height |
|---|---|
| Starter, Low | 30 to 45 px |
| Medium, Upper | 30 to 60 px |
| Hard | 35 to 65 px |
| Severe | 45 to 80 px |
| Elite and up | 50 px or more |

Keep the frame snug to the drawing. The hit circle is 0.8 times the frame's
shorter side (`src/battle.cpp`), so empty canvas makes an enemy easier to hit.
The user accepted that small enemies get bigger hit circles as they grow.

## Poses and animation

- 4 to 5 distinct poses at 260 ms (`STEP_MS`, the user: anything smoother reads
  wrong). A sheet with more cells holds each pose across several cells.
- A pose's meaning in the fight stays the same: the frame a shot leaves on, an
  open mouth, an `alt` or `flap` sheet.
- No water under enemies in battle sprites (the user, 2026-11-02).

## Redrawing an existing enemy

Keep the design idea: the same creature, signature features, main colours, mood,
view and attack poses. Change how it is drawn, not what it is, unless the user
asks for a new design.

## Exceptions

- **Bosses kept as they are** (the user, 2026-11-04): 6 Wakmangganchi Aragondi,
  23 Olgoi-Khorkhoi, 30 Dajna, 49 Physeter, 52 Sannaja, 98 Boiuna, 100 Flesh
  Planet.
- **Others kept as they are** (the user, 2026-11-04): 12 Ebigane, 13 Beast of the
  Charred Forests, 31 Man-Eating Boulder, 46 Lusca, 63 Hidebehind, 65 Mice That
  Eat Iron, 99 Fad Felen.
- **81 Ieltxu** is near-black on purpose. It lights up in its fire pose.
- **97 Ro** is the one black enemy. Its hide stays black, and it reads through
  lighter charcoal and red accents.
- **Sprites already in B or C stay as they are**, including those over the limit
  of 3 tones, until the user asks for them to change.

## Checking

```
python tools/enemy_style.py 29              # an installed enemy, every sheet
python tools/enemy_style.py draft.png --tier LOW
python tools/enemy_style.py --queue         # the redraws still to do
```

FAIL breaks a hard rule. WARN is a number outside the range the approved sprites
sit in, for a person to look at. The checker cannot judge eyes, anatomy or
whether shade shapes follow the body, so nothing is finished until the user has
approved it. The words to send PixelLab are in
`approved_enemy_study/STYLE_BRIEF.md`.
