import copy
import pytest
from hand_example import ITEMS, WEIGHTS
from src.config import SIGNALS, WEIGHTS as CONFIG_WEIGHTS
from src.ranker import rank, validate_items
import src.tester as tester
import src.verdicts as verdicts


def items_with(change):
    """Copy of the hand example with one edit applied, for building bad data."""
    items = copy.deepcopy(ITEMS)
    change(items)
    return items


# Each bad dataset is paired with the reason it is bad.
BAD_ITEMS = {
    "empty list": [],
    "duplicate id": items_with(lambda i: i[1].update(id=i[0]["id"])),
    "mixed id types": items_with(lambda i: i[1].update(id=7)),
    "missing signal": items_with(lambda i: i[0]["signals"].pop("s2")),
    "extra signal": items_with(lambda i: i[0]["signals"].update(s4=0.5)),
    "value too high": items_with(lambda i: i[0]["signals"].update(s1=1.4)),
    "value negative": items_with(lambda i: i[0]["signals"].update(s1=-0.1)),
    "value None": items_with(lambda i: i[0]["signals"].update(s1=None)),
    "value a string": items_with(lambda i: i[0]["signals"].update(s1="0.5")),
    "value a bool": items_with(lambda i: i[0]["signals"].update(s1=True)),
    "value NaN": items_with(lambda i: i[0]["signals"].update(s1=float("nan"))),
    "no id": items_with(lambda i: i[0].pop("id")),
    "no signals": items_with(lambda i: i[0].pop("signals")),
}

BAD_WEIGHTS = {
    "empty": {},
    "sum below 1": {"s1": 0.5, "s2": 0.3, "s3": 0.1},
    "sum above 1": {"s1": 0.5, "s2": 0.3, "s3": 0.3},
    "negative weight": {"s1": 0.7, "s2": 0.5, "s3": -0.2},
    "weight a string": {"s1": "0.5", "s2": 0.3, "s3": 0.2},
    "weight NaN": {"s1": float("nan"), "s2": 0.3, "s3": 0.2},
}


def test_hand_example_is_valid():
    validate_items(ITEMS, WEIGHTS)  # should not raise


def test_config_weights_are_valid():
    assert list(CONFIG_WEIGHTS) == SIGNALS
    assert sum(CONFIG_WEIGHTS.values()) == pytest.approx(1.0)


def test_boundary_values_zero_and_one_accepted():
    items = items_with(lambda i: (i[0]["signals"].update(s1=0.0), i[1]["signals"].update(s1=1)))
    validate_items(items, WEIGHTS)


def test_zero_weight_accepted():
    items = [{"id": 1, "title": "", "signals": {"a": 0.5, "b": 0.5}}]
    validate_items(items, {"a": 1.0, "b": 0.0})


@pytest.mark.parametrize("reason", BAD_ITEMS)
def test_bad_items_rejected(reason):
    with pytest.raises(ValueError):
        validate_items(BAD_ITEMS[reason], WEIGHTS)


@pytest.mark.parametrize("reason", BAD_WEIGHTS)
def test_bad_weights_rejected(reason):
    with pytest.raises(ValueError):
        validate_items(ITEMS, BAD_WEIGHTS[reason])


@pytest.mark.parametrize("reason", BAD_ITEMS)
def test_rank_rejects_bad_items(reason):
    with pytest.raises(ValueError):
        rank(BAD_ITEMS[reason], WEIGHTS)


@pytest.mark.parametrize("reason", BAD_WEIGHTS)
def test_rank_rejects_bad_weights(reason):
    with pytest.raises(ValueError):
        rank(ITEMS, BAD_WEIGHTS[reason])


def test_duplicate_ids_no_longer_answer_about_the_wrong_item():
    # Before validation, the tester silently used the first of two items with the same id.
    with pytest.raises(ValueError):
        tester.test_signal(BAD_ITEMS["duplicate id"], WEIGHTS, "A", "s1")


def test_verdicts_reject_bad_data():
    # get_verdict re-ranks to find the strongest driver, so it is covered too.
    bad = BAD_ITEMS["value too high"]
    result = {"item_id": "B", "signal": "s1", "rank_before": 3, "rank_after": 3, "dropped_out": False}
    with pytest.raises(ValueError):
        verdicts.get_verdict("s1", bad[1], result, bad, WEIGHTS)
