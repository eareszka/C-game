# Project memory

- Enemy 83 — Beast of Barrisdale: still needs a blocking animation during phase 2, when it hovers and catches player shots. The approved grounded idle and airborne animation are implemented; the blocking animation remains unfinished. (2026-10-11)


## Approved crafting stage (2026-10-15)

23 craftables; reusable recipe books bought with Gold in town book shops. New items are craftable inventory entries only; effects are deferred. Sleeping Bag retired. Escape Charm reusable; O2 Ring renamed O2 Charm. White Fur renamed Fur; Tripodero Legbone merged into Bone; Horn includes tusks.

### Recipes and book prices

- KNIFE: 2 WOOD + 3 ore; book 10 Gold; output 1.
- DAGGER: 2 WOOD + 3 ore; book 10 Gold; output 1.
- CLUB: 3 BONE + 3 ore; book 15 Gold; output 1.
- BAND-AID: 1 HIDE + 1 FLOWER; book 15 Gold; output 1.
- ANTIDOTE: 1 POISON GLAND + 1 FLOWER; book 20 Gold; output 1.
- RAFT: 10 WOOD + 3 VINE; book 30 Gold; output 1.
- CAMPFIRE: 6 WOOD + 4 STONE + 1 EVERLASTING EMBER; book 40 Gold; output 1.
- MEDKIT: 2 REGENERATIVE TISSUE + 2 HIDE + 2 VINE; book 60 Gold; output 1.
- BOMB: 2 BRONZE + 2 OILBLOOM + 1 EVERLASTING EMBER; book 70 Gold; output 1.
- SAIL: 6 WING SKIN + 4 VINE; book 80 Gold; output 1.
- AXE: 2 WOOD + 2 VINE + 3 ore; book 80 Gold; output 1.
- SMOKE BOMB: 4 WOOD + 2 HIDE + 2 ESSENCE; book 100 Gold; output 1.
- ESCAPE CHARM: 3 STONE + 4 VINE + 2 ENCHANTED WOOD; book 120 Gold; output 1.
- COLD-WEATHER GEAR: 6 WHITE FUR + 4 HIDE + 6 FEATHER; book 120 Gold; output 1.
- HALBERD: 2 WOOD + 3 ore + 1 OLD SPEARHEAD (first craft only); book 140 Gold; output 1.
- SPYGLASS: 1 EYE LENS + 3 BONE; book 160 Gold; output 1.
- DIVING FINS: 3 WING SKIN + 3 BONE + 4 GRIP SCALES; book 180 Gold; output 1.
- KATANA: 2 WOOD + 3 ore + 1 MOON STEEL (first craft only); book 180 Gold; output 1.
- SWIFT BOOTS: 6 HIDE + 4 WIND SINEW + 6 FEATHER + 6 GRIP SCALES; book 200 Gold; output 1.
- COMPASS: 4 BRONZE + 1 EYE LENS + 3 ESSENCE; book 250 Gold; output 1.
- O2 CHARM: 3 WATER RING + 10 GILLS; book 300 Gold; output 1.
- BINOCULARS: 2 EYE LENS + 2 HORN + 2 VINE; book 400 Gold; output 1.
- SCYTHE: 2 WOOD + 3 ore + 1 REAPERS EDGE (first craft only); book 500 Gold; output 1.

### Approved material sources (enemy IDs)

- HIDE: 00, 01, 09, 17, 50, 53, 55, 79, 86, 87.
- VINE: 02, 58, 61, 63.
- FEATHER: 03, 57, 67, 68, 75.
- FLOWER: 08, 22, 51, 70.
- OILBLOOM: 08, 22, 51, 70.
- FUR: 20, 28, 41, 48, 62.
- WING SKIN: 10, 12, 83.
- BONE: 38, 59, 62, 64, 66.
- EYE LENS: 06, 11, 52.
- HORN: 77, 84, 90.
- EVERLASTING EMBER: 07, 24, 73, 81, 97.
- WATER RING: 18, 49, 51.
- GILLS: 14, 15, 43, 46, 96.
- REGENERATIVE TISSUE: 60, 71, 89.
- POISON GLAND: 05, 21, 25, 32, 35, 56, 69, 74.
- SPIRIT ESSENCE: 29, 30, 34, 36, 37, 42, 44, 80, 88, 95.
- PLAGUE RESIDUE: 99.
- LAVA CHARM: 07, 13, 97.
- WIND SINEW: 16, 45.
- GRIP SCALES: 27, 39, 72, 85, 93, 98.
- ENCHANTED WOOD: 78.

Man-Eating Boulder (31) and Tse’nagahi (33): independent once-per-victory rolls, one each: Stone 100%, Bronze 40%, Emerald 20%, Veyrite 10%, Dravium 5%, Kharvite 2%, Reality Shard 0.5%. No other enemy uses ore rolls. All other assigned drops give one of each per victory. Bullet/laser cancellation gives at most 6 extra Wood/Stone combined, never more rare materials. Unassigned enemies give EXP and common bonuses only.

Unassigned: 04 Lili, 19 Skeljaskrimsli, 23 Olgoi-Khorkhoi, 26 Akhekh, 40 Slide-Rock Bolter, 47 Moha-Moha, 54 Billdad, 65 Mice That Eat Iron, 76 Loch Oich Monster, 82 Nadubi, 91 Kurrea, 92 Siehnam, 94 Trochus, 100 Flesh Planet.

### Deferred effects and rules

Band-Aid: partial heal; Medkit: full heal; Antidote: cure poison; Campfire: consumed on placement, permanent warp point; Bomb: battle explosive; Smoke Bomb: break pursuit. Those six are consumables. Escape Charm: reusable return to current dungeon entrance. Cold-weather Gear: prevents cold HP drain; entering cold without protection displays a warning. Swift Boots: faster walking/sprinting; Diving Fins: faster swimming; O2 Charm: no oxygen loss underwater. Spyglass: see tier 2 on zoom-out; Binoculars: tier 1. Compass: reveal current dungeon map. Lava Charm: attach to raft for lava travel. Plague Residue: weapon poison coating, duration undecided. Spirit Essence retains More Shots upgrades (2, then 4); Oilbloom retains Faster upgrades. Exact gameplay effect tuning, equipment slots and regional book stock remain deferred.

### Stage implementation defaults

Book purchasing is included, through existing town book-shop counters, all 23 titles stocked. Scythe Book is most expensive at 500 Gold. All crafts spend materials and store outputs; no new gameplay effects in this stage. Existing weapons, raft and sail retain their behavior. Old free Raft/Sail book grants become shop purchases; existing owned books survive save migration. Books and permanent gear cap at one; resources and the six consumables cap at 999. New save version 3 reads version 2 saves.

31 named resources: Wood, Stone, Gold, Flower, Gravestone (legacy), Oilbloom, Hide, Bone, Spirit Essence, Bronze, Emerald, Veyrite, Dravium, Kharvite, Reality Shard, Vine, Feather, Fur, Wing Skin, Eye Lens, Horn, Everlasting Ember, Water Ring, Gills, Regenerative Tissue, Poison Gland, Plague Residue, Lava Charm, Wind Sinew, Grip Scales, Enchanted Wood.

Sail remains 6 Wing Skin + 4 Vine, intended around middle progression. Spyglass intended 3/5 and Binoculars 5/5; shared high-tier Eye Lens sources remain a balance consideration. Gathering and Gravestone removal are deferred. New effects, regional shop stock, equipment slots, heal amounts, movement bonuses, poison duration and crafting balance playtests remain future work.
