"""Simple consistency check, run after a signal has been switched off.

WHAT IT CHECKS: for the post the person asked about, take each of the OTHER four signals and
get its verdict twice with the same verdict engine and thresholds:
  before = in the original feed
  after  = in the feed with the switched-off signal already off
and report whether the verdict word changed. A change means that verdict depended on the
signal that was switched off.

WHAT IT DOES NOT SHOW: whether any verdict or reason is correct, or faithful to the model.
It compares our own verdicts with each other, nothing more. It does not use a second model
or any outside ground truth, and one post is checked at a time.
"""

from src.config import TAU1, TAU2, FEED_SIZE
from src.tester import test_signal
from src.verdicts import get_verdict


def consistency_check(items, weights, item, switched_off, tau1=TAU1, tau2=TAU2,
                      feed_size=FEED_SIZE):
    """Return {"item_id", "switched_off", "rows": [{"signal","before","after","changed"}],
    "any_changed"}. Rows cover every signal except `switched_off`, in the weights' order."""
    if switched_off not in weights:
        raise ValueError(f"Unknown signal: {switched_off!r}")
    rows = []
    for signal in weights:
        if signal == switched_off:
            continue
        before = _verdict(items, weights, item, signal, None, tau1, tau2, feed_size)
        after = _verdict(items, weights, item, signal, [switched_off], tau1, tau2, feed_size)
        rows.append({"signal": signal, "before": before, "after": after, "changed": before != after})
    return {"item_id": item["id"], "switched_off": switched_off, "rows": rows,
            "any_changed": any(r["changed"] for r in rows)}


def _verdict(items, weights, item, signal, already_off, tau1, tau2, feed_size):
    result = test_signal(items, weights, item["id"], signal, feed_size, already_off)
    return get_verdict(signal, item, result, items, weights, tau1, tau2, already_off)["verdict"]
