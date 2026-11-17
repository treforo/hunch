# AI log

| Date | What I asked | What AI produced | What I checked | What I changed or rejected |
|---|---|---|---|---|
| [2026-11-16] | Stage 0: repo structure visualization, README skeleton, log template | [] | Any missing features | New Layout implemented |
| [2026-11-16] | Stage 1: plan for ranker and counterfactual tester | Plan with assumptions,16 tests | Read the plan before approving it; ran pytest; compared with my paper calculation: result and who was right | Found that the AI's planned test (mean vs zero giving different rankings) was impossible, because a constant shift doesn't change order. The test was rewritten to compare scores instead. This also changes my report argument for "off = mean". |
| [2026-11-17] | Setup help (Python, git, venv on Windows) | Commands and fixes | Ran them myself | `pip.exe` was blocked by Application Control, so I used `python -m pip` and `python -m pytest`, and will put those commands in the README. Result: 18 passed. |