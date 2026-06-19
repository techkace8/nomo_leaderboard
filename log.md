# NOMO — Build Log

A running record of what's been built and key decisions. Newest first.

---

## 2026-06-09 — System working end-to-end ✅

**Milestone:** Full pipeline live and verified with two real members on two
Gmail accounts (Akshay 46.1, Techkace 41.2) — no duplicates, clean ranking.

### Architecture (data flow)
```
Member sheets (separate Gmails, shared with admin account)
  → "sheet_link" tab holds their URLs (col B, row 2 down)
  → Apps Script syncScores() reads each, computes score, ranks
  → writes admin's "🏆 Top_Achievers" tab
  → Streamlit app reads it live, shows leaderboard + ↻ Refresh button
```

### Scoring (15-day rolling window, unified across Apps Script + ⭐ My Score)
| Component | Weight | Rule |
|---|---|---|
| Streak | 40% | `min(days/15,1)*40` — a day counts if ANY of D/F/H = "Yes" |
| Avg Energy | 30% | `avg(energy)/5*30` |
| Wins | 20% | `min(wins/15,1)*20` |
| Participation | 10% | showed up at all |

### Key components
- **`app.py`** — Streamlit Cloud app. Auto-connects via secrets, reads
  Top_Achievers (header on row 4, skips banner), shows ranked board.
  ↻ REFRESH button calls the Web App, then page goes static (no polling).
- **`NOMO_AppsScript.js`** — `syncScores` (hourly trigger + Web App `doGet`).
  Reads member URLs from the **sheet_link** tab. Token-guarded.
- **`nomo_sheet.py`** — service-account helper to edit the live sheet from
  Python (no Excel open/close).
- **`gen_secrets.py`** — generates the Streamlit secrets TOML (local only).

### Bugs fixed today
1. **Sample data wouldn't go live** — `get_all_records()` choked on the
   row-1 styled banner. Fixed: `_read_leaderboard()` uses row 4 as headers,
   skips banner + empty member slots.
2. **Duplicate/mismatched names on refresh** — `syncScores` wrote members
   by fixed array position then sorted in place, so names and scores drifted.
   Fixed: compute into memory → sort → clear → write once; PREV SCORE carried
   by name, not row position.
3. **Refresh hit the sheet repeatedly** — per-second rerun loop for the
   countdown animation. Removed; page is now static after a refresh.
4. **Member URLs wiped on re-paste** — moved them out of the script into the
   `sheet_link` tab. Add a member = add a row.

### Setup decisions
- **Service account** `nomo-editor@nomo-498911.iam.gserviceaccount.com`
  (project `nomo-498911`) — shared on the admin sheet as Editor.
- **Refresh trigger:** hourly (manual button covers on-demand). Can bump to
  15/5 min later — quota is a non-issue (~5s/run, ~90 min/day budget).
- **Token** lives only in Streamlit secrets + the deployed script. Public
  repo has a placeholder.
- **Everything is free** — Sheets, Apps Script, Streamlit Cloud, GitHub.

### Add a member (the workflow now)
1. They make their own copy of the tracker.
2. They share it with the **admin account** (Viewer/Editor).
3. Add a row in the **sheet_link** tab with their sheet URL.
4. Next hourly sync (or a Refresh click) picks them up automatically.
