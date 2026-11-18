"""Verdict engine: turns a guess plus a tester result into a verdict with numbers.

Rules, checked in this order:
  1. Guess is "other"                              -> Not used
  2. item dropped out of the feed, or fall >= tau1 -> Supported
  3. fall >= tau2 (and < tau1)                     -> Partly supported
  4. otherwise (fall of 0 or 1, or a rise)         -> Not supported, plus the strongest driver
fall = rank_after - rank_before, so a bigger fall means the signal mattered more.
"""

from src.config import (TAU1, TAU2, SUPPORTED, PARTLY_SUPPORTED, NOT_SUPPORTED,
                        NOT_USED, OTHER_GUESS)
from src.tester import test_signal


def get_verdict(guess, item, test_result, items, weights, tau1=TAU1, tau2=TAU2,
                already_off=None):
    """Return {"verdict", "before_rank", "after_rank", "strongest_driver", "message"}.

    guess:       one of the signal names in `weights`, or "other".
    test_result: the dict from test_signal for this item and this guess
                 (not needed, so may be None, when the guess is "other").
    items, weights: needed to find the strongest driver (re-ranks once per signal).
    already_off: signals already switched off (default none). The strongest-driver search
                 then works inside that feed and skips those signals.
    """
    signals = list(weights)

    # Rule 1: a guess the feed has no signal for. No ranks to report.
    if guess == OTHER_GUESS:
        names = ", ".join(_name(s) for s in signals)
        return _result(NOT_USED, None, None, None,
                       f"Not used: this feed doesn't use that. It uses: {names}.")

    # A typo must not fall through to "Not supported" and look like a real answer.
    if guess not in signals:
        raise ValueError(f"Unknown guess: {guess!r}")
    if test_result["item_id"] != item["id"] or test_result["signal"] != guess:
        raise ValueError("test_result is not for this item and guess")

    before = test_result["rank_before"]
    after = test_result["rank_after"]
    fall = after - before

    # Rule 2. Dropping out counts even for a fall of 1 or 2 places (boundary cases 10 and 11):
    # the person sees the item leave their feed.
    if test_result["dropped_out"] or fall >= tau1:
        extra = " It drops out of the feed." if test_result["dropped_out"] else ""
        return _result(SUPPORTED, before, after, None,
                       f"Supported: without {_name(guess)} this item goes from "
                       f"#{before} to #{after}.{extra}")

    # Rule 3
    if fall >= tau2:
        return _result(PARTLY_SUPPORTED, before, after, None,
                       f"Partly supported: without {_name(guess)} this item falls "
                       f"from #{before} to #{after}.")

    # Rule 4
    driver = _strongest_driver(item, items, weights, already_off)
    message = (f"Not supported: without {_name(guess)} this item goes from "
               f"#{before} to #{after}, which is less than {tau2} places down.")
    if driver is None:
        message += " Switching off any single signal does not push it down."
    else:
        message += (f" The signal that matters most for this item is {_name(driver['signal'])} "
                    f"(#{driver['rank_before']} → #{driver['rank_after']}).")
    return _result(NOT_SUPPORTED, before, after, driver, message)


def _strongest_driver(item, items, weights, already_off=None):
    """The signal whose removal drops this item furthest, or None if none drops it.
    Ties go to the signal that comes first in `weights`, so the answer is deterministic.
    """
    best = None
    best_fall = 0  # a signal must push the item down by at least 1 place to count
    for signal in weights:
        if already_off and signal in already_off:
            continue  # already off, so switching it off again changes nothing
        r = test_signal(items, weights, item["id"], signal, already_off=already_off)
        fall = r["rank_after"] - r["rank_before"]
        if fall > best_fall:  # strict ">" keeps the earlier signal on a tie
            best_fall = fall
            best = {"signal": signal, "rank_before": r["rank_before"],
                    "rank_after": r["rank_after"]}
    return best


def _result(verdict, before, after, driver, message):
    return {"verdict": verdict, "before_rank": before, "after_rank": after,
            "strongest_driver": driver, "message": message}


def _name(signal):
    return signal.replace("_", " ")
