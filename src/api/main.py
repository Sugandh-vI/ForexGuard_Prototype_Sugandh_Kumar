from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

from src.models.scorer import ForexGuardScorer

app = FastAPI(title="ForexGuard API")

# ---- Initialize Scorer (loads model once) ----
scorer = ForexGuardScorer()


# ---- Input Schema ----
class Event(BaseModel):
    data: Dict[str, Any]


# ---- Health Check ----
@app.get("/")
def home():
    return {"status": "API is running"}


# ---- Prediction Endpoint ----
@app.post("/score")
def score(event: Event):
    result = scorer.score(event.data)
    return result