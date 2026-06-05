import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

st.set_page_config(
    page_title="NOMO — Top Achievers",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@300;400;500;600&display=swap');

html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#ffffff!important}
[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="block-container"]{background:#ffffff!important}
.block-container{padding:3rem 4rem 5rem!important;max-width:1000px!important}
#MainMenu,footer,header{visibility:hidden}
[data-testid="stToolbar"]{display:none}
.viewerBadge_container__1QSob{display:none!important}
#stDecoration{display:none}

/* HEADER */
.nomo-title{font-family:'Playfair Display',serif;font-size:2.6rem;font-weight:900;color:#111;letter-spacing:-.03em;line-height:1}
.nomo-title em{font-style:italic;color:#1a6b4a}
.nomo-tag{font-size:10px;color:#aaa;letter-spacing:.14em;text-transform:uppercase;font-family:monospace;margin-top:8px}
.nomo-updated{font-size:11px;color:#aaa;font-family:monospace;text-align:right;padding-top:20px}
.nomo-divider{border:none;border-top:2px solid #111;margin:20px 0 32px}

/* INFO BAR */
.info-bar{background:#f8f8f6;border-left:3px solid #1a6b4a;padding:10px 16px;font-size:12px;color:#666;font-family:monospace;margin-bottom:28px}

/* METRICS */
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:2px solid #111;margin-bottom:36px}
.metric-cell{padding:20px 22px;border-right:2px solid #111}
.metric-cell:last-child{border-right:none}
.metric-lbl{font-size:9px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#aaa;font-family:monospace;margin-bottom:8px}
.metric-val{font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:700;color:#111;line-height:1}
.metric-sub{font-size:11px;color:#aaa;margin-top:4px}

/* SECTION TITLE */
.sec-title{font-size:9px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#aaa;font-family:monospace;margin-bottom:14px}

/* LEADERBOARD ROWS */
.lb-row{display:flex;align-items:center;gap:16px;padding:16px 20px;background:#fff;border:1.5px solid #111;margin-bottom:-1.5px}
.lb-row:first-child{border-radius:10px 10px 0 0}
.lb-row:last-child{border-radius:0 0 10px 10px;margin-bottom:0}
.lb-rank{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;width:28px;text-align:center;flex-shrink:0;color:#111}
.lb-name{font-size:14px;font-weight:600;color:#111;width:110px;flex-shrink:0;letter-spacing:-.01em}
.lb-bar-bg{flex:1;height:5px;background:#f0f0ee;border-radius:0}
.lb-bar{height:100%;border-radius:0}
.lb-score{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#111;width:68px;text-align:right;flex-shrink:0;line-height:1}
.lb-denom{font-size:11px;color:#aaa;font-weight:400}
.lb-chg{font-size:11px;font-family:monospace;width:40px;text-align:center;flex-shrink:0}
.up{color:#1a6b4a;font-weight:600}.dn{color:#c13a3a;font-weight:600}.eq{color:#aaa}
.lb-badge{font-size:9px;font-weight:600;padding:4px 10px;letter-spacing:.06em;text-transform:uppercase;font-family:monospace;flex-shrink:0;border:1.5px solid}
.b-elite{background:#e8f5f0;color:#085041;border-color:#085041}
.b-star{background:#fdf3e3;color:#7a4a0a;border-color:#c17f2a}
.b-ontrack{background:#e8f0fb;color:#0c3d8a;border-color:#2a5fa8}
.b-building{background:#f0eefb;color:#3c2a8a;border-color:#6b3fc4}
.b-starting{background:#f5f5f5;color:#888;border-color:#ccc}

/* BREAKDOWN TABLE */
.bd-table{width:100%;border-collapse:collapse;font-size:12px;margin-top:4px}
.bd-table th{text-align:left;padding:8px 12px;font-size:9px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#aaa;font-family:monospace;border-bottom:2px solid #111}
.bd-table td{padding:11px 12px;border-bottom:1px solid #eee;color:#111;font-size:13px}
.bd-table tr:last-child td{border-bottom:none}
.bd-table tr:hover td{background:#fafaf8}
.td-score{font-weight:700;color:#1a6b4a;font-family:'Playfair Display',serif;font-size:15px}
.td-m{color:#888}

/* WEIGHTS */
.wt-row{display:flex;gap:0;margin-top:12px;border:1.5px solid #111}
.wt-pill{flex:1;padding:10px 8px;text-align:center;font-size:10px;font-family:monospace;color:#555;border-right:1.5px solid #111}
.wt-pill:last-child{border-right:none}
.wt-pill span{display:block;font-weight:700;color:#111;font-size:13px;margin-top:2px}

.band-row{display:flex;gap:0;margin-top:10px;border:1.5px solid #111}
.band-pill{flex:1;padding:8px 6px;text-align:center;font-size:9px;font-family:monospace;letter-spacing:.04em;border-right:1.5px solid #111}
.band-pill:last-child{border-right:none}

[data-testid="stSidebar"]{background:#fafaf8!important}

@media(max-width:768px){
  .block-container{padding:1.5rem 1.2rem 3rem!important}
  .nomo-title{font-size:1.6rem!important}
  .metric-grid{grid-template-columns:repeat(2,1fr)!important}
  .metric-cell:nth-child(2){border-right:none!important}
  .metric-cell:nth-child(3){border-top:2px solid #111!important}
  .metric-cell:nth-child(4){border-top:2px solid #111!important;border-right:none!important}
  .lb-row{flex-wrap:wrap;gap:8px;padding:12px 14px}
  .lb-name{width:80px!important;font-size:13px!important}
  .lb-score{font-size:1.1rem!important;width:52px!important}
  .lb-bar-bg{width:100%!important;order:5;flex-basis:100%}
  .lb-badge{font-size:8px!important}
  .lb-chg{width:30px!important}
  .wt-row{flex-wrap:wrap}
  .wt-pill{flex-basis:33%!important;border-bottom:1.5px solid #111}
  .band-row{flex-wrap:wrap}
  .band-pill{flex-basis:33%!important;border-bottom:1.5px solid #111}
  .bd-table{font-size:11px!important}
  .bd-table th,.bd-table td{padding:7px 8px!important}
  .nomo-updated{font-size:10px!important;padding-top:8px!important}
}
</style>
""", unsafe_allow_html=True)

# ── helpers ──────────────────────────────────────────────
def band(s):
    if s>=90: return "Elite","b-elite"
    if s>=75: return "Star","b-star"
    if s>=60: return "On Track","b-ontrack"
    if s>=40: return "Building","b-building"
    return "Starting","b-starting"

def bar_color(s):
    if s>=75: return "#1a6b4a"
    if s>=60: return "#2a5fa8"
    if s>=40: return "#6b3fc4"
    return "#ccc"

def chg_html(curr, prev):
    try:
        d = round(float(curr) - float(prev), 1)
        if d > 0: return f'<span class="lb-chg up">▲{d}</span>'
        if d < 0: return f'<span class="lb-chg dn">▼{abs(d)}</span>'
        return '<span class="lb-chg eq">—</span>'
    except: return '<span class="lb-chg eq">New</span>'

def medal(r):
    return {1:"🥇",2:"🥈",3:"🥉"}.get(r, str(r))

# ── data ─────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_sheet(url, creds_json):
    try:
        c = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=["https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(c)
        ws = gc.open_by_url(url).worksheet("🏆 Top_Achievers")
        return pd.DataFrame(ws.get_all_records()), None
    except Exception as e:
        return None, str(e)

def sample():
    return pd.DataFrame([
        {"RANK":1,"NAME":"Aditya",  "STREAK":14,"BI-WEEKLY HRS":22,"PASSION BALANCE":3,"AVG ENERGY":4.4,"WINS":13,"NOMO SCORE":82.1,"PREV SCORE":78.5},
        {"RANK":2,"NAME":"Rohan",   "STREAK":13,"BI-WEEKLY HRS":25,"PASSION BALANCE":3,"AVG ENERGY":3.9,"WINS":11,"NOMO SCORE":79.4,"PREV SCORE":81.0},
        {"RANK":3,"NAME":"Meera",   "STREAK":10,"BI-WEEKLY HRS":14,"PASSION BALANCE":3,"AVG ENERGY":3.7,"WINS":9, "NOMO SCORE":63.2,"PREV SCORE":60.0},
        {"RANK":4,"NAME":"Priya",   "STREAK":8, "BI-WEEKLY HRS":12,"PASSION BALANCE":2,"AVG ENERGY":4.1,"WINS":7, "NOMO SCORE":55.8,"PREV SCORE":54.0},
        {"RANK":5,"NAME":"Karthik", "STREAK":6, "BI-WEEKLY HRS":9, "PASSION BALANCE":2,"AVG ENERGY":3.5,"WINS":5, "NOMO SCORE":44.7,"PREV SCORE":46.0},
        {"RANK":6,"NAME":"Divya",   "STREAK":5, "BI-WEEKLY HRS":7, "PASSION BALANCE":1,"AVG ENERGY":3.2,"WINS":4, "NOMO SCORE":36.1,"PREV SCORE":33.0},
    ])

# ── sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Connect your sheet")
    url = st.text_input("Top_Achievers Sheet URL", placeholder="https://docs.google.com/spreadsheets/...")
    creds = st.text_area("Service Account JSON", placeholder='{"type":"service_account"...}', height=120)
    st.button("Connect", use_container_width=True)
    st.markdown("---")
    st.caption("No sheet connected? Sample data loads automatically.")
    st.markdown("---")
    st.markdown("**Get credentials:**")
    st.caption("1. console.cloud.google.com → New project")
    st.caption("2. Enable Sheets API + Drive API")
    st.caption("3. Create Service Account → download JSON")
    st.caption("4. Share sheet with service account email (viewer)")

# ── load ──────────────────────────────────────────────────
df, err = None, None
using_sample = False
if url and creds:
    df, err = load_sheet(url, creds)
    if err: st.sidebar.error(err)
if df is None:
    df = sample(); using_sample = True

sc = next((c for c in df.columns if "NOMO" in c.upper() and "SCORE" in c.upper()), None)
pc = next((c for c in df.columns if "PREV" in c.upper()), None)
nc = next((c for c in df.columns if "NAME" in c.upper()), "NAME")
if sc:
    df[sc] = pd.to_numeric(df[sc], errors="coerce").fillna(0)
    df = df.sort_values(sc, ascending=False).reset_index(drop=True)
    df["RANK"] = df.index + 1

# ── header ────────────────────────────────────────────────
c1, c2 = st.columns([3,1])
with c1:
    st.markdown('<div class="nomo-title">NOMO — <em>Top Achievers</em></div>', unsafe_allow_html=True)
    st.markdown('<div class="nomo-tag">15-day rolling · Discover → Track → Connect → Build → Sustain</div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="nomo-updated">{datetime.now().strftime("%d %b %Y · %H:%M")}</div>', unsafe_allow_html=True)

st.markdown('<hr class="nomo-divider">', unsafe_allow_html=True)

if using_sample:
    st.markdown('<div class="info-bar">Sample data — connect your Top_Achievers sheet in the sidebar to go live</div>', unsafe_allow_html=True)

# ── metrics ───────────────────────────────────────────────
total = len(df)
avg = round(df[sc].mean(), 1) if sc else "—"
top = round(df[sc].max(), 1) if sc else "—"
top_name = df[nc].iloc[0] if len(df) > 0 else "—"

st.markdown(f"""
<div class="metric-grid">
  <div class="metric-cell"><div class="metric-lbl">Multipassionates</div><div class="metric-val">{total}</div><div class="metric-sub">in cohort</div></div>
  <div class="metric-cell"><div class="metric-lbl">Cohort avg</div><div class="metric-val">{avg}</div><div class="metric-sub">out of 100</div></div>
  <div class="metric-cell"><div class="metric-lbl">Top score</div><div class="metric-val">{top}</div><div class="metric-sub">{top_name}</div></div>
  <div class="metric-cell"><div class="metric-lbl">Window</div><div class="metric-val">15</div><div class="metric-sub">rolling days</div></div>
</div>
""", unsafe_allow_html=True)

# ── leaderboard ───────────────────────────────────────────
st.markdown('<div class="sec-title">Leaderboard</div>', unsafe_allow_html=True)

lb_html = ""
for _, row in df.iterrows():
    r = int(row.get("RANK", _ + 1))
    name = str(row.get(nc, "—"))
    score = float(row.get(sc, 0)) if sc else 0
    prev = row.get(pc, "") if pc else ""
    bl, bc = band(score)
    m = medal(r)
    lb_html += f"""
    <div class="lb-row">
      <div class="lb-rank">{m}</div>
      <div class="lb-name">{name}</div>
      <div class="lb-bar-bg"><div class="lb-bar" style="width:{min(score,100)}%;background:{bar_color(score)}"></div></div>
      <div class="lb-score">{score:.1f}<span class="lb-denom">/100</span></div>
      {chg_html(score, prev)}
      <span class="lb-badge {bc}">{bl}</span>
    </div>"""

st.markdown(lb_html, unsafe_allow_html=True)

# ── breakdown ─────────────────────────────────────────────
st.markdown('<hr class="nomo-divider" style="margin-top:32px">', unsafe_allow_html=True)
st.markdown('<div class="sec-title">Score breakdown</div>', unsafe_allow_html=True)

if sc and len(df) > 0:
    rows = ""
    for _, row in df.iterrows():
        sv = float(row.get(sc, 0)) if sc else 0
        stk = next((row.get(c,"—") for c in df.columns if "STREAK" in c.upper()), "—")
        hrs = next((row.get(c,"—") for c in df.columns if "HRS" in c.upper() or "HOUR" in c.upper()), "—")
        bal = next((row.get(c,"—") for c in df.columns if "BALANCE" in c.upper()), "—")
        eng = next((row.get(c,"—") for c in df.columns if "ENERGY" in c.upper()), "—")
        win = next((row.get(c,"—") for c in df.columns if "WIN" in c.upper()), "—")
        rows += f"""<tr>
          <td>{row.get(nc,"—")}</td>
          <td class="td-m">{stk}</td><td class="td-m">{hrs}h</td>
          <td class="td-m">{bal}</td><td class="td-m">{eng}</td>
          <td class="td-m">{win}</td>
          <td class="td-score">{sv:.1f}</td>
        </tr>"""
    st.markdown(f"""
    <table class="bd-table">
      <thead><tr>
        <th>Name</th><th>Streak</th><th>Bi-wkly hrs</th>
        <th>Balance</th><th>Energy</th><th>Wins</th><th>Score</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>""", unsafe_allow_html=True)

# ── scoring weights ───────────────────────────────────────
st.markdown('<hr class="nomo-divider" style="margin-top:32px">', unsafe_allow_html=True)
st.markdown('<div class="sec-title">How scores are calculated</div>', unsafe_allow_html=True)
st.markdown("""
<div class="wt-row">
  <div class="wt-pill">Streak<span>30%</span></div>
  <div class="wt-pill">Bi-wkly hrs<span>25%</span></div>
  <div class="wt-pill">Passion balance<span>20%</span></div>
  <div class="wt-pill">Avg energy<span>15%</span></div>
  <div class="wt-pill">Wins logged<span>10%</span></div>
</div>
<div class="band-row" style="margin-top:10px">
  <div class="band-pill" style="background:#e8f5f0;color:#085041">Elite<br><b>90+</b></div>
  <div class="band-pill" style="background:#fdf3e3;color:#7a4a0a">Star<br><b>75–89</b></div>
  <div class="band-pill" style="background:#e8f0fb;color:#0c3d8a">On Track<br><b>60–74</b></div>
  <div class="band-pill" style="background:#f0eefb;color:#3c2a8a">Building<br><b>40–59</b></div>
  <div class="band-pill" style="background:#f5f5f5;color:#888">Starting<br><b>0–39</b></div>
</div>
""", unsafe_allow_html=True)
