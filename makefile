CXX = g++
CXXFLAGS = -w -std=c++17 -Iinclude -MMD -MP
SDL_FLAGS = $(shell pkg-config --cflags --libs sdl2 SDL2_image)

SRC = $(wildcard src/*.cpp)
OBJ = $(SRC:.cpp=.o)
DEP = $(OBJ:.o=.d)

TARGET = game

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(OBJ) -o $(TARGET) $(SDL_FLAGS) -lm -lpthread

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

-include $(DEP)

run: game
	./game

tile_editor: tools/tile_editor.cpp
	$(CXX) -std=c++17 -O2 tools/tile_editor.cpp -o tile_editor $(SDL_FLAGS)

clean:
	rm -f src/*.o $(TARGET) tile_editor
