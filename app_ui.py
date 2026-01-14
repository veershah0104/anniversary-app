# app_ui.py
import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime
import math
import subprocess
import sys
import time
import os

# --- 🚀 CLOUD AUTO-BOOTSTRAPPER ---
# This block ensures the Backend starts automatically when the app loads on the cloud
def start_backend():
    # Check if backend is already running
    try:
        requests.get("http://127.0.0.1:8000")
        return # It's running!
    except:
        # Not running? Start it in the background!
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3) # Give it 3 seconds to wake up

start_backend()
# ------------------------------------

# --- CONFIG ---
API_URL = "http://127.0.0.1:8000"
NEXT_MEET_DATE = datetime(2026, 5, 20) 

# Coordinates (Hong Kong -> Canterbury)
MY_LAT, MY_LON = 22.2988, 114.1722   # Hong Kong
HER_LAT, HER_LON = 51.2955, 1.0586   # Canterbury
MY_CITY = "Hong Kong"
HER_CITY = "Canterbury"

st.set_page_config(page_title="LDR Dashboard", page_icon="❤️", layout="wide")

# --- 🎨 VISUAL STYLING (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    
    /* SYNC CARDS */
    .mood-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #333;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .user-name { font-size: 24px; font-weight: bold; color: #FFF; margin-bottom: 5px;}
    .mood-text { font-size: 18px; color: #DDD; font-style: italic; margin: 10px 0; }
    .rating-box { font-size: 16px; font-weight: bold; padding: 5px 15px; border-radius: 20px; color: #000; display: inline-block; margin-top: 10px;}

    /* INFO CARDS */
    .info-card {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .card-title { font-size: 14px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 5px; color: #FFF; }
    .card-value { font-size: 28px; font-weight: 800; margin-top: 5px; color: #FFF; }
    .card-sub { font-size: 12px; opacity: 0.8; color: #EEE; }

    /* Gradients */
    .dist-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .time-card { background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); }
    .weather-card { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }

    /* LOVE LETTER */
    .love-note {
        background-color: #fff9c4;
        color: #4a4a4a;
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
    .note-signature { text-align: right; font-weight: bold; margin-top: 15px; color: #d32f2f; }

    /* DATE TICKET STYLE */
    .date-card {
        background-color: #262730;
        border: 2px dashed #FF4B4B;
        border-radius: 12px;
        padding: 25px;
        color: #EEE;
        margin-top: 15px;
        text-align: center;
        font-size: 18px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# --- HELPERS ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return int(R * c)

def get_data():
    try:
        w_my = requests.get(f"{API_URL}/dashboard/weather", params={"lat": MY_LAT, "lon": MY_LON}).json()
        w_her = requests.get(f"{API_URL}/dashboard/weather", params={"lat": HER_LAT, "lon": HER_LON}).json()
        statuses = requests.get(f"{API_URL}/dashboard/statuses").json()
        return w_my, w_her, statuses
    except:
        return None, None, None

def get_rating_color(rating):
    if rating >= 8: return "#69F0AE" 
    if rating >= 4: return "#FFD740" 
    return "#FF5252" 

# --- MAIN UI ---
st.title("❤️ Relationship Sync")

my_w, her_w, statuses = get_data()

# 1. TOP SECTION: SYNC CARDS
if statuses:
    c1, c2 = st.columns(2)
    with c1:
        veer = statuses.get("Veer", {})
        col = get_rating_color(veer.get('rating', 5))
        st.markdown(f"""
<div class="mood-card">
<div class="user-name">🧑‍💻 Veer</div>
<div class="mood-text">"{veer.get('mood', 'Loading...')}"</div>
<div class="rating-box" style="background-color: {col};">Feels: {veer.get('rating')}/10</div>
</div>
""", unsafe_allow_html=True)
        
    with c2:
        rishi = statuses.get("Rishi", {})
        col = get_rating_color(rishi.get('rating', 5))
        st.markdown(f"""
<div class="mood-card">
<div class="user-name">👩‍❤️‍👨 Rishi</div>
<div class="mood-text">"{rishi.get('mood', 'Loading...')}"</div>
<div class="rating-box" style="background-color: {col};">Feels: {rishi.get('rating')}/10</div>
</div>
""", unsafe_allow_html=True)

# Update form
with st.expander("📝 Update Status"):
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        who = st.radio("User", ["Veer", "Rishi"], horizontal=True, label_visibility="collapsed")
        rate = st.slider("Rating", 1, 10, 8)
    with col_u2:
        msg = st.text_input("Mood", placeholder="Status update...")
        if st.button("Sync 🔄", use_container_width=True):
            if msg:
                try:
                    resp = requests.post(f"{API_URL}/dashboard/update", json={"user": who, "mood": msg, "rating": rate})
                    resp.raise_for_status()
                    st.success("Updated!")
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection failed: {e}")
                except Exception as e:
                    if "Rerun" not in str(type(e)): st.error(f"Error: {e}")
                    else: raise e

st.divider()

# 2. MIDDLE SECTION
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

    t1 = my_w['temperature'] if my_w else "--"
    t2 = her_w['temperature'] if her_w else "--"
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

# 3. BOTTOM SECTION
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
                    res = requests.post(f"{API_URL}/ai/love-letter", json={"mood": vibe}).json()
                    content = res["ai_message"]
                    st.markdown(f"""
<div class="love-note">
{content.replace(chr(10), '<br>')}
<div class="note-signature">- Forever yours, Veer</div>
</div>
""", unsafe_allow_html=True)
                except:
                    st.error("AI is sleeping.")
        else:
            st.info("👈 Tap a vibe button to generate a letter!")

with tab2:
    st.header("The Teleport Deck 🎲")
    st.write("Let the AI plan your perfect virtual date.")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_duration = st.selectbox("How much time do you have?", 
                                     ["30 Mins (Quick)", "1 Hour (Standard)", "2 Hours (Movie/Game)", "All Night (Event)"])
    with col_d2:
        date_vibe = st.selectbox("What's the vibe?", 
                                 ["Lazy & Chill", "Active & Fun", "Romantic & Sexy", "Deep Talk", "Gaming", "Competitive"])
    
    if st.button("Plan Our Date 🎟️", use_container_width=True):
        with st.spinner("Consulting the Cupid Algorithm..."):
            try:
                payload = {"duration": date_duration, "vibe": date_vibe}
                res = requests.post(f"{API_URL}/dates/generate", json=payload).json()
                idea = res["date_idea"]
                st.markdown(f"""
<div class="date-card">
{idea.replace(chr(10), '<br>')}
</div>
""", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Backend Error: {e}")