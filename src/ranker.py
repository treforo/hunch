"""Ranker: score = weighted sum of signals, sorted high to low.

An item is a dict:  {"id": 7, "title": "...", "signals": {"topic_affinity": 0.8, ...}}
Signal values are floats from 0 to 1.
"""

SORT_DECIMALS = 9  # scores closer than this are treated as equal when sorting


def validate_items(items, weights, tolerance=1e-9):
    """Raise ValueError if the data could make a ranking silently wrong.
    rank() calls this every time, so tester.py and verdicts.py are covered too.
    Checks: weights are non-empty, numeric, not negative and sum to 1; there is
    at least one item; every item has an id and signals; ids are unique and all
    the same type (so sorting by id works); each item has exactly the weighted
    signals; every signal value is a number from 0 to 1.
    """
    if not weights:
        raise ValueError("No weights")
    for signal, weight in weights.items():
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not weight >= 0:
            raise ValueError(f"Weight for {signal!r} must be a number that is not negative")
    if abs(sum(weights.values()) - 1.0) > tolerance:
        raise ValueError(f"Weights sum to {sum(weights.values())}, expected 1.0")

    if not items:
        raise ValueError("No items")

    seen_ids = set()
    id_type = None
    for item in items:
        if "id" not in item or "signals" not in item:
            raise ValueError("Every item needs an 'id' and 'signals'")
        item_id = item["id"]

        if id_type is None:
            id_type = type(item_id)
        elif type(item_id) is not id_type:
            raise ValueError("Item ids must all be the same type")
        if item_id in seen_ids:
            raise ValueError(f"Duplicate item id: {item_id!r}")
        seen_ids.add(item_id)

        if set(item["signals"]) != set(weights):
            raise ValueError(f"Item {item_id!r} signals do not match the weights")
        for signal, value in item["signals"].items():
            # "not 0 <= value <= 1" also rejects NaN, which fails every comparison
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or not 0 <= value <= 1:
                raise ValueError(f"Item {item_id!r}: {signal} = {value!r} is not a number from 0 to 1")


def signal_mean(items, signal):
    """Feed-wide mean of one signal, over ALL items passed in (not just the top 10)."""
    return sum(item["signals"][signal] for item in items) / len(items)


def rank(items, weights, off=None):
    """Return the items sorted by score (highest first), each as a new dict:
        {"id", "title", "score", "rank", "breakdown"}
    - breakdown maps each signal to its weighted contribution (weight * value),
      so the contributions add up to the score.
    - rank is 1-based: 1 is the top item.
    - off: a signal name, or a list of names, to "switch off". Each signal's value
      is replaced, for every item, by that signal's own feed-wide mean (not
      zero). Each mean is computed from the ORIGINAL values, before any
      replacement. None or an empty list switches nothing off.
    - Ties: higher score first; equal scores are ordered by item id ascending,
      so the result is always the same. Scores are rounded to 9 decimal places
      for sorting only, so float noise (~1e-16) can't break a tie that is a
      real tie on paper. The score returned is not rounded.
    - The input items are never modified.
    - Raises ValueError for bad data (see validate_items) or an unknown `off`.
    """
    validate_items(items, weights)
    off_signals = _as_list(off)
    for signal in off_signals:
        if signal not in weights:
            raise ValueError(f"Unknown signal: {signal!r}")

    # One mean per switched-off signal, all taken from the original values.
    off_values = {signal: signal_mean(items, signal) for signal in off_signals}

    scored = []
    for item in items:
        breakdown = {}
        for signal, weight in weights.items():
            value = off_values[signal] if signal in off_values else item["signals"][signal]
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


def _as_list(off):
    """None -> [], "popularity" -> ["popularity"], a list stays a list."""
    if off is None:
        return []
    if isinstance(off, str):
        return [off]
    return list(off)
