# hunch
IIS Assignment 2
# Hunch: testing your own theory of why a post appears

README prose word count: [x]  <!-- exclude code and setup commands -->
Submitted release/commit: [v1.0-submission / hash]

## Project status
- **Made:** [one or two lines]
- **Implemented:** [ ]
- **Simulated:** [ ] (e.g. the seeded world and personas)
- **Planned / unfinished:** [ ] (e.g. LLM parsing of free-text guesses)

## Technology stack
| Part | Technology | What it does |
|---|---|---|
| Backend | Python, [FastAPI/Flask] | [ ] |
| Front end | Plain HTML/CSS/JS | [ ] |
| Tests | pytest | [ ] |
| AI tools | Claude | Helped write code, docs and drafts (see AI assistance) |

**Design decisions**

| Decision | Value | Reason |
|---|---|---|
| Feed size | 40 items ranked, top 10 shown | Large enough for an item's rank to move a long way (e.g. #3 → #38), small enough to check by hand. |
| Weights | topic affinity 0.35, followed account 0.25, popularity 0.15, recency 0.15, similar users 0.10 (sum = 1.0) | Personal signals outweigh crowd signals. These weights are invented for this simulation and are not Facebook's. |
| tau1 (Supported) | Item drops out of the top 10, or falls by 5 or more places | A fall of 5 places is half the visible feed, which a person would notice. |
| tau2 (Partly) | Falls by 2 to 4 places | A small shuffle that is more than noise but not a clear change. |
| "Off" means | Feed-wide mean of that signal, not zero | Zero would make the item look penalised, so removing the signal would confound the test. The mean makes it neutral. |
| Seed | 42 | A fixed seed makes the world, screenshots and results reproducible. |

**Definitions**
- Rank is defined as 1 to 40. The feed is ranks 1 to 10. Ties are broken by item id (with lower id first).
- before_rank and after_rank are the item's ranks before and after the signal is switched off.
- fall = after_rank − before_rank (negative or zero means no fall).
- dropped_out = before_rank ≤ 10 AND after_rank ≥ 11.
- Guesses are only offered for items currently in the feed (ranks 1 to 10).

**Verdict rules (checked in this order)**
1. Guess is "other" → Not used.
2. dropped_out OR fall ≥ 5 → Supported.
3. fall 2 to 4 → Partly supported.
4. fall ≤ 1 (including rises) → Not supported, naming the strongest driver.

**Still undecided:** [ ]

## Running or inspecting the work
```bash
# setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # added at Stage 1/4

# tests
pytest

# mini check
python scripts/mini_check.py

# scenarios
python scripts/scenarios.py

# app
[command added at Stage 4]
```
No API keys are needed. [Update if this changes.]

## Development record
| Stage | What changed | Why | What I checked | Commit |
|---|---|---|---|---|
| 0 Repo and context | [ ] | [ ] | [ ] | [link] |

## AI assistance
- **Tools:** [ ]
- **What I asked for:** [ ]
- **Examples of what I checked or changed:** [2-3 real examples]
- **If no AI was used for a part:** say so.

## Additional files
- `ai-log.md`: running log of prompts, checks and changes
- `docs/`: diagram source, screenshots, mini check output
- [ZIP files, if any, and how to use them]