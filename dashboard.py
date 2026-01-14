# app/routers/dashboard.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json
import os

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

DB_FILE = "status_db.json"

# --- INITIAL DATA STRUCTURE ---
DEFAULT_DB = {
    "Veer": {"mood": "Missing you", "rating": 5, "last_updated": "Just now"},
    "Rishi": {"mood": "Excited for the weekend", "rating": 8, "last_updated": "Just now"}
}

# --- DATA MODELS ---
class StatusUpdate(BaseModel):
    user: str   # "Veer" or "Rishi"
    mood: str
    rating: int # 1-10

# --- HELPERS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump(DEFAULT_DB, f)
        return DEFAULT_DB
    
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_DB

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- ENDPOINTS ---

@router.get("/weather")
def get_weather(lat: float, lon: float):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        resp = requests.get(url)
        return resp.json()["current_weather"]
    except:
        # Fallback if API fails
        return {"temperature": 0}

@router.get("/statuses")
def get_statuses():
    """Returns the mood board for both people."""
    return load_db()

@router.post("/update")
def update_status(update: StatusUpdate):
    """Updates a specific person's mood."""
    db = load_db()
    
    # Update the specific user
    db[update.user] = {
        "mood": update.mood,
        "rating": update.rating,
        "last_updated": "Just now"
    }
    
    save_db(db)
    return {"status": "Updated", "data": db}