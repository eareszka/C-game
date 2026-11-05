# Enemy sprite style

The one rule for every enemy battle sprite (the user, 2026-11-04). It is measured
from the 26 sprites the user picked as what the game's enemies should look like.
They are on the style board.

## The style

NES style at every size. Sprites are crisp, chunky and readable, with flat
colours and a black outline, and every pixel looks placed on purpose. A big enemy
is drawn the same way as a small one, with more pixels and the same crispness.

## Size

Enemies grow as their tier and difficulty rise. The game draws every sprite at
2x. Never scale art: one art pixel stays one art pixel. Keep the frame snug to the
drawing, because the hit circle comes from the frame's size.

| Tier | Longer side |
|---|---|
| Starter | 20 px |
| Low | 15 to 31 px |
| Medium | 18 to 32 px |
| Upper | 26 to 48 px |
| Hard | 38 to 66 px |
| Severe | 52 to 80 px |
| Elite | 66 to 96 px |
| Boss 1 | 100 to 150 px |
| Boss 2 | 160 to 260 px |
| Boss 3 | 280 px |

## Shape

- **One creature, one strong silhouette.** It reads at a glance on black.
- **Exaggerate what makes it that creature.** Small sprites can be stubby and
  cute, and bigger ones can take on real proportions.
- **Clean runs and clear steps.** Avoid long smooth curves that look like vector
  art.
- **Keep big sprites crisp.** Give them line work, plates, ridges, teeth and other
  pixel-level detail. Large plain smooth areas break the style.

## Colour and shade

- Only colours from the game's palette, at most 8 plus black. Most sprites use 4
  to 8.
- Flat hard fills. No gradients, soft edges or see-through pixels. No dithering,
  hatching or speckle.
- At most three tones per material, with clear steps between them.
- Light comes from the upper left, and shade follows the body.
- Tiny details are welcome when each one is a real feature, such as a tooth, a
  claw, a horn tip or a stripe.

## Line

- A black outline, 1 px wide, round the silhouette. Never doubled.
- Black lines inside separate the parts. About 8 to 15% of the drawn pixels are
  black inside the outline.

## The black arena

The battle draws on pure black, so the player never sees a black outline.

- No part may be drawn only in black, because it vanishes.
- No body may be mostly close to black.
- The sprite must read on black. Black is what the player gets.

## Eyes

Each eye is one solid mark of 1 to 2 px: black on lit skin, or one accent colour
on dark hide. Never a ring, an iris with a pupil or a white glint. X eyes and skull
sockets are allowed as character features.

## Poses

When a brief asks for poses: 4 to 5 distinct poses, each held 260 ms, with big
steps between them. Every view and pose has the same body proportions. No water
under an enemy.

## Keeping the design

The user likes every enemy's design. Keep the creature in the brief: the same
signature features, main colours and mood. Change how it is drawn, not what it is.

## Done

A sprite is done when the checker shows no failures and the user has approved it.
