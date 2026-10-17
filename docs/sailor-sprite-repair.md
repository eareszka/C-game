# Sailor fishing sprite repair

Fixed the disconnected rod grip in both 40×28 fishing cels. Added a short forearm, cuff, and sleeve through transparent pixels only. Original sailor pixels, tackle pixels, feet, frame locations, westward facing, and two 600 ms durations are preserved. Runtime sheet remains 80×28.

Final assets:

- `assets/npcs/sailor_fisher_fishing.png`
- `assets/npcs/sailor_fisher_fishing.json`
- `art/npcs/sailor_fisher_fishing.aseprite`

Used the built-in imagegen tool to obtain a connected-grip reference. Its draft changed the character proportions and was not installed as runtime art. The final repair was applied to the existing editable source through native Aseprite (`tools/fix_sailor_grip.lua`); the reproducible sprite composer was updated to match. The reference is retained at `build_tmp/npc_review/sailor_grip_imagegen_reference.png`. Final enlarged preview: `build_tmp/npc_review/sailor_grip_fixed_preview.png`. Runtime capture: `build_tmp/npc_review/sailor_fisher_phase_5.png`.

Exact imagegen prompt, with the existing fishing sheet as edit target and sailor walking sheet as identity reference; transparent background enabled:

> Precise pixel-art sprite repair for a game. Image 1 is the edit target, an 80x28 pixel horizontal sheet of TWO 40x28 fishing cels. Image 2 is the existing sailor identity reference, do not redesign. Fix the visibly disconnected grip: in BOTH cels add the sailor's short westward forearm and hand so the hand directly grips the lower end of the existing fishing rod, with no transparent gap. Keep the sailor's existing left-facing head, hat, body, feet, existing black outlines and exact limited flat colors. Keep both characters in exactly their existing location relative to the 40x28 frame, feet planted at the same baseline. Keep rod, line and float existing positions, with second cel's existing tiny bob motion. True transparent background. No text, no scenery, no extra frames. Maintain exact target dimensions 80x28 if supported. Hard pixel grid and no antialiasing. This is an edit of the existing two cels, not a new character design.

Verified connected grip pixels in both frames, exact preservation of opaque sailor pixels and the complete feet region, dimensions, and exported 600 ms frame timings. `sailorfishercheck` passes on seeds 387 and 2026; its phase captures show the updated sprite.
