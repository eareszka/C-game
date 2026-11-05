# Enemy style reference pack for PixelLab

**NES style at every size (the user, 2026-11-04), growing with tier and difficulty.** `SPRITE_STYLE.md` is the rule, measured from the 26 sprites the user picked, and `tools/sprite_agent/` makes each sprite with a fresh agent that reads only the rule, the prompt and its brief. This brief describes the old rule and its board, so don't send them.

What PixelLab gets when it draws an enemy. The rules themselves are in
`art/direction/SPRITE_STYLE.md`, which wins wherever the two differ.

## Style image

`style_bc_native_512.png`, listed in `style_bc_native_512.json`. It holds 22
sprites from styles B and C that come out clean on `tools/enemy_style.py`, at
native pixels on transparent, with nothing scaled. `tools/pixellab_enemy.py`
sends it by default. Rebuild it with `python tools/enemy_style.py --board`.

It is a style reference, not a request to generate a roster or a collage.
PixelLab sometimes copies parts of it, so check every result for pieces that came
from the board.

## Words to include in each generation request

Keep the total prompt within 2000 characters (500 on the instruction-only route).
Start with what the creature is and what must stay, then add:

> Redraw this as the same creature in the style of the reference: one coherent
> flat 2D pixel sprite on a transparent ground. Hard flat colour fills, at most
> three tones per material, with shade shapes that follow the body and light from
> the upper left. One pixel of black for the outline and the lines between parts.
> Real animals keep natural proportions and weight; monsters keep a clear, strong
> shape with an easy-to-find face. No chibi. No gradients, soft shading, dithering,
> hatching, speckle, fur or scale texture, and no antialiasing. No water or ground.
> Eyes are one solid mark of one or two pixels, never a ring, iris or glint. Every
> part needs a colour, because the game's background is pure black.

## Limits of the workflow

The CLI has no command that reads the bible and certifies a sprite. PixelLab only
receives the style image and the prompt, so getting a reference is not proof of
compliance. `tools/enemy_style.py` and the user's approval are the checks. New
paid requests follow the credit rules in `docs/enemy-restyle-prompt.md`.

## History

The older files in this folder are retired and kept for reference:
`approved_42_fronts_native_512.png` and the other `approved_*` boards, `analysis.json`,
and the `NN_*_frame0.png` crops. They hold 42 sprites approved before the style
audit, including styles A, D and E, and the old anchors 0, 1, 3 and 8. The rules
sent with them asked for chibi anatomy.

97 Ro was generated from `approved_42_fronts_native_512.png` through PixelLab
after explicit per-call approval. The first reference board was rejected for
exceeding 512 pixels, at no charge. The successful request reported 10 generations,
and the draft was palette-cleaned and validated. The user's exception for Ro is
black skin: since 2026-10-18 it keeps the black outline like everything else, its
hide is a charcoal ramp and red is only an accent, for readability on dark
backdrops. That exception applies to Ro alone.
