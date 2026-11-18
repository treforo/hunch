"""Thin API: GET /feed, POST /guess, and the single page. All logic lives in ranker/tester/verdicts."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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


def feed_rows():
    """The top FEED_SIZE items, with rank, score and per-signal breakdown."""
    return [row for row in rank(ITEMS, WEIGHTS) if row["rank"] <= FEED_SIZE]


@app.get("/")
def page():
    return FileResponse(STATIC / "index.html")


@app.get("/feed")
def feed():
    return {"feed": feed_rows()}


@app.post("/guess")
def guess(body: Guess):
    item = next((i for i in ITEMS if i["id"] == body.item_id), None)
    if item is None:
        raise HTTPException(404, "Unknown item")
    # Guesses are only offered for items in the feed (the engine does not enforce this).
    if body.item_id not in {row["id"] for row in feed_rows()}:
        raise HTTPException(400, "That item is not in the feed")
    if body.guess != OTHER_GUESS and body.guess not in WEIGHTS:
        raise HTTPException(400, "Unknown guess")

    # "other" maps to no signal, so there is nothing to switch off.
    result = None if body.guess == OTHER_GUESS else test_signal(ITEMS, WEIGHTS, item["id"], body.guess)
    verdict = get_verdict(body.guess, item, result, ITEMS, WEIGHTS)
    return {"item_id": item["id"], "guess": body.guess, **verdict}
