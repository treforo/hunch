import pytest
from hand_example import ITEMS, WEIGHTS
import src.tester as tester  # imported as a module so pytest doesn't collect test_signal as a test


def test_hand_example_before_and_after():
    result = tester.test_signal(ITEMS, WEIGHTS, "E", "s1")
    assert result["rank_before"] == 2
    assert result["rank_after"] == 5
    assert result["item_id"] == "E" and result["signal"] == "s1"


def test_dropped_out_when_pushed_past_feed_size():
    # E goes #2 -> #5. With a feed of 2 it was in and is now out.
    assert tester.test_signal(ITEMS, WEIGHTS, "E", "s1", feed_size=2)["dropped_out"] is True
    # With a feed of 5, #5 is still in.
    assert tester.test_signal(ITEMS, WEIGHTS, "E", "s1", feed_size=5)["dropped_out"] is False


def test_rank_exactly_at_feed_size_is_not_dropped():
    # A goes #3 -> #4.
    assert tester.test_signal(ITEMS, WEIGHTS, "A", "s1", feed_size=4)["dropped_out"] is False
    assert tester.test_signal(ITEMS, WEIGHTS, "A", "s1", feed_size=3)["dropped_out"] is True


def test_item_already_outside_feed_is_not_reported_as_dropped():
    # D goes #5 -> #3; with feed_size=2 it was never in the feed.
    assert tester.test_signal(ITEMS, WEIGHTS, "D", "s1", feed_size=2)["dropped_out"] is False


def test_constant_signal_changes_nothing():
    items = [
        {"id": 1, "title": "", "signals": {"a": 0.5, "b": 0.9}},
        {"id": 2, "title": "", "signals": {"a": 0.5, "b": 0.1}},
    ]
    result = tester.test_signal(items, {"a": 0.5, "b": 0.5}, 2, "a")
    assert result["rank_before"] == result["rank_after"] == 2


def test_unknown_item_raises():
    with pytest.raises(ValueError):
        tester.test_signal(ITEMS, WEIGHTS, "Z", "s1")


def test_unknown_signal_raises():
    with pytest.raises(ValueError):
        tester.test_signal(ITEMS, WEIGHTS, "A", "nope")


# ---- several signals off together (hand working in test_ranker.py) ----
# s1 and s2 off gives C, A, D, E, B. So E goes #2 -> #4, B goes #1 -> #5.
def test_signals_hand_example():
    result = tester.test_signals(ITEMS, WEIGHTS, "E", ["s1", "s2"])
    assert result["rank_before"] == 2 and result["rank_after"] == 4
    assert result["signals"] == ["s1", "s2"]
    result = tester.test_signals(ITEMS, WEIGHTS, "B", ["s1", "s2"])
    assert result["rank_before"] == 1 and result["rank_after"] == 5


def test_signals_dropped_out_uses_feed_size():
    # E goes #2 -> #4: with a feed of 3 it drops out, with a feed of 4 it does not.
    assert tester.test_signals(ITEMS, WEIGHTS, "E", ["s1", "s2"], feed_size=3)["dropped_out"] is True
    assert tester.test_signals(ITEMS, WEIGHTS, "E", ["s1", "s2"], feed_size=4)["dropped_out"] is False


def test_signals_with_one_name_matches_test_signal():
    one = tester.test_signal(ITEMS, WEIGHTS, "E", "s1")
    many = tester.test_signals(ITEMS, WEIGHTS, "E", ["s1"])
    assert (one["rank_before"], one["rank_after"]) == (many["rank_before"], many["rank_after"])


def test_signals_empty_list_raises():
    with pytest.raises(ValueError):
        tester.test_signals(ITEMS, WEIGHTS, "E", [])


def test_signals_unknown_signal_raises():
    with pytest.raises(ValueError):
        tester.test_signals(ITEMS, WEIGHTS, "E", ["s1", "nope"])


# ---- already_off: testing inside a feed that already has a signal off ----
# Hand working (test_ranker.py): with s1 off the order is C, B, D, A, E, so E is #5.
# With s1 and s2 both off the order is C, A, D, E, B, so E is #4.
def test_already_off_hand_example():
    result = tester.test_signal(ITEMS, WEIGHTS, "E", "s2", already_off=["s1"])
    assert result["rank_before"] == 5 and result["rank_after"] == 4


def test_already_off_accepts_a_single_name():
    one = tester.test_signal(ITEMS, WEIGHTS, "E", "s2", already_off="s1")
    assert (one["rank_before"], one["rank_after"]) == (5, 4)


def test_switching_off_a_signal_that_is_already_off_raises():
    with pytest.raises(ValueError):
        tester.test_signal(ITEMS, WEIGHTS, "E", "s1", already_off=["s1"])


def test_unknown_already_off_raises():
    with pytest.raises(ValueError):
        tester.test_signal(ITEMS, WEIGHTS, "E", "s2", already_off=["nope"])
