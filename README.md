# Four Castle Chronicles

A top-down 2D RPG written from scratch in C++17 and SDL2. You explore a procedurally
generated world, clear dungeons, fight bullet-pattern battles, craft gear and build a
raft to leave the starting island. The world is seeded, so the same seed always builds
the same world.

<!-- Add a gameplay screenshot or GIF here, e.g. docs/screenshots/overworld.png -->

**Status:** `0.1.0-beta`. The beta covers the starting island, the town of Bloom, the
mainland and the first three bosses. There's no music or sound yet. See
[CHANGELOG.md](CHANGELOG.md).

## Features

- **Seeded world generation.** A 9-million-tile overworld is built in about two dozen
  passes, with coasts, cliffs, towns and dungeon sites, and comes out identical for a
  given seed on every machine.
- **Dungeons.** Generated cave systems in several archetypes, with difficulty tiers and
  stairs bound to the overworld.
- **Battles.** Real-time bullet-pattern fights against a roster of enemies and bosses,
  with switchable weapons and loot drops.
- **Crafting.** Recipe books from the book shop, resources from trees, rocks and ore
  veins, and a raft that's worn like boots.
- **A living town.** NPCs (courier, gardener, fisher, sailor, woodcutter, residents)
  follow daily routines on a world clock.
- **Permanent consequences.** Nothing grows back: trees you cut and enemies you beat
  stay gone across saves.
- **Versioned saves.** The save format is on version 18, and older saves still load.

## Building

### Linux

```sh
sudo apt install g++ make pkg-config libsdl2-dev libsdl2-image-dev
make            # builds ./game
make run        # builds and launches
```

### Windows

Builds with the MSYS2 MINGW64 toolchain. Once it's installed, `make` works from cmd,
PowerShell or Git Bash. The makefile re-enters MINGW64 by itself. Full setup and
gotchas are in [BUILD_WINDOWS.md](BUILD_WINDOWS.md).

```bat
make            :: builds game.exe
run.bat         :: runs it with the SDL2 DLLs on PATH
dist.bat        :: packages a zip that runs on a PC without MSYS2
```

## Running

```sh
./game              # normal play: title screen, saving
./game <seed>       # play a specific world seed
./game --debug      # test mode: starts in the spawn house, enables debug keys
```

Assets and `save.dat` are resolved next to the executable, however it's launched.

## Controls

| Key | Action |
|---|---|
| Arrows / WASD | Move |
| Shift | Sprint |
| Ctrl | Crouch |
| Z / Enter / Space | Confirm, talk, open; hold to shoot in battle |
| X | Back |
| Q / E | Switch weapon |
| Tab | Menu (items, crafting, save) |
| M | Map |
| Mouse wheel | Zoom |
| F11 | Fullscreen |
| Hold Esc 3 s | Quit |

## Headless tools

The game's own objects also link into about 20 console tools that run without a
window. They check the game's rules across many seeds. Build any of them with
`make <name>` and run from the repo root.

| Tool | What it checks |
|---|---|
| `dngportals` | Every dungeon's stairs connect correctly to the overworld. Exits non-zero on a broken invariant, so it can gate a build |
| `storycheck` | Story stages, which boss sites stand, and the compass lead on real worlds |
| `killcheck` | Beaten spawners, broken ore veins and felled trees stay gone when the world is regenerated from its seed |
| `craftcheck` | Crafting recipes, loot caps, save migration from older formats, and menu rendering |
| `battlecensus` | Plays a fight headless with a dodge bot: hits taken, bullet peak vs. the cap, point-blank spawns |
| `spawncensus` | Dungeon difficulty quantiles and which enemies spawn where |
| `dngcensus` | Dungeon archetype distribution across many world seeds |
| `shot` / `dngshot` | Headless overworld and cave screenshots |

## Engineering notes

- **Optimizing deterministic worldgen.** Compiling with `-O2` cut world generation from
  24 s to 4 s. Every tile and overlay was hashed on four seeds before and after, to prove
  the world didn't change. `-ffast-math` and anything else that reorders float math is
  deliberately left off, because a world that differs between builds is a bug that only
  shows up on someone else's machine.
- **Save compatibility.** Each save carries a format version. Loading an older save
  migrates it forward instead of discarding it.
- **Debug hooks stay out of the shipped game.** Tracing builds such as `coastprobe` and
  `sheetcensus` compile a separate copy of the objects, so the release binary never
  carries the hooks.

## Project layout

```
src/        game source (.cpp)
include/    headers
assets/     tilesets, sprites, fonts loaded at runtime
tools/      headless check tools (C++) and art/asset scripts (Python, Lua)
art/        sprite sources and art direction
docs/       design notes (NPC routines, dialogue cases)
packaging/  tester README bundled with beta builds
```

Sprites are made in Aseprite. Some sprite drafts were generated with PixelLab and then
cleaned up by hand. The Python and Lua scripts in `tools/` handle that pipeline.
