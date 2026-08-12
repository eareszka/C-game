#!/usr/bin/env bash
# Render one window of mountains per seed and measure it, so "does it look like
# this on every seed" is answered with numbers rather than with a shrug.
#
# The art is the same on every seed — it is baked into the sheet — so what is
# actually in question is the shape the mask comes out, and whether the band
# drawn on it keeps its thickness. Run from the repo root inside MINGW64.
#
# Rendering only: MINGW64, which is the shell that has the SDL DLLs on PATH,
# does not have python on it. Measure the output afterwards from a shell that
# does — `for f in sweep_*.png; do python tools/band_width.py $f half; done`.
set -u
seeds="$*"
: "${seeds:=407 463 387 398 99 5150 1234 7 20260812 555}"
for s in $seeds; do
  if ./shot.exe "$s" "sweep_$s.png" >/dev/null 2>&1; then
    echo "seed $s: rendered"
  else
    echo "seed $s: FAILED"
  fi
done
