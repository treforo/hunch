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
