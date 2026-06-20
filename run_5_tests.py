"""
5 test cases — write to Tracker, predict from Tracker, verify from Daily Log.
No cross-contamination between prediction and verification.
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8")
from datetime import date, timedelta
from nomo_sheet import open_sheet

ss = open_sheet()
trk = ss.worksheet("📅 Tracker")
log = ss.worksheet("📅 Daily Log")

EPOCH = date(1899, 12, 30)

def col_letter(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

# Tracker checkbox rows (0-indexed within get range)
# P1: rows 8-12 = sheet rows, P2: 15-19, P3: 22-26
# Cols D(4)=day1 .. AJ(36)=day33
P1_ROWS = [8,9,10,11,12]    # sheet row numbers
P2_ROWS = [15,16,17,18,19]
P3_ROWS = [22,23,24,25,26]
ALL_ROWS = P1_ROWS + P2_ROWS + P3_ROWS
DAYS = 33  # D..AJ

def clear_all_checkboxes():
    """Set all checkbox cells to FALSE."""
    batch = []
    for row in ALL_ROWS:
        for day in range(DAYS):
            c = col_letter(4 + day)
            batch.append({"range": f"{c}{row}", "values": [[False]]})
    trk.batch_update(batch, value_input_option="RAW")

def set_checks(pattern):
    """
    pattern = dict: { (passion_idx 0/1/2, subtask_idx 0-4, day_idx 0-32): True/False }
    Only sets True cells (rest already cleared).
    """
    row_map = [P1_ROWS, P2_ROWS, P3_ROWS]
    batch = []
    for (p, s, d), val in pattern.items():
        sheet_row = row_map[p][s]
        c = col_letter(4 + d)
        batch.append({"range": f"{c}{sheet_row}", "values": [[val]]})
    if batch:
        trk.batch_update(batch, value_input_option="RAW")

def predict_from_tracker():
    """Read Tracker only. Return (predicted_score, detail_lines)."""
    b35 = trk.acell("B35", value_render_option="UNFORMATTED_VALUE").value
    start_serial = trk.acell("B6", value_render_option="UNFORMATTED_VALUE").value
    data = trk.get("D8:AJ27", value_render_option="UNFORMATTED_VALUE")
    while len(data) < 20:
        data.append([])
    p1_rows = data[0:5]
    p2_rows = data[7:12]
    p3_rows = data[14:19]

    today = date.today()
    today_serial = (today - EPOCH).days
    window_start = today_serial - 15

    def checked(row, col):
        try: return bool(row[col])
        except: return False

    streak = energy_sum = energy_cnt = wins = 0
    lines = []
    for day_idx in range(33):
        day_serial = start_serial + day_idx
        if day_serial > today_serial:
            break
        p1 = sum(1 for r in p1_rows if checked(r, day_idx))
        p2 = sum(1 for r in p2_rows if checked(r, day_idx))
        p3 = sum(1 for r in p3_rows if checked(r, day_idx))
        total = p1 + p2 + p3
        energy_raw = total / b35 * 5 if b35 else 0
        energy = min(round(energy_raw), 5)
        energy = max(1, energy) if total > 0 else 0
        k_yes = total > 0
        in_window = window_start <= day_serial <= today_serial
        day_date = EPOCH + timedelta(days=int(day_serial))
        if in_window and k_yes:
            streak += 1
            energy_sum += energy
            energy_cnt += 1
        if in_window and k_yes:
            wins += 1
        lines.append(f"  day{day_idx+1} {day_date} P1={p1} P2={p2} P3={p3} E={energy} K={'Y' if k_yes else 'N'} win={'Y' if (in_window and k_yes) else 'N'}")

    avg_e = energy_sum / energy_cnt if energy_cnt else 0
    s = min(streak,15)/15*40
    e = avg_e/5*30
    w = min(wins,15)/15*20
    p = min(streak,15)/15*10
    total_score = round(s+e+w+p, 1)
    lines.append(f"  Streak={streak} AvgE={avg_e:.2f} Wins={wins}")
    lines.append(f"  S/40={s:.1f} E/30={e:.1f} W/20={w:.1f} P/10={p:.1f} => {total_score}")
    return total_score, lines

def verify_from_dlog(expected_streak_nonzero=True):
    """Poll Daily Log J2 until it stabilises (or 60s timeout)."""
    prev = None
    for attempt in range(12):   # up to 60 seconds
        time.sleep(5)
        j2 = log.acell("J2", value_render_option="UNFORMATTED_VALUE").value
        val = float(j2) if j2 else 0.0
        k7 = log.acell("K7", value_render_option="UNFORMATTED_VALUE").value
        d13 = trk.acell("D13", value_render_option="UNFORMATTED_VALUE").value
        print(f"    [poll {attempt+1}] D13={d13} K7={k7!r} J2={val}")
        if val == prev and attempt > 0:
            break   # stable
        prev = val
    return val

# ── TEST CASES ────────────────────────────────────────────────────────────────
# B35=7: P1 has 2 subtasks (rows 8-9), P2 has 3 (rows 15-17), P3 has 2 (rows 22-23)
# Actually reading from sheet:
b35_val = int(trk.acell("B35", value_render_option="UNFORMATTED_VALUE").value)

test_cases = {
    "TC1 — Perfect 11 days, all subtasks every day": {
        (p, s, d): True
        for p, rows in [(0, range(5)), (1, range(5)), (2, range(5))]
        for s in rows
        for d in range(11)  # day1..day11 (10 Jun - 20 Jun = today)
    },
    "TC2 — Only P1 subtask 1, all 11 days": {
        (0, 0, d): True for d in range(11)
    },
    "TC3 — All subtasks but only first 3 days": {
        (p, s, d): True
        for p in range(3) for s in range(5) for d in range(3)
    },
    "TC4 — Alternating days (odd days only, 11 days window)": {
        (p, s, d): True
        for p in range(3) for s in range(5)
        for d in [0,2,4,6,8,10]  # days 1,3,5,7,9,11
    },
    "TC5 — Zero (nothing checked)": {},
}

results = []
for tc_name, pattern in test_cases.items():
    print(f"\n{'='*60}")
    print(f"Running {tc_name}")
    clear_all_checkboxes()
    time.sleep(2)
    if pattern:
        set_checks(pattern)
    time.sleep(10)

    predicted, detail = predict_from_tracker()
    print("\n[TRACKER PREDICTION]")
    for l in detail:
        print(l)

    actual = verify_from_dlog(expected_streak_nonzero=bool(pattern))
    print(f"\n[DAILY LOG ACTUAL] J2 = {actual}")
    match = abs(predicted - actual) < 0.5
    print(f"MATCH: {'✅' if match else '❌'}  predicted={predicted}  actual={actual}")
    results.append((tc_name, predicted, actual, match))

print(f"\n{'='*60}")
print("FINAL RESULTS")
print(f"{'='*60}")
for tc, pred, act, ok in results:
    print(f"{'✅' if ok else '❌'}  {tc}")
    print(f"    Predicted={pred}  Actual={act}  Diff={abs(pred-act):.1f}")
passed = sum(1 for _,_,_,ok in results if ok)
print(f"\n{passed}/5 test cases passed")