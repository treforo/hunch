import pytest
from fastapi.testclient import TestClient
from src.api import app, ITEMS, WEIGHTS
from src.config import FEED_SIZE, NOT_USED
from src.ranker import rank

client = TestClient(app)
PLANTED = [i for i in ITEMS if i["design_role"] in ("single", "social")]  # expected values come from the design table


def test_feed_has_ten_ranked_items_with_breakdown():
    rows = client.get("/feed").json()["feed"]
    assert [r["rank"] for r in rows] == list(range(1, FEED_SIZE + 1))
    for row in rows:
        assert set(row["breakdown"]) == set(WEIGHTS)
        assert sum(row["breakdown"].values()) == pytest.approx(row["score"])
        assert row["title"]


def test_feed_order_matches_the_ranker():
    rows = client.get("/feed").json()["feed"]
    assert [r["id"] for r in rows] == [r["id"] for r in rank(ITEMS, WEIGHTS)][:FEED_SIZE]


@pytest.mark.parametrize("item", PLANTED, ids=lambda i: f"{i['planted_key']}")
@pytest.mark.parametrize("kind", ["correct", "wrong"])
def test_guess_matches_the_design_table(item, kind):
    guess, expected = item["expected"][kind]
    body = client.post("/guess", json={"item_id": item["id"], "guess": guess}).json()
    assert body["verdict"] == expected
    assert body["item_id"] == item["id"] and body["guess"] == guess
    assert set(body) >= {"verdict", "before_rank", "after_rank", "strongest_driver", "message"}


def test_other_guess_is_not_used_with_no_ranks():
    item = PLANTED[0]
    body = client.post("/guess", json={"item_id": item["id"], "guess": "other"}).json()
    assert body["verdict"] == NOT_USED
    assert body["before_rank"] is None and body["after_rank"] is None


def test_unknown_item_is_404():
    assert client.post("/guess", json={"item_id": 9999, "guess": "recency"}).status_code == 404


def test_item_outside_the_feed_is_400():
    outside = next(i for i in ITEMS if i["design_role"] == "background")
    assert client.post("/guess", json={"item_id": outside["id"], "guess": "recency"}).status_code == 400


def test_unknown_guess_is_400():
    assert client.post("/guess", json={"item_id": PLANTED[0]["id"], "guess": "populrity"}).status_code == 400


def test_missing_field_is_422():
    assert client.post("/guess", json={"item_id": PLANTED[0]["id"]}).status_code == 422


def test_page_and_static_files_are_served():
    page = client.get("/")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"]
    assert "Something else (e.g. a friend shared it)" in client.get("/static/app.js").text
    assert client.get("/static/style.css").status_code == 200


# ---- /switch_off ----
from src.config import SUPPORTED  # noqa: E402

T_ITEMS = [i for i in ITEMS if i.get("planted_cause") == "topic_affinity"]
OTHER_PLANTED = [i for i in ITEMS if "planted_cause" in i and i not in T_ITEMS]


def switch(signal="topic_affinity", item_id=None):
    body = {"signal": signal}
    if item_id is not None:
        body["item_id"] = item_id
    return client.post("/switch_off", json=body)


def test_switch_off_topic_removes_the_topic_items_and_keeps_the_other_planted_ones():
    # From the design: the two topic-cause items fall to the all-average level; the other 8 planted
    # items keep their cause and stay in the top 10.
    ids = {r["id"] for r in switch().json()["feed"]}
    assert not ids & {i["id"] for i in T_ITEMS}
    assert {i["id"] for i in OTHER_PLANTED} <= ids


def test_switch_off_returns_ten_rows_in_ranker_order_with_previous_rank():
    body = switch("recency").json()
    expected = [r["id"] for r in rank(ITEMS, WEIGHTS, off="recency")][:FEED_SIZE]
    assert [r["id"] for r in body["feed"]] == expected and body["signal"] == "recency"
    original = {r["id"]: r["rank"] for r in rank(ITEMS, WEIGHTS)}
    for row in body["feed"]:
        assert row["previous_rank"] == original[row["id"]]


def test_feed_is_unchanged_after_a_switch_off():
    before = client.get("/feed").json()
    switch()
    assert client.get("/feed").json() == before  # the server keeps no switched-off state


def test_consistency_is_null_without_an_item_and_present_with_one():
    assert switch().json()["consistency"] is None
    out = switch("topic_affinity", T_ITEMS[0]["id"]).json()["consistency"]
    assert [r["signal"] for r in out["rows"]] == [s for s in WEIGHTS if s != "topic_affinity"]
    assert out["item_id"] == T_ITEMS[0]["id"]


def test_switch_off_errors():
    assert switch("other").status_code == 400
    assert switch("populrity").status_code == 400
    assert switch("recency", 9999).status_code == 404
    outside = next(i for i in ITEMS if i["design_role"] == "background")
    assert switch("recency", outside["id"]).status_code == 400
    assert client.post("/switch_off", json={}).status_code == 422


def test_page_has_the_switch_off_and_reset_controls():
    js = client.get("/static/app.js").text
    assert "Switch this signal off for my feed" in js and "Reset" in js
