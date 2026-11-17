# Verdict boundary cases
 
Hand-worked from the verdict rules in the README, before any verdict code was written. These are the expected values for the verdict engine tests. They must not be computed by the code under test.
 
## Definitions
 
- Rank is 1 to 40. The feed is ranks 1 to 10. Ties are broken by item id (lower id first).
- `before_rank` and `after_rank` are the item's ranks before and after the guessed signal is switched off.
- `fall = after_rank - before_rank` (zero or negative means no fall).
- `dropped_out = before_rank <= 10 AND after_rank >= 11`.
- Guesses are only offered for items currently in the feed (ranks 1 to 10).
- Thresholds: tau1 = 5 places, tau2 = 2 places.
## Verdict rules (checked in this order)
 
1. Guess is "other" -> **Not used**.
2. `dropped_out` OR `fall >= 5` -> **Supported**.
3. `fall` 2 to 4 -> **Partly supported**.
4. `fall <= 1` (including rises) -> **Not supported**, naming the strongest driver.
## Boundary cases
 
| # | Guess | before | after | fall | Dropped out? | Expected verdict | What it tests |
|---|-------|--------|-------|------|--------------|------------------|---------------|
| 1 | signal | 3 | 3 | 0 | no | Not supported | No change |
| 2 | signal | 3 | 4 | 1 | no | Not supported | Just below tau2 |
| 3 | signal | 3 | 5 | 2 | no | Partly supported | tau2 boundary |
| 4 | signal | 3 | 7 | 4 | no | Partly supported | Just below tau1 |
| 5 | signal | 3 | 8 | 5 | no | Supported | tau1 boundary |
| 6 | signal | 3 | 2 | -1 | no | Not supported | Item rises |
| 7 | signal | 5 | 10 | 5 | no | Supported | tau1, stays in feed |
| 8 | signal | 6 | 10 | 4 | no | Partly supported | Last place in feed, not dropped |
| 9 | signal | 6 | 11 | 5 | yes | Supported | Drop-out and tau1 together |
| 10 | signal | 9 | 11 | 2 | yes | Supported | Drop-out overrides tau2 |
| 11 | signal | 10 | 11 | 1 | yes | Supported | Drop-out overrides tau2 |
| 12 | signal | 3 | 38 | 35 | yes | Supported | Large fall |
| 13 | "other" | any | any | any | any | Not used | Unmodelled guess |
 
## Design decision on cases 10 and 11
 
An item near the bottom of the feed becomes "Supported" after a fall of only 1 or 2 places, because it left the feed.
 
- **Option A (rule as written):** the person sees the item vanish, so for them it did not survive. Simple to explain.
- **Option B (stricter):** require both a drop-out and a fall of at least tau2. Case 11 would become Not supported even though the item disappeared.

**My decision:** Option A (rule as written). An item that drops out of the top 10 is Supported, even if it only falls 1 or 2 places.

**My reason:** The question Hunch answers is "would this item still appear in my feed without this signal?" Rank matters because it is what the person sees, so an item that leaves the feed has not survived the test, however small the fall. Option B would tell the person their guess was wrong in case 11 (#10 → #11) even though the item disappeared, which is a false denial on exactly the evidence the person cares about. Option A is also simpler to state and to test, with one rule for drop-out and one for fall size. The cost is that an item near the cutoff can be marked Supported on a very small rank change, which may overstate how much the signal matters. I reduce this by always showing the numbers (e.g. "#10 → #11") so the person can judge the size of the change. I also record items near the cutoff as a known limitation in the report.