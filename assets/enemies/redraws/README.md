# Installed enemy redraws

`src/battle.cpp` loads these eight reviewed first poses: 17 Qiqirn,
41 Sasnalkahi, 49 Physeter, 51 Aspidochelone, 64 Dungavenhooter,
76 Loch Oich Monster, 77 Hoga, and 97 RO.

Aspidochelone uses the revision without water. RO uses black skin and red
outlines. The originals in `assets/enemies/` and the reviewed drawing files
in `art/enemies/` are preserved. `installation.json` records hashes, source
paths, dimensions, layouts, frame counts, and the backup directory.

Only one pose has been drawn for each enemy. The project's normal direction
fallback supplies the other sheet slots, mirroring left views, and its
one-pixel breathing method supplies three subtle states. Existing frame
counts are retained to preserve gameplay frame hooks and timing. Qiqirn's
movement sheet uses the new pose too; a distinct gallop cycle, directional
views, and attack poses are still future art work.

The Aseprite sources are tagged with the drawn `D` view. The existing
`tools/enemy_sheet.py export` workflow reproduces every runtime PNG exactly.
The game build and three-second battle-render smoke checks for all eight
passed. Screenshots and logs are in `build_tmp/enemy_redraw_install_review/`.
No paid generation was used for installation.
