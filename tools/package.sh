#!/bin/sh
# Package a playable build into dist/: game.exe, every MinGW DLL it loads
# (followed through SDL2_image's image libraries), assets/ without the
# Aseprite sources, the README and the changelog -- then a zip of it all.
# Run from MSYS2 MINGW64 at the repo root; dist.bat does that.
set -e

VERSION=$(sed -n 's/^#define GAME_VERSION "\(.*\)"/\1/p' include/version.h)
NAME="FourCastleChronicles-$VERSION"
OUT="dist/$NAME"

make

rm -rf "$OUT" "dist/$NAME.zip"
mkdir -p "$OUT"
cp game.exe "$OUT/"

# Every DLL under /mingw64 that game.exe needs, directly or through another.
# ldd already walks the whole tree; SDL2_image is linked at build time, so its
# png/jpeg/webp/... libraries show up here too.
ldd game.exe | awk '$3 ~ /^\/mingw64\// { print $3 }' | sort -u | while read -r dll; do
    cp "$dll" "$OUT/"
done

# The game reads only from assets/; the .aseprite sources stay home.
mkdir -p "$OUT/assets"
(cd assets && find . -type f ! -name '*.aseprite' -print) | while read -r f; do
    mkdir -p "$OUT/assets/$(dirname "$f")"
    cp "assets/$f" "$OUT/assets/$f"
done

cp packaging/README.txt "$OUT/README.txt"
cp CHANGELOG.md "$OUT/CHANGELOG.md"

# MSYS2 has no zip by default; Windows PowerShell does.
powershell.exe -NoProfile -Command "Compress-Archive -Path '$OUT' -DestinationPath 'dist/$NAME.zip' -Force"

echo "packaged: dist/$NAME.zip"
ls "$OUT"/*.dll | sed 's|.*/|  |'
