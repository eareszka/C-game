CXX = g++
CXXFLAGS = -w -std=c++17 -Iinclude -MMD -MP
SDL_FLAGS = $(shell pkg-config --cflags --libs sdl2 SDL2_image)

# MinGW's linker appends .exe, so the target name has to match or make will
# relink every time and `make run` won't find the binary it just built. Ask the
# compiler what it targets rather than trusting $(OS), which isn't exported into
# every shell that can run this makefile.
ifneq (,$(findstring mingw,$(shell $(CXX) -dumpmachine)))
    EXE = .exe
endif

# Without pkg-config the SDL flags come back empty and the link fails with a
# wall of undefined SDL_* references. Fail early with something actionable.
ifeq ($(strip $(SDL_FLAGS)),)
ifneq ($(MAKECMDGOALS),clean)
$(error pkg-config found no SDL2 flags. On Windows, build from an MSYS2 MINGW64 shell or use build.bat, which enters one for you)
endif
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
