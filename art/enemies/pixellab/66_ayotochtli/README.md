# 66 Ayotochtli

First-frame design generated 2026-10-18 through PixelLab CLI 0.7.0, using
the native 48x35 original and approved style board. The dry run estimated
30 generations on `edit-images-v2`; the API reported 10. `result.json` and
the provider manifest identify the raw output, which is preserved separately.

`frame0_review.png` and `66_ayotochtli_frame0_review.aseprite` contain the
cleaned design. The local palette pass merged three redundant shades to
meet eight colors plus black and shifted the image by (1,4) pixels to match
the original horizontal center and ground line without resampling.
`review.json` records these changes and confirms original asset hashes.
The user approved this first-frame design and requested rolling plus all
battle frames. Its Aseprite pixels were checked against the generation input.

## Battle frames

Native size remains 48x35. The game uses three standing frames, playback
0/1/0/2 with durations 400/250/400/250 ms, and four rolling frames at 70 ms.
Standing frame 1 is the defensive hunch and shell-plate attack hook. The
curled rolling pose and genuine end-over-end tumbling are separate from
the standing/hunching animation. Existing behavior and timing are retained.

`tools/ayotochtli_battle.py` runs staged jobs, each with a separate output
workspace and ledger under `pixellab-out/66-ayotochtli-battle/`. It dry-runs
each call, bounds its estimate, saves results, reuses collected jobs and
refuses unresolved ledger entries. Up to three independent jobs run at once.

```powershell
python tools/ayotochtli_battle.py poses --generate
python tools/ayotochtli_battle.py cycles --generate
python tools/ayotochtli_battle.py rolls --generate
python tools/ayotochtli_battle.py pack
```

Omit `--generate` for dry runs. Animation calls request four frames, which
may return a conditioning image plus four generated frames. The packer
selects three stand/hunch poses and four rolling poses, preserves the exact
approved front resting frame, and supplies the left directions by mirroring.
All outputs use the same nine-color approved palette. Raw generations remain
unchanged. It writes separate tagged standing and rolling Aseprite review
sources, runtime-layout PNGs, per-direction GIFs and overview boards under
`battle/`. Visual review remains necessary after numeric validation.

The total additional API estimate is 17 generations: two rotations at 3,
one curled-pose edit at 1, and ten animation requests at 1 each.

The simple-edit endpoint enforces two constraints absent from the CLI's
initial dry-run validation: descriptions at most 500 characters and image
dimensions divisible by four. Its first two rejected attempts are preserved
in the `roll-pose` and `roll-pose-v2` ledgers; the corrected `roll-pose-v3`
uses one extra transparent row (48x36), then restores the 48x35 canvas with
no resampling or opaque-pixel loss. Future simple edits validate both limits
locally before submission.

Some standing rotations nearly fill the native height. For these, animation
inputs receive four transparent rows above and below (48x43); the packer
restores the native ground line and rejects any returned subject taller than
35 pixels instead of clipping it. The approved direction inputs stay at
48x35. Optional `idles` and `rollviews` stages allow independent standing
cycles and ball rotations to run concurrently; saved results are reused.
`--workers 1`, `2` or `3` controls a stage's independent jobs.

Standing Aseprite frame durations are 400/250/250 ms for the three stored
poses; the GIF previews reproduce the actual game's four-beat 0/1/0/2 loop.
Rolling previews use the game's four frames at 70 ms.

## Completed animation review

All five unique standing/hunching cycles and five rolling cycles are complete;
the three left directions mirror their matching right views. Runtime-layout
PNGs are `battle/66_ayotochtli_idle.png` (1152x35, three frames per direction)
and `battle/66_ayotochtli_roll.png` (1536x35, four frames per direction).
Matching tagged Aseprite sources were opened together for user review. All
frames are 48x35, use the same nine-color approved palette and binary alpha,
and round-trip through Aseprite with no pixel differences. The exact approved
front resting frame is preserved. Overview boards and per-direction GIFs are
alongside the sources; GIF timing matches the real engine playback.

The staged game renderer simulated 12 seconds through both combat phases and
matched the original gameplay log exactly: zero hits, peak 76 bullets, zero
frames at cap, same movement and projectile metrics. Five screenshots and
logs are under `build_tmp/ayotochtli_battle_review/after/`, with the baseline
under `before/`. Original game assets remain unchanged; animation approval
and installation are pending, so 66 is not yet marked DONE in the tracker.

Additional animation cost: **13 generations**, confirmed by the balance
decreasing from 1969 to **1956** (estimate 17). The two simple-edit validation
rejections did not add a charge. Three jobs lost network access during
polling and were recovered by their existing job IDs using the `recover`
stage, with no replacement generations. The final rear roll had failed DNS
resolution before submission; the `last-roll` stage submitted that one job.
Recovery records and collection manifests are preserved. Failed ledger rows
contain CLI estimates; the provider manifests and balance establish actual
cost. The first-frame design separately cost 10 generations.

## Visible tracker

After the finished animations are reviewed, approved and installed, run:

```powershell
python tools/enemy_redraw_sheet.py --complete 66
```

This updates the art status and visible `enemy_rating.png` together. Drafts
are not marked DONE. Sprite status is separate from `include/ready.h`.

## Installed for testing (2026-10-18)

The user requested adding the reviewed animations to the game for testing.
`src/battle.cpp` now loads the standing and rolling PNGs from
`assets/enemies/redraws/`, with matching Aseprite sources. The installation
used `python tools/ayotochtli_install.py`, which validates the reviewed
hashes and exports, preserves all original assets, records the installation
and immediately refreshes the visible tracker. Enemy 66 is marked DONE.

Game and battle-checker builds passed. A 12-second battle check using the
installed paths matched the original and staged logs exactly. Both binaries
contain the new asset paths; exports and preserved original hashes were
verified. Logs and five screenshots are in
`build_tmp/ayotochtli_battle_review/installed/`. No paid calls were used.

To test interactively, launch `run.bat`, press F3, type `AYOTOCHTLI`, and
press Enter. Search by name; the list's number is a tier-sorted rank, not
the enemy ID.
