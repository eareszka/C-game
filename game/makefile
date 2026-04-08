CXX = g++
CXXFLAGS = -Wall -Wextra -std=c++17 -Iinclude
SDL_FLAGS = $(shell pkg-config --cflags --libs sdl2 SDL2_image)

SRC = $(wildcard src/*.cpp)
OBJ = $(SRC:.cpp=.o)

TARGET = game

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(OBJ) -o $(TARGET) $(SDL_FLAGS) -lm

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

run: game
	./game

clean:
	rm -f src/*.o $(TARGET)
