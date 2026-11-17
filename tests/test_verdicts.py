import pytest
from hand_example import ITEMS, WEIGHTS
import src.verdicts as verdicts
from src.config import (TAU1, TAU2, SUPPORTED, PARTLY_SUPPORTED, NOT_SUPPORTED, NOT_USED)

S, P, N = SUPPORTED, PARTLY_SUPPORTED, NOT_SUPPORTED
ITEM_A = ITEMS[0]  # id "A"


def fake_result(before, after, dropped, item_id="A", signal="s1"):
    """A hand-built tester result, so the rank numbers are exactly what the case says."""
    return {"item_id": item_id, "signal": signal, "rank_before": before,
            "rank_after": after, "dropped_out": dropped}


# Expected verdicts copied by hand from docs/boundary_cases.md (cases 1-12).
# They are NOT computed by the engine. (case, before, after, dropped_out, expected)
BOUNDARY_CASES = [
    (1, 3, 3, False, N),    # no change
    (2, 3, 4, False, N),    # just below tau2
    (3, 3, 5, False, P),    # tau2 boundary
    (4, 3, 7, False, P),    # just below tau1
    (5, 3, 8, False, S),    # tau1 boundary
    (6, 3, 2, False, N),    # item rises
    (7, 5, 10, False, S),   # tau1, stays in feed
    (8, 6, 10, False, P),   # last place in feed, not dropped
    (9, 6, 11, True, S),    # drop-out and tau1 together
    (10, 9, 11, True, S),   # drop-out overrides tau2
    (11, 10, 11, True, S),  # drop-out overrides tau2
    (12, 3, 38, True, S),   # large fall
]


@pytest.mark.parametrize("case,before,after,dropped,expected", BOUNDARY_CASES)
def test_boundary_cases(case, before, after, dropped, expected):
    out = verdicts.get_verdict("s1", ITEM_A, fake_result(before, after, dropped),
                               ITEMS, WEIGHTS)
    assert out["verdict"] == expected
    assert out["before_rank"] == before and out["after_rank"] == after


def test_case_13_other_is_not_used():
    out = verdicts.get_verdict("other", ITEM_A, None, ITEMS, WEIGHTS)
    assert out["verdict"] == NOT_USED
    assert out["before_rank"] is None and out["after_rank"] is None
    assert out["strongest_driver"] is None
    for signal in WEIGHTS:  # the message lists every signal the feed does use
        assert signal in out["message"]


def test_config_thresholds_are_sensible():
    assert TAU1 > TAU2 >= 1
    assert (TAU1, TAU2) == (5, 2)  # the values in the boundary cases file


def test_thresholds_are_parameters():
    # With tau1=3, tau2=1, a fall of 3 is Supported and a fall of 1 is Partly supported.
    big = verdicts.get_verdict("s1", ITEM_A, fake_result(3, 6, False), ITEMS, WEIGHTS,
                               tau1=3, tau2=1)
    small = verdicts.get_verdict("s1", ITEM_A, fake_result(3, 4, False), ITEMS, WEIGHTS,
                                 tau1=3, tau2=1)
    assert big["verdict"] == S and small["verdict"] == P


def test_messages_contain_the_numbers():
    out = verdicts.get_verdict("s1", ITEM_A, fake_result(3, 38, True), ITEMS, WEIGHTS)
    assert "#3" in out["message"] and "#38" in out["message"]
    assert "drops out" in out["message"]


# ---- strongest driver ----
# Hand example worked on paper (weights 0.5/0.3/0.2). Item E is #2 normally.
#   s1 off -> E is #5 (fall 3)
#   s2 off (s2 mean 0.48) -> E is #1 (a rise)
#   s3 off (s3 mean 0.40) -> E is #2 (no change)
# so the strongest driver of E is s1, #2 -> #5.
ITEM_E = ITEMS[4]


def test_strongest_driver_is_named_with_ranks():
    # Guess s2 (E rises, so Not supported); the real driver is s1.
    out = verdicts.get_verdict("s2", ITEM_E, fake_result(2, 1, False, "E", "s2"),
                               ITEMS, WEIGHTS)
    assert out["verdict"] == N
    assert out["strongest_driver"] == {"signal": "s1", "rank_before": 2, "rank_after": 5}
    assert "s1" in out["message"]


def test_driver_only_for_not_supported():
    for before, after, dropped in [(3, 5, False), (3, 8, False), (10, 11, True)]:
        out = verdicts.get_verdict("s1", ITEM_A, fake_result(before, after, dropped),
                                   ITEMS, WEIGHTS)
        assert out["strongest_driver"] is None


def test_driver_tie_goes_to_first_signal():
    # Items worked by hand: T falls 1 place (#1 -> #2) when either a or b is off.
    items = [
        {"id": "T", "title": "", "signals": {"a": 0.6, "b": 0.6}},
        {"id": "U", "title": "", "signals": {"a": 1.0, "b": 0.0}},
        {"id": "V", "title": "", "signals": {"a": 0.0, "b": 1.0}},
    ]
    t = items[0]
    out = verdicts.get_verdict("b", t, fake_result(1, 2, False, "T", "b"),
                               items, {"a": 0.5, "b": 0.5})
    assert out["strongest_driver"]["signal"] == "a"
    out = verdicts.get_verdict("a", t, fake_result(1, 2, False, "T", "a"),
                               items, {"b": 0.5, "a": 0.5})
    assert out["strongest_driver"]["signal"] == "b"  # order of the weights decides


def test_no_signal_lowers_item_gives_no_driver():
    # Item 1 stays #1 whichever single signal is switched off (worked by hand).
    items = [
        {"id": 1, "title": "", "signals": {"a": 0.5, "b": 0.9}},
        {"id": 2, "title": "", "signals": {"a": 0.5, "b": 0.1}},
    ]
    out = verdicts.get_verdict("a", items[0], fake_result(1, 1, False, 1, "a"),
                               items, {"a": 0.5, "b": 0.5})
    assert out["verdict"] == N
    assert out["strongest_driver"] is None


# ---- errors ----
def test_unknown_guess_raises():
    with pytest.raises(ValueError):
        verdicts.get_verdict("populrity", ITEM_A, fake_result(3, 3, False), ITEMS, WEIGHTS)


def test_mismatched_item_raises():
    with pytest.raises(ValueError):
        verdicts.get_verdict("s1", ITEM_A, fake_result(3, 3, False, item_id="B"),
                             ITEMS, WEIGHTS)


def test_mismatched_signal_raises():
    with pytest.raises(ValueError):
        verdicts.get_verdict("s1", ITEM_A, fake_result(3, 3, False, signal="s2"),
                             ITEMS, WEIGHTS)


def test_works_with_the_real_tester_output():
    # End to end on the hand example: E under s1 goes #2 -> #5, a fall of 3 = Partly supported.
    import src.tester as tester
    result = tester.test_signal(ITEMS, WEIGHTS, "E", "s1")
    out = verdicts.get_verdict("s1", ITEM_E, result, ITEMS, WEIGHTS)
    assert out["verdict"] == P
