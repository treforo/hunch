import copy
import pytest
from hand_example import (ITEMS, WEIGHTS, SCORES, ORDER, SCORES_S1_OFF, ORDER_S1_OFF)
from src.ranker import rank, signal_mean


def test_hand_example_ranking_and_scores():
    result = rank(ITEMS, WEIGHTS)
    assert [r["id"] for r in result] == ORDER
    for row in result:
        assert row["score"] == pytest.approx(SCORES[row["id"]])


def test_breakdown_sums_to_score():
    for row in rank(ITEMS, WEIGHTS):
        assert sum(row["breakdown"].values()) == pytest.approx(row["score"])


def test_ranks_run_one_to_n_without_gaps():
    assert [r["rank"] for r in rank(ITEMS, WEIGHTS)] == [1, 2, 3, 4, 5]


def test_tie_broken_by_item_id():
    items = [
        {"id": 2, "title": "", "signals": {"s": 0.5}},
        {"id": 1, "title": "", "signals": {"s": 0.5}},
    ]
    assert [r["id"] for r in rank(items, {"s": 1.0})] == [1, 2]


def test_signal_mean_hand_value():
    assert signal_mean(ITEMS, "s1") == pytest.approx(0.6)


def test_off_matches_hand_example():
    result = rank(ITEMS, WEIGHTS, off="s1")
    assert [r["id"] for r in result] == ORDER_S1_OFF
    for row in result:
        assert row["score"] == pytest.approx(SCORES_S1_OFF[row["id"]])


def test_off_uses_mean_not_zero():
    # Replacing a signal by ANY constant for all items shifts every score by the
    # same amount, so the ORDER is the same for mean and zero. The scores differ
    # by weight * mean (0.5 * 0.6 = 0.30 here), so we test the scores.
    off = {r["id"]: r["score"] for r in rank(ITEMS, WEIGHTS, off="s1")}
    zero_items = copy.deepcopy(ITEMS)
    for item in zero_items:
        item["signals"]["s1"] = 0.0
    zero = {r["id"]: r["score"] for r in rank(zero_items, WEIGHTS)}
    for item_id in off:
        assert off[item_id] - zero[item_id] == pytest.approx(0.30)
    assert [r["id"] for r in rank(zero_items, WEIGHTS)] == ORDER_S1_OFF


def test_input_not_modified():
    before = copy.deepcopy(ITEMS)
    rank(ITEMS, WEIGHTS, off="s1")
    assert ITEMS == before


def test_unknown_off_signal_raises():
    with pytest.raises(ValueError):
        rank(ITEMS, WEIGHTS, off="nope")


def test_float_noise_does_not_break_a_tie():
    # 0.3 and 0.30000000000000004 are equal on paper. Without rounding in the
    # sort, item 2 (the larger float) would rank first. With it, the tie goes
    # to the lower id, so item 1 is first.
    items = [
        {"id": 1, "title": "", "signals": {"s": 0.3}},
        {"id": 2, "title": "", "signals": {"s": 0.1 + 0.2}},
    ]
    assert 0.1 + 0.2 != 0.3  # the noise really exists
    assert [r["id"] for r in rank(items, {"s": 1.0})] == [1, 2]


def test_real_difference_still_orders_correctly():
    items = [
        {"id": 1, "title": "", "signals": {"s": 0.30}},
        {"id": 2, "title": "", "signals": {"s": 0.31}},
    ]
    assert [r["id"] for r in rank(items, {"s": 1.0})] == [2, 1]


# ---- several signals off together ----
# Hand working (weights 0.5 / 0.3 / 0.2). Means: s1 = 0.6, s2 = (0.2+0.9+0.5+0.7+0.1)/5 = 0.48.
# With s1 and s2 both replaced, they add 0.5*0.6 + 0.3*0.48 = 0.30 + 0.144 = 0.444 to everyone,
# so each score is 0.444 + 0.2*s3:
#   A: 0.444 + 0.10 = 0.544   B: 0.444 + 0.02 = 0.464   C: 0.444 + 0.18 = 0.624
#   D: 0.444 + 0.06 = 0.504   E: 0.444 + 0.04 = 0.484
# Ranking: C, A, D, E, B
def test_two_signals_off_matches_hand_example():
    result = rank(ITEMS, WEIGHTS, off=["s1", "s2"])
    assert [r["id"] for r in result] == ["C", "A", "D", "E", "B"]
    expected = {"A": 0.544, "B": 0.464, "C": 0.624, "D": 0.504, "E": 0.484}
    for row in result:
        assert row["score"] == pytest.approx(expected[row["id"]])


def test_list_of_one_matches_a_plain_name():
    assert rank(ITEMS, WEIGHTS, off=["s1"]) == rank(ITEMS, WEIGHTS, off="s1")


def test_none_and_empty_list_switch_nothing_off():
    assert rank(ITEMS, WEIGHTS, off=[]) == rank(ITEMS, WEIGHTS)


def test_repeated_name_in_list_is_harmless():
    assert rank(ITEMS, WEIGHTS, off=["s1", "s1"]) == rank(ITEMS, WEIGHTS, off="s1")


def test_unknown_name_in_list_raises():
    with pytest.raises(ValueError):
        rank(ITEMS, WEIGHTS, off=["s1", "nope"])
