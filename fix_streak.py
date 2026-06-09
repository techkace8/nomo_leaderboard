import sys, openpyxl
sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook('NOMO_passion_tracker.xlsx')
ws = wb['⭐ My Score']

log = "'📅 Daily Log'"

# Streak & Participation: count distinct rows where ANY of D/F/H = "Yes" in last 15 days
# SUMPRODUCT handles the OR logic across columns
streak = (
    "=IFERROR(MIN(SUMPRODUCT((" + log + "!A$4:A$93>=TODAY()-15)*(" + log + "!A$4:A$93<=TODAY())*"
    "((" + log + "!D$4:D$93=\"Yes\")+(" + log + "!F$4:F$93=\"Yes\")+(" + log + "!H$4:H$93=\"Yes\")>0)),15)/15*40,0)"
)

energy = (
    "=IFERROR(AVERAGEIFS(" + log + "!I$4:I$93,"
    + log + "!A$4:A$93,\">=\"&(TODAY()-15),"
    + log + "!A$4:A$93,\"<=\"&TODAY())/5*30,0)"
)

wins = (
    "=IFERROR(MIN(COUNTIFS(" + log + "!A$4:A$93,\">=\"&(TODAY()-15),"
    + log + "!A$4:A$93,\"<=\"&TODAY(),"
    + log + "!J$4:J$93,\"<>\"\"\"),15)/15*20,0)"
)

participation = (
    "=IFERROR(MIN(SUMPRODUCT((" + log + "!A$4:A$93>=TODAY()-15)*(" + log + "!A$4:A$93<=TODAY())*"
    "((" + log + "!D$4:D$93=\"Yes\")+(" + log + "!F$4:F$93=\"Yes\")+(" + log + "!H$4:H$93=\"Yes\")>0)),15)/15*10,0)"
)

ws['D5'] = streak
ws['D6'] = energy
ws['D7'] = wins
ws['D8'] = participation

print('D5:', streak)
print('D6:', energy)
print('D7:', wins)
print('D8:', participation)

wb.save('NOMO_passion_tracker.xlsx')
print('Saved.')
