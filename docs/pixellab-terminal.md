# PixelLab terminal enemy workflow

Visible tracker: after every approved sprite fix is installed, run
`python tools/enemy_redraw_sheet.py --complete ID`. This marks the art status
DONE and regenerates `enemy_rating.png` in one command. Keep the gameplay
ready gate separate. When the old external Bible checker is unavailable,
the chart labels its basic primary-sheet checks LOCAL (palette, alpha,
layout), rather than claiming full style compliance. Roperite's tracker
entry was refreshed; Ayotochtli's new draft is awaiting its animation review.

Ayotochtli's animations were subsequently reviewed and installed for testing
at the user's request. Both battle sheets now load from `assets/enemies/redraws/`;
enemy 66 is marked DONE and the visible tracker was refreshed automatically
by `tools/ayotochtli_install.py`. Installed battle-render checks and builds passed.

Installed 2026-10-18 with `uv tool install pixellab-cli`: community CLI
version **0.7.0**, Python 3.12. Verify with `pixellab-cli --version` and
`pixellab-cli --help`. Upstream: https://github.com/protonspy/pixellab-cli.
The local CLI calls the hosted PixelLab API; generation needs internet and
account credits. Only PixelLab is needed; do not configure fal or run setup.

Run these commands from the repository root in PowerShell. Keep all work in
the terminal; use Aseprite batch mode for exports/conversion, without a GUI.
Existing art direction and approval rules remain applicable. The user explicitly
requested opening the completed Roperite generation in Aseprite for review;
that review launch is authorized as an exception to terminal-only work.

## Credential and balance

In your own terminal, run `pixellab-cli config set pixellab-secret` and enter
the PixelLab bearer token at its hidden prompt. Never pass `--value`, paste a
token into chat, or put it in a script. The default credential file is
`~/.pixellab.json`, outside the repository and command history. This command
sets only the PixelLab credential. `pixellab-cli config show` reports sources
without displaying values. Do not create a repository credential file.

```powershell
pixellab-cli config show
powershell -NoProfile -ExecutionPolicy Bypass -File tools/roperite_pixellab.ps1 -Action Balance
```

## Roperite first frame

Roperite remains unfinished in `art/enemies/redraw_status.json`. Start with
one first frame only. Source extraction uses Aseprite's native canvas,
98x65 (the generator script's old 96x64 constant is not the runtime size):

```powershell
& 'C:\Program Files\Aseprite\Aseprite.exe' -b --frame-range 0,0 assets/enemies/61_roperite.aseprite --save-as art/enemies/pixellab/61_roperite/source_frame0.png
powershell -NoProfile -ExecutionPolicy Bypass -File tools/roperite_pixellab.ps1
```

Default action is **DryRun**. It saves `dry-run.json` with the complete
serialized request and prints its route and estimate. Source and style board
are embedded in the request, with the prompt from `prompt.txt`. The approved
board is `art/direction/approved_enemy_study/approved_42_fronts_native_512.png`;
the companion `STYLE_BRIEF.md` supplies the drawing rules, with its old RO
task-specific exceptions excluded. Input hashes are recorded in `inputs.json`.
First-frame occupied bounds are `(35,14)-(63,64)`, exclusive coordinates.

Verified route: `edit-images-v2`, `edit_with_reference`, output 98x65,
transparent background, **estimated 30 generations**. A sprite request using
`--from` and `--style` fails validation because that route requires the style
image to match the output size; do not rescale the approved native board to
force it through. Estimate is not a balance or a final charge.

After reviewing the saved dry run and explicitly approving this paid call:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/roperite_pixellab.ps1 -Action Generate
```

Generate is the only action that supplies `--yes`; the script disables
environment auto-consent. Drafts, manifests and ledger go to
`pixellab-out/61-roperite-drafts`, separately from installed assets. If a paid
job times out, collect the existing job rather than generate again:

```powershell
pixellab-cli --workspace pixellab-out/61-roperite-drafts --subject 61-roperite job show JOB_ID --kind sprites --name 61-roperite-frame0-draft
```

## Local checks and cleanup

Replace `DRAFT.png` and `CLEAN.png` with actual separate draft paths:

```powershell
python tools/roperite_review.py DRAFT.png
python tools/roperite_review.py DRAFT.png --clean-to CLEAN.png
python tools/roperite_review.py CLEAN.png
& 'C:\Program Files\Aseprite\Aseprite.exe' -b CLEAN.png --save-as REVIEW.aseprite
```

Cleanup maps opaque RGB values to the exact project palette, preserving
transparency and the raw draft. Unexpected size or partial alpha requires
review before cleanup. Validation reports dimensions, bounds, transparency,
palette membership, color budget, black-pixel count and original input hashes.
Outlines, shading, anatomy and style compliance require visual review; these
metrics cannot approve a design. Do not overwrite originals, mark 61 done,
animate it or install it in the game until design approval.

## Verification status

CLI version/help and local dry run verified. Both embedded reference PNGs
were checked against their input bytes. The installed edit command returns
from its dry-run branch before constructing an API client; an additional
offline run with HTTP disabled confirms this request sends no paid call.
Source extraction matches the runtime first frame pixel for pixel.
The original frame has 10 opaque colors (all on palette), so it correctly
fails the proposed nine-color draft budget. No original colors were changed.
Authentication verified 2026-10-18 with a read-only balance query: 1,995 of
2,000 generations remaining, $0 USD credits. Only the PixelLab credential is
configured, in the home file outside Git. The sandbox blocked the initial
network connection; the approved network-enabled retry succeeded.

## Roperite generation and review (2026-10-18)

User approved the estimated 30-generation request and requested opening it in
Aseprite. One request completed through `edit-images-v2`; the API reported
**10 generations**, verified by the balance decreasing from 1,995 to 1,985.
Job ID: `9da2b202-ffa6-419a-8462-21e3aa114b2b`.
Raw draft and provider manifest remain under
`pixellab-out/61-roperite-drafts/61-roperite/sprites/v1/`.

Local cleanup saved `art/enemies/pixellab/61_roperite/61_roperite_frame0_clean.png`
and batch conversion created `61_roperite_frame0_review.aseprite` in the same
directory, opened in the Aseprite GUI at the user's request. The raw draft had
428 off-palette pixels; the separate cleaned copy has zero, eight opaque
colors, binary transparency, the exact 98x65 canvas and original occupied
bounds `(35,14)-(63,64)`. `review.json` records these checks and confirms all
original input hashes remain unchanged. Palette mapping does not certify
outline/shading quality or design approval. Enemy 61 remains unfinished and
uninstalled pending user review; no animations generated.

The user subsequently approved the first-frame design and requested battle
running animations. All eight directions are now prepared as a separate
review draft, with five distinct cycles plus mirrored left views. See
`art/enemies/pixellab/61_roperite/running/README.md` for the generation records,
repeatable commands, artifacts and staged battle-render verification. The
new work reported 6 generations total. Installed game assets remain unchanged.

The user then approved the animation and requested installation. Enemy 61 is
now marked done and loaded from `assets/enemies/redraws/61_roperite.png`.
Original assets and the saved review are preserved. The installed copy omits
one duplicate front frame found in the saved review, retaining five frames
in every direction. Game build and installed battle-render verification passed;
see the running README for details. Installation used no paid generation.
