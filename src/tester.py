"""Counterfactual tester: would this item still rank as high without a signal?"""

from src.config import FEED_SIZE
from src.ranker import rank


def test_signal(items, weights, item_id, signal, feed_size=FEED_SIZE):
    """Switch `signal` off (feed-wide mean), re-rank, and report where `item_id` lands.

    Returns {"item_id", "signal", "rank_before", "rank_after", "dropped_out"}.
    Ranks are positions among ALL items, so an item can go from #3 to #38.
    dropped_out is True only if the item was in the feed before (rank <= feed_size)
    and is not after (rank > feed_size). Rank exactly equal to feed_size is still in.
    """
    if signal not in weights:
        raise ValueError(f"Unknown signal: {signal!r}")
    before, after, dropped = _compare(items, weights, item_id, signal, feed_size)
    return {"item_id": item_id, "signal": signal, "rank_before": before,
            "rank_after": after, "dropped_out": dropped}


def test_signals(items, weights, item_id, signals, feed_size=FEED_SIZE):
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
    before, after, dropped = _compare(items, weights, item_id, signals, feed_size)
    return {"item_id": item_id, "signals": signals, "rank_before": before,
            "rank_after": after, "dropped_out": dropped}


def _compare(items, weights, item_id, off, feed_size):
    before = _rank_of(rank(items, weights), item_id)
    after = _rank_of(rank(items, weights, off=off), item_id)
    return before, after, before <= feed_size and after > feed_size


def _rank_of(ranking, item_id):
    for row in ranking:
        if row["id"] == item_id:
            return row["rank"]
    raise ValueError(f"Unknown item id: {item_id!r}")
