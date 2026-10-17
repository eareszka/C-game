# Sailor dialogue and UI text cases

NPC **10005** now uses Grandma's friendly conversation format while awake. This replaces the earlier silent behavior. Sleeping retains a single snoring line.

## Every phase and exact greeting

| Phase | Text | Interaction |
|---|---|---|
| Fishing | Good day! Just doing a little fishing. What do you need? | Topic menu |
| Walking home | Good day! I'm heading home. What do you need? | Topic menu |
| Walking to bed | Good evening! About to turn in. What do you need? | Topic menu |
| Waking / walking to exit | Good morning! What do you need? | Topic menu |
| Walking to river | Good day! I'm off to the river. What do you need? | Topic menu |
| Sleeping | Zzzz... | Single line, no topic menu |
| Dissolving inside | None | No TALK prompt |
| Appearing outside | None | No TALK prompt |
| Dissolving outside | None | No TALK prompt |
| Appearing inside | None | No TALK prompt |

## Awake topic choices and exact responses

1. **What's there to do in town?**

   I usually spend a little time fishing by the river, then head home for a rest. But if you're looking for a little adventure, there's a small cave south of town and a graveyard to the northwest.

2. **Where am I?**

   Uses the same location-aware answer as Grandma. At the river and inside his town-0 cottage:

   You're in the town of Bloom, right in the heart of our world we call Vaalbara.

3. **No**

   Closes the menu without an extra response.

## Edge cases

| Case | Expected behavior |
|---|---|
| New game / older-save migration | Starts fishing and uses the fishing greeting when approached; no automatic greeting popup |
| Approach from any direction | TALK uses the standard distance check (strictly within 40 pixels); approaching alone never opens dialogue |
| Z, Enter, or Space | Opens the current greeting/menu, or the sleeping line; no action during doorway effects |
| Repeated confirmation | Uses the existing shared topic-menu and speech controls, including input consumption |
| Cancel / No | Shared conversation closes; no extra sailor response |
| Ask either topic repeatedly | Same response; no inventory changes, quest changes, or new unlocks |
| Fishing conversation | Sailor keeps facing west and keeps the rod pose; does not turn toward player |
| Talk while walking | World and NPC movement pause together while dialogue is open; walking resumes afterward |
| Talk while sleeping | Zzzz... only, never the awake menu; clock pauses while the line is open |
| Exactly at hour 10 / hour 12 | Sleeping line at hour 10; waking greeting at hour 12, selected from the current phase |
| Pause, menu, map, or someone else's conversation | Existing shared pause/input rules apply; no unsolicited sailor text |
| Save/load in every phase | Current greeting/menu or sleep line is derived from the restored phase; no automatic popup |
| Subsequent cycles | Same state-based greetings and topics, without a separate first-meeting state |
| Every story stage | Same sailor greetings and topic answers in ARC1, TURN, DESCENT, OPEN, and AMNESIA |
| Debug enabled or disabled | Same interaction; no separate sailor entry in the static debug dialogue catalogue |
| Wrong room, another town's interior 3, wrong entrance, offscreen | No remote dialogue; sailor resolves only at its actual location and town-0 doorway |
| Other NPCs nearby | Standard NPC selection order chooses a nearby talkable NPC; text belongs to the selected NPC |
| Notes or chests nearby | Awake/sleeping sailor uses normal talkable-NPC interaction priority; doorway effects do not reserve interaction |
| Shop request | No shop exists; no SHOP / TALK / LEAVE shop menu |
| Invalid topic indices -1 or 3 | No response; no state changes |
| Topic request during sleep or doorway effects | No conversation and no answers, even if called directly |
| Direct shared location helper call | Can build generic location text; the awake Where am I? option now exposes it normally |
| Route failure / missing shoreline / overlong travel | Stationary at home in sleeping fallback, so interaction says Zzzz...; diagnostics remain console-only |
| Wrapping / paging | Standard speech renderer handles the longer town-activities answer; all new literal text uses supported ASCII punctuation |

The original fisherman (**10004**) retains his own dialogue. His lines cannot replace the sailor's greetings because they use separate IDs and line functions.

## Console diagnostics (not dialogue)

- Sailor fisher: planning town 0 shoreline route
- Sailor fisher: no valid west shoreline within one tile
- Sailor fisher: no route; stationary at home
- SailorFisher: journey exceeds twelve-hour cycle
- Shared routing may also log Resident: inaccessible endpoint (...) or Resident: no route to ... before a successful fallback.

## Verification

`sailorfishercheck` passes on seeds 387 and 2026. It checks every phase across all five story stages, with debug both enabled and disabled, including after each phase's save/load: topic labels, location answer, town-activities answer, sleep-only line, no doorway dialogue, no shop, invalid choices, and unchanged story flags. Routine timing, collision, fixed fishing facing, and hourly skips also pass. Main-loop keyboard behavior and interaction priority above are verified by source inspection; they are not automated keyboard-driven UI tests.
