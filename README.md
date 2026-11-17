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

**Design decisions** (each with a one-line reason)
| Decision | Value | Reason |
|---|---|---|
| Feed size | 40 items, top 10 shown | [ ] |
| Weights | [ ] | [ ] |
| tau1 (Supported) | [ ] | [ ] |
| tau2 (Partly) | [ ] | [ ] |
| "Off" means | feed-wide mean | [ ] |
| Seed | [ ] | [ ] |

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