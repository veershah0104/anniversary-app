# app/models.py
from pydantic import BaseModel
from typing import Optional

# ... (Keep existing classes like DateIdea and LoveLetterRequest) ...

class LoveLetterRequest(BaseModel):
    mood: str
    length: str = "medium"

# --- NEW CLASS FOR DATE GENERATOR ---
class DateGenRequest(BaseModel):
    duration: str  # e.g. "30 mins", "2 hours"
    vibe: str      # e.g. "Sexy", "Lazy", "Active"

