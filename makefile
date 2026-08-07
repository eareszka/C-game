CXX = g++
CXXFLAGS = -w -std=c++17 -Iinclude -MMD -MP
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

.PHONY: all run clean tile_editor

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

clean:
	rm -f src/*.o src/*.d $(TARGET) tile_editor$(EXE)

endif
