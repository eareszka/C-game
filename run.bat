@echo off
REM Launch the game on Windows.
REM game.exe is linked against the MSYS2 MinGW64 SDL2 DLLs, so those must be on
REM PATH. Assets are loaded relative to the working directory, so cd here first.

set "MINGW_BIN=C:\msys64\mingw64\bin"

if not exist "%MINGW_BIN%\SDL2.dll" (
    echo ERROR: SDL2.dll not found in %MINGW_BIN%
    echo Install it from an MSYS2 MINGW64 shell with:
    echo     pacman -S mingw-w64-x86_64-SDL2 mingw-w64-x86_64-SDL2_image
    pause
    exit /b 1
)

cd /d "%~dp0"

if not exist "game.exe" (
    echo ERROR: game.exe not found. Build it first - see BUILD_WINDOWS.md
    pause
    exit /b 1
)

REM Call by explicit path: some environments set NoDefaultCurrentDirectoryInExePath,
REM which stops cmd from resolving "game.exe" out of the current directory.
set "PATH=%MINGW_BIN%;%PATH%"
"%~dp0game.exe" %*
