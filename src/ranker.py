"""Ranker: score = weighted sum of signals, sorted high to low.

An item is a dict:  {"id": 7, "title": "...", "signals": {"topic_affinity": 0.8, ...}}
Signal values are floats from 0 to 1.
"""

SORT_DECIMALS = 9  # scores closer than this are treated as equal when sorting


def signal_mean(items, signal):
    """Feed-wide mean of one signal, over ALL items passed in (not just the top 10)."""
    return sum(item["signals"][signal] for item in items) / len(items)


def rank(items, weights, off=None):
    """Return the items sorted by score (highest first), each as a new dict:
        {"id", "title", "score", "rank", "breakdown"}
    - breakdown maps each signal to its weighted contribution (weight * value),
      so the contributions add up to the score.
    - rank is 1-based: 1 is the top item.
    - off: name of one signal to "switch off". Its value is replaced, for every
      item, by that signal's feed-wide mean (not zero). The mean is computed
      once, from the ORIGINAL values, before any replacement.
    - Ties: higher score first; equal scores are ordered by item id ascending,
      so the result is always the same. Scores are rounded to 9 decimal places
      for sorting only, so float noise (~1e-16) can't break a tie that is a
      real tie on paper. The score returned is not rounded.
    - The input items are never modified.
    """
    if off is not None and off not in weights:
        raise ValueError(f"Unknown signal: {off!r}")

    off_value = signal_mean(items, off) if off is not None else None

    scored = []
    for item in items:
        breakdown = {}
        for signal, weight in weights.items():
            value = off_value if signal == off else item["signals"][signal]
            breakdown[signal] = weight * value
        scored.append({
            "id": item["id"],
            "title": item.get("title", ""),
            "score": sum(breakdown.values()),
            "breakdown": breakdown,
        })

    scored.sort(key=lambda row: (-round(row["score"], SORT_DECIMALS), row["id"]))
    for position, row in enumerate(scored, start=1):
        row["rank"] = position
    return scored
