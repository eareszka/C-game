CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -Iinclude
SDL_FLAGS = $(shell pkg-config --cflags --libs sdl2 SDL2_image)

SRC = $(wildcard src/*.c)
OBJ = $(SRC:.c=.o)

TARGET = game

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(OBJ) -o $(TARGET) $(SDL_FLAGS) -lm

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

run: game
	./game

clean:
	rm -f src/*.o $(TARGET)
