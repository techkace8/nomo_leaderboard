import sys; sys.stdout.reconfigure(encoding="utf-8")
from datetime import date
from nomo_sheet import open_sheet

ss = open_sheet()
trk = ss.worksheet("📅 Tracker")

# ── read raw data ────────────────────────────────────────────
b35 = trk.acell("B35", value_render_option="UNFORMATTED_VALUE").value  # total subtasks
start_serial = trk.acell("B6", value_render_option="UNFORMATTED_VALUE").value  # start date serial

# rows 8-12 = P1 subtasks, 15-19 = P2, 22-26 = P3
# cols D(4)..AJ(36) = days 1..33
data = trk.get("D8:AJ27", value_render_option="UNFORMATTED_VALUE")
# pad rows to 20
while len(data) < 20:
    data.append([])

p1_rows = data[0:5]    # rows 8-12
p2_rows = data[7:12]   # rows 15-19
p3_rows = data[14:19]  # rows 22-26

today = date.today()
EPOCH = date(1899, 12, 30)
today_serial = (today - EPOCH).days
window_start = today_serial - 15

print(f"B35 (total subtasks) = {b35}")
print(f"Start serial = {start_serial} | Today serial = {today_serial} | Window [{window_start}..{today_serial}]")
print()

def checked(row, col):
    try: return bool(row[col])
    except: return False

print(f"{'Day':<6}{'Date':<12}{'P1ck':<6}{'P2ck':<6}{'P3ck':<6}{'Total':<7}{'E raw':<8}{'Energy':<8}{'K'}")
print("-"*65)

streak = energy_vals = wins = 0
energy_sum = energy_cnt = 0

for day_idx in range(33):  # cols 0..32 = D..AJ
    day_serial = start_serial + day_idx
    if day_serial > today_serial:
        break

    p1 = sum(1 for r in p1_rows if checked(r, day_idx))
    p2 = sum(1 for r in p2_rows if checked(r, day_idx))
    p3 = sum(1 for r in p3_rows if checked(r, day_idx))
    total_checked = p1 + p2 + p3

    energy_raw = total_checked / b35 * 5 if b35 else 0
    energy = round(energy_raw)
    energy = max(1, energy) if total_checked > 0 else 0

    k_yes = total_checked > 0

    day_date = EPOCH + __import__("datetime").timedelta(days=int(day_serial))
    in_window = window_start <= day_serial <= today_serial

    if in_window and k_yes:
        streak += 1
        if energy > 0:
            energy_sum += energy
            energy_cnt += 1
    if in_window and total_checked > 0:
        wins += 1  # proxy: logged = win

    print(f"{day_idx+1:<6}{str(day_date):<12}{p1:<6}{p2:<6}{p3:<6}{total_checked:<7}{energy_raw:<8.2f}{energy:<8}{'Yes' if k_yes else ''}")

print()
avg_e = energy_sum / energy_cnt if energy_cnt else 0
s = min(streak,15)/15*40
e = avg_e/5*30
w = min(wins,15)/15*20
p = min(streak,15)/15*10
total = round(s+e+w+p, 1)
print(f"Streak={streak}  AvgEnergy={avg_e:.2f}  Wins={wins}")
print(f"Streak/40={s:.1f}  Energy/30={e:.1f}  Wins/20={w:.1f}  Particip/10={p:.1f}")
print(f"TOTAL = {total}")