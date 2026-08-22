CXX = g++
# -O2 because the player waits for worldgen. It is two dozen passes over a
# nine-million-tile map, and unoptimised it took twenty-four seconds against
# four with this on -- the same world either way, verified by hashing every tile
# and overlay on four seeds before and after. No -ffast-math and nothing else
# that would let the compiler reassociate float arithmetic: worldgen is seeded
# and reproducible, and a world that differs between builds is a bug that only
# shows up on someone else's machine.
CXXFLAGS = -O2 -w -std=c++17 -Iinclude -MMD -MP
# Lazy on purpose: expanding this outside MSYS2 makes make print a CreateProcess
# warning, so the forwarding decision below is taken without touching it.
SDL_FLAGS = $(shell pkg-config --cflags --libs sdl2 SDL2_image)

# The SDL2 toolchain lives in MSYS2 MINGW64 and pkg-config is only on PATH
# inside it, so `make` from PowerShell, cmd or Git Bash used to link with no SDL
# libraries at all. Re-enter MINGW64 and run the real build there instead.
#
# HAVE_PKGCONF is the test for "already inside MINGW64": that POSIX path only
# resolves for MSYS2's own make. A Windows make reads it as C:\mingw64\... and
# finds nothing, which is exactly the answer we want from cmd or Git Bash.
MSYS2_BASH   := $(wildcard C:/msys64/usr/bin/bash.exe)
HAVE_PKGCONF := $(wildcard /mingw64/bin/pkg-config.exe)

ifneq ($(MSYS2_BASH),)
    ifeq ($(HAVE_PKGCONF),)
        ifneq ($(MSYS2_FORWARDED),1)
            FORWARD_TO_MSYS2 := 1
        endif
    endif
endif

ifeq ($(FORWARD_TO_MSYS2),1)

GOALS := $(if $(MAKECMDGOALS),$(MAKECMDGOALS),all)

.PHONY: $(GOALS) msys2-forward

# Every goal hangs off the single forwarding rule, so `make clean all` crosses
# into MSYS2 once rather than once per goal.
$(GOALS): msys2-forward
	@:

msys2-forward:
	@MSYSTEM=MINGW64 "$(MSYS2_BASH)" -lc \
		'cd "$(CURDIR)" && exec make MSYS2_FORWARDED=1 $(GOALS)'

else

ifeq ($(strip $(SDL_FLAGS)),)
ifneq ($(MAKECMDGOALS),clean)
$(error pkg-config found no SDL2 flags. From an MSYS2 MINGW64 shell: pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-pkgconf mingw-w64-x86_64-SDL2 mingw-w64-x86_64-SDL2_image make)
endif
endif

# MinGW's linker appends .exe, so the target name has to match or make will
# relink every time and `make run` won't find the binary it just built. Ask the
# compiler what it targets rather than trusting $(OS), which isn't exported into
# every shell that can run this makefile.
ifneq (,$(findstring mingw,$(shell $(CXX) -dumpmachine)))
    EXE = .exe
endif

SRC = $(wildcard src/*.cpp)
OBJ = $(SRC:.cpp=.o)
DEP = $(OBJ:.o=.d)

TARGET = game$(EXE)

.PHONY: all run clean tile_editor dngshot dngcensus shot

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(OBJ) -o $(TARGET) $(SDL_FLAGS) -lm -lpthread

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

-include $(DEP)

run: $(TARGET)
	./$(TARGET)

# Alias so `make tile_editor` still works when the real output is tile_editor.exe
tile_editor: tile_editor$(EXE)

tile_editor$(EXE): tools/tile_editor.cpp
	$(CXX) -std=c++17 -O2 tools/tile_editor.cpp -o $@ $(SDL_FLAGS)

# Shared recipe for the headless console tools -- they link the game's own
# objects minus its main() and run without a window. dungeon.h pulls in SDL.h,
# which #defines main to SDL_main unless SDL_MAIN_HANDLED is set first -- and
# pkg-config's own --cflags injects -Dmain=SDL_main independently of that, same
# gotcha documented in tools/genprof.cpp. -Umain cancels the latter;
# SDL_MAIN_HANDLED stops the former; stripping -lSDL2main/-mwindows keeps these
# plain console exes instead of windowed ones wanting a WinMain.
HEADLESS_OBJ  = $(filter-out src/main.o,$(OBJ))
HEADLESS_LIBS = $(shell pkg-config --libs sdl2 SDL2_image | sed 's/-lSDL2main//; s/-mwindows//')
HEADLESS_CXX  = $(CXX) -std=c++17 -O2 -Iinclude -w -DSDL_MAIN_HANDLED \
                $(shell pkg-config --cflags sdl2 SDL2_image) -Umain

# Headless cave-art preview tool.
dngshot: dngshot$(EXE)

dngshot$(EXE): tools/dngshot.cpp $(HEADLESS_OBJ)
	$(HEADLESS_CXX) tools/dngshot.cpp $(HEADLESS_OBJ) -o $@ $(HEADLESS_LIBS) -lm -lpthread

# Dungeon archetype census across many world seeds. Run it from the repo root --
# it reads assets/tileset.png by relative path.
dngcensus: dngcensus$(EXE)

dngcensus$(EXE): tools/dngcensus.cpp $(HEADLESS_OBJ)
	$(HEADLESS_CXX) tools/dngcensus.cpp $(HEADLESS_OBJ) -o $@ $(HEADLESS_LIBS) -lm -lpthread

# Headless overworld screenshot, and the whole-world mask views behind its
# SHOT_* environment switches.
shot: shot$(EXE)

shot$(EXE): tools/shot.cpp $(HEADLESS_OBJ)
	$(HEADLESS_CXX) tools/shot.cpp $(HEADLESS_OBJ) -o $@ $(HEADLESS_LIBS) -lm -lpthread

clean:
	rm -f src/*.o src/*.d $(TARGET) tile_editor$(EXE) dngshot$(EXE) dngcensus$(EXE) shot$(EXE)

endif
