# Hunch: testing your own theory of why a post appears

IIS Assignment 2 · Treasure Maduforo · 2735196
README prose word count: about 1340 (code blocks and setup commands excluded)
Repository: [link] · Submitted release/commit: [v1.0-submission tag or commit hash, added at freeze]

## Project status
Stages 0 to 4 are finished. The switch-off control and consistency check (Stage 5) are not started.

- **Made so far:** a simulated feed where five invented signals rank 40 items; a tester that switches a signal off and re-ranks; a verdict engine that judges a guess from the rank change; a seeded world with hand-planted causes; a mini check that compares the verdicts with the planted causes.
- **Implemented:** ranker with input validation (`src/ranker.py`); counterfactual tester for one signal or several together (`src/tester.py`); verdict engine with Supported, Partly supported, Not supported and Not used (`src/verdicts.py`); mini check (`scripts/mini_check.py`); 141 pytest tests.
- **Interface (implemented):** thin FastAPI API (`src/api.py`: `GET /feed`, `POST /guess`) and a single-page front end in plain HTML/CSS/JS (`static/`) with a feed of cards, a guess picker (five signals plus "Something else") and a verdict panel. Verdicts are shown as words with a symbol, not colour alone. Not yet checked by a person in a browser: [your result].
- **Simulated:** the world (`src/world.py`): 40 items, 10 planted causes, one user profile, seed 42. Signals, weights and causes are invented, not Facebook's.
- **Planned, not built:** switch-off control and consistency check (Stage 5, may be cut to planned); scenario script `scripts/scenarios.py`, screenshots and diagram (Stages 6 and 7); LLM parsing of free-text guesses (no model chosen).

## Technology stack
| Part | Technology | What it does | Status |
|---|---|---|---|
| Language | Python 3.10+ (developed on 3.15.2, Windows) | Ranker, tester, verdicts, world | Implemented |
| Tests | pytest | Unit tests, hand-worked examples | Implemented |
| Backend | FastAPI, uvicorn | Serves the feed and verdicts; httpx for API tests | Implemented |
| Front end | Plain HTML/CSS/JS | Feed cards, guess picker, verdict panel | Implemented |
| LLM | None | Would parse free-text guesses | Planned, no model chosen |
| AI tool | Claude (chat) | Helped write code, tests and drafts | See AI assistance |

**Design decisions**

| Decision | Value | Reason |
|---|---|---|
| Feed size | 40 items ranked, top 10 shown | Large enough for an item's rank to move a long way (e.g. #3 → #38), small enough to check by hand. |
| Weights | topic affinity 0.35, followed account 0.25, popularity 0.15, recency 0.15, similar users 0.10 | Personal signals outweigh crowd signals. Invented for this simulation, not Facebook's. |
| "Off" means | Feed-wide mean of that signal, not zero | Keeps displayed scores at a typical level instead of lowering them. Any constant gives the same ranking, including zero, so this affects the scores shown, not the verdicts. |
| Verdict is based on | Rank change, not score change | Rank is what the person sees, and a large score contribution may not change the rank. |
| tau1 (Supported) | Drops out of the top 10, or falls 5 or more places | A fall of 5 is half the visible feed, which a person would notice. |
| tau2 (Partly) | Falls 2 to 4 places | More than a small shuffle, but not a clear change. |
| Drop-out rule | Dropping out is Supported even for a fall of 1 or 2 | The question is whether the item would still appear; see `docs/boundary_cases.md` (cases 10 and 11). |
| Ties | Lower item id first; scores within 1e-9 count as equal | Makes the ranking deterministic and stops float noise breaking ties. |
| Input checks | `rank` rejects bad data (values outside 0 to 1, duplicate ids, weights not summing to 1, and so on) | Those errors would otherwise change rankings with no warning. |
| Seed | 42 | Reproducible world, screenshots and results. |
| World design | 10 planted items, 8 fillers, 22 background | 8 single-cause items, 1 social item and 1 redundant pair fill the feed; the fillers sit just above the average score. |

**Definitions**
- Rank runs 1 to 40. The feed is ranks 1 to 10.
- fall = rank after − rank before. dropped_out = rank before ≤ 10 and rank after ≥ 11.
- Guesses are only offered for items in the feed (enforced by the Stage 4 UI, not by the engine).

**Verdict rules (implemented, checked in this order)**
1. Guess is "other" → Not used.
2. dropped_out or fall ≥ 5 → Supported.
3. fall 2 to 4 → Partly supported.
4. fall ≤ 1 (including rises) → Not supported, naming the strongest driver.

**Still undecided:** whether the consistency check survives the Day 3 cut line.

## Running or inspecting the work
Requires Python 3.10 or newer. No API keys are needed.

```bash
python -m venv venv
venv\Scripts\activate              # Mac/Linux: source venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest                   # 141 tests
python scripts/mini_check.py       # prints the mini check tables
python -m uvicorn src.api:app      # starts the app; open http://127.0.0.1:8000
```

Stop the server with Ctrl+C. Not built yet: `scripts/scenarios.py`. To inspect without running anything, read `docs/mini_check_output.txt`.

## Known limits
- The world is simulated and defines the truth. There are no participants, so nothing is claimed about how people respond or how Facebook works.
- The mini check matches by construction: the data was built so the verdicts should follow. It shows that the design and the engine agree, not that the engine is accurate in general.
- The design check holds for seed 42. About a quarter of other seeds (54 of 200 tried) fail it, because the background score cap sits close to the average score. The generator raises an error for those.
- The redundant pair is a rank effect: each signal contributes separately to a weighted sum, so a single-signal test can miss a combined effect among neighbouring items. The pair item sits at rank 9, near the cutoff.
- Partly supported and items near the cutoff are tested only by unit tests, not planted in the world.
- Only one guess per test. Free-text guesses, interacting signals and a person's own data are not handled.

## Development record
| Stage | What changed | Why | What I checked | Commit |
|---|---|---|---|---|
| 0 Repo and context | Repo structure, CLAUDE.md rules, README skeleton, AI log | Keep scope small and stop unbuilt work being described as built, which the marking penalises | [your check] | [link] |
| 1 Ranker and tester | `rank` with per-signal breakdown, `test_signal`, hand example. A planned test (mean and zero give different rankings) turned out impossible and was replaced by a score-difference test. Float-tie rounding added. | Breakdown makes each score explainable; any constant shifts all scores equally; float noise could break ties. | Hand example against my paper calculation: [your result and who was right]. 18 tests pass; the tie test fails if the rounding is removed. | [link] |
| 1b Validation | `validate_items`, called by every `rank` | Duplicate ids, out-of-range values and bad weights gave wrong answers silently. | 86 tests pass; 21 fail if the validation call is removed. | [link] |
| 2 Verdict engine | `src/verdicts.py`, tau1 and tau2 in `config.py`, strongest driver | Verdicts from rank change; unknown guesses and mismatched results raise errors instead of looking like answers. | 12 boundary cases from `docs/boundary_cases.md` copied in as fixed numbers; changing `>=` to `>` at either threshold fails tests; 42 tests pass. | [link] |
| 3 World and mini check | `src/world.py`, `scripts/mini_check.py`, `off` accepts several signals | Known planted causes without participants; the pair test needs two signals off at once. | `check_design` tests the data without calling the tester; seed 42 passes; 18 of 18 rows match; flipping one expected verdict gives 17 of 18; 115 tests pass. | [link] |
| 4 API and UI | `src/api.py`, `static/`, `tests/test_api.py` | Thin API over the existing engine; plain front end so the interaction can be shown and screenshotted. The API refuses items outside the feed because the engine does not. | API tests take expected verdicts from the world's design table; live server answered `/feed`, `/guess` and `/`; 141 tests pass. [Your hand run of all three scenarios in the browser.] | [link] |

## AI assistance
- **Tool:** Claude (chat).
- **What I asked for:** the repo structure and documents; the ranker and tester; the verdict engine; the seeded world and mini check; explanations of edge cases; Windows setup help. Plans were requested before code each time.
- **Checked or changed:**
  - A test Claude planned was impossible, because replacing a signal with any constant leaves the order unchanged. It was replaced and the README reason for "off = mean" was corrected.
  - I decided to leave the world validator until Stage 3, then to enforce validation inside `rank` so the tester and verdict engine are covered too.
  - The mini check can fail: flipping one expected verdict in a temporary copy gave 17 of 18.
  - [your own change, from `ai-log.md`]
- **Not AI:** `docs/boundary_cases.md` was written by me before the verdict code. The tests copy its expected values.

## Additional files
- `ai-log.md`: running log of prompts, checks and changes.
- `CLAUDE.md`: rules given to Claude for this project.
- `docs/boundary_cases.md`: 13 hand-worked verdict cases.
- `docs/mini_check_output.txt`: output of `scripts/mini_check.py` on seed 42.
- Screenshots and the system diagram will be added to `docs/` in Stages 4 to 7. No ZIP files.