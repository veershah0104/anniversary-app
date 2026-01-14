# app/routers/dates.py
from fastapi import APIRouter
from app.models import DateGenRequest
from app.services.llm import generate_gpt_response
import random

router = APIRouter(
    prefix="/dates",
    tags=["LDR Date Deck"]
)

# --- THE BACKUP BRAIN (Local Database) ---
# Used when Google AI is rate-limited or offline.
BACKUP_DATES = [
    # 30 Mins + Chill/Lazy
    {"duration": "30 Mins", "vibe": "Lazy", "idea": "**Coffee & Crossword**\nFind a crossword online (like NYT mini). Screen share and solve it together while sipping coffee. No rush, just teamwork."},
    {"duration": "30 Mins", "vibe": "Lazy", "idea": "**Spotify DJ Session**\nStart a Spotify 'Jam' session. Take turns playing one song that describes your mood right now. Lie in bed and just listen."},
    
    # 1 Hour + Fun/Active
    {"duration": "1 Hour", "vibe": "Active", "idea": "**The Wikipedia Race**\nStart at the same random Wikipedia page. Race to get to the page for 'Steve Jobs' using only blue links. Loser buys dinner next visit!"},
    {"duration": "1 Hour", "vibe": "Fun", "idea": "**Virtual House Tour**\nGo on Zillow/Rightmove. Pick a random city (e.g., Tokyo) and find the craziest $10M house. Tour it together on screen share and critique the furniture."},
    
    # 2 Hours + Romantic/Sexy
    {"duration": "2 Hours", "vibe": "Romantic", "idea": "**Dinner & A Movie (Synced)**\nOrder the exact same cuisine (e.g., Thai). Start a movie on 'Teleparty' or count down '3, 2, 1' to press play. Eat and watch together."},
    {"duration": "2 Hours", "vibe": "Sexy", "idea": "**The Question Game (Deep)**\nFind a list of '36 Questions to Fall in Love'. Turn off the lights, light a candle, and ask them back and forth. No phones allowed except for the call."},
    
    # Generic Fallbacks (Works for anything)
    {"duration": "Any", "vibe": "Any", "idea": "**PowerPoint Night**\nMake a silly 5-slide presentation on a random topic (e.g., 'Why I would survive a zombie apocalypse') and present it to each other."}
]

def get_backup_date(duration, vibe):
    """Finds a matching date from the local list."""
    # 1. Try to find an exact match
    matches = [d for d in BACKUP_DATES if duration in d["duration"] and vibe in d["vibe"]]
    
    # 2. If no exact match, just pick a random fun one
    if not matches:
        return random.choice(BACKUP_DATES)["idea"]
    
    return random.choice(matches)["idea"]

@router.post("/generate")
def generate_date_idea(request: DateGenRequest):
    """
    Tries AI first. If AI fails (Quota Error), falls back to Local Database.
    """
    system_instruction = (
        "You are an expert dating coach for long-distance couples. "
        "Suggest ONE creative, specific virtual date idea based on the user's constraints. "
        "Format guidelines: \n"
        "1. Start with a catchy **Title** in bold.\n"
        "2. Provide a short, exciting description of what they will do.\n"
        "3. Mention any prep needed.\n"
        "4. Keep it fun and actionable."
        "5. if the choosen vibe is lets say gaming then tell me a game I can play for free online"
        "6. tell me exactly how to get the date done, what platform to use, and any other details."
        "7. If romantic and secy vibe is picked then you can give 18+ date ideas and something lusty, Doesnt always have to be lusty tho it can just be cute and romantic"
        "8. Dont give me the same date idea again and again, try be unique"
        "9. if the same prompt is given again then think of something new maybe a new game or a new version of something that was similar"
    )
    
    user_prompt = f"Plan a date with this Duration: {request.duration}. And this Vibe: {request.vibe}."
    
    # --- 1. TRY AI ---
    ai_result = generate_gpt_response(system_instruction, user_prompt)
    
    # --- 2. CHECK FOR FAILURE ---
    # If the AI returns the error message we programmed in llm.py
    if "AI Error" in ai_result or "Quota exceeded" in ai_result:
        print(f"⚠️ AI Failed/Rate Limited. Using Backup for {request.vibe}...")
        return {"date_idea": get_backup_date(request.duration, request.vibe)}
    
    # --- 3. SUCCESS ---
    return {"date_idea": ai_result}