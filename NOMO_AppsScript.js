// NOMO Daily Tracker — Apps Script
// Paste in: Extensions → Apps Script → save
// Set trigger: Triggers → Add → syncScores → Time-driven → Hour timer → Every hour
//
// Member sheet URLs live in the "sheet_link" tab (column B, from row 2 down) —
// NOT in this code. To add a member: add a row in sheet_link with their URL.
// Re-pasting this script never wipes the member list.

const LINK_TAB = "sheet_link";  // tab holding member sheet URLs in column B
const MEMBER_TEMPLATE_ID = "1OaO8jzrOtNmRoY9btCBYffhAfvv8Ei8rKPVqF7iO2AM"; // NOMO_passion_tracker_member
const FORM_RESPONSES_TAB = "Form Responses 1";

// Read member sheet URLs from the sheet_link tab (col B, row 2 downward).
function getMenteeSheets() {
  const master = SpreadsheetApp.getActiveSpreadsheet();
  const tab = master.getSheetByName(LINK_TAB);
  if (!tab) {
    Logger.log(`"${LINK_TAB}" tab not found — add it with headers Sl_no | link`);
    return [];
  }
  const last = tab.getLastRow();
  if (last < 2) return [];
  const urls = tab.getRange(2, 2, last - 1, 1).getValues()  // B2:B<last>
    .map(r => (r[0] || "").toString().trim())
    .filter(u => u && u.startsWith("http"));
  return urls;
}

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

  const menteeSheets = getMenteeSheets();   // URLs from the sheet_link tab
  Logger.log(`Found ${menteeSheets.length} member sheet(s) in "${LINK_TAB}"`);

  // ── DAILY BASELINE for the change arrow ───────────────────────────────
  // The arrow (▲/▼) must be the SAME for every viewer all day, no matter who
  // refreshes or how often. So PREV SCORE is a "yesterday's closing" baseline
  // that only advances ONCE per calendar day — the first sync of a new day.
  // Manual refreshes recompute live scores but never move the baseline.
  //
  // Read the existing board: col 6 (idx 5) = current NOMO, col 7 (idx 6) = PREV.
  const props = PropertiesService.getScriptProperties();
  const todayKey = Utilities.formatDate(today, Session.getScriptTimeZone(), "yyyy-MM-dd");
  const lastBaselineDate = props.getProperty("lastBaselineDate");
  const newDay = (lastBaselineDate !== todayKey);

  const existing = lb.getRange(5, 1, Math.max(menteeSheets.length, 1), 7).getValues();

  // baselineByName = the PREV SCORE every viewer should see today.
  // - New day: snapshot each member's CURRENT score now → becomes today's baseline.
  // - Same day: reuse the PREV already on the board (don't move it).
  const baselineByName = {};
  existing.forEach(r => {
    const nm = (r[1] || "").toString().trim();
    if (!nm) return;
    const curr = r[5];   // current NOMO score
    const prev = r[6];   // existing PREV (today's baseline, if already set)
    if (newDay) {
      if (curr !== "" && curr !== null) baselineByName[nm] = curr;
    } else {
      if (prev !== "" && prev !== null) baselineByName[nm] = prev;
    }
  });

  // Compute every active member into an in-memory array. No writes yet —
  // this avoids the write-by-position vs. sort-by-score race condition.
  const results = [];
  menteeSheets.forEach((url, i) => {
    try {
      const ss = SpreadsheetApp.openByUrl(url);
      const profile = ss.getSheetByName("👤 My Profile");
      const log = ss.getSheetByName("📅 Daily Log");
      if (!profile || !log) return;

      // name
      let name = (profile.getRange("D4").getValue() || "").toString().trim();
      if (!name || name.includes("←")) return;  // skip unfilled profiles

      // read log A4:J38 — A=date,B=day,C=P1,D=yes/no,E=P2,F=yes/no,G=P3,H=yes/no,I=energy,J=win
      const logData = log.getRange("A4:J38").getValues();

      const window15 = logData.filter(r => {
        const d = parseSheetDate(r[0]);
        if (!d) return false;
        if (!r[2] || r[2] === "") return false;
        return d >= windowStart && d <= today;
      });

      Logger.log(`${name}: ${window15.length} rows in 15-day window`);

      let streak = 0, avgEnergy = 0, wins = 0, total = 0;
      if (window15.length > 0) {
        // 1. STREAK — distinct days shown up (at least one Yes in D/F/H)
        const shownUpDays = new Set();
        window15.forEach(r => {
          const yesNo = [r[3], r[5], r[7]].map(v => (v||"").toString().trim().toLowerCase());
          if (yesNo.includes("yes")) {
            const d = parseSheetDate(r[0]);
            if (d) shownUpDays.add(d.toDateString());
          }
        });
        streak = shownUpDays.size;
        const streakScore = Math.min(streak / 15, 1) * 40;

        // 2. AVG ENERGY (col I = index 8)
        const energies = window15.map(r => parseInt(r[8])).filter(e => !isNaN(e) && e > 0);
        avgEnergy = energies.length > 0 ? energies.reduce((a,b) => a+b, 0) / energies.length : 0;
        const energyScore = (avgEnergy / 5) * 30;

        // 3. WINS (col J = index 9)
        wins = window15.filter(r => r[9] && r[9].toString().trim() !== "").length;
        const winsScore = Math.min(wins / 15, 1) * 20;

        // 4. PARTICIPATION 10% — showed up at all
        const participationScore = Math.min(streak / 15, 1) * 10;

        total = Math.round((streakScore + energyScore + winsScore + participationScore) * 10) / 10;
      }

      // PREV SCORE = today's daily baseline for this member (same for everyone,
      // all day). Blank only if there is no baseline yet (brand-new member).
      const base = baselineByName.hasOwnProperty(name) ? baselineByName[name] : "";
      const prevScore = (base !== "" && base !== total) ? base : "";

      results.push({
        name: name,
        streak: streak,
        avgEnergy: Math.round(avgEnergy * 10) / 10,
        wins: wins,
        total: total,
        prevScore: prevScore,
      });

    } catch(e) {
      Logger.log(`Multipassionate ${i+1} error: ${e.message}`);
    }
  });

  // Safety guard: collapse any same-name members to a single row (keep the
  // higher score). Clean data shouldn't trigger this, but a stray D4 typo or a
  // duplicate URL must never put two identical names on the board again.
  const byName = {};
  results.forEach(m => {
    const key = m.name.toLowerCase();
    if (!byName[key] || m.total > byName[key].total) {
      if (byName[key]) Logger.log(`Duplicate name "${m.name}" — keeping higher score`);
      byName[key] = m;
    } else {
      Logger.log(`Duplicate name "${m.name}" — dropping lower score`);
    }
  });
  const deduped = Object.keys(byName).map(k => byName[k]);

  // Sort by score desc, assign rank, build the full block.
  deduped.sort((a, b) => b.total - a.total);

  // Clear the old data block first (so removed/duplicate members don't linger).
  // Clear generously (member count or 50 rows) so stale rows never survive.
  const blockRows = Math.max(menteeSheets.length, deduped.length, 50);
  lb.getRange(5, 1, blockRows, 7).clearContent();

  if (deduped.length > 0) {
    const out = deduped.map((m, idx) => [
      idx + 1, m.name, m.streak, m.avgEnergy, m.wins, m.total, m.prevScore,
    ]);
    lb.getRange(5, 1, out.length, 7).setValues(out);
  }

  // Stamp the sync time (IST) into H3 so the web app shows "data as of …"
  // identically for every viewer — not each viewer's own page-load time.
  // (Row 1/2 are merged banner cells, so H3 is the first free cell.)
  const stamp = Utilities.formatDate(new Date(), "Asia/Kolkata", "dd MMM yyyy · HH:mm");
  lb.getRange("H3").setValue("Synced: " + stamp + " IST");

  // Mark today's baseline as set, so further syncs today won't move PREV.
  if (newDay) {
    props.setProperty("lastBaselineDate", todayKey);
    Logger.log(`New-day baseline captured for ${todayKey}`);
  }

  Logger.log(`NOMO synced ${deduped.length} member(s) at ` + new Date());
}

// ─────────────────────────────────────────────────────────
// WEB APP ENTRY POINT — lets the Streamlit "Refresh" button
// trigger a sync on demand via a URL.
//
// Deploy: Apps Script editor → Deploy → New deployment →
//   type "Web app" → Execute as "Me" → Access "Anyone" → Deploy.
// Copy the Web App URL into app.py (REFRESH_URL).
//
// Optional shared secret: set SCRIPT_TOKEN below and pass ?token=... in the
// request so random visitors can't trigger your sync. Leave "" to disable.PASTE_YOUR_SECRET_TOKEN_HERE  
// ─────────────────────────────────────────────────────────
const SCRIPT_TOKEN = "PASTE_YOUR_SECRET_TOKEN_HERE"; // must match SCRIPT_TOKEN in Streamlit secrets — keep the real value out of public code

function doGet(e) {
  const out = { ok: false };
  try {
    if (SCRIPT_TOKEN && (!e || !e.parameter || e.parameter.token !== SCRIPT_TOKEN)) {
      out.error = "unauthorized";
      return ContentService
        .createTextOutput(JSON.stringify(out))
        .setMimeType(ContentService.MimeType.JSON);
    }
    syncScores();
    out.ok = true;
    out.synced_at = new Date().toISOString();
  } catch (err) {
    out.error = err.message;
  }
  return ContentService
    .createTextOutput(JSON.stringify(out))
    .setMimeType(ContentService.MimeType.JSON);
}

// ─────────────────────────────────────────────────────────
// ONBOARDING — fires on Google Form submit
// Trigger: Form submit → onFormSubmit
// ─────────────────────────────────────────────────────────

function onFormSubmit(e) {
  try {
    const master = SpreadsheetApp.getActiveSpreadsheet();
    const linkTab = master.getSheetByName(LINK_TAB);

    // Read form response values
    const row   = e.values;  // [Timestamp, Full Name, Email, Passion1, Passion2, Passion3]
    const name  = (row[1] || "").toString().trim();
    const email = (row[2] || "").toString().trim();
    const p1    = (row[3] || "").toString().trim();
    const p2    = (row[4] || "").toString().trim();
    const p3    = (row[5] || "").toString().trim();

    if (!name || !email) {
      Logger.log("Onboarding skipped — missing name or email");
      return;
    }

    // Check for duplicate email in sheet_link
    const existingUrls = linkTab.getDataRange().getValues();
    for (let i = 1; i < existingUrls.length; i++) {
      if ((existingUrls[i][2] || "").toString().trim().toLowerCase() === email.toLowerCase()) {
        Logger.log(`Duplicate email ${email} — skipping`);
        return;
      }
    }

    // Copy member template
    const templateFile = DriveApp.getFileById(MEMBER_TEMPLATE_ID);
    const copy = templateFile.makeCopy(`NOMO — ${name}`);
    const copyId = copy.getId();
    const memberSS = SpreadsheetApp.openById(copyId);

    // Fill My Profile
    const profile = memberSS.getSheetByName("👤 My Profile");
    const today = new Date();
    const dateStr = Utilities.formatDate(today, Session.getScriptTimeZone(), "dd-MM-yyyy");

    profile.getRange("D4").setValue(name);
    profile.getRange("D5").setValue(dateStr);
    profile.getRange("D6").setValue([p1, p2, p3].filter(p => p).length);
    if (p1) profile.getRange("C9").setValue(p1);
    if (p2) profile.getRange("C10").setValue(p2);
    if (p3) profile.getRange("C11").setValue(p3);

    // Share with member (editor access)
    copy.addEditor(email);

    // Get the sheet URL
    const memberUrl = `https://docs.google.com/spreadsheets/d/${copyId}/edit`;

    // Write to sheet_link: Sl_no | URL | Email | Name
    const lastRow = Math.max(linkTab.getLastRow(), 1);
    const slNo = lastRow; // header is row 1, so lastRow gives correct sl_no
    linkTab.appendRow([slNo, memberUrl, email, name]);

    // Email the member
    const subject = "🎯 Your NOMO Passion Tracker is Ready!";
    const body = `Hi ${name},

Welcome to NOMO — your personal passion tracker is all set!

📊 Your Tracker (fill this daily):
${memberUrl}

Your passions are already loaded:
${p1 ? "• " + p1 : ""}
${p2 ? "• " + p2 : ""}
${p3 ? "• " + p3 : ""}

🏆 Leaderboard (see where you rank):
https://nomo-leaderboard.streamlit.app/

Start logging from today (${dateStr}). Fill in "YES/NO", your energy (1-5), and "Today's Win" every day.

Your scores update on the leaderboard every hour.

Let's go! 🚀

— NOMO Team`;

    MailApp.sendEmail(email, subject, body);

    Logger.log(`Onboarded: ${name} (${email}) — ${memberUrl}`);

  } catch(err) {
    Logger.log("Onboarding error: " + err.message);
  }
}

