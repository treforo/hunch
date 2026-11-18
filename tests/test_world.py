import copy
import random
import pytest
from src.config import SEED, WEIGHTS, SUPPORTED, NOT_SUPPORTED, NOT_USED, OTHER_GUESS, FEED_SIZE
from src.ranker import rank, signal_mean
from src.world import (generate_world, check_design, PLANTED_DESIGN, CAUSE_VALUE, PAIR_VALUE,
                       SOCIAL_OFFSET, USER_PROFILE)

WORLD = generate_world()
ITEMS = WORLD["items"]


def role(name):
    return [i for i in ITEMS if i["design_role"] == name]


def test_same_seed_gives_the_same_world():
    assert generate_world(SEED) == generate_world(SEED)


def test_another_seed_gives_a_different_world():
    other = generate_world(0)   # seed 0 satisfies the design checks
    assert other["items"] != ITEMS


def test_generator_does_not_touch_global_random_state():
    random.seed(123)
    expected = random.random()
    random.seed(123)
    generate_world()
    assert random.random() == expected


def test_some_seeds_fail_the_design_check():
    # Known limit: the construction only holds for some seeds (seed 1 puts a background item
    # at or above the average score). Seed 42, the one used, is checked above.
    with pytest.raises(ValueError):
        generate_world(1)


def test_forty_items_with_unique_ids_one_to_forty():
    assert sorted(i["id"] for i in ITEMS) == list(range(1, 41))


def test_role_counts():
    assert len(role("single")) == 8
    assert len(role("social")) == 1
    assert len(role("redundant_pair")) == 1
    assert len(role("filler")) == 8
    assert len(role("background")) == 22
    assert len([i for i in ITEMS if "planted_cause" in i]) == 10


def test_user_profile_present():
    assert WORLD["user"] == USER_PROFILE and USER_PROFILE["name"]


def test_means_in_world_match_the_data():
    for s in WEIGHTS:
        assert WORLD["means"][s] == pytest.approx(signal_mean(ITEMS, s), abs=1e-12)


def test_single_cause_items_have_one_high_signal_and_four_at_the_mean():
    for item in role("single"):
        cause = item["planted_cause"]
        assert cause in WEIGHTS
        assert item["signals"][cause] == CAUSE_VALUE
        for s in WEIGHTS:
            if s != cause:
                assert item["signals"][s] == pytest.approx(signal_mean(ITEMS, s), abs=1e-9)


def test_cause_counts_match_the_design():
    causes = sorted(i["planted_cause"] for i in role("single"))
    assert causes == ["followed_account"] * 2 + ["popularity"] * 2 + ["recency"] \
        + ["similar_users"] + ["topic_affinity"] * 2


def test_redundant_pair_item_has_both_signals_high():
    rp = role("redundant_pair")[0]
    assert rp["planted_cause"] == "popularity+similar_users"
    assert rp["signals"]["popularity"] == PAIR_VALUE and rp["signals"]["similar_users"] == PAIR_VALUE
    for s in ("topic_affinity", "followed_account", "recency"):
        assert rp["signals"][s] == pytest.approx(signal_mean(ITEMS, s), abs=1e-9)


def test_social_item_is_diffuse_and_maps_to_no_signal():
    soc = role("social")[0]
    assert "friend" in soc["planted_cause"] and soc["planted_cause"] not in WEIGHTS
    for s in WEIGHTS:  # slightly above the mean on every signal, none dominant
        assert soc["signals"][s] - signal_mean(ITEMS, s) == pytest.approx(SOCIAL_OFFSET, abs=1e-9)


def test_the_ten_planted_items_are_exactly_the_feed():
    top = {r["id"] for r in rank(ITEMS, WEIGHTS) if r["rank"] <= FEED_SIZE}
    assert top == {i["id"] for i in ITEMS if "planted_cause" in i}


def test_all_signal_values_are_between_zero_and_one():
    for item in ITEMS:
        for value in item["signals"].values():
            assert 0 <= value <= 1


# ---- the hand-written design table ----
def test_design_table_labels_and_guesses():
    for spec in PLANTED_DESIGN:
        if spec["role"] == "redundant_pair":
            assert set(spec["pair_truth"]) == set(spec["causes"])
            assert set(spec["pair_truth"].values()) == {SUPPORTED}
            continue
        guess, verdict = spec["correct"]
        wrong, wrong_verdict = spec["wrong"]
        assert wrong_verdict == NOT_SUPPORTED
        assert wrong in WEIGHTS and wrong not in spec["causes"]
        if spec["role"] == "single":
            assert guess == spec["causes"][0] and verdict == SUPPORTED
        else:
            assert guess == OTHER_GUESS and verdict == NOT_USED


def test_items_carry_their_expected_values():
    for item in ITEMS:
        if "planted_cause" in item:
            assert "expected" in item
        else:
            assert "expected" not in item


# ---- check_design catches a broken world ----
def broken(change):
    world = copy.deepcopy(WORLD)
    change(world["items"])
    return world


def test_check_design_accepts_the_real_world():
    check_design(WORLD)


def test_check_design_rejects_a_non_cause_signal_off_the_mean():
    def change(items):
        single = next(i for i in items if i["design_role"] == "single")
        cause = single["planted_cause"]
        other = next(s for s in WEIGHTS if s != cause)
        single["signals"][other] += 0.1
    with pytest.raises(ValueError):
        check_design(broken(change))


def test_check_design_rejects_a_background_item_that_outranks_the_planted_ones():
    def change(items):
        bg = next(i for i in items if i["design_role"] == "background")
        bg["signals"] = {s: 1.0 for s in WEIGHTS}
    with pytest.raises(ValueError):
        check_design(broken(change))
