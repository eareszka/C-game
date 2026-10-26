# 67 Lagopus

Generated with PixelLab CLI 0.7.0. The user approved the first-frame design
in `67_lagopus_frame0_review.aseprite`. The cleaned source is
`idle_frame0_clean.png`; its native 62x45 canvas, bounds and nine-color
palette are recorded in `review.json`. Original assets and raw generations
remain separate. The first edit cost 10 generations (estimate 30).

The game uses three grounded poses, played 0/1/0/2 at
400/250/400/250 ms, and four flight frames at 110 ms. Grounded frame 1
and frame 2 retain their wing-up and wing-down attack cues. Animation
requests preserve the approved bird's broad wings, feathered feet, red
eye combs and black tail. All eight battle directions are exported;
the left views mirror their right counterparts.

```powershell
python tools/pixellab_enemy.py art/enemies/pixellab/67_lagopus/job.json rotate idle --generate
python tools/lagopus_battle.py prepare
python tools/lagopus_battle.py animate
python -u tools/lagopus_battle.py animate --generate
python tools/lagopus_battle.py pack
```

The `animate` command without `--generate` only validates and saves dry
runs. Eight independent animation calls each estimate one generation.
The shared direction rotation reported one generation (estimate three).
Saved results are reused; unresolved submitted jobs must be recovered
by their job IDs rather than submitted again. Raw responses and ledgers
are under `pixellab-out/67-lagopus/`.

Preparation and packing run through the terminal. Aseprite batch mode
handles conversion and verifies exact PNG round trips. The finished
review sources are opened in Aseprite for visual approval, following the
user's preference. Drafts are not installed or marked DONE before that
approval. Installation must also update `art/enemies/redraw_status.json`
and the visible `enemy_rating.png` with
`python tools/enemy_redraw_sheet.py --complete 67`.

## Animation review ready

`67_lagopus_idle_review.aseprite` contains three grounded poses per
direction; `67_lagopus_fly_review.aseprite` contains four airborne poses.
Both were opened together for user review. Their runtime-layout PNGs
are `idle_sheet.png` (1488x45) and `fly_sheet.png` (1984x45).
The labelled `*_all_directions.png` boards and `*_playback.gif` files
show all eight directions with the game's playback timing.

`animation_review.json` confirms binary alpha, the exact approved palette,
pixel-exact Aseprite export, preserved front resting frame and unchanged
original inputs. The rotation plus eight animations cost 9 generations,
bringing this design's total reported cost to 19 generations.

A staged 12-second battle-renderer run (seed 3872026) matched the original
log exactly: zero hits, peak 650 bullets, no frames at cap, six fast moves
totalling 2.8 seconds. Logs and five screenshots per run are under
`build_tmp/lagopus_battle_review/before/` and `after/`. Only staged copies
were replaced. Animation approval and game installation are pending;
67 remains incomplete in the visible tracker.
