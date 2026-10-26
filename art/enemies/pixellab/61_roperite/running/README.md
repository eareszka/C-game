# Roperite running animation

The user approved `../61_roperite_frame0_clean.png` and requested running
animations for the positions Roperite uses in battle (2026-10-18).

The battle renderer uses D, DR, R, UR, U, UL, L, DL, selected from velocity.
Five distinct views are generated; UL/L/DL mirror UR/R/DR, matching the old
source layout. Native frame size stays 98x65. The existing cycle is five
frames at 260 ms with the lasso attack on frame 2; its timing is preserved.

`generate-8-rotations-v3` was dry-run estimated at 3 generations, reported
1 generation. Raw rotations remain in
`pixellab-out/61-roperite-animation/61-roperite/rotations/v1/`. Inputs use
the approved eight-color palette and share its ground line without pixel
resampling. D uses the exact approved image, rather than the model's rotation.

Each direction is animated with `animate-with-text-v3`, eight frames per
request (five is not supported by the API), estimated at 1 generation per
request. Each request is dry-run validated immediately before submission.
`*-dry-run.json` and `*-result.json` record inputs and returned files/cost.
The description asks for an in-place sprint, alternating leg contacts,
body bob, a trailing segmented rattle tail, and a midpoint rope-lasso flick.

Reproduction commands from the project root:

```powershell
python tools/roperite_run_pack.py prepare
powershell -NoProfile -ExecutionPolicy Bypass -File tools/roperite_run_generate.ps1
# Submit the five paid calls only with user authorization:
powershell -NoProfile -ExecutionPolicy Bypass -File tools/roperite_run_generate.ps1 -Generate
python tools/roperite_run_pack.py pack
```

The API may return the source plus eight generated frames (nine PNGs).
The packer samples frames 0,2,4,6,8 for nine-frame responses, or 0,2,4,5,7
for eight-frame responses, placing the requested midpoint flick on attack
frame 2, and preserves each direction's input as frame 0.
All frames map to the approved palette. It rejects partial transparency,
unexpected dimensions, insufficient distinct poses, and failed Aseprite
round trips. It produces per-direction GIFs and a tagged Aseprite review
source alongside a 3920x65 runtime-layout PNG. Raw generations and original
assets remain separate. Inspect the resulting motion visually; the prompt
and numeric checks do not certify anatomy or the lasso flick.

## Completed checks

All five runs completed successfully, each reporting 1 generation. Including
the rotation, the running-animation work cost **6 generations** (estimate 8).
Each returned nine PNGs: the conditioning pose plus eight animation frames.
The review source contains five direction tags (D, DR, R, UR, U), five frames
each; the runtime-layout PNG includes all eight directions, five frames each.
The exact approved front image is retained at D frame 0. Every runtime pixel
uses binary alpha and the same eight colors as the approved design. The
3920x65 sheet round-trips through Aseprite without any pixel differences.

`all-directions-review.png` shows all 40 runtime frames; `*-run.gif` previews
each direction. `review.json` records sizes, palette, source frame selection,
occupied bounds, attack-frame index and hashes.

The actual game's `battlecensus` renderer loaded the new PNG in an isolated
staging folder and simulated 12 seconds through both combat phases. It matched
the original sheet's gameplay log exactly: zero hits, peak 75 bullets,
zero frames at the bullet cap, and the same movement and projectile metrics.
Screenshots and logs: `build_tmp/roperite_run_review/after/`; the baseline is
under `before/`. This validates sheet compatibility and preserves the existing
attack timing; it does not approve the new artwork or certify that every
generated pose visually aligns with the existing projectile origin points.

## Approved and installed (2026-10-18)

The user approved the animation and requested installation. The game now
loads `assets/enemies/redraws/61_roperite.png`, with its matching Aseprite
source, and enemy 61 is marked done. The saved review file contains an extra
duplicate of front frame 1; its drawings otherwise match the reviewed PNG
exactly. `tools/roperite_install.py` preserves that saved file and removes
only the duplicate in the installed copy, keeping all five directions at
five frames and retaining attack timing. The installation manifest records
both source and installed hashes, the normalization, and preserved original
asset hashes.

`build.bat all battlecensus` completed successfully. Both binaries reference
the installed path. A fresh 12-second battle check from the project root
matched the staged and original gameplay metrics exactly; screenshots and
logs are under `build_tmp/roperite_run_review/installed/`. The installed
Aseprite exports pixel-for-pixel to its PNG. No paid calls during installation.
