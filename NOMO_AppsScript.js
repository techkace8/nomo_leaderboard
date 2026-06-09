// NOMO Daily Tracker — Apps Script
// Paste in: Extensions → Apps Script → save
// Set trigger: Triggers → Add → syncScores → Time-driven → Day timer → 11pm
// Add more mentees: just add their URL to the array — no other changes needed

const MENTEE_SHEETS = [
  "https://docs.google.com/spreadsheets/d/1iVh6CR94BuF5QTdg5krQeMwUuuqlYrfpcuEkpfAViao/edit?usp=sharing", // Multipassionate 1
  "PASTE_SHEET_URL_HERE", // Multipassionate 2
  "PASTE_SHEET_URL_HERE", // Multipassionate 3
  "PASTE_SHEET_URL_HERE", // Multipassionate 4
  "PASTE_SHEET_URL_HERE", // Multipassionate 5
  "PASTE_SHEET_URL_HERE", // Multipassionate 6
  "PASTE_SHEET_URL_HERE", // Multipassionate 7
  "PASTE_SHEET_URL_HERE", // Multipassionate 8
  "PASTE_SHEET_URL_HERE", // Multipassionate 9
  "PASTE_SHEET_URL_HERE", // Multipassionate 10
];

// Convert any date value from Google Sheets to a clean JS Date at midnight
function parseSheetDate(val) {
  if (!val || val === "") return null;
  try {
    if (val instanceof Date) {
      const d = new Date(val);
      d.setHours(0, 0, 0, 0);
      return d;
    }
    const str = val.toString().trim();
    if (/^\d{2}-\d{2}-\d{4}$/.test(str)) {
      const [dd, mm, yyyy] = str.split("-");
      const d = new Date(`${yyyy}-${mm}-${dd}`);
      d.setHours(0, 0, 0, 0);
      return d;
    }
    const d = new Date(val);
    d.setHours(0, 0, 0, 0);
    return isNaN(d.getTime()) ? null : d;
  } catch(e) { return null; }
}

function syncScores() {
  const master = SpreadsheetApp.getActiveSpreadsheet();
  const lb = master.getSheetByName("🏆 Top_Achievers");

  const today = new Date(); today.setHours(0,0,0,0);
  const windowStart = new Date(today);
  windowStart.setDate(today.getDate() - 15);

  const needed = MENTEE_SHEETS.length + 4;
  if (lb.getLastRow() < needed) lb.insertRowsAfter(lb.getLastRow(), needed - lb.getLastRow());

  MENTEE_SHEETS.forEach((url, i) => {
    try {
      if (!url || url === "PASTE_SHEET_URL_HERE") return;

      const row = i + 5;
      const ss = SpreadsheetApp.openByUrl(url);
      const profile = ss.getSheetByName("👤 My Profile");
      const log = ss.getSheetByName("📅 Daily Log");
      if (!profile || !log) return;

      // name
      const name = profile.getRange("D4").getValue();
      if (name && !name.toString().includes("←") && name.toString().trim() !== "") {
        lb.getRange(row, 2).setValue(name.toString().trim());
      }

      // read log A4:J93 — cols: A=date, B=day, C=P1, D=yes/no, E=P2, F=yes/no, G=P3, H=yes/no, I=energy, J=win
      const logData = log.getRange("A4:J93").getValues();

      const window15 = logData.filter(r => {
        const d = parseSheetDate(r[0]);
        if (!d) return false;
        if (!r[2] || r[2] === "") return false;
        return d >= windowStart && d <= today;
      });

      Logger.log(`${name}: ${window15.length} rows in 15-day window`);

      if (window15.length === 0) {
        // save prev before zeroing
        const curr = lb.getRange(row, 6).getValue();
        if (curr !== "" && curr !== 0) lb.getRange(row, 7).setValue(curr);
        lb.getRange(row, 3, 1, 4).setValues([[0, 0, 0, 0]]);
        return;
      }

      // 1. STREAK — distinct days shown up (at least one Yes in D/F/H)
      const shownUpDays = new Set();
      window15.forEach(r => {
        const yesNo = [r[3], r[5], r[7]].map(v => (v||"").toString().trim().toLowerCase());
        if (yesNo.includes("yes")) {
          const d = parseSheetDate(r[0]);
          if (d) shownUpDays.add(d.toDateString());
        }
      });
      const streak = shownUpDays.size;
      const streakScore = Math.min(streak / 15, 1) * 40;

      // 2. AVG ENERGY (col I = index 8)
      const energies = window15.map(r => parseInt(r[8])).filter(e => !isNaN(e) && e > 0);
      const avgEnergy = energies.length > 0 ? energies.reduce((a,b) => a+b, 0) / energies.length : 0;
      const energyScore = (avgEnergy / 5) * 30;

      // 3. WINS (col J = index 9)
      const wins = window15.filter(r => r[9] && r[9].toString().trim() !== "").length;
      const winsScore = Math.min(wins / 15, 1) * 20;

      // 4. MISSING 10% — leave as participation bonus (showed up at all)
      const participationScore = Math.min(streak / 15, 1) * 10;

      const total = Math.round((streakScore + energyScore + winsScore + participationScore) * 10) / 10;

      // save prev score before overwriting
      const curr = lb.getRange(row, 6).getValue();
      if (curr !== "" && curr !== total) lb.getRange(row, 7).setValue(curr);

      // write: col3=streak, col4=avgEnergy, col5=wins, col6=nomoScore, col7=prevScore(already set above)
      lb.getRange(row, 3).setValue(streak);
      lb.getRange(row, 4).setValue(Math.round(avgEnergy * 10) / 10);
      lb.getRange(row, 5).setValue(wins);
      lb.getRange(row, 6).setValue(total);

    } catch(e) {
      Logger.log(`Multipassionate ${i+1} error: ${e.message}`);
    }
  });

  // sort by NOMO score desc, then rank
  const range = lb.getRange(5, 1, MENTEE_SHEETS.length, 7);
  const data = range.getValues();
  data.sort((a, b) => (b[5]||0) - (a[5]||0));
  data.forEach((row, i) => row[0] = i + 1);
  range.setValues(data);

  Logger.log("NOMO synced at " + new Date());
}

// ─────────────────────────────────────────────────────────
// Run ONCE per mentee sheet to set up date column in Daily Log
// Extensions → Apps Script → paste → Run formatDates
// ─────────────────────────────────────────────────────────

function formatDates() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const log = ss.getSheetByName("📅 Daily Log");
  if (!log) { Logger.log("Daily Log sheet not found"); return; }

  const dateRange = log.getRange("A4:A93");
  dateRange.setNumberFormat("DD-MM-YYYY");

  const rule = SpreadsheetApp.newDataValidation()
    .requireDate()
    .setAllowInvalid(false)
    .setHelpText("Enter a valid date. Format: DD-MM-YYYY")
    .build();
  dateRange.setDataValidation(rule);

  const profile = ss.getSheetByName("👤 My Profile");
  const startVal = profile.getRange("D5").getValue();

  if (!startVal || startVal === "") {
    Logger.log("No start date in Profile D5 — fill that first, then run again");
    SpreadsheetApp.getUi().alert("Fill your Start Date in Profile tab first, then run this again.");
    return;
  }

  const startDate = new Date(startVal);
  startDate.setHours(0,0,0,0);

  if (isNaN(startDate.getTime())) {
    Logger.log("Invalid start date in Profile D5");
    SpreadsheetApp.getUi().alert("Start date in Profile is invalid. Enter it as: 5 June 2026");
    return;
  }

  for (let i = 0; i < 90; i++) {
    const d = new Date(startDate);
    d.setDate(startDate.getDate() + i);
    log.getRange(4 + i, 1).setValue(d);
  }

  for (let i = 0; i < 90; i++) {
    const r = 4 + i;
    log.getRange(r, 2).setFormula(`=TEXT(A${r},"DDD")`);
  }

  log.getRange("A4:A93").setNumberFormat("DD-MM-YYYY");

  Logger.log("Dates formatted successfully from " + startDate.toDateString());
  SpreadsheetApp.getUi().alert("Done! Dates are now set from " + startDate.toDateString());
}
