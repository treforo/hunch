"""Mini check: do the tester and verdict engine agree with the planted causes?

Run from the repo root:  python scripts/mini_check.py
Expected verdicts come from the hand-written design table in src/world.py
(PLANTED_DESIGN), never from the tester or verdict engine.
"""

import sys
from pathlib import Path

# Lets "from src..." work when this file is run as a script from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SEED, TAU1, TAU2, FEED_SIZE, OTHER_GUESS  # noqa: E402
from src.tester import test_signal, test_signals  # noqa: E402
from src.verdicts import get_verdict  # noqa: E402
from src.world import generate_world  # noqa: E402


def ranks_text(out):
    if out["before_rank"] is None:
        return "-"
    return f"#{out['before_rank']} -> #{out['after_rank']}"


def main():
    world = generate_world()
    items, weights = world["items"], world["weights"]
    by_id = {i["id"]: i for i in items}

    print(f"Hunch mini check | seed {SEED} | {len(items)} items | feed = top {FEED_SIZE} "
          f"| tau1 = {TAU1}, tau2 = {TAU2}")
    print()

    # ---- Part 1: single-cause and social items, correct and adjacent wrong guess ----
    planted = sorted((i for i in items if i["design_role"] in ("single", "social")),
                     key=lambda i: i["id"])
    header = (f"{'item':>4}  {'planted cause':<28} {'guess':<17} {'ranks':<12} "
              f"{'expected':<16} {'actual':<16} {'match':<5} strongest driver")
    print(header)
    print("-" * len(header))
    matches = total = 0
    for item in planted:
        for kind in ("correct", "wrong"):
            guess, expected = item["expected"][kind]
            result = None if guess == OTHER_GUESS else test_signal(items, weights, item["id"], guess)
            out = get_verdict(guess, item, result, items, weights)
            ok = out["verdict"] == expected
            matches += ok
            total += 1
            driver = out["strongest_driver"]
            driver_text = (f"{driver['signal']} (#{driver['rank_before']} -> #{driver['rank_after']})"
                           if driver else "-")
            print(f"{item['id']:>4}  {item['planted_cause']:<28} {guess:<17} {ranks_text(out):<12} "
                  f"{expected:<16} {out['verdict']:<16} {'yes' if ok else 'NO':<5} {driver_text}")
    print()
    print(f"Matches: {matches} of {total}")
    print()

    # ---- Part 2: the redundant pair ----
    rp = next(i for i in items if i["design_role"] == "redundant_pair")
    pair = rp["planted_cause"].split("+")
    truth = rp["expected"]["pair_truth"]
    print(f"Redundant pair: item {rp['id']}, causes {pair[0]} and {pair[1]} (both real causes)")
    print("Ground truth from the design: each guess is true, so each should be Supported.")
    print()
    print(f"{'switched off':<28} {'ranks':<12} {'dropped out':<12} {'verdict':<16} ground truth")
    for signal in pair:
        result = test_signal(items, weights, rp["id"], signal)
        out = get_verdict(signal, rp, result, items, weights)
        print(f"{signal:<28} {ranks_text(out):<12} {'yes' if result['dropped_out'] else 'no':<12} "
              f"{out['verdict']:<16} {truth[signal]}")
    both = test_signals(items, weights, rp["id"], pair)
    fall = both["rank_after"] - both["rank_before"]
    meets = both["dropped_out"] or fall >= TAU1
    print(f"{' + '.join(pair):<28} #{both['rank_before']} -> #{both['rank_after']:<6} "
          f"{'yes' if both['dropped_out'] else 'no':<12} "
          f"{'(no single guess)':<16} meets the Supported rule: {'yes' if meets else 'no'} "
          f"(fall {fall}, dropped out: {'yes' if both['dropped_out'] else 'no'})")


if __name__ == "__main__":
    main()
