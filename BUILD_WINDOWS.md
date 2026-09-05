# Building on Windows

The project is C++17 + SDL2 and was developed on Linux/WSL2. It builds on Windows
essentially unchanged using the **MSYS2 MINGW64** toolchain, which supplies the
`g++`, `make`, `pkg-config` and SDL2 packages the existing `makefile` expects.

## One-time setup

1. Install [MSYS2](https://www.msys2.org/) to the default location (`C:\msys64`).
2. Open the **MSYS2 MINGW64** shell (not "MSYS", not "UCRT64") and install the
   toolchain and libraries:

   ```sh
   pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-pkgconf \
                      mingw-w64-x86_64-SDL2 mingw-w64-x86_64-SDL2_image make
   ```

## Build and run

`make` works from any shell -- cmd, PowerShell, Git Bash, or an MSYS2 MINGW64
shell:

```bat
make                 :: builds game.exe
make run             :: builds and launches
make tile_editor     :: builds the tile editor
make clean           :: removes objects and binaries
```

Outside MINGW64 there is no `pkg-config` on `PATH`, and the `clean` and `run`
recipes want `rm` and `./game.exe`, so a native build there would link with no
SDL2 libraries at all. The makefile detects that case and re-enters MSYS2's
MINGW64 environment to run the real build, staying in the current directory.
Nothing has to be on `PATH` for that but `make` itself -- no PowerShell profile
function, no wrapper.

### Batch-file wrappers

`build.bat` and `run.bat` do the same job without needing `make` on `PATH`:

```bat
build.bat             :: builds game.exe
build.bat tile_editor :: builds the tile editor
build.bat clean       :: removes objects and binaries
run.bat               :: runs the game
```

## Notes and gotchas

- **DLLs must be on `PATH`.** `game.exe` links against the MinGW SDL2 DLLs in
  `C:\msys64\mingw64\bin`. Double-clicking `game.exe` in Explorer fails with a
  missing-`SDL2.dll` error. `run.bat` prepends that directory to `PATH`, so use it
  (or run from a MINGW64 shell, where it is already on `PATH`).

  To make the game redistributable instead, copy the DLLs it needs next to the
  exe. From a MINGW64 shell:

  ```sh
  ldd game.exe | grep mingw64 | awk '{print $3}' | xargs -I{} cp {} .
  ```

- **Assets are loaded by relative path** (e.g. `assets/Sprite-0001.png`), so the
  game must be launched with the project root as the working directory.
  `run.bat` handles this.

- **`-mwindows` hides the console.** `pkg-config --libs sdl2` adds `-mwindows`,
  so `printf` diagnostics go nowhere when launched from Explorer. Launch from a
  terminal via `run.bat` to see them, or link with `-mconsole` while debugging.

- **`SCHED_IDLE` is Linux-only.** The background map-generation thread in
  `src/tilemap.cpp` lowers its own priority. That call is now `#ifdef`-guarded and
  uses `SetThreadPriority(..., THREAD_PRIORITY_LOWEST)` on Windows.

- **Stale Linux build artifacts.** `.o`/`.d` files and the `game_asan`, `game_dbg`,
  `tile_editor` ELF binaries were committed to the repo before `.gitignore` was
  added. They are ELF, not PE, and the `.d` files reference `/usr/include/SDL2/...`,
  which makes `make` fail with "No rule to make target". Delete them before the
  first Windows build:

  ```sh
  rm -f src/*.o src/*.d game_asan game_dbg tile_editor tools/tile_editor
  ```
