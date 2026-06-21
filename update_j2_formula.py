import sys; sys.stdout.reconfigure(encoding="utf-8")
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)

WINDOW = 7  # week length in days — keep in sync with NOMO_AppsScript.js
# Weekly RESET aligned to the member's start date (F2). The current week starts at
#   weekStart = F2 + INT((TODAY()-F2)/WINDOW) * WINDOW
# so day WINDOW+1 begins a fresh week (start 14th: wk1=14..20; day8=21st starts
# wk2 and only the 21st counts until that week fills).
WEEKSTART = f"($F$2+INT((TODAY()-$F$2)/{WINDOW})*{WINDOW})"
W      = f"(A$7:A$39>={WEEKSTART})*(A$7:A$39<=TODAY())"
STREAK = f"SUMPRODUCT({W}*(K$7:K$39=\"Yes\"))"
SUME   = f"SUMPRODUCT({W}*ISNUMBER(I$7:I$39)*I$7:I$39)"
CNTE   = f"SUMPRODUCT({W}*ISNUMBER(I$7:I$39))"
WINS   = f"SUMPRODUCT({W}*ISNUMBER(I$7:I$39)*(I$7:I$39>=3))"

J2 = (
    "=IFERROR(ROUND("
    f"MIN({STREAK},{WINDOW})/{WINDOW}*50"
    f"+IFERROR({SUME}/{CNTE},0)/5*30"
    f"+MIN({WINS},{WINDOW})/{WINDOW}*20"
    ",1),0)"
)

members = {
    "Admin (admin sheet)":  None,  # handled via open_sheet
    "Member Template":      "1OaO8jzrOtNmRoY9btCBYffhAfvv8Ei8rKPVqF7iO2AM",
    "Akshay Kumble":        "1LkvUNCR1UN9Y0OXCVIyFgD9ZT26dOKiS1_2-_yW_SfM",
    "Aditya N":             "1l5CXHu5wXTq5h9aEC4oJS2o2Zxet33E8vb0xWPmhTIM",
    "Shradha Vadhone":      "1tZ_W-YUOgu5eQmoXTjrjje_R7_Eq5xGgZN-EFun5hOY",
    "Kumble":               "1-0Ms8JuHtbT_MhgaxBN3ptq5P2NfenRYrm1qn_ahWVs",
}

from nomo_sheet import open_sheet
admin_ss = open_sheet()

sheets = {"Admin": admin_ss}
for name, sid in list(members.items())[1:]:
    sheets[name] = gc.open_by_key(sid)

for name, ss in sheets.items():
    try:
        tabs = [w.title for w in ss.worksheets()]
        log_tab = next((t for t in tabs if "Daily Log" in t), None)
        if not log_tab:
            print(f"{name}: No Daily Log tab found — tabs: {tabs}")
            continue
        log = ss.worksheet(log_tab)
        log.update(range_name="J2", values=[[J2]], value_input_option="USER_ENTERED")
        written = log.acell("J2", value_render_option="FORMULA").value
        print(f"{name}: J2 written OK" if "SUMPRODUCT" in written else f"{name}: PROBLEM - {written}")
    except Exception as e:
        print(f"{name}: ERROR - {e}")