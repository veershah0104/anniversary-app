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

# --- 🧠 THE AI BRAIN (Directly inside the file) ---
# This fixes the "NameError" completely.
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

# --- CONFIG ---
NEXT_MEET_DATE = datetime(2026, 5, 20) 
STATUS_FILE = "status_db.json"

# Coordinates (Hong Kong -> Canterbury)
MY_LAT, MY_LON = 22.2988, 114.1722   # Hong Kong
HER_LAT, HER_LON = 51.2955, 1.0586   # Canterbury
MY_CITY = "Hong Kong"
HER_CITY = "Canterbury"

st.set_page_config(page_title="LDR Dashboard", page_icon="❤️", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 VISUAL STYLING (CSS FIXED) ---
st.markdown("""
<style>
    /* 1. Main Background -> Dark */
    .stApp { background-color: #0E1117; }
    
    /* 2. General Text -> White (For dashboard) */
    h1, h2, h3, p, div, span, label { color: #E0E0E0 !important; }
    
    /* 3. INPUT BOXES (Fix for Date Planner) */
    /* This ensures dropdown text is readable */
    .stSelectbox div[data-baseweb="select"] {
        color: white !important;
        background-color: #262730 !important;
    }
    .stSelectbox label { font-size: 1.2rem; font-weight: bold; }

    /* 4. SYNC CARDS */
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

    /* 5. INFO CARDS */
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

    /* 6. LOVE LETTER (The "White on White" Fix) */
    /* We explicitly force BLACK text inside the yellow note */
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
    /* This rule overrides the global white text rule for the note content */
    .love-note, .love-note div, .love-note p, .love-note span {
        color: #2c2c2c !important; 
    }
    .note-signature { 
        text-align: right; 
        font-weight: bold; 
        margin-top: 15px; 
        color: #d32f2f !important; /* Red Signature */
    }

    /* 7. DATE TICKET */
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

# --- DATABASE LOGIC ---
DEFAULT_DB = {
    "Veer": {"mood": "Missing you", "rating": 5},
    "Rishi": {"mood": "Excited for the weekend", "rating": 8}
}

def load_db():
    if not os.path.exists(STATUS_FILE):
        return DEFAULT_DB
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_DB

def save_db(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

# --- AI WRAPPERS ---
def get_ai_letter(mood):
    nickname = random.choice(["Rishi", "Chokri"])
    prompt = (
        f"You are Veer writing to {nickname}. LDR 3 years. "
        "Write a short, casual, authentic note. No formal AI words. "
        "Use contractions (I'm, can't). Be sweet or teasing. "
        f"Topic: {mood}. End with '- Forever yours, Veer'"
    )
    return generate_groq_response(prompt, "Write the note.")

def get_ai_date(duration, vibe):
    prompt = (
        "Suggest ONE specific virtual date idea. "
        "Format: **Title**\nDescription. "
        f"Constraints: {duration}, {vibe}."
    )
    return generate_groq_response(prompt, "Plan the date.")

def get_rating_color(rating):
    if rating >= 8: return "#69F0AE" 
    if rating >= 4: return "#FFD740" 
    return "#FF5252" 

# --- MAIN APP UI ---

st.title("❤️ Relationship Sync")

# 1. LOAD DATA
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
<div class="mood-text">"{veer.get('mood')}"</div>
<div class="rating-box" style="background-color: {col};">Feels: {veer.get('rating')}/10</div>
</div>
""", unsafe_allow_html=True)
    
with c2:
    rishi = db.get("Rishi", {})
    col = get_rating_color(rishi.get('rating', 5))
    st.markdown(f"""
<div class="mood-card">
<div class="user-name">👩‍❤️‍👨 Rishi</div>
<div class="mood-text">"{rishi.get('mood')}"</div>
<div class="rating-box" style="background-color: {col};">Feels: {rishi.get('rating')}/10</div>
</div>
""", unsafe_allow_html=True)

# 3. UPDATE FORM
with st.expander("📝 Update Status"):
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        who = st.radio("User", ["Veer", "Rishi"], horizontal=True, label_visibility="collapsed")
        rate = st.slider("Rating", 1, 10, 8)
    with col_u2:
        msg = st.text_input("Mood", placeholder="Status update...")
        if st.button("Sync 🔄", use_container_width=True):
            if msg:
                db[who] = {"mood": msg, "rating": rate}
                save_db(db)
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
tab1, tab2 = st.tabs(["💌 Anytime Love Letter", "🎲 AI Date Planner"])

with tab1:
    st.markdown("### ✨ Need a little love?")
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        st.write("Pick a vibe:")
        vibe = None
        if st.button("🥺 Missing You", use_container_width=True): vibe = "Missing you deeply"
        if st.button("🥰 Just Because", use_container_width=True): vibe = "Just wanted to say I love you"
        if st.button("🌧️ Bad Day", use_container_width=True): vibe = "Cheer me up, I had a hard day"
        if st.button("🔥 Flirty", use_container_width=True): vibe = "Feeling flirty and romantic"
    with col_t2:
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

with tab2:
    st.header("The Teleport Deck 🎲")
    st.write("Let the AI plan your perfect virtual date.")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_duration = st.selectbox("How much time?", ["30 Mins", "1 Hour", "2 Hours", "All Night"])
    with col_d2:
        date_vibe = st.selectbox("Vibe?", ["Lazy", "Active", "Romantic", "Deep Talk", "Gaming"])
    
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
