"""
NOMO — Multipassionate Leaderboard
Streamlit app. Reads the admin master Top_Achievers tab and shows a live leaderboard.
The "Update" button triggers the Apps Script Web App to re-sync scores.

Deploy:
  1. Push this file + requirements.txt to a GitHub repo
  2. share.streamlit.io → New app → point to app.py
  3. In app Settings → Secrets, add:
       GSHEET_CSV_URL = "https://docs.google.com/.../export?format=csv&gid=<TopAchievers_gid>"
       APPS_SCRIPT_URL = "https://script.google.com/macros/s/XXXX/exec"
"""

import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="NOMO Leaderboard", page_icon="🏆",
                   layout="centered", initial_sidebar_state="collapsed")

# ── Styling ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');
#MainMenu, header, footer {visibility: hidden;}
.stApp { background: #FAF8F3; }
.block-container { padding-top: 2rem; max-width: 760px; }
.nomo-title { font-family:'Playfair Display',serif; font-size:2.6rem; font-weight:700;
  color:#1A1A1A; text-align:center; margin-bottom:0; letter-spacing:-0.5px; }
.nomo-sub { font-family:'Inter',sans-serif; font-size:0.85rem; color:#888;
  text-align:center; margin-top:4px; margin-bottom:1.5rem; }
.row { display:flex; align-items:center; background:#FFFFFF; border-radius:14px;
  padding:14px 18px; margin-bottom:10px; box-shadow:0 1px 4px rgba(0,0,0,0.05);
  border:1px solid #F0EEE9; }
.rank { font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:700;
  width:48px; text-align:center; color:#1A1A1A; }
.name { font-family:'Inter',sans-serif; font-size:1.05rem; font-weight:600;
  color:#1A1A1A; flex:1; padding-left:8px; }
.metrics { display:flex; gap:18px; align-items:center; }
.metric { text-align:center; }
.metric .val { font-family:'Inter',sans-serif; font-weight:600; font-size:1.1rem; color:#1B4332; }
.metric .lbl { font-family:'Inter',sans-serif; font-size:0.62rem; color:#999;
  text-transform:uppercase; letter-spacing:0.5px; }
.gold { background:linear-gradient(135deg,#FBF3D5,#FFFFFF); border-color:#E8D9A0; }
.silver { background:linear-gradient(135deg,#F0F0F2,#FFFFFF); border-color:#DADCE0; }
.bronze { background:linear-gradient(135deg,#F5EBDD,#FFFFFF); border-color:#E5D2B8; }
.bar-bg { background:#EDEAE3; height:6px; border-radius:3px; margin-top:8px; width:100%; }
.bar-fill { background:#2D6A4F; height:6px; border-radius:3px; }
.stButton button { background:#1B4332; color:#FFF; font-family:'Inter',sans-serif;
  font-weight:600; border:none; border-radius:10px; padding:0.5rem 1.5rem; width:100%; }
.stButton button:hover { background:#2D6A4F; }
.foot { font-family:'Inter',sans-serif; font-size:0.72rem; color:#AAA;
  text-align:center; margin-top:2rem; line-height:1.6; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nomo-title">NOMO Leaderboard</div>', unsafe_allow_html=True)
st.markdown('<div class="nomo-sub">Rolling 15-day consistency · Multipassionates</div>',
            unsafe_allow_html=True)


@st.cache_data(ttl=30)
def load_data(csv_url: str) -> pd.DataFrame:
    # Top_Achievers layout: row1 title, row2 timestamp, row3 headers, row4+ data.
    # Data sits in columns B:F (col A is blank). Read raw, then locate the header row.
    raw = pd.read_csv(csv_url, header=None, dtype=str)
    raw = raw.dropna(how="all")
    # Find the header row = the one containing "Rank"
    header_idx = None
    for i in range(len(raw)):
        rowvals = [str(x).strip().lower() for x in raw.iloc[i].tolist()]
        if any("rank" in v for v in rowvals):
            header_idx = i
            break
    if header_idx is None:
        header_idx = 0
    headers = [str(x).strip() for x in raw.iloc[header_idx].tolist()]
    body = raw.iloc[header_idx + 1:].copy()
    body.columns = headers
    # Drop fully-empty columns (the blank col A) and empty rows
    body = body.dropna(axis=1, how="all").dropna(how="all")
    # Keep only rows that have a name
    name_col = next((c for c in body.columns
                     if "passion" in str(c).lower() or "name" in str(c).lower()), None)
    if name_col is not None:
        body = body[body[name_col].notna() & (body[name_col].astype(str).str.strip() != "")]
    return body.reset_index(drop=True)


def get_sample() -> pd.DataFrame:
    return pd.DataFrame({
        "Rank": ["🥇", "🥈", "🥉", 4, 5],
        "Multipassionate": ["Aditya", "AK", "Shradha", "Riya", "Karan"],
        "Score": [93, 87, 80, 67, 53],
        "Streak": [14, 9, 12, 5, 3],
        "Wins (15d)": [13, 11, 10, 6, 4],
    })


# ── Update button ──
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄  Sync Latest Scores"):
        script_url = st.secrets.get("APPS_SCRIPT_URL", "")
        if not script_url:
            st.warning("No APPS_SCRIPT_URL set in Secrets.")
        else:
            with st.spinner("Syncing… this takes ~30–60 seconds"):
                try:
                    requests.get(script_url, timeout=120)
                    time.sleep(2)
                    st.cache_data.clear()
                    st.success("Synced! Leaderboard refreshed below.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Sync failed: {e}")

st.write("")

# ── Load + render ──
csv_url = st.secrets.get("GSHEET_CSV_URL", "")
if csv_url:
    try:
        df = load_data(csv_url)
    except Exception as e:
        st.error(f"Couldn't read the sheet: {e}")
        df = get_sample()
        st.info("Showing sample data.")
else:
    df = get_sample()
    st.info("Demo mode — add GSHEET_CSV_URL in Secrets to go live.")

# Normalize column names
df.columns = [str(c).strip() for c in df.columns]
col_rank = next((c for c in df.columns if "rank" in c.lower()), df.columns[0])
col_name = next((c for c in df.columns if "passion" in c.lower() or "name" in c.lower()), df.columns[1])
col_score = next((c for c in df.columns if "score" in c.lower()), None)
col_streak = next((c for c in df.columns if "streak" in c.lower()), None)
col_wins = next((c for c in df.columns if "win" in c.lower()), None)

max_score = 100
for i, row in df.iterrows():
    cls = ""
    if i == 0: cls = "gold"
    elif i == 1: cls = "silver"
    elif i == 2: cls = "bronze"

    rank = row.get(col_rank, i + 1)
    name = row.get(col_name, "—")
    score = row.get(col_score, 0) if col_score else 0
    streak = row.get(col_streak, 0) if col_streak else 0
    wins = row.get(col_wins, 0) if col_wins else 0

    try: score_i = int(float(score))
    except: score_i = 0
    try: streak_i = int(float(streak))
    except: streak_i = 0
    try: wins_i = int(float(wins))
    except: wins_i = 0

    pct = min(100, max(0, score_i))

    st.markdown(f"""
    <div class="row {cls}">
      <div class="rank">{rank}</div>
      <div style="flex:1;">
        <div class="name">{name}</div>
        <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;"></div></div>
      </div>
      <div class="metrics">
        <div class="metric"><div class="val">{score_i}</div><div class="lbl">Score</div></div>
        <div class="metric"><div class="val">{streak_i}</div><div class="lbl">Streak</div></div>
        <div class="metric"><div class="val">{wins_i}</div><div class="lbl">Wins</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="foot">
  Score = days shown up in the last 15 days ÷ 15 × 100<br>
  Showing up = at least one passion marked Yes that day · Wins shown for motivation
</div>
""", unsafe_allow_html=True)
