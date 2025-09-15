/**
 * Trinity Core — Lucifer Bridge (Apps Script)
 * Author: ChatGPT (for Peshkata)
 * Menu: Trinity Core → Run Lucifer Bridge / Weekly Review / Install Triggers / Remove Triggers
 */

const LOG_SHEET = 'Trinity Core Log';
const REVIEW_SHEET = 'Weekly Review';

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Trinity Core')
    .addItem('Run Lucifer Bridge', 'runLuciferBridge')
    .addItem('Weekly Review', 'weeklyReview')
    .addSeparator()
    .addItem('Install Triggers', 'installTriggers')
    .addItem('Remove Triggers', 'removeTriggers')
    .addToUi();
  ensureSheets();
}

function ensureSheets() {
  const ss = SpreadsheetApp.getActive();
  let sheet = ss.getSheetByName(LOG_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(LOG_SHEET);
    sheet.appendRow([
      'Timestamp','Date',
      'L1 TruthCheck',
      'L2 Mercy/Knowledge',
      'L3 Humility Note',
      'L4 Evidence Plan',
      'L5 Venus Correction',
      'Tilt (-3 Mercy .. +3 Rebellion)',
      'Pride Flags Count (0..7)',
      'Notes'
    ]);
    sheet.setFrozenRows(1);
  }
  if (!ss.getSheetByName(REVIEW_SHEET)) {
    const r = ss.insertSheet(REVIEW_SHEET);
    r.appendRow(['Week Start','Week End','Entries','Avg Tilt','Total Pride Flags','Notes']);
    r.setFrozenRows(1);
  }
}

function runLuciferBridge() {
  ensureSheets();
  const html = HtmlService.createHtmlOutputFromFile('Panel')
    .setTitle('Trinity Core — Lucifer Bridge')
    .setWidth(420);
  SpreadsheetApp.getUi().showSidebar(html);
}

function submitLuciferForm(data) {
  ensureSheets();
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(LOG_SHEET);
  const now = new Date();
  const dateOnly = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  sheet.appendRow([
    now, dateOnly,
    data.l1 || '', data.l2 || '', data.l3 || '', data.l4 || '', data.l5 || '',
    Number(data.tilt || 0),
    Number(data.prideCount || 0),
    data.notes || ''
  ]);
  return { ok: true };
}

function weeklyReview() {
  ensureSheets();
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(LOG_SHEET);
  const review = ss.getSheetByName(REVIEW_SHEET);

  const values = sheet.getDataRange().getValues();
  if (values.length <= 1) return;

  const tz = Session.getScriptTimeZone();
  const now = new Date();
  // Compute current week Monday..Sunday
  const day = now.getDay(); // 0=Sun..6=Sat
  const offsetToMonday = ((day + 6) % 7);
  const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - offsetToMonday);
  const sunday = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 6);

  // scan rows in current week
  const rows = values.slice(1).filter(r => {
    if (!r[0]) return false;
    const ts = new Date(r[0]);
    return ts >= monday && ts <= sunday;
  });
  if (rows.length === 0) return;

  const avgTilt = rows.reduce((a, r) => a + Number(r[7] || 0), 0) / rows.length;
  const prideSum = rows.reduce((a, r) => a + Number(r[8] || 0), 0);

  review.appendRow([
    Utilities.formatDate(monday, tz, 'yyyy-MM-dd'),
    Utilities.formatDate(sunday, tz, 'yyyy-MM-dd'),
    rows.length,
    avgTilt,
    prideSum,
    (avgTilt > 1 || prideSum >= 9) ? '⚠️ Pride risk — apply L1–L3 reset' : 'OK'
  ]);
}

function installTriggers() {
  removeTriggers();
  // Daily noon reminder (cannot open UI; can only log or send email)
  ScriptApp.newTrigger('dailyNudge')
    .timeBased()
    .atHour(12).everyDays(1)
    .create();
  // Weekly review Sunday 18:00
  ScriptApp.newTrigger('weeklyReview')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.SUNDAY)
    .atHour(18)
    .create();
  SpreadsheetApp.getUi().alert('Installed daily (12:00) and weekly (Sun 18:00) triggers.');
}

function removeTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
}

function dailyNudge() {
  // Triggers are headless. We send a nudge via email if possible, else add a note to the sheet.
  ensureSheets();
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(LOG_SHEET);
  const email = Session.getActiveUser().getEmail();
  const msg = 'Trinity Core — Lucifer Bridge: Open the sheet → Trinity Core → Run Lucifer Bridge and log L1–L5 for today.';
  try {
    if (email) {
      MailApp.sendEmail(email, 'Trinity Core — Daily L‑check', msg);
    } else {
      sheet.getRange(1,1).setNote(msg);
    }
  } catch (e) {
    sheet.getRange(1,1).setNote('Daily nudge: ' + msg + ' (email failed: ' + e + ')');
  }
}
