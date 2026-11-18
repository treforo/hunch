import pytest
from hand_example import ITEMS, WEIGHTS
from src.consistency import consistency_check

# Hand example, item E, s1 switched off. Other signals: s2, s3 (worked on paper, see test_ranker.py).
#   Original feed:  s2 -> E #2 to #1 (a rise), s3 -> E #2 to #2.      Both Not supported.
#   With s1 off:    s2 -> E #5 to #4 (a rise), s3 -> E #5 to #5.      Both Not supported.
# So nothing changes.
def test_hand_example_nothing_changes():
    out = consistency_check(ITEMS, WEIGHTS, ITEMS[4], "s1")
    assert [r["signal"] for r in out["rows"]] == ["s2", "s3"]
    for row in out["rows"]:
        assert (row["before"], row["after"], row["changed"]) == ("Not supported", "Not supported", False)
    assert out["any_changed"] is False
    assert out["switched_off"] == "s1" and out["item_id"] == "E"


# Small world worked by hand: weights a .4, b .4, c .2; thresholds tau1 = 2, tau2 = 1.
#   Z (a .8, b .9, c .1)  P (a .9, b .1, c .05)  Q (a .85, b .2, c .75)  R (a .1, b .3, c 0)
#   Means: a .6625, b .375, c .225.
#   Original order Z .70, Q .57, P .41, R .16: Z is #1.
#   Z, b off:        Q .64, P .52, Z .49, R .19  -> #3, fall 2 -> Supported
#   Z, c off:        Z .725, Q .465, P .445, R .205 -> #1, fall 0 -> Not supported
#   a off already:   Z .645, Q .495, R .385, P .315 -> Z is #1
#   a and b off:     Q .565, Z .435, P .425, R .415 -> #2, fall 1 -> Partly supported
#   a and c off:     Z .67, R .43, Q .39, P .35      -> #1, fall 0 -> Not supported
SMALL = [
    {"id": "Z", "title": "", "signals": {"a": 0.8, "b": 0.9, "c": 0.1}},
    {"id": "P", "title": "", "signals": {"a": 0.9, "b": 0.1, "c": 0.05}},
    {"id": "Q", "title": "", "signals": {"a": 0.85, "b": 0.2, "c": 0.75}},
    {"id": "R", "title": "", "signals": {"a": 0.1, "b": 0.3, "c": 0.0}},
]
SMALL_WEIGHTS = {"a": 0.4, "b": 0.4, "c": 0.2}


def test_a_verdict_that_changes_is_flagged():
    out = consistency_check(SMALL, SMALL_WEIGHTS, SMALL[0], "a", tau1=2, tau2=1)
    rows = {r["signal"]: r for r in out["rows"]}
    assert (rows["b"]["before"], rows["b"]["after"], rows["b"]["changed"]) == ("Supported", "Partly supported", True)
    assert (rows["c"]["before"], rows["c"]["after"], rows["c"]["changed"]) == ("Not supported", "Not supported", False)
    assert out["any_changed"] is True


def test_rows_cover_exactly_the_other_signals():
    out = consistency_check(SMALL, SMALL_WEIGHTS, SMALL[0], "b", tau1=2, tau2=1)
    assert [r["signal"] for r in out["rows"]] == ["a", "c"]


def test_changed_agrees_with_before_and_after():
    out = consistency_check(SMALL, SMALL_WEIGHTS, SMALL[0], "a", tau1=2, tau2=1)
    for row in out["rows"]:
        assert row["changed"] == (row["before"] != row["after"])


def test_item_that_falls_out_of_the_feed_is_still_checked():
    # feed of 1: Z is in it originally. With a off Z is still #1, so the check runs without error.
    out = consistency_check(SMALL, SMALL_WEIGHTS, SMALL[0], "a", tau1=2, tau2=1, feed_size=1)
    assert len(out["rows"]) == 2


def test_unknown_signal_raises():
    with pytest.raises(ValueError):
        consistency_check(ITEMS, WEIGHTS, ITEMS[4], "nope")
