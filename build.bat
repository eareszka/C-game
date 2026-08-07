@echo off
REM Build the game on Windows by shelling into the MSYS2 MINGW64 environment,
REM which provides g++, make, pkg-config and the SDL2 libraries the makefile wants.
REM Pass any make target through, e.g. `build.bat clean` or `build.bat tile_editor`.

set "MSYS2_BASH=C:\msys64\usr\bin\bash.exe"

if not exist "%MSYS2_BASH%" (
    echo ERROR: MSYS2 not found at C:\msys64
    echo Install it from https://www.msys2.org/ then run, in a MINGW64 shell:
    echo     pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-pkgconf mingw-w64-x86_64-SDL2 mingw-w64-x86_64-SDL2_image make
    pause
    exit /b 1
)

cd /d "%~dp0"

set "MSYSTEM=MINGW64"
set "CHERE_INVOKING=1"
"%MSYS2_BASH%" -lc "make %*"
