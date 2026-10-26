# White-blade origins, 2026-10-19

User clarified: change the short returning pink bars.

Replaced approximate polar origins with native pixel measurements of both
white tips on all 12 idle and 12 spinning frames. Idle left blade is shorter
than the spinning blade; origins now follow actual head lean/heave and bob,
plus the spinning sheet's pixel rounding. Bars release from on_idle_frame so
fire-before-frame-callback order cannot emit from a stale blade position.
The release waits up to one 170 ms animation frame for the matching displayed
frame; the interval setting and returning-bar behavior remain unchanged.

Build: make all battlecensus passed with workspace TMP/TEMP/TMPDIR.
check.cpp captured all 48 actual launch origins through the public callback;
Python checked each against white bone pixels in the installed PNGs. Callback
capacity zero/one/two and no duplicate releases passed. Confirmed long laser
implementation and all source outside this class/comment unchanged.

60 s census seeds 1?5: 8 hits each, peak 79/1024, tightest -1.0 px;
focus-speed seed 1: 3 hits, peak 75/1024, tightest -0.5 px.
Every run: zero frames at cap, zero spawns within 40 px.
Previous default: 9 hits, 73 peak; previous focus: 8 hits, 80 peak.
These differences follow corrected origins and frame-aligned launches.

Debug handoff: F3, search OLGOI, Enter. Check short bars leaving each white
blade at the instant of launch, in both standing and spinning phases.
