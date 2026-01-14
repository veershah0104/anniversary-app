# app/routers/ai.py
from fastapi import APIRouter
from app.models import LoveLetterRequest
from app.services.llm import generate_gpt_response
import random

router = APIRouter(
    prefix="/ai",
    tags=["AI Features"]
)

@router.post("/love-letter")
def generate_love_letter(request: LoveLetterRequest):
    """
    Generates a 'Human-sounding' note.
    Customized for Veer -> Rishi/Chokri.
    """
    
    nickname = random.choice(["Rishi", "Chokri"])

    # --- THE MAGIC SAUCE: "Anti-Robot" Instructions ---
    system_instruction = (
        f"You are me who's name is Veer. You are writing a short, sweet note to your girlfriend, {nickname}. "
        "Context: We have been in Long-distance relationship since the past 3 years and My girlfriend will be reading the note, so say something that would make her smile"

        "TONE GUIDELINES (STRICT):"
        "1. Write EXACTLY like a real person who would write short cute letters. Casual, warm, and authentic."
        "2. DO NOT use 'AI words' like: testament, unwavering, profound, tapestry, symphony, beacon, merely, dwelling and dont be too formal"
        "3. Use contractions (use 'I'm' instead of 'I am', 'can't' instead of 'cannot')."
        "4. Focus on small, real feelings (missing her voice, craving food, wanting a hug, missing cuddling, wish I was beside her) rather than 'eternal soul' stuff."
        "5. Be slightly witty or teasing, not overly dramatic."
        "6. the specific feeling is the feeling my girlfriend is feeling NOT ME, so make sure that is shes having a bad day you comfort her"
        "7. Make sure the note is related to the specific feeling and it should sound like I am talking to her."
        "8. DO NOT MAKE A STORY UP SUCH AS I AM HAVING A BAD DAY and stuff like that"
        "9. dont be too cringe and lovey dovey, if shes feeling flirty you can match that energy and talk dirty"

        f" MANDATORY FORMAT:"
        f"- Start with: ' Dear {nickname},'"
    )
    
    user_prompt = f"Write a note about this specific feeling: {request.mood}. Keep it under 80 words."

    ai_result = generate_gpt_response(system_instruction, user_prompt)

    return {
        "status": "success",
        "recipient": nickname,
        "mood_detected": request.mood,
        "ai_message": ai_result
    }