"""Thin API: GET /feed, POST /guess, and the single page. All logic lives in ranker/tester/verdicts."""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.consistency import consistency_check
from src.config import FEED_SIZE, OTHER_GUESS
from src.ranker import rank
from src.tester import test_signal
from src.verdicts import get_verdict
from src.world import generate_world

STATIC = Path(__file__).resolve().parent.parent / "static"  # found relative to this file

WORLD = generate_world()  # built once at startup (seed 42); the API holds no other state
ITEMS, WEIGHTS = WORLD["items"], WORLD["weights"]

app = FastAPI(title="Hunch")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class Guess(BaseModel):
    item_id: int
    guess: str


class SwitchOff(BaseModel):
    signal: str
    item_id: Optional[int] = None  # the post the person asked about, for the consistency check


def feed_rows(off=None):
    """The top FEED_SIZE items, with rank, score and per-signal breakdown (optionally with a signal off)."""
    return [row for row in rank(ITEMS, WEIGHTS, off=off) if row["rank"] <= FEED_SIZE]


def feed_item(item_id):
    """The item with this id, if it is in the ORIGINAL feed. 404 if unknown, 400 if outside the feed."""
    item = next((i for i in ITEMS if i["id"] == item_id), None)
    if item is None:
        raise HTTPException(404, "Unknown item")
    # Guesses are only offered for items in the feed (the engine does not enforce this).
    if item_id not in {row["id"] for row in feed_rows()}:
        raise HTTPException(400, "That item is not in the feed")
    return item


@app.get("/")
def page():
    return FileResponse(STATIC / "index.html")


@app.get("/feed")
def feed():
    return {"feed": feed_rows()}


@app.post("/guess")
def guess(body: Guess):
    item = feed_item(body.item_id)
    if body.guess != OTHER_GUESS and body.guess not in WEIGHTS:
        raise HTTPException(400, "Unknown guess")

    # "other" maps to no signal, so there is nothing to switch off.
    result = None if body.guess == OTHER_GUESS else test_signal(ITEMS, WEIGHTS, item["id"], body.guess)
    verdict = get_verdict(body.guess, item, result, ITEMS, WEIGHTS)
    return {"item_id": item["id"], "guess": body.guess, **verdict}


@app.post("/switch_off")
def switch_off(body: SwitchOff):
    """Re-rank the whole feed with one signal at its feed-wide mean. Nothing is stored on the
    server: Reset on the page simply asks GET /feed again."""
    if body.signal not in WEIGHTS:  # "other" maps to no signal, so it cannot be switched off
        raise HTTPException(400, "Unknown signal")
    item = feed_item(body.item_id) if body.item_id is not None else None

    original_rank = {row["id"]: row["rank"] for row in rank(ITEMS, WEIGHTS)}
    rows = [dict(row, previous_rank=original_rank[row["id"]]) for row in feed_rows(off=body.signal)]
    consistency = consistency_check(ITEMS, WEIGHTS, item, body.signal) if item else None
    return {"signal": body.signal, "feed": rows, "consistency": consistency}
