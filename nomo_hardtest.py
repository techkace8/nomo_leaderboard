"""
NOMO HARD TEST — pre-prod rigorous validation harness.

Design principles:
  * INDEPENDENT reference implementation of the scoring spec (does NOT read the
    sheet's own J2 formula — re-derives expected score from first principles).
  * "Bypass TODAY()" is done by moving the START DATE (F2) relative to the real
    today, since the sheet's TODAY() cannot be overridden. This lets us position
    the challenge at any day/week boundary and test future + out-of-window dates.
  * Checkboxes are set by PHYSICAL ROW, independent of subtask NAMES — so we can
    reproduce the "deleted subtasks but boxes still checked" loophole (B35=0).
  * Every Google API call is wrapped with exponential backoff (429-safe) so the
    suite survives 4 agents hitting the API in parallel on different sheets.

Usage:
  python nomo_hardtest.py --sheet member         # one sheet
  python nomo_hardtest.py --all                  # all four, sequential
"""
import sys, time, math, argparse, json, copy
sys.stdout.reconfigure(encoding="utf-8")
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError
from datetime import date, timedelta

EPOCH  = date(1899, 12, 30)
WINDOW = 7  # week length — the spec under test

SHEETS = {
    "member":  "1OaO8jzrOtNmRoY9btCBYffhAfvv8Ei8rKPVqF7iO2AM",
    "akshay":  "1LkvUNCR1UN9Y0OXCVIyFgD9ZT26dOKiS1_2-_yW_SfM",
    "aditya":  "1l5CXHu5wXTq5h9aEC4oJS2o2Zxet33E8vb0xWPmhTIM",
    "shradha": "1tZ_W-YUOgu5eQmoXTjrjje_R7_Eq5xGgZN-EFun5hOY",
}

P1_ROWS = [8, 9, 10, 11, 12]
P2_ROWS = [15, 16, 17, 18, 19]
P3_ROWS = [22, 23, 24, 25, 26]
ROWS    = [P1_ROWS, P2_ROWS, P3_ROWS]
ALL_CB_ROWS = P1_ROWS + P2_ROWS + P3_ROWS
DAYS = 33  # columns D(4)..AJ(36)


# ── API plumbing ───────────────────────────────────────────────────────────────
def _auth():
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    return gspread.authorize(creds)

def backoff(fn, *a, **k):
    """Run a gspread call with exponential backoff on 429/5xx."""
    delay = 2.0
    for attempt in range(7):
        try:
            return fn(*a, **k)
        except APIError as e:
            code = getattr(e.response, "status_code", None)
            if code in (429, 500, 502, 503) and attempt < 6:
                time.sleep(delay); delay = min(delay * 2, 40)
                continue
            raise

def backoff_batch(ws, batch, **kw):
    """batch_update with backoff. gspread mutates the batch dicts IN PLACE
    (prepends the sheet title to each range), so a naive retry double-prefixes
    the range -> APIError 400. Pass a FRESH deep copy on every attempt."""
    delay = 2.0
    for attempt in range(7):
        try:
            return ws.batch_update(copy.deepcopy(batch), **kw)
        except APIError as e:
            code = getattr(e.response, "status_code", None)
            if code in (429, 500, 502, 503) and attempt < 6:
                time.sleep(delay); delay = min(delay * 2, 40)
                continue
            raise

def col_letter(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


# ── sheet mutation ───────────────────────────────────────────────────────────
def set_start_date(log, start_d):
    """Write F2 as an unambiguous ISO date so the whole A-column re-derives."""
    backoff(log.update, range_name="F2",
            values=[[start_d.isoformat()]], value_input_option="USER_ENTERED")

def set_subtask_names(trk, n1, n2, n3):
    """Name the first n subtasks per passion (drives B13/B20/B27 -> B35)."""
    batch = []
    for rows, n in zip(ROWS, (n1, n2, n3)):
        vals = [["task" if i < n else ""] for i in range(5)]
        batch.append({"range": f"B{rows[0]}:B{rows[-1]}", "values": vals})
    backoff_batch(trk, batch, value_input_option="USER_ENTERED")

def clear_all_checks(trk):
    batch = [{"range": f"{col_letter(4 + d)}{row}", "values": [[False]]}
             for row in ALL_CB_ROWS for d in range(DAYS)]
    backoff_batch(trk, batch, value_input_option="RAW")

def set_checks(trk, checks):
    """checks: {day_idx: (c1,c2,c3)} -> check first c physical rows per passion."""
    batch = []
    for day_idx, counts in checks.items():
        col = col_letter(4 + day_idx)
        for rows, c in zip(ROWS, counts):
            for i, row in enumerate(rows):
                if i < c:
                    batch.append({"range": f"{col}{row}", "values": [[True]]})
    if batch:
        backoff_batch(trk, batch, value_input_option="RAW")

def read_j2(log):
    v = backoff(log.acell, "J2", value_render_option="UNFORMATTED_VALUE").value
    return float(v) if v not in (None, "") else 0.0


# ── INDEPENDENT reference implementation (the spec, re-derived) ──────────────────
def rnd(x):
    """Google-Sheets ROUND: half away from zero (x >= 0 here)."""
    return math.floor(x + 0.5)

def reference_score(start_serial, names, checks, today_serial):
    """Compute the expected NOMO score WITHOUT reading the sheet formula."""
    n1, n2, n3 = names
    b35 = n1 + n2 + n3
    if today_serial < start_serial:
        return 0.0  # challenge not begun
    week_start = start_serial + ((today_serial - start_serial) // WINDOW) * WINDOW

    streak = wins = e_sum = e_cnt = 0
    for day_idx in range(DAYS):
        day_serial = start_serial + day_idx
        if day_serial > today_serial:
            continue  # FUTURE dates never count
        c1, c2, c3 = checks.get(day_idx, (0, 0, 0))
        c1 = min(c1, 5); c2 = min(c2, 5); c3 = min(c3, 5)  # physical row cap
        total = c1 + c2 + c3
        # energy mirrors sheet: MIN(ROUND(total/B35*5),5); blank when B35=0 or rounds to 0
        energy = min(rnd(total / b35 * 5), 5) if b35 > 0 and total > 0 else 0
        k_yes = (c1 >= 1 or c2 >= 1 or c3 >= 1)  # col K = any passion worked
        in_window = week_start <= day_serial <= today_serial
        if in_window and k_yes:
            streak += 1
        if in_window and energy >= 1:   # blank energy excluded from average
            e_sum += energy; e_cnt += 1
        if in_window and energy >= 3:
            wins += 1
    avg = e_sum / e_cnt if e_cnt else 0
    score = (min(streak, WINDOW) / WINDOW * 50
             + avg / 5 * 30
             + min(wins, WINDOW) / WINDOW * 20)
    return round(score, 1)


# ── scenario suite (20) ──────────────────────────────────────────────────────
# Each: start_offset = how many days ago the challenge started (today = day start_offset).
#       names = (n1,n2,n3); checks = {day_idx:(c1,c2,c3)}; note = intent.
def build_scenarios(today_serial):
    S = []
    def add(name, start_offset, names, checks, note):
        S.append(dict(name=name, start_offset=start_offset, names=names,
                      checks=checks, note=note))

    # --- basics / day 1 ---
    add("01 day1 perfect", 0, (5,5,5), {0:(5,5,5)},
        "fresh day, all subtasks -> energy5, streak1, win1")
    add("02 day1 one-box (energy rounds to blank)", 0, (5,5,5), {0:(1,0,0)},
        "1/15 -> ROUND0 -> blank energy; streak still counts (loophole check)")
    add("03 day1 three-box energy1", 0, (5,5,5), {0:(1,1,1)},
        "3/15 -> energy1; no win")

    # --- full week 1 ---
    add("04 day7 perfect week", 6, (5,5,5),
        {d:(5,5,5) for d in range(7)}, "7/7 days full -> 100")
    add("05 day7 4of7 full", 6, (5,5,5),
        {d:(5,5,5) for d in range(4)}, "4 full days -> streak4,wins4")

    # --- WEEK RESET boundary (day 8) ---
    add("06 day8 reset, today empty", 7, (5,5,5),
        {d:(5,5,5) for d in range(7)}, "week1 full but today empty -> 0 (RESET)")
    add("07 day8 reset, today full", 7, (5,5,5),
        {**{d:(5,5,5) for d in range(7)}, 7:(5,5,5)}, "only today counts -> 40")
    add("08 day8 reset, today energy3", 7, (5,5,5),
        {**{d:(5,5,5) for d in range(7)}, 7:(3,3,0)}, "today 6/15->energy2? check")

    # --- FUTURE date exclusion ---
    add("09 future ignored", 0, (5,5,5), {0:(5,5,5), 1:(5,5,5), 5:(5,5,5)},
        "today full + future days full -> still 40")
    add("10 future only -> 0", 0, (5,5,5), {1:(5,5,5), 3:(5,5,5)},
        "only future checked, today empty -> 0")
    add("11 full load incl future", 6, (5,5,5),
        {d:(5,5,5) for d in range(DAYS)}, "all 33 days full; only days0-6 count -> 100")

    # --- OUT-OF-WINDOW (previous week) exclusion ---
    add("12 prev-week ignored", 7, (5,5,5),
        {d:(5,5,5) for d in range(7)}, "day8: only week1 checked -> 0")
    add("13 week2 mid (day10)", 9, (5,5,5),
        {**{d:(5,5,5) for d in range(7)}, 7:(5,5,5), 8:(5,5,5), 9:(5,5,5)},
        "weekStart=day8; last 3 days count -> streak3")
    add("14 week3 boundary (day15)", 14, (5,5,5),
        {d:(5,5,5) for d in range(14)}, "day15 reset; today empty -> 0")

    # --- SUBTASK count permutations / deletion loophole ---
    add("15 names deleted, boxes checked", 0, (0,0,0), {0:(2,2,1)},
        "B35=0 div-by-zero -> energy blank; streak counts -> 7.1 (LOOPHOLE)")
    add("16 names(1,0,0) single", 0, (1,0,0), {0:(1,0,0)},
        "B35=1, 1 check -> energy5 -> 40")
    add("17 asym names(2,3,0)", 0, (2,3,0), {0:(1,1,0)},
        "B35=5, 2 checks -> energy2")
    add("18 energy cap (overcheck)", 0, (2,2,2), {0:(5,5,5)},
        "15 boxes / B35=6 -> 12.5 -> MIN cap 5 -> 40 ([15/6] bug guard)")

    # --- rounding boundaries ---
    add("19 round 2.5 -> 3", 0, (5,5,0), {0:(5,0,0)},
        "5/10*5=2.5 -> ROUND up to 3 -> win")
    add("20 round 1.5 -> 2", 0, (5,5,0), {0:(3,0,0)},
        "3/10*5=1.5 -> ROUND to 2 -> no win")

    # attach absolute start serials
    for s in S:
        s["start_serial"] = today_serial - s["start_offset"]
    return S


# ── engine ───────────────────────────────────────────────────────────────────
def run_sheet(key, verbose=True):
    gc = _auth()
    ss = backoff(gc.open_by_key, SHEETS[key])
    log = ss.worksheet("📅 Daily Log")
    trk = ss.worksheet("🎯 Tracker")

    today_serial = (date.today() - EPOCH).days
    saved_f2 = backoff(log.acell, "F2", value_render_option="FORMULA").value

    scenarios = build_scenarios(today_serial)
    results = []
    try:
        for sc in scenarios:
            start_d = EPOCH + timedelta(days=sc["start_serial"])
            set_start_date(log, start_d)
            set_subtask_names(trk, *sc["names"])
            clear_all_checks(trk)
            set_checks(trk, sc["checks"])
            time.sleep(2.2)  # let TODAY()-driven formulas settle before read
            actual = read_j2(log)
            expected = reference_score(sc["start_serial"], sc["names"],
                                       sc["checks"], today_serial)
            ok = abs(actual - expected) < 0.15
            results.append(dict(name=sc["name"], expected=expected, actual=actual,
                                ok=ok, note=sc["note"]))
            if verbose:
                flag = "PASS" if ok else "FAIL"
                print(f"  [{flag}] {sc['name']:38} exp={expected:6} act={actual:6}  {sc['note']}")
    finally:
        # ALWAYS restore start date + clean checkboxes, even on crash
        backoff(log.update, range_name="F2", values=[[saved_f2]],
                value_input_option="USER_ENTERED")
        clear_all_checks(trk)

    passed = sum(r["ok"] for r in results)
    print(f"\n{key.upper()}: {passed}/{len(results)} passed")
    fails = [r for r in results if not r["ok"]]
    if fails:
        print("  FAILURES:")
        for r in fails:
            print(f"    {r['name']}: expected {r['expected']} got {r['actual']} — {r['note']}")
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", choices=list(SHEETS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true", help="emit JSON summary")
    args = ap.parse_args()

    targets = list(SHEETS) if args.all else [args.sheet or "member"]
    summary = {}
    for k in targets:
        print(f"\n{'='*70}\nHARD TEST — sheet: {k}\n{'='*70}")
        res = run_sheet(k)
        summary[k] = {"passed": sum(r["ok"] for r in res), "total": len(res),
                      "fails": [r["name"] for r in res if not r["ok"]]}
    if args.json:
        print("\nJSON_SUMMARY=" + json.dumps(summary))