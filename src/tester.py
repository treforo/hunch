"""Counterfactual tester: would this item still rank as high without a signal?"""

from src.config import FEED_SIZE
from src.ranker import rank


def test_signal(items, weights, item_id, signal, feed_size=FEED_SIZE, already_off=None):
    """Switch `signal` off (feed-wide mean), re-rank, and report where `item_id` lands.

    Returns {"item_id", "signal", "rank_before", "rank_after", "dropped_out"}.
    Ranks are positions among ALL items, so an item can go from #3 to #38.
    dropped_out is True only if the item was in the feed before (rank <= feed_size)
    and is not after (rank > feed_size). Rank exactly equal to feed_size is still in.
    already_off: signals that are ALREADY switched off. "Before" is then the feed with
    those off, and "after" has `signal` off as well. Default: none (the original feed).
    """
    if signal not in weights:
        raise ValueError(f"Unknown signal: {signal!r}")
    before, after, dropped = _compare(items, weights, item_id, [signal], feed_size, already_off)
    return {"item_id": item_id, "signal": signal, "rank_before": before,
            "rank_after": after, "dropped_out": dropped}


def test_signals(items, weights, item_id, signals, feed_size=FEED_SIZE, already_off=None):
    """Like test_signal, but switches several signals off together.

    Used to show what a single-signal test can miss. Returns
    {"item_id", "signals", "rank_before", "rank_after", "dropped_out"}.
    """
    signals = list(signals)
    if not signals:
        raise ValueError("No signals given")
    for signal in signals:
        if signal not in weights:
            raise ValueError(f"Unknown signal: {signal!r}")
    before, after, dropped = _compare(items, weights, item_id, signals, feed_size, already_off)
    return {"item_id": item_id, "signals": signals, "rank_before": before,
            "rank_after": after, "dropped_out": dropped}


def _names(already_off, weights):
    """None -> [], one name -> [name], a list stays a list. Every name must be a known signal."""
    if already_off is None:
        return []
    names = [already_off] if isinstance(already_off, str) else list(already_off)
    for name in names:
        if name not in weights:
            raise ValueError(f"Unknown signal: {name!r}")
    return names


def _compare(items, weights, item_id, off, feed_size, already_off=None):
    base = _names(already_off, weights)
    for signal in off:
        if signal in base:
            raise ValueError(f"{signal!r} is already switched off")
    before = _rank_of(rank(items, weights, off=base), item_id)
    after = _rank_of(rank(items, weights, off=base + list(off)), item_id)
    return before, after, before <= feed_size and after > feed_size


def _rank_of(ranking, item_id):
    for row in ranking:
        if row["id"] == item_id:
            return row["rank"]
    raise ValueError(f"Unknown item id: {item_id!r}")
