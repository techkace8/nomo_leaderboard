import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time
import requests
from datetime import datetime

# ── refresh button config ─────────────────────────────────
# Web App URL from: Apps Script → Deploy → New deployment → Web app.
# Paste the /exec URL here (or set it in Streamlit secrets as REFRESH_URL).
REFRESH_URL = st.secrets.get("REFRESH_URL", "")
SCRIPT_TOKEN = st.secrets.get("SCRIPT_TOKEN", "")  # set in Streamlit secrets — never hardcode
COOLDOWN_SECONDS = 60

st.set_page_config(
    page_title="NOMO — Top Achievers",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');

html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#ffffff!important}
[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="block-container"]{background:#ffffff!important}
.block-container{padding:3rem 4rem 5rem!important;max-width:1000px!important}
#MainMenu,footer,header{visibility:hidden!important}
[data-testid="stToolbar"]{display:none!important}
[data-testid="stToolbarActions"]{display:none!important}
.viewerBadge_container__1QSob{display:none!important}
.viewerBadge_link__1S137{display:none!important}
#stDecoration{display:none!important}
button[kind="header"]{display:none!important}
[data-testid="baseButton-header"]{display:none!important}

/* HEADER */
.nomo-title{font-family:'DM Serif Display',serif;font-size:2.6rem;font-weight:900;color:#111;letter-spacing:-.03em;line-height:1}
.nomo-title em{font-style:normal;text-transform:uppercase;color:#1a6b4a;letter-spacing:.01em}
.nomo-tag{font-size:10px;color:#aaa;letter-spacing:.14em;text-transform:uppercase;font-family:monospace;margin-top:8px}
.nomo-updated{font-size:11px;color:#aaa;font-family:monospace;text-align:left;padding-top:10px}
.nomo-divider{border:none;border-top:2px solid #111;margin:20px 0 32px}

/* INFO BAR */
.info-bar{background:#f8f8f6;border-left:3px solid #1a6b4a;padding:10px 16px;font-size:12px;color:#666;font-family:monospace;margin-bottom:28px}

/* METRICS */
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:2px solid #111;margin-bottom:36px}
.metric-cell{padding:20px 22px;border-right:2px solid #111}
.metric-cell:last-child{border-right:none}
.metric-lbl{font-size:9px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#aaa;font-family:monospace;margin-bottom:8px}
.metric-val{font-family:'DM Serif Display',serif;font-size:2.4rem;font-weight:700;color:#111;line-height:1}
.metric-sub{font-size:11px;color:#aaa;margin-top:4px}

/* SECTION TITLE */
.sec-title{font-size:9px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#aaa;font-family:monospace;margin-bottom:14px}

/* LEADERBOARD ROWS */
.lb-row{display:flex;align-items:center;gap:16px;padding:16px 20px;background:#fff;border:1.5px solid #111;margin-bottom:-1.5px}
.lb-row:first-child{border-radius:10px 10px 0 0}
.lb-row:last-child{border-radius:0 0 10px 10px;margin-bottom:0}
.lb-rank{font-family:'DM Serif Display',serif;font-size:1.1rem;font-weight:700;width:28px;text-align:center;flex-shrink:0;color:#111}
.lb-name{font-size:14px;font-weight:600;color:#111;width:110px;flex-shrink:0;letter-spacing:-.01em}
.lb-bar-bg{flex:1;height:5px;background:#f0f0ee;border-radius:0}
.lb-bar{height:100%;border-radius:0}
.lb-score{font-family:'DM Serif Display',serif;font-size:1.4rem;font-weight:700;color:#111;width:68px;text-align:right;flex-shrink:0;line-height:1}
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
.td-score{font-weight:700;color:#1a6b4a;font-family:'DM Serif Display',serif;font-size:15px}
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

/* REFRESH BUTTON wrap — floats right on desktop, full-width below title on mobile */
.refresh-btn-wrap{margin-bottom:6px}
@media(min-width:769px){
  .refresh-btn-wrap{position:absolute;top:1.2rem;right:2rem;width:160px}
}

/* REFRESH BUTTON — outlined pill matching the editorial design */
div[data-testid="stButton"] > button{
  background:#fff!important;
  color:#111!important;
  border:1.5px solid #111!important;
  border-radius:0!important;
  font-family:monospace!important;
  font-size:11px!important;
  font-weight:600!important;
  letter-spacing:.12em!important;
  text-transform:uppercase!important;
  padding:9px 4px!important;
  margin-top:18px!important;
  box-shadow:none!important;
  transition:background .12s ease,color .12s ease;
}
div[data-testid="stButton"] > button:hover:not(:disabled){
  background:#1a6b4a!important;
  color:#fff!important;
  border-color:#1a6b4a!important;
}
div[data-testid="stButton"] > button:active:not(:disabled){
  background:#111!important;border-color:#111!important;color:#fff!important;
}
div[data-testid="stButton"] > button:disabled{
  background:#f5f5f3!important;
  color:#aaa!important;
  border-color:#ddd!important;
  cursor:not-allowed;
}
div[data-testid="stButton"] > button:focus{box-shadow:none!important;outline:none!important}

.lb-denom{font-size:11px;color:#aaa;font-weight:400;white-space:nowrap}

@media(max-width:768px){
  .block-container{padding:1.4rem 1rem 3rem!important}
  .nomo-title{font-size:1.7rem!important;line-height:1.1}
  .nomo-tag{font-size:9px!important}
  .nomo-updated{font-size:10px!important;text-align:left!important;padding-top:6px!important}
  .nomo-divider{margin:10px 0 18px!important}
  div[data-testid="stButton"] > button{margin-top:4px!important;padding:8px 4px!important;font-size:11px!important}

  /* metrics: 2x2 grid */
  .metric-grid{grid-template-columns:repeat(2,1fr)!important}
  .metric-cell{padding:16px 14px!important}
  .metric-val{font-size:2rem!important}
  .metric-cell:nth-child(2){border-right:none!important}
  .metric-cell:nth-child(3){border-top:2px solid #111!important}
  .metric-cell:nth-child(4){border-top:2px solid #111!important;border-right:none!important}

  /* leaderboard: name+score+badge on row 1, full-width bar on row 2 */
  .lb-row{flex-wrap:wrap;gap:7px 10px;padding:13px 14px}
  .lb-rank{font-size:1rem!important;width:24px!important}
  .lb-name{flex:1!important;width:auto!important;font-size:14px!important;min-width:0}
  .lb-score{font-size:1.25rem!important;width:auto!important;flex-shrink:0}
  .lb-denom{font-size:10px!important}
  .lb-chg{width:auto!important;flex-shrink:0;min-width:34px}
  .lb-badge{font-size:8px!important;padding:3px 7px!important;flex-shrink:0}
  .lb-bar-bg{width:100%!important;order:9;flex-basis:100%;height:6px!important}

  .wt-row{flex-wrap:wrap}
  .wt-pill{flex-basis:33%!important;border-bottom:1.5px solid #111}
  .band-row{flex-wrap:wrap}
  .band-pill{flex-basis:33%!important;border-bottom:1.5px solid #111}
  .bd-table{font-size:11px!important}
  .bd-table th,.bd-table td{padding:7px 8px!important}
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
SCOPES = ["https://spreadsheets.google.com/feeds",
          "https://www.googleapis.com/auth/drive"]

# Top_Achievers layout: row 1 banner, row 2 subtitle, row 3 blank,
# row 4 = column headers, row 5+ = data.
HEADER_ROW = 4

def _read_leaderboard(ws):
    """Build a DataFrame from the Top_Achievers tab, accounting for the
    styled banner rows above the real header (row 4). Skips empty member
    slots — only members who have actually been scored are kept."""
    rows = ws.get_all_values()              # list of lists, all cells as strings
    if len(rows) < HEADER_ROW:
        return pd.DataFrame()
    # H3 (row 3, col 8) holds "Synced: … IST" written by the Apps Script —
    # the same data-freshness stamp for every viewer. (Rows 1-2 are merged
    # banner cells, so H3 is the first free cell.) Stash it on the frame.
    synced = ""
    if len(rows) >= 3 and len(rows[2]) >= 8:
        synced = rows[2][7].strip()
    headers = [h for h in rows[HEADER_ROW - 1] if h.strip()]
    ncol = len(headers)
    # locate NAME and NOMO SCORE columns
    name_i = next((i for i, h in enumerate(headers) if "NAME" in h.upper()), 1)
    score_i = next((i for i, h in enumerate(headers)
                    if "NOMO" in h.upper() and "SCORE" in h.upper()), None)
    data = []
    for r in rows[HEADER_ROW:]:             # data starts the row after headers
        cells = (r + [""] * ncol)[:ncol]    # pad/trim to header width
        if not cells[name_i].strip():       # no NAME → empty slot
            continue
        if score_i is not None and not cells[score_i].strip():
            continue                        # placeholder member, not yet scored
        data.append(cells)
    df = pd.DataFrame(data, columns=headers)
    df.attrs["synced"] = synced
    return df

@st.cache_data(ttl=300)
def load_sheet(url, creds_json):
    """Connect using a service-account JSON string (sidebar path)."""
    try:
        c = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
        gc = gspread.authorize(c)
        ws = gc.open_by_url(url).worksheet("🏆 Top_Achievers")
        return _read_leaderboard(ws), None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=300)
def load_sheet_from_secrets():
    """Auto-connect using SHEET_URL + [gcp_service_account] in Streamlit secrets."""
    try:
        sa = dict(st.secrets["gcp_service_account"])
        url = st.secrets["SHEET_URL"]
        c = Credentials.from_service_account_info(sa, scopes=SCOPES)
        gc = gspread.authorize(c)
        ws = gc.open_by_url(url).worksheet("🏆 Top_Achievers")
        return _read_leaderboard(ws), None
    except Exception as e:
        return None, str(e)

def has_secrets():
    try:
        return "gcp_service_account" in st.secrets and "SHEET_URL" in st.secrets
    except Exception:
        return False

def trigger_sync():
    """Call the Apps Script Web App to recompute the leaderboard on demand.
    Returns (ok: bool, message: str)."""
    if not REFRESH_URL:
        return False, "No REFRESH_URL configured"
    try:
        params = {"token": SCRIPT_TOKEN} if SCRIPT_TOKEN else {}
        r = requests.get(REFRESH_URL, params=params, timeout=60)
        data = r.json()
        if data.get("ok"):
            return True, "Synced"
        return False, data.get("error", "Sync failed")
    except Exception as e:
        return False, str(e)

def sample():
    return pd.DataFrame([
        {"RANK":1,"NAME":"Aditya",  "STREAK":14,"AVG ENERGY":4.4,"WINS":13,"NOMO SCORE":82.1,"PREV SCORE":78.5},
        {"RANK":2,"NAME":"Rohan",   "STREAK":13,"AVG ENERGY":3.9,"WINS":11,"NOMO SCORE":79.4,"PREV SCORE":81.0},
        {"RANK":3,"NAME":"Meera",   "STREAK":10,"AVG ENERGY":3.7,"WINS":9, "NOMO SCORE":63.2,"PREV SCORE":60.0},
        {"RANK":4,"NAME":"Priya",   "STREAK":8, "AVG ENERGY":4.1,"WINS":7, "NOMO SCORE":55.8,"PREV SCORE":54.0},
        {"RANK":5,"NAME":"Karthik", "STREAK":6, "AVG ENERGY":3.5,"WINS":5, "NOMO SCORE":44.7,"PREV SCORE":46.0},
        {"RANK":6,"NAME":"Divya",   "STREAK":5, "AVG ENERGY":3.2,"WINS":4, "NOMO SCORE":36.1,"PREV SCORE":33.0},
    ])

# ── sidebar ───────────────────────────────────────────────
url, creds = "", ""
with st.sidebar:
    if has_secrets():
        st.markdown("### ✅ Connected")
        st.caption("Live leaderboard — auto-connected via app secrets.")
    else:
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
if has_secrets():
    # Cloud path: auto-connect to the configured leaderboard
    df, err = load_sheet_from_secrets()
    if err: st.error(f"Could not load live leaderboard: {err}")
elif url and creds:
    # Manual path: credentials pasted in the sidebar
    df, err = load_sheet(url, creds)
    if err: st.sidebar.error(err)
if df is None or df.empty:
    df = sample(); using_sample = True

sc = next((c for c in df.columns if "NOMO" in c.upper() and "SCORE" in c.upper()), None)
pc = next((c for c in df.columns if "PREV" in c.upper()), None)
nc = next((c for c in df.columns if "NAME" in c.upper()), "NAME")
if sc:
    df[sc] = pd.to_numeric(df[sc], errors="coerce").fillna(0)
    df = df.sort_values(sc, ascending=False).reset_index(drop=True)
    df["RANK"] = df.index + 1

# ── header ────────────────────────────────────────────────
synced = df.attrs.get("synced", "") if df is not None else ""
stamp = synced if synced else "Sample data"
last = st.session_state.get("last_refresh", 0.0)
cooling = (time.time() - last) < COOLDOWN_SECONDS

_c1, _c2 = st.columns([1, 3])
with _c1:
    st.image("nomo_logo.jpg", width=140)
with _c2:
    st.markdown('<div class="nomo-title" style="padding-top:18px"><em>Top Achievers</em></div>', unsafe_allow_html=True)
st.markdown('<div class="nomo-tag">15-day rolling · Discover → Track → Connect → Build → Sustain</div>', unsafe_allow_html=True)
st.markdown(f'<div class="nomo-updated">{stamp}</div>', unsafe_allow_html=True)

# Refresh button — full width on mobile, right-aligned pill on desktop via CSS
st.markdown('<div class="refresh-btn-wrap">', unsafe_allow_html=True)
if not REFRESH_URL:
    st.button("↻ REFRESH", disabled=True, use_container_width=True,
              help="Set REFRESH_URL in secrets to enable live refresh")
elif cooling:
    st.button("↻ UPDATED", disabled=True, use_container_width=True,
              help="Just refreshed — wait a moment before syncing again")
else:
    if st.button("↻ REFRESH", use_container_width=True,
                 help="Recompute the leaderboard from everyone's latest logs"):
        with st.spinner("Syncing leaderboard…"):
            ok, msg = trigger_sync()
            if ok:
                time.sleep(4)
        st.session_state["last_refresh"] = time.time()
        if ok:
            load_sheet.clear()
            load_sheet_from_secrets.clear()
            st.rerun()
        else:
            st.toast(f"Refresh failed: {msg}", icon="⚠️")
st.markdown('</div>', unsafe_allow_html=True)

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
  <div class="metric-cell"><div class="metric-lbl">Multipassionates</div><div class="metric-val">{total}</div><div class="metric-sub">in Total</div></div>
  <div class="metric-cell"><div class="metric-lbl">Avg score</div><div class="metric-val">{avg}</div><div class="metric-sub">out of 100</div></div>
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
        eng = next((row.get(c,"—") for c in df.columns if "ENERGY" in c.upper()), "—")
        win = next((row.get(c,"—") for c in df.columns if "WIN" in c.upper()), "—")
        prv = next((row.get(c,"—") for c in df.columns if "PREV" in c.upper()), "—")
        rows += f"""<tr>
          <td>{row.get(nc,"—")}</td>
          <td class="td-m">{stk}</td><td class="td-m">{eng}</td>
          <td class="td-m">{win}</td><td class="td-m">{prv}</td>
          <td class="td-score">{sv:.1f}</td>
        </tr>"""
    st.markdown(f"""
    <table class="bd-table">
      <thead><tr>
        <th>Name</th><th>Streak</th><th>Avg Energy</th>
        <th>Wins</th><th>Prev Score</th><th>Score</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>""", unsafe_allow_html=True)

# ── scoring weights ───────────────────────────────────────
st.markdown('<hr class="nomo-divider" style="margin-top:32px">', unsafe_allow_html=True)
st.markdown('<div class="sec-title">How scores are calculated</div>', unsafe_allow_html=True)
st.markdown("""
<div class="wt-row">
  <div class="wt-pill">Streak<span>40%</span></div>
  <div class="wt-pill">Avg energy<span>30%</span></div>
  <div class="wt-pill">Wins logged<span>20%</span></div>
  <div class="wt-pill">Prev score<span>display only</span></div>
</div>
<div class="band-row" style="margin-top:10px">
  <div class="band-pill" style="background:#e8f5f0;color:#085041">Elite<br><b>90+</b></div>
  <div class="band-pill" style="background:#fdf3e3;color:#7a4a0a">Star<br><b>75–89</b></div>
  <div class="band-pill" style="background:#e8f0fb;color:#0c3d8a">On Track<br><b>60–74</b></div>
  <div class="band-pill" style="background:#f0eefb;color:#3c2a8a">Building<br><b>40–59</b></div>
  <div class="band-pill" style="background:#f5f5f5;color:#888">Starting<br><b>0–39</b></div>
</div>
""", unsafe_allow_html=True)
