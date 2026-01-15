# app_ui.py
import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
import math
import json
import os
import random
import requests # Only for Weather
from groq import Groq
from streamlit_gsheets import GSheetsConnection

# --- CONFIG ---
NEXT_MEET_DATE = datetime(2026, 5, 20) 
MY_LAT, MY_LON = 22.2988, 114.1722   # Hong Kong
HER_LAT, HER_LON = 51.2955, 1.0586   # Canterbury
MY_CITY = "Hong Kong"
HER_CITY = "Canterbury"

# --- 🧠 THE AI BRAIN (Embedded & Robust) ---
def generate_groq_response(system_prompt, user_prompt):
    # Get API Key securely
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return "⚠️ Error: Missing Groq API Key. Please add it to Streamlit Secrets."

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- 📸 IMAGE UPLOAD ENGINE (ImgBB) ---
def upload_to_imgbb(image_file):
    """Uploads binary image data to ImgBB and returns the URL."""
    api_key = st.secrets.get("IMGBB_API_KEY")
    if not api_key:
        st.error("⚠️ Missing ImgBB API Key in Secrets.")
        return None

    try:
        payload = {"key": api_key}
        # ImgBB expects the file to be sent as 'image'
        files = {"image": image_file.getvalue()}
        response = requests.post("https://api.imgbb.com/1/upload", params=payload, files=files)
        data = response.json()
        return data["data"]["url"]
    except Exception as e:
        st.error(f"Upload Failed: {e}")
        return None

# --- ☁️ GOOGLE SHEETS DATABASE (The New Sync Logic) ---
def get_db_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_db():
    """Reads data from Google Sheet"""
    try:
        conn = get_db_connection()
        # Read the sheet as a DataFrame (cols: User, Mood, Rating, Photo)
        df = conn.read(worksheet="Sheet1", usecols=[0, 1, 2, 3], ttl=0)
        
        # Convert to our dictionary format
        db = {}
        for _, row in df.iterrows():
            # Handle potential empty rows
            if pd.notna(row['User']):
                # FIX: Force capitalization (veer -> Veer) so it matches the UI keys
                user_key = str(row['User']).strip().capitalize()
                
                db[user_key] = {
                    "mood": row['Mood'],
                    "rating": int(row['Rating']) if pd.notna(row['Rating']) else 5,
                    "photo": row['Photo'] if pd.notna(row['Photo']) else None
                }
        return db
    except Exception as e:
        # Fallback if sheet fails so app doesn't crash
        return {"Veer": {"mood": "Offline", "rating": 5, "photo": None}, "Rishi": {"mood": "Offline", "rating": 5, "photo": None}}

def save_db(user, mood, rating, photo=None):
    """Writes specific user update to Google Sheet"""
    try:
        conn = get_db_connection()
        df = conn.read(worksheet="Sheet1", usecols=[0, 1, 2, 3], ttl=0)
        
        # Identify Row Index (Veer=0, Rishi=1)
        # We capitalize the input user to ensure we find the right match if needed
        idx = 0 if user.capitalize() == "Veer" else 1
        
        # Update values
        df.at[idx, "Mood"] = mood
        df.at[idx, "Rating"] = rating
        if photo:
            df.at[idx, "Photo"] = photo
            
        # Push back to Google
        conn.update(worksheet="Sheet1", data=df)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

# --- AI WRAPPERS (With Your Custom Prompts) ---
def get_ai_letter(mood):
    nickname = random.choice(["Rishi", "Chokri"])
    
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
    
    user_prompt = f"Write a note about this specific feeling: {mood}. Keep it under 80 words."

    return generate_groq_response(system_instruction, user_prompt)

def get_ai_date(duration, vibe):
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
        "7. If romantic and sexy vibe is picked then you can give 18+ date ideas and something lusty, Doesnt always have to be lusty tho it can just be cute and romantic"
        "8. Dont give me the same date idea again and again, try be unique"
        "9. if the same prompt is given again then think of something new maybe a new game or a new version of something that was similar"
    )
    
    user_prompt = f"Plan a date with this Duration: {duration}. And this Vibe: {vibe}."
    
    # 1. Try AI
    ai_result = generate_groq_response(system_instruction, user_prompt)
    
    # 2. Check for Failure
    if "AI Error" in ai_result or "Quota exceeded" in ai_result:
        # Fallback Logic
        return get_backup_date(duration, vibe)
    
    return ai_result

# --- BACKUP DATE SYSTEM ---
BACKUP_DATES = [
    {"duration": "30 Mins", "vibe": "Lazy", "idea": "**Coffee & Crossword**\nFind a crossword online (like NYT mini). Screen share and solve it together while sipping coffee. No rush, just teamwork."},
    {"duration": "1 Hour", "vibe": "Active", "idea": "**The Wikipedia Race**\nStart at the same random Wikipedia page. Race to get to the page for 'Steve Jobs' using only blue links. Loser buys dinner next visit!"},
    {"duration": "2 Hours", "vibe": "Romantic", "idea": "**Dinner & A Movie (Synced)**\nOrder the exact same cuisine (e.g., Thai). Start a movie on 'Teleparty' or count down '3, 2, 1' to press play. Eat and watch together."},
    {"duration": "Any", "vibe": "Any", "idea": "**PowerPoint Night**\nMake a silly 5-slide presentation on a random topic (e.g., 'Why I would survive a zombie apocalypse') and present it to each other."}
]

def get_backup_date(duration, vibe):
    matches = [d for d in BACKUP_DATES if duration in d["duration"] and vibe in d["vibe"]]
    if not matches:
        return random.choice(BACKUP_DATES)["idea"]
    return random.choice(matches)["idea"]

# --- APP SETUP ---
st.set_page_config(page_title="LDR Dashboard", page_icon="❤️", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 VISUAL STYLING (CSS FIXED) ---
st.markdown("""
<style>
    /* 1. Main Background -> Dark */
    .stApp { background-color: #0E1117; }
    
    /* 2. General Text -> White (For dashboard) */
    h1, h2, h3, p, div, span, label { color: #E0E0E0 !important; }
    
    /* 3. DARK BUTTON STYLE */
    div.stButton > button {
        background-color: #161B22 !important; /* Dark Github-like grey */
        color: white !important;
        border: 1px solid #30363D !important;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px;
        transition: all 0.2s ease-in-out;
        width: 100%; /* Full width */
        margin-bottom: 10px;
    }
    div.stButton > button:hover {
        border-color: #8B949E !important; 
        background-color: #21262D !important; 
        color: #58A6FF !important; 
    }

    /* 4. INPUT BOXES (Fix for Date Planner) */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: white !important;
    }
    .stSelectbox label, .stTextInput label { color: #E0E0E0 !important; }

    /* 5. SYNC CARDS */
    .mood-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #333;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .user-name { font-size: 24px; font-weight: bold; color: #FFF !important; margin-bottom: 5px;}
    .mood-text { font-size: 18px; color: #DDD !important; font-style: italic; margin: 10px 0; }
    .rating-box { font-size: 16px; font-weight: bold; padding: 5px 15px; border-radius: 20px; color: #000 !important; display: inline-block; margin-top: 10px;}

    /* 6. INFO CARDS */
    .info-card {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
        color: white !important;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .card-title { font-size: 14px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 5px; color: #FFF !important; }
    .card-value { font-size: 28px; font-weight: 800; margin-top: 5px; color: #FFF !important; }
    .card-sub { font-size: 12px; opacity: 0.8; color: #EEE !important; }

    .dist-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .time-card { background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); }
    .weather-card { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }

    /* 7. LOVE LETTER (The "White on White" Fix) */
    .love-note {
        background-color: #fff9c4 !important;
        padding: 25px;
        border-radius: 2px;
        box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
        font-family: 'Courier New', Courier, monospace;
        font-size: 18px;
        line-height: 1.6;
        transform: rotate(-1deg);
        border-left: 5px solid #ffeb3b;
        margin-top: 20px;
    }
    /* Explicitly force BLACK text inside the note */
    .love-note, .love-note div, .love-note p, .love-note span {
        color: #2c2c2c !important; 
    }
    .note-signature { 
        text-align: right; 
        font-weight: bold; 
        margin-top: 15px; 
        color: #d32f2f !important; /* Red Signature */
    }

    /* 8. DATE TICKET */
    .date-card {
        background-color: #262730;
        border: 2px dashed #FF4B4B;
        border-radius: 12px;
        padding: 25px;
        color: #EEE !important;
        margin-top: 15px;
        text-align: center;
        font-size: 18px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# --- INTERNAL FUNCTIONS ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return int(R * c)

def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        resp = requests.get(url, timeout=5)
        return resp.json()["current_weather"]
    except:
        return {"temperature": "--"}

def get_rating_color(rating):
    if rating >= 8: return "#69F0AE" 
    if rating >= 4: return "#FFD740" 
    return "#FF5252" 

# --- MAIN APP UI ---
st.title("❤️ Relationship Sync")

# 1. LOAD DATA (FROM GOOGLE SHEETS)
db = load_db()
w_my = get_weather(MY_LAT, MY_LON)
w_her = get_weather(HER_LAT, HER_LON)

# 2. SYNC CARDS
c1, c2 = st.columns(2)
with c1:
    veer = db.get("Veer", {})
    col = get_rating_color(veer.get('rating', 5))
    st.markdown(f"""
<div class="mood-card">
<div class="user-name">🧑‍💻 Veer</div>
<div class="mood-text">"{veer.get('mood', 'Loading...')}"</div>
<div class="rating-box" style="background-color: {col};">Feels: {veer.get('rating', 5)}/10</div>
</div>
""", unsafe_allow_html=True)
    
with c2:
    rishi = db.get("Rishi", {})
    col = get_rating_color(rishi.get('rating', 5))
    st.markdown(f"""
<div class="mood-card">
<div class="user-name">👩‍❤️‍👨 Rishi</div>
<div class="mood-text">"{rishi.get('mood', 'Loading...')}"</div>
<div class="rating-box" style="background-color: {col};">Feels: {rishi.get('rating', 5)}/10</div>
</div>
""", unsafe_allow_html=True)

# 3. UPDATE FORM (UPDATED TO USE GOOGLE SAVE_DB)
with st.expander("📝 Update Status"):
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        who = st.radio("User", ["Veer", "Rishi"], horizontal=True, label_visibility="collapsed")
        rate = st.slider("Rating", 1, 10, 8)
    with col_u2:
        msg = st.text_input("Mood", placeholder="Status update...")
        if st.button("Sync 🔄", use_container_width=True):
            if msg:
                with st.spinner("Syncing to Cloud..."):
                    # Call the new Google Sheets save function
                    success = save_db(who, msg, rate)
                    if success:
                        st.success("Updated!")
                        st.rerun()

st.divider()

# 4. MAP & INFO
st.subheader("🌍 Live Connection")
col_map, col_info = st.columns([2.5, 1])

with col_map:
    map_df = pd.DataFrame({"start_lat": [MY_LAT], "start_lon": [MY_LON], "end_lat": [HER_LAT], "end_lon": [HER_LON]})
    layer = pdk.Layer(
        "ArcLayer", data=map_df,
        get_source_position=["start_lon", "start_lat"], get_target_position=["end_lon", "end_lat"],
        get_width=6, get_source_color=[100, 255, 218, 160], get_target_color=[255, 64, 129, 160],
        get_tilt=15
    )
    view = pdk.ViewState(latitude=(MY_LAT+HER_LAT)/2, longitude=(MY_LON+HER_LON)/2, zoom=1, pitch=35)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, map_style="dark", height=400))

with col_info:
    dist_km = calculate_distance(MY_LAT, MY_LON, HER_LAT, HER_LON)
    st.markdown(f"""
<div class="info-card dist-card">
<div class="card-title">Distance Apart</div>
<div class="card-value">{dist_km:,} km</div>
<div class="card-sub">{MY_CITY} ↔ {HER_CITY}</div>
</div>
""", unsafe_allow_html=True)

    delta = NEXT_MEET_DATE - datetime.now()
    st.markdown(f"""
<div class="info-card time-card">
<div class="card-title">Next Meeting</div>
<div class="card-value">{delta.days} Days</div>
<div class="card-sub">Until we hug again</div>
</div>
""", unsafe_allow_html=True)

    t1 = w_my.get('temperature', '--')
    t2 = w_her.get('temperature', '--')
    st.markdown(f"""
<div class="info-card weather-card">
<div class="card-title">Current Weather</div>
<div style="display: flex; justify-content: space-around; margin-top: 10px;">
<div><div style="font-size: 20px; font-weight:bold; color:white;">{t1}°C</div><div style="font-size: 10px; color:white;">{MY_CITY}</div></div>
<div style="border-left: 1px solid rgba(255,255,255,0.3);"></div>
<div><div style="font-size: 20px; font-weight:bold; color:white;">{t2}°C</div><div style="font-size: 10px; color:white;">{HER_CITY}</div></div>
</div>
</div>
""", unsafe_allow_html=True)

# 5. FEATURES TABS
st.divider()
tab1, tab2, tab3 = st.tabs(["📸 Locket", "💌 Anytime Love Letter", "🎲 AI Date Planner"])

# --- TAB 1: LOCKET (NEW) ---
with tab1:
    st.markdown("### 📸 Live Locket")
    
    # Display Existing Photos
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.write("**Veer's View**")
        v_photo = db.get("Veer", {}).get("photo")
        if v_photo: st.image(v_photo, use_container_width=True)
        else: st.info("No photo yet")
    with col_p2:
        st.write("**Rishi's View**")
        r_photo = db.get("Rishi", {}).get("photo")
        if r_photo: st.image(r_photo, use_container_width=True)
        else: st.info("No photo yet")
        
    st.divider()
    
    # Upload New Photo
    st.write("#### 🤳 Update Your Locket")
    photo_input = st.camera_input("Take a pic", label_visibility="collapsed")
    
    if photo_input:
        # Selector for who is posting (Default to Veer for now, or add radio)
        poster = st.radio("Posting as:", ["Veer", "Rishi"], horizontal=True, key="poster_radio")
        
        if st.button("Post to Locket 📨", use_container_width=True):
            with st.spinner("Uploading to cloud..."):
                # 1. Upload to ImgBB
                img_url = upload_to_imgbb(photo_input)
                
                if img_url:
                    # 2. Save URL to Google Sheet (re-using save_db logic but only updating photo)
                    # We need to fetch current mood/rating to avoid overwriting them with blanks
                    current_data = db.get(poster, {})
                    curr_mood = current_data.get("mood", "Updated Photo")
                    curr_rate = current_data.get("rating", 5)
                    
                    success = save_db(poster, curr_mood, curr_rate, photo=img_url)
                    if success:
                        st.success("Posted!")
                        st.rerun()

# --- TAB 2: LOVE LETTER ---
with tab2:
    st.markdown("### ✨ Need a little love?")
    st.write("Pick a vibe:")
    
    vibe = None
    if st.button("🥺 Missing You", use_container_width=True): vibe = "Missing you deeply"
    if st.button("🥰 Just Because", use_container_width=True): vibe = "Just wanted to say I love you"
    if st.button("🌧️ Bad Day", use_container_width=True): vibe = "She had a hard day, comfort her"
    if st.button("🔥 Flirty", use_container_width=True): vibe = "Feeling flirty and romantic"

    if vibe:
        with st.spinner("Penning a note..."):
            try:
                content = get_ai_letter(vibe)
                st.markdown(f"""
<div class="love-note">
{content.replace(chr(10), '<br>')}
<div class="note-signature">- Forever yours, Veer</div>
</div>
""", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Groq Error: {e}")

# --- TAB 3: DATE PLANNER ---
with tab3:
    st.header("The Teleport Deck 🎲")
    st.write("Let the AI plan your perfect virtual date.")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_duration = st.selectbox("How much time?", ["30 Mins", "1 Hour", "2 Hours", "All Night"])
    with col_d2:
        date_vibe = st.selectbox("Vibe?", ["Lazy", "Active", "Romantic & Sexy", "Deep Talk", "Gaming"])
    
    if st.button("Plan Our Date 🎟️", use_container_width=True):
        with st.spinner("Thinking..."):
            try:
                idea = get_ai_date(date_duration, date_vibe)
                st.markdown(f"""
<div class="date-card">
{idea.replace(chr(10), '<br>')}
</div>
""", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Groq Error: {e}")
