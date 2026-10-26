# Alber validation, 2026-10-19

Changed only Alber gameplay in src/enemies.cpp. Existing workspace changes preserved.

Both baseline and final `make all battlecensus` passed with MSYS paths and workspace TMPDIR.
60-second seeds 1?5:

| Run | Hits | Peak / 1024 | Cap frames | Spawns <40 px | Tightest pass |
| --- | --- | --- | --- | --- | --- |
| Baseline default bot | 0 each | 51?58 | 0 | 0 | 10.2?18.3 px |
| Final default bot | 0 each | 79 | 0 | 0 | 7.9 px |
| Final 70 px/s bot | 0 each | 91 | 0 | 0 | 1.5 px |

Final pattern has no RNG: identical results across seeds are expected.
Both phases have zero hits for both dodge bots. Stationary control at (320,400):
59 hit events before 30 s, 79 after (census events, not independent human damage).
Stationary hits are primarily aimed 210 px/s fans, plus sweeps and phase-2 embers.
No point-blank spawns in these runs. Existing engine guard suppresses ring shedding
within 40 px of the player. This does not prove safety for every player position.

check.cpp passed: output bounds including zero capacity, continuous motion at half HP,
explicit mouth origins, 5 damage, two configured eight-shot sheds 0.8 s apart.
Direct simulation: phase 1 551 shots / 30 s, phase 2 722 / 30 s, 13 embers.
Phase-2 glide expands continuously over one second to avoid a position jump.
Rendered transition/phase-2 trace and stationary-hit PNGs saved in after/.

Human handoff: game.exe --debug, F3, type ALBER, Enter. Play both halves.
After the human playtest, run python tools/playtest_report.py if trial telemetry
was recorded. BOSS1 comparison and ELITE assessment remain pending human results.
No tiers, HP/gear, shared helpers, engine, ready.h, or commits changed.
