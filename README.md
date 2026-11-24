# Hunch: testing your own theory of why a post appears

IIS Assignment 2 · Treasure Maduforo · 2735196
README word count: ~1000


## Project status
Hunch is a simulated social feed. The person picks a theory ("I'm seeing this because of X"), and Hunch switches that signal off, re-ranks the feed and returns a verdict with the numbers.

- **Implemented:** ranker with input validation; tester that switches one or several signals off; verdict engine (Supported, Partly supported, Not supported, Not used); consistency check; FastAPI API (`/feed`, `/guess`, `/switch_off`); single-page UI with a guess picker, verdict panel, switch-off control and Reset; mini check; 161 pytest tests.
- **Simulated:** the world (`src/world.py`): 40 items, 10 planted causes, one user profile, seed 42. The five signals, weights and causes are invented, not Facebook's.
- **Visual placeholders that do nothing:** search, side navigation, composer, Like, Comment, Share. Names, captions and pictures are invented and play no part in ranking.
- **Planned, not built:** LLM parsing of free-text guesses (no code, no model chosen); `scripts/scenarios.py` (storyboard frames were taken from the running app instead).
- **Not done:** no participants and no evaluation beyond the mini check.

## Technology stack
| Part | Technology | What it does |
|---|---|---|
| Language | Python 3.10+ (developed on 3.15.2, Windows) | Ranker, tester, verdicts, world |
| API | FastAPI, uvicorn | Serves the feed, verdicts and the page |
| Front end | Plain HTML, CSS and JavaScript | Feed cards, picker, verdict panel |
| Tests | pytest, httpx | Unit and API tests |
| AI tool | Claude | Helped write tests and some code |

**Undecided:** which model would parse free-text guesses (planned only).



## Running or inspecting the work
(Requires Python 3.10 or newer. No API keys are needed.)

```bash
python -m venv venv
venv\Scripts\activate              # for Mac/Linux: source venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest                   # includes 161 tests
python scripts/mini_check.py       # prints the mini check tables
python -m uvicorn src.api:app      # open the UI at http://127.0.0.1:8000
```

- Stop the app with Ctrl+C.
- Item numbers in this README come from seed 42.


## Development record

| Stage | What changed and why | What I checked | Commit |
|---|---|---|---|
| 0 Setup | Structure for Repo, README and AI log | Ensuring scope adheres with project requirements | [5563d57](https://github.com/treforo/hunch/commit/5563d57cf1212268c03011c859ee19fa39ecf5ba), [fd34925](https://github.com/treforo/hunch/commit/fd3492506f73172ddde874f20e290da65292ab60), [d5d471e](https://github.com/treforo/hunch/commit/d5d471e3ff1f89f092da2373edade5f4996c3d9b) |
| 1 Ranker and tester | Weighted-sum `rank` with breakdown, `test_signal`, hand example. A planned mean-vs-zero test was impossible and became a score test. Rounding added so float noise cannot break ties. | Hand example against my paper calculation: Matched my results. The tie test fails without the rounding | [ebedb55](https://github.com/treforo/hunch/commit/ebedb55a3873d865a47b7c9245994292766611df), [848915e](https://github.com/treforo/hunch/commit/848915e51e52e0f58c03eeb516634022b254ae0c) |
| 2 Verdict engine | Verdicts from rank change, with tau1 and tau2 in `config.py`. Validation added to `rank`, because bad data changed rankings silently. Both were committed together. | 12 boundary cases from my `docs/boundary_cases.md` hard-coded; changing `>=` to `>` fails tests; 21 tests fail without the validation call | [52454c3](https://github.com/treforo/hunch/commit/52454c396dc933836169a06f666bf9cfbe05ec76) |
| 3 World and mini check | Seeded world with planted causes, `off` taking several signals for the redundant pair, `scripts/mini_check.py` | `check_design` tests the data without the tester. 18 of 18 rows match; flipping one expected verdict gives 17 of 18 | [495ec63](https://github.com/treforo/hunch/commit/495ec6303a4ab281f951000c771ff85893da1fdc) |
| 4 API and UI | FastAPI, plain-JS page. The API refuses items outside the feed, because the engine does not. Later commits restyled the page as a social feed with unique placeholder content. | API tests take expected verdicts from the design table.| [3dce83b](https://github.com/treforo/hunch/commit/3dce83b4258f1aacb39b143ca9ce44bcc62a408f)|
| 5 Switch-off | `POST /switch_off`, `already_off` option, consistency check, Reset, old-rank cues. The server keeps no state. | Earlier tests unchanged; a verdict flip worked by hand for the consistency test | [553e10d](https://github.com/treforo/hunch/commit/553e10dd3b0a3837fa299a449297b45fee9be1fa) |


## AI assistance
- **Tool:** Claude

| Date | What I asked | What AI produced | What I checked | What I changed or rejected |
|---|---|---|---|---|
| 2026-11-16 |repo structure, README skeleton, log template | Folder layout, README skeleton, log template.  | Whether the structure covered the brief's requirements. | Decided to cut the extra evaluation from the report scope. |
| 2026-11-17 | plan for the ranker and counterfactual tester, then the code | Plan with assumptions, then drafts for `config.py`, `ranker.py`, `tester.py` |  Ran pytest. Compared tests with my paper calculation. | Its own planned test (mean vs zero giving different rankings) was impossible, because a constant shift does not change the order. I confirmed this by hand. The test now compares scores, and my report argument for "off = mean" changed. |
| 2026-11-17 | Setup help: Python, git, venv on Windows | Commands and fixes. | Ran them myself. | `pip.exe` was blocked by Application Control, so I use `python -m pip` and `python -m pytest`. Declined the long-path and PATH prompts in the Python installer. |
| 2026-11-17 | verdict engine | `src/verdicts.py` | The expected values for the boundary tests come from my own `docs/boundary_cases.md`, written before the code. Changing `>=` to `>` at either threshold fails 3 tests. Item E's driver worked on paper matches. 21 tests fail if the validation call is removed. | Kept the drop-out rule as written (Option A, boundary cases 10 and 11). Raised errors for unknown guesses and mismatched results instead of returning a verdict. Enforced validation inside `rank`, so the tester and verdict engine are covered too. |
| 2026-11-18 | plan for FastAPI and single-page UI |  `static/` files and `tests/test_api.py` (141 tests). | The install check for FastAPI passed on my machine. The live server answered `/feed`, `/guess` and the page. | Chose FastAPI over Flask after the install check. The API refuses items outside the feed, because the engine does not. |
| 2026-11-18 | switch-off control and consistency check |  `src/consistency.py`, an `already_off` option on the tester and verdicts | A verdict flip for the consistency test worked by hand. Live run for item 7: similar users changed from Not supported to Partly supported. My browser check: Reset and switch-off work. | Approved a server that keeps no state, and hiding the guess buttons while a signal is off.|

## Additional files
- `docs/`: `boundary_cases.md`, `mini_check_output.txt`, 

