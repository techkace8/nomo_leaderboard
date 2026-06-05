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
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@300;400;500&display=swap');

html,body,[class*="css"]{font-family:'Inter',sans-serif}
.block-container{padding:2.5rem 3rem 4rem;max-width:960px}

.logo{font-family:'Playfair Display',serif;font-size:2rem;font-weight:900;letter-spacing:-.02em;line-height:1;margin-bottom:4px}
.logo em{font-style:italic;color:#0F6E56}
.tagline{font-size:11px;color:#99998f;letter-spacing:.12em;text-transform:uppercase;font-family:monospace}
.divider{height:1px;background:#e8e7e2;margin:20px 0}

.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:24px 0}
.mc{background:#fff;border:1px solid #eeeee9;border-radius:12px;padding:16px 18px}
.mc-l{font-size:10px;color:#99998f;text-transform:uppercase;letter-spacing:.1em;font-family:monospace;margin-bottom:6px}
.mc-v{font-family:'Playfair Display',serif;font-size:2rem;font-weight:700;color:#111;line-height:1}
.mc-s{font-size:11px;color:#99998f;margin-top:3px}

.stitle{font-size:10px;font-weight:500;color:#99998f;text-transform:uppercase;letter-spacing:.12em;font-family:monospace;margin-bottom:12px;margin-top:24px}

.lb{background:#fff;border:1px solid #eeeee9;border-radius:10px;padding:14px 18px;margin-bottom:7px;display:flex;align-items:center;gap:12px}
.lb:hover{border-color:#d4d3cc}
.lb-medal{font-size:18px;width:26px;text-align:center;flex-shrink:0}
.lb-rank{font-size:12px;color:#99998f;width:18px;text-align:center;font-family:monospace;flex-shrink:0}
.lb-name{font-size:14px;font-weight:500;color:#111;width:100px;flex-shrink:0}
.lb-bar-bg{flex:1;height:6px;background:#f5f5f2;border-radius:999px;overflow:hidden}
.lb-bar{height:100%;border-radius:999px}
.lb-score{font-family:'Playfair Display',serif;font-size:18px;font-weight:700;color:#111;width:60px;text-align:right;flex-shrink:0}
.lb-denom{font-size:11px;color:#99998f;font-weight:400}
.lb-chg{font-size:11px;font-family:monospace;width:38px;text-align:center;flex-shrink:0}
.up{color:#0F6E56}.dn{color:#c13a3a}.eq{color:#99998f}
.badge{font-size:10px;padding:3px 9px;border-radius:999px;font-weight:500;flex-shrink:0;letter-spacing:.02em}
.b-elite{background:#e1f5ee;color:#085041}
.b-star{background:#faeeda;color:#633806}
.b-ontrack{background:#e6f1fb;color:#0c447c}
.b-building{background:#eeedfe;color:#3c3489}
.b-starting{background:#f5f5f2;color:#99998f}

.break-table{width:100%;border-collapse:collapse;font-size:12px}
.break-table th{text-align:left;padding:7px 10px;color:#99998f;font-size:10px;text-transform:uppercase;letter-spacing:.08em;font-family:monospace;font-weight:500;border-bottom:1px solid #eeeee9}
.break-table td{padding:10px;border-bottom:1px solid #f5f5f2;color:#111}
.break-table tr:last-child td{border-bottom:none}
.break-table tr:hover td{background:#fafaf8}
.td-score{font-weight:500;color:#0F6E56}
.td-muted{color:#99998f}

.weights{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.wp{background:#f5f5f2;border-radius:8px;padding:6px 12px;font-size:12px;color:#555}
.wp span{font-weight:500;color:#111}

.info-bar{background:#f5f5f2;border-radius:8px;padding:10px 14px;font-size:12px;color:#99998f;font-family:monospace;margin-bottom:20px}

[data-testid="stSidebar"]{background:#fafaf8}
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
    if s>=75: return "#1D9E75"
    if s>=60: return "#378ADD"
    if s>=40: return "#7F77DD"
    return "#B4B2A9"

def chg_html(curr,prev):
    try:
        d=round(float(curr)-float(prev),1)
        if d>0: return f'<span class="lb-chg up">▲{d}</span>'
        if d<0: return f'<span class="lb-chg dn">▼{abs(d)}</span>'
        return '<span class="lb-chg eq">—</span>'
    except: return '<span class="lb-chg eq">New</span>'

def medal(r):
    return {1:"🥇",2:"🥈",3:"🥉"}.get(r,"")

# ── data ─────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_sheet(url,creds_json):
    try:
        c=Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=["https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"])
        gc=gspread.authorize(c)
        ws=gc.open_by_url(url).worksheet("🏆 Top_Achievers")
        return pd.DataFrame(ws.get_all_records()),None
    except Exception as e:
        return None,str(e)

def sample():
    return pd.DataFrame([
        {"RANK":1,"NAME":"Aditya",  "STREAK":14,"BI-WEEKLY HRS":22,"PASSION BALANCE":20,"AVG ENERGY":4.4,"WINS":13,"NOMO SCORE":82.1,"PREV SCORE":78.5},
        {"RANK":2,"NAME":"Rohan",   "STREAK":13,"BI-WEEKLY HRS":25,"PASSION BALANCE":20,"AVG ENERGY":3.9,"WINS":11,"NOMO SCORE":79.4,"PREV SCORE":81.0},
        {"RANK":3,"NAME":"Meera",   "STREAK":10,"BI-WEEKLY HRS":14,"PASSION BALANCE":20,"AVG ENERGY":3.7,"WINS":9, "NOMO SCORE":63.2,"PREV SCORE":60.0},
        {"RANK":4,"NAME":"Priya",   "STREAK":8, "BI-WEEKLY HRS":12,"PASSION BALANCE":13,"AVG ENERGY":4.1,"WINS":7, "NOMO SCORE":55.8,"PREV SCORE":54.0},
        {"RANK":5,"NAME":"Karthik", "STREAK":6, "BI-WEEKLY HRS":9, "PASSION BALANCE":13,"AVG ENERGY":3.5,"WINS":5, "NOMO SCORE":44.7,"PREV SCORE":46.0},
        {"RANK":6,"NAME":"Divya",   "STREAK":5, "BI-WEEKLY HRS":7, "PASSION BALANCE":7, "AVG ENERGY":3.2,"WINS":4, "NOMO SCORE":36.1,"PREV SCORE":33.0},
    ])

# ── sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Connect sheet")
    url=st.text_input("Google Sheet URL",placeholder="https://docs.google.com/...")
    creds=st.text_area("Service account JSON",placeholder='{"type":"service_account"...}',height=100)
    connect=st.button("Connect",use_container_width=True)
    st.markdown("---")
    st.caption("No sheet connected? Sample data loads automatically.")
    st.markdown("---")
    st.markdown("**How to get credentials:**")
    st.caption("1. console.cloud.google.com → New project")
    st.caption("2. Enable Sheets API + Drive API")
    st.caption("3. Create Service Account → download JSON key")
    st.caption("4. Share Top_Achievers sheet with service account email (viewer)")
    st.markdown("---")
    st.markdown("**How to get credentials:**")
    st.caption("1. console.cloud.google.com → New project")
    st.caption("2. Enable Sheets API + Drive API")
    st.caption("3. Create Service Account → download JSON key")
    st.caption("4. Share Top_Achievers sheet with service account email (viewer)")

# ── load ──────────────────────────────────────────────────
df,err=None,None
using_sample=False
if url and creds:
    df,err=load_sheet(url,creds)
    if err: st.sidebar.error(err)
if df is None:
    df=sample(); using_sample=True

sc=next((c for c in df.columns if "NOMO" in c.upper()),None)
pc=next((c for c in df.columns if "PREV" in c.upper()),None)
nc=next((c for c in df.columns if "NAME" in c.upper()),"NAME")
if sc:
    df[sc]=pd.to_numeric(df[sc],errors="coerce").fillna(0)
    df=df.sort_values(sc,ascending=False).reset_index(drop=True)
    df["RANK"]=df.index+1

# ── header ────────────────────────────────────────────────
col1,col2=st.columns([3,1])
with col1:
    st.markdown('<div class="logo">NOMO — <em>Top Achievers</em></div>',unsafe_allow_html=True)
    st.markdown('<div class="tagline">15-day rolling · Discover → Track → Connect → Build → Sustain</div>',unsafe_allow_html=True)
with col2:
    st.markdown(f'<div style="text-align:right;font-size:11px;color:#99998f;font-family:monospace;padding-top:16px">Updated {datetime.now().strftime("%d %b · %H:%M")}</div>',unsafe_allow_html=True)

if using_sample:
    st.markdown('<div class="info-bar">Showing sample data — connect your Top_Achievers sheet in the sidebar</div>',unsafe_allow_html=True)

st.markdown('<div class="divider"></div>',unsafe_allow_html=True)

# ── metrics ───────────────────────────────────────────────
total=len(df)
avg=round(df[sc].mean(),1) if sc else "—"
top=round(df[sc].max(),1) if sc else "—"
top_name=df[nc].iloc[0] if len(df)>0 else "—"
top3=df[df["RANK"]<=3][sc].count() if sc else 0

st.markdown(f"""
<div class="metrics">
  <div class="mc"><div class="mc-l">Mentees</div><div class="mc-v">{total}</div><div class="mc-s">in cohort</div></div>
  <div class="mc"><div class="mc-l">Cohort avg</div><div class="mc-v">{avg}</div><div class="mc-s">out of 100</div></div>
  <div class="mc"><div class="mc-l">Top score</div><div class="mc-v">{top}</div><div class="mc-s">{top_name}</div></div>
  <div class="mc"><div class="mc-l">Window</div><div class="mc-v">15</div><div class="mc-s">rolling days</div></div>
</div>
""",unsafe_allow_html=True)

# ── leaderboard ───────────────────────────────────────────
st.markdown('<div class="stitle">Leaderboard</div>',unsafe_allow_html=True)

for _,row in df.iterrows():
    r=int(row.get("RANK",_+1))
    name=str(row.get(nc,"—"))
    score=float(row.get(sc,0)) if sc else 0
    prev=row.get(pc,"") if pc else ""
    bl,bc=band(score)
    m=medal(r)
    rank_html=f'<div class="lb-medal">{m}</div>' if m else f'<div class="lb-rank">{r}</div>'

    st.markdown(f"""
    <div class="lb">
      {rank_html}
      <div class="lb-name">{name}</div>
      <div class="lb-bar-bg"><div class="lb-bar" style="width:{min(score,100)}%;background:{bar_color(score)}"></div></div>
      <div class="lb-score">{score:.1f}<span class="lb-denom">/100</span></div>
      {chg_html(score,prev)}
      <span class="badge {bc}">{bl}</span>
    </div>
    """,unsafe_allow_html=True)

# ── breakdown ─────────────────────────────────────────────
st.markdown('<div class="divider"></div>',unsafe_allow_html=True)
st.markdown('<div class="stitle">Score breakdown</div>',unsafe_allow_html=True)

if sc and len(df)>0:
    rows=""
    for _,row in df.iterrows():
        score_val=float(row.get(sc,0)) if sc else 0
        # find columns flexibly
        streak_val=next((row.get(c,"—") for c in df.columns if "STREAK" in c.upper()),("—"))
        hrs_val=next((row.get(c,"—") for c in df.columns if "HRS" in c.upper() or "HOUR" in c.upper()),("—"))
        bal_val=next((row.get(c,"—") for c in df.columns if "BALANCE" in c.upper() or "PASSION" in c.upper()),("—"))
        eng_val=next((row.get(c,"—") for c in df.columns if "ENERGY" in c.upper()),("—"))
        win_val=next((row.get(c,"—") for c in df.columns if "WIN" in c.upper()),("—"))
        rows+=f"""<tr>
          <td>{row.get(nc,"—")}</td>
          <td class="td-muted">{streak_val}</td>
          <td class="td-muted">{hrs_val}h</td>
          <td class="td-muted">{bal_val}</td>
          <td class="td-muted">{eng_val}</td>
          <td class="td-muted">{win_val}</td>
          <td class="td-score">{score_val:.1f}</td>
        </tr>"""
    st.markdown(f"""
    <table class="break-table">
      <thead><tr>
        <th>Name</th><th>Streak</th><th>Bi-wkly hrs</th>
        <th>Balance</th><th>Energy</th><th>Wins</th><th>Score</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>""",unsafe_allow_html=True)

# ── weights ───────────────────────────────────────────────
st.markdown('<div class="divider"></div>',unsafe_allow_html=True)
st.markdown('<div class="stitle">How scores are calculated</div>',unsafe_allow_html=True)
st.markdown("""
<div class="weights">
  <div class="wp">Streak <span>30%</span></div>
  <div class="wp">Bi-weekly hours <span>25%</span></div>
  <div class="wp">Passion balance <span>20%</span></div>
  <div class="wp">Avg energy <span>15%</span></div>
  <div class="wp">Wins logged <span>10%</span></div>
</div>
<div class="weights" style="margin-top:8px">
  <div class="wp">Elite <span>90+</span></div>
  <div class="wp">Star <span>75–89</span></div>
  <div class="wp">On Track <span>60–74</span></div>
  <div class="wp">Building <span>40–59</span></div>
  <div class="wp">Starting <span>0–39</span></div>
</div>
""",unsafe_allow_html=True)
