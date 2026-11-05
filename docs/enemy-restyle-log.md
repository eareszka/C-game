# Enemy restyle log

One row per enemy as it is installed (`docs/enemy-restyle-prompt.md`). The new hit radius is 0.8 times the frame's shorter side, in screen pixels at 2x.

| # | Enemy | Old frame | New frame | New hit radius | Drawn height | Generations | Hand fixes |
|---|---|---|---|---|---|---|---|
| 34 | Anaye | 130x118 | 130x118 | 94.4 (unchanged) | 76 at idle (unchanged) | 16 | Frame 0: folded to 8 colours plus black, one violet shared by blade and robe (`664b95`), plate gaps inside one material recoloured `34343e`, eyes cut to a 2 px mark under a brow (`hand_frame0.py`). Poses: lilac specks back to steel, pose 7's blade rim painted, redo2's pale slash pasted behind pose 7 (`anim/poses.py`). 9 distinct poses kept at the user's choice, over the bible's 4 to 5. Interior black 15 to 18% left in. Coded points unchanged: blade measures (18, 104) against (19, 105). |
