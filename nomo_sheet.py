"""
NOMO — direct Google Sheet access helper.

Reusable connection layer so other scripts can edit the live sheet
without re-doing auth. Uses the service account key in service_account.json.

Usage:
    from nomo_sheet import open_sheet
    ss = open_sheet()                  # opens the default NOMO sheet
    log = ss.worksheet("📅 Daily Log")
"""
import gspread
from google.oauth2.service_account import Credentials

# The live NOMO sheet (the one shared with the service account)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1YZ0b-f6Kyl8r60sXf0jBYo63YfLHe0KPM9Q62CQnxts/edit"

KEY_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def client():
    """Authorized gspread client."""
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def open_sheet(url: str = SHEET_URL):
    """Open the spreadsheet by URL and return the Spreadsheet object."""
    return client().open_by_url(url)


if __name__ == "__main__":
    # Connection smoke test
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    ss = open_sheet()
    print("Connected to:", ss.title)
    print("Tabs:")
    for ws in ss.worksheets():
        print(f"  - {ws.title}  ({ws.row_count}x{ws.col_count})")
