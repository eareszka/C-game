@echo off
REM Build a zip a player can run: game.exe, the DLLs it needs, assets/ and the
REM README, in dist\. Runs tools/package.sh inside MSYS2 MINGW64, as build.bat does.

set "MSYS2_BASH=C:\msys64\usr\bin\bash.exe"

if not exist "%MSYS2_BASH%" (
    echo ERROR: MSYS2 not found at C:\msys64 - see BUILD_WINDOWS.md
    pause
    exit /b 1
)

cd /d "%~dp0"

set "MSYSTEM=MINGW64"
set "CHERE_INVOKING=1"
"%MSYS2_BASH%" -lc "sh tools/package.sh"
