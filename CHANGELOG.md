# Changelog

## 0.1.0-beta (unreleased)

The first build for testers: the starting island, Bloom, the mainland, and the first three bosses.

- Losing a fight wakes you at home with full health and poison cured. Before this, you were left at 0 HP.
- **One desert, one snow country, one wasteland.** They used to be scattered as five to nine patches each, and the wasteland could be almost missing from a world. Now each is a single region about four minutes' walk across: the desert nearer home on the ocean side, the snow and the wasteland farther out toward the mountains. Forest and meadow are unchanged.
- Saves now name the world they were played in. A save from before this change will not continue (CONTINUE is greyed with a note); NEW GAME replaces it.
- Only finished enemies appear in dungeons (`include/ready.h`). Boss sites without a finished boss say "NOT YET".
- On the map, enemies without their own small sprite are drawn as a shrunk battle sprite instead of a red square.
- Skvader, Wolpertinger and Treesqueak now fire from their heads and mouths, not their middles.
- Olgoi-Khorkhoi (boss 23) now has 1200 HP, up from 165.
- The test keys (T to win a battle, T to skip an hour, F1) only work in `--debug`.
- The game finds its assets and save file next to `game.exe`, however it is launched.
- The title screen shows the version, a note that beta saves may be wiped, and where to report bugs.
- `dist.bat` builds a zip that runs on a PC without MSYS2.
- **Nothing grows back.** Trees, rocks, gravestones, oilblooms, cave ore veins and every dungeon enemy you beat stay gone, across saves. In a pack fight, each enemy you beat stays dead even if you lose to a later one.
- Each starter dungeon now holds at least two Treesqueaks, so the raft's Vine can always be found. The great bat drops all 6 Wing Skin for the sail.
- The raft is worn like the boots: crafting it puts it on, and ITEMS can take it off (not while you're on water).
- Skvader now has 180 HP (was 240) and Treesqueak 240 (was 320).
- The save format is now version 18. Older saves still load: a raft you own starts worn, and nothing counts as destroyed.
- **Sound.** A small built-in mixer (no SDL_mixer, no new DLLs) plays effects the game synthesizes at start-up: shots, hits, grazes, being hit, an enemy's phase change, weapon swaps, victory and its pickups, defeat, the wipe into a fight, the menus and title, the speech box typing, swinging at and breaking things, chests, level-ups and stairs. Any clip can be replaced by a WAV of the same name in `assets/sound/` (`shot.wav`, `enemy_hit.wav`, ...); `make sfxdump` writes them all out to listen to.
- OPTIONS on the title screen has MASTER and SOUND volumes, 0-10. They and fullscreen are kept in `settings.txt` beside `game.exe`.
