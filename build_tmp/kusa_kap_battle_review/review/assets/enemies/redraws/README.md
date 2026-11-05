# Installed enemy redraws

`src/battle.cpp` loads these eight reviewed first poses: 17 Qiqirn,
41 Sasnalkahi, 49 Physeter, 51 Aspidochelone, 64 Dungavenhooter,
76 Loch Oich Monster, 77 Hoga, and 97 RO.

61 Roperite is also installed with its approved running animation: five
unique direction cycles plus three mirrored left views, five 98x65 frames
per direction at the existing 260 ms, preserving the frame-2 attack hook.
Its PNG and Aseprite source are `61_roperite.png` and `61_roperite.aseprite`.
The saved review had one extra duplicate front frame; only the installed
copy omits it. Original assets and the saved review remain intact.

66 Ayotochtli is installed with all eight battle directions: three standing/
hunching frames in `66_ayotochtli.png`, and four curled-ball rolling frames
in `66_ayotochtli_roll.png`, with matching tagged Aseprite sources. Native
48x35 frames, the 0/1/0/2 standing loop, frame-1 attack hook and 70 ms rolling
frames are unchanged. The reviewed sources and original four assets are
preserved. Enemy 66 is DONE in the refreshed visible `enemy_rating.png`.

Aspidochelone uses the revision without water. RO is the only black enemy: charcoal hide, black
outline, red only on the eyes, mouth and wing veins (2026-10-18 redraw,
`tools/ro_install.py`; the earlier red-outline sheet is backed up). The originals in `assets/enemies/` and the reviewed drawing files
in `art/enemies/` are preserved. `installation.json` records hashes, source
paths, dimensions, layouts, frame counts, and the backup directory.

Only one pose has been drawn for each of the original eight enemies. The project's normal direction
fallback supplies the other sheet slots, mirroring left views, and its
one-pixel breathing method supplies three subtle states. Existing frame
counts are retained to preserve gameplay frame hooks and timing. Qiqirn's
movement sheet uses the new pose too; a distinct gallop cycle, directional
views, and attack poses are still future art work.

Those eight Aseprite sources are tagged with the drawn `D` view. The existing
`tools/enemy_sheet.py export` workflow reproduces every runtime PNG exactly.
The game build and three-second battle-render smoke checks for all eight
passed. Screenshots and logs are in `build_tmp/enemy_redraw_install_review/`.
No paid generation was used for installation.

Roperite's game build and 12-second installed battle-render check passed,
with gameplay metrics identical to its original and staged sheets. Logs and
five screenshots are in `build_tmp/roperite_run_review/installed/`. Its export
round trip is pixel-exact; enemy 61 is marked done. No paid calls were used
for this installation.

Ayotochtli's game and battle-checker builds passed. A 12-second installed
battle-render test matched the original/staged gameplay metrics exactly;
screenshots and logs are in `build_tmp/ayotochtli_battle_review/installed/`.
Both installed Aseprite sources export pixel-for-pixel to their PNGs.

32 Angont (2026-10-18) is a PixelLab front pose (job af594b04, 10 generations)
hand-mapped to the palette by `tools/angont_recolor.py gold`: gold-olive coils
with a tan belly band and a few blotches instead of the old scale lattice, and
its three poison skulls redrawn as shaded pale-green pixel skulls. Front only,
five frames, breathing below row 36; `tools/angont_install.py` installed it.
The original sheet in `assets/enemies/` is untouched.
