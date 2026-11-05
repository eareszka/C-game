# Enemy restyle: prompt for the agent doing it

**Stopped by the user on 2026-11-04. Don't run this prompt.** The B and C rule it draws to has been replaced by NES style at every size (`art/direction/SPRITE_STYLE.md`), and its redraws were put back.

Paste everything under "The prompt". The queue table below it is part of the
brief, and the prompt tells the agent to read it here.

## The prompt

You are redrawing the enemy battle sprites in the queue below through PixelLab so they match this
game's art bible, while keeping each creature's design. Work from the repo root,
`C:\Users\13178\OneDrive - UWM\Desktop\projects\C-game`.

**Read these first, in order:**
1. `art/direction/SPRITE_STYLE.md`: the bible, and the final word on style.
2. `docs/enemy-restyle-prompt.md`: this brief, with the queue table.
3. `art/direction/approved_enemy_study/STYLE_BRIEF.md`: the words to send PixelLab.
4. `docs/pixellab-terminal.md` and the docstring of `tools/pixellab_enemy.py`: the pipeline.

Before each enemy, read its class in `src/enemies.cpp` and its line in
`ENEMY_SHEETS` in `src/battle.cpp`.

**The job.** Redraw the queue in the table's order, one enemy at a time.
`python tools/enemy_style.py --queue` shows what's left.

**Don't touch:** 12, 13, 31, 46, 63, 65 and 99 (the user, 2026-11-04: keep them as they are); sprites already in styles B or C, other than the ones in the table; bosses 6, 23, 30, 49, 52, 98
and 100; bullet patterns; logs and footprints; map minis, even if a sprite's
height changes.

**Keep the design idea.** This is a restyle, not a redesign. Keep the same
creature, signature features, main colours, mood, view and attack poses, and send
the current sprite as the PixelLab source. If PixelLab drifts, sharpen the prompt
and retry, or fix it by hand with a small script in the enemy's folder. If it
still won't hold, stop and ask. Only make a new design if the user asks for one.

**For each enemy,** work in a new `art/enemies/pixellab/<NN_name>/redo_bc/` folder
and leave earlier work in place:
1. Write `job.json` and the prompt: what the creature is, plus the words from
   `STYLE_BRIEF.md`. The tool sends the new style board by default. **If the frame
   must grow to reach the bible's height for its tier, never send an enlarged
   sprite** (the user, 2026-11-04). Describe what the current sprite looks like and
   let PixelLab draw it at the target size: `describe` and `size` in
   `tools/restyle_queue.json`, then `python tools/restyle_run.py describe ID
   --generate` and `pick ID N`. The tool makes the blank base and sets `replaces`.
2. Run `source`, then `edit` as a dry run, then `edit --generate`, then `clean`.
3. Fold to 8 colours plus black, at most 3 tones per material. Merge small patches
   with `flat()` from `art/enemies/pixellab/36_cu_sith/views.py`. Fix eyes by hand.
4. Run `python tools/enemy_style.py <frame.png> --tier <TIER>`. Clear every FAIL
   and look into every WARN. Then look at it yourself on black and on grey.
5. **Stop for approval of frame 0.** Show the old and new versions side by side.
6. Then run `rotate` for the same views it has now. Rotate labels are often a step
   off, so look at every output and assign views by eye. Run `animate` and redo
   each `flap` and `alt` sheet too. Cut to 4 to 5 distinct poses at 260 ms, holding
   poses across cells where the sheet has more cells. Run `pack`.
7. **Stop for approval of the animation.**
8. Run `install`, then `make`. Install backs up the old sheet, points `battle.cpp`
   at the new one and marks the enemy done on the chart.
9. Add a row to `docs/enemy-restyle-log.md`: id, old and new frame size, new hit
   radius, drawn height, generations used, and any hand fixes.

**Keep the game working:**
- Keep each sheet's frame count, layout and direction rows, and what each pose
  means. The table lists the ones that matter, and `Enemy::anim_frame` picks poses
  by number.
- A `flap` sheet must keep the idle's cell width, because `battle.cpp` works out
  its frame count from that. An `alt` sheet can have its own size.
- **Coded sprite points:** 12, 13, 31, 34, 43, 54, 55, 63, 80 and 84 fire from
  coordinates on the sprite, such as a gullet, cup or claw. Keep that feature in
  place with `anchor` in `job.json`, or update the numbers in `src/enemies.cpp` in
  the same step. Don't change anything else about the fight.
- The hit circle grows with the frame (0.8 times the shorter side). The user has
  accepted this, so don't add code for it. Keep frames snug and log the new radius.

**Credits.** Run `pixellab-cli --json balance` before and after each enemy. It was
725 on 2026-11-04, and this job may need more than that. Paid stages are dry runs
until you pass `--generate`. Up to 60 generations per enemy is already approved;
past that, ask. Stop and ask when fewer than 60 remain. Never resubmit a job that
timed out: collect it with `pixellab-cli job show`.

**Approvals.** Nothing installs without the user's approval at both stops. At the
start, ask whether they're reviewing in Aseprite on the laptop or on their phone,
and save the `.aseprite` either way. They have rejected work before for too many
shades, animation that's too smooth, and eyes that are too detailed, so check
those before showing anything.

**Other work in this repo.** Another session may be working here. Re-read a sheet
right before you start on it, and tell the user if it changed. Leave other
folders alone. Don't commit or push unless asked.

**When you stop,** report: what's done, what's left, credits used and remaining,
every enemy whose drawn height changed (its map mini may need resizing), every hit
radius that changed (for a playtest), and anything fixed by hand.

## The queue, in order

Frames are as of 2026-11-04. "Idle 3" means three idle frames. The design ideas
are starting points; the current sprite is the real reference.

| # | Enemy | Tier | Frame | Sheets | Design idea | Poses and code to keep |
|---|---|---|---|---|---|---|
| 0 | Skvader | Starter | 20x17 | idle 3 | Hare with antlers and spread bird wings: brown fur, pale belly, gold-brown wings | |
| 1 | Wolpertinger | Low | 20x19 | idle 3 | The Skvader's harder cousin: antlers, red-tipped wings, fangs | |
| 2 | Treesqueak | Low | 20x19 | idle 3 | Upright tan and brown squirrel creature, known for its squeak | |
| 3 | Qique | Low | 20x20 | idle 3, flap | Crested rooster: white head, red crest, orange beak, navy body, orange wing tips | Flap is its wingbeat |
| 4 | Lili | Low | 28x22 | idle 3 | Round pink many-legged scuttler with a big magenta mouth | The 3 frames are its run, stepped by `anim_frame` |
| 5 | Crowing Crested Cobra | Low | 26x24 | idle 3, flap | Coiled cream snake with a red crest, rearing to crow | Flap is its slither |
| 50 | Teakettler | Low | 32x29 | idle 3, flap | Small brown dog-like creature with big pink ears; steam from its nostrils | Frame 1 is the whistle, mouth open. Flap walks backwards |
| 53 | Come-at-a-Body | Low | 42x29 | idle 3, flap | Brown woodchuck with a tan belly | Frame 1 spits, fur up and fangs bared. Flap is the rush |
| 54 | Billdad | Low | 28x27 | idle 3, flap, alt | Peach beaver-like animal with long hind legs and a big round brown tail | Frame 1 is the spring. Alt is leap and slam. Flap has its back to us: in the air, tail raised, tail down, standing. **Coded tail point** |
| 55 | Wapaloosie | Low | 26x26 | idle 3, alt | Rust inchworm-squirrel with fungus on its hump | Frame 1 is the full hump. Alt is reared on its back legs. **Coded spore point.** The log sheet stays |
| 66 | Ayotochtli | Low | 48x35 | idle 3, flap | Tan armadillo with long rabbit ears and a banded shell | Frame 1 is the hunch that sheds plates. Flap is the curled ball rolling |
| 68 | Shuyu | Low | 50x41 | idle 3, flap | Red-feathered chicken with several small heads on thin necks, and three tails | Frames 1 and 2 are heads plucking, and each fires. Flap is wings beating |
| 8 | Snawfus | Medium | 28x31 | idle 3 | White stag with pink-blossom antlers and a blue haze of breath | |
| 9 | Questing Beast | Medium | 36x31 | idle 3, flap | Orange leopard-spotted body on thin deer legs, with a green snake head on a long neck | Flap is its walk |
| 11 | Paoxiao | Medium | 30x27 | idle 3, flap, alt | Grey goat body with a human face, and an eye under its arm | Mouth opens wide on frame 2 for its wail. Flap is the leap. Alt has the mouth closed |
| 14 | Lodsilungur | Medium | 32x23 | idle 3 | Fat pale silver trout facing the viewer, with a beard and red mouth | |
| 15 | Ofuguggi | Medium | 32x23 | idle 3, flap | Dark grey fish with reversed fins; give it enough colour to read on black | Frame 1 is its breath. Flap swims backwards, tail first |
| 24 | Zoureg | Upper | 44x29 | idle 6 at 170 ms, flap, alt | Fire serpent: red and orange coils with a white-hot blade tip | Flap is the dash, uncoiled and thrown like a knife. Alt is drawn back, glowing hotter |
| 64 | Dungavenhooter | Upper | 98x65 | idle 8 | Added by the user. Squat olive crocodilian with no mouth, amber eyes and a grey spiked club on its curled tail | The 8 frames are one tail slap; frame 6 is the club hitting the ground in a crown of dust. **Coded club landing per view (`Dungavenhooter::club`).** Its ringed eyes become the bible's solid mark |
| 80 | Bes Kotak | Upper | 98x65 | idle 5 | Blocky floating wooden chest spirit with glowing amber eyes and stubby hands | Frame 2 the lid lifts and the mouth slot gapes. **Coded box points** |
| 42 | Nykur | Hard | 58x51 | idle 3 | Added by the user, and **it must end up larger**. Dapple-grey water horse with a wet dark-green mane and backward hooves | Show the size before paying. Frame 1 tosses its head, mane swinging out; frame 2 lowers its head, beckoning. **Coded hooves, mane and muzzle (`Nykur::at`), measured on 58x51, so they move with the new frame** |
| 43 | Sazae-Oni | Hard | 54x51 | idle 3 | Spiky khaki turban sea-snail shell with a red demon face and tusks | Frame 2 shrinks back. **Coded mouth and shell points** |
| 84 | Kigutilik | Hard | 98x65 | idle 5 | Violet stilt-legged beast with a walrus head and a cup on its head that gushes water | Frame 2 jaws open. **Coded cup, tusks and mouth.** Its cup top is black today; give it colour |
| 47 | Moha-Moha | Severe | 98x65 | idle 24 rows at 100 ms | Added by the user. Long-necked green lizard in a grey domed shell, with a brown forked tail fin and a cream edge along its neck | Side view, always facing right. Cut to the bible's 4 to 5 poses at 260 ms. No coded points. Its glinting eye becomes the bible's solid mark |
| 48 | Bjarndyrakongur | Elite | 64x142 | idle 12 rows at 162 ms | Standing polar bear king, the user's own drawing: white fur, orange ear tufts, a striped horn with a star | Breath rising, hands swaying, star twinkling, a cold-breath puff from its mouth |
| 51 | Aspidochelone | Elite | 130x81 | idle 8 rows | Huge sea turtle carrying a palm-tree island with sand and a small campfire; no water beneath | Breathing |
| 95 | Wendigo | Elite | 102x66 | idle 3 | Bone demon of winter: skull face, crimson eyes, huge spiked arms, ice horns, icicles | Arms rise and spread. No fight yet |
| 97 | Ro | Elite | 130x81 | idle 8 rows | The one black enemy: roaring bat-winged beast with charcoal hide and red eyes, mouth and wing veins | Breathing. No fight yet. It stays black and must read through lighter charcoal |
| 34 | Anaye | Boss 2 | 130x118 | idle 9 rows | Armoured bone-masked titan with a feather crest and a reality-shard axe | 9 poses picked by `Anaye::anim_frame`: idle, lift, slam. **Coded point where the blade lands** |
