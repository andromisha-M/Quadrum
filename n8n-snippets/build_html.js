const ctx = $('Folder Context').first().json;
const totals = $('Collect Final Rows').first().json;
const md = String(($('Append Summary To MD').first().json || {}).mdText || '');

// Pull the machine-readable records the per-file steps left in the .md
const entries = [];
const re = /<!--DATA ([\s\S]*?)-->/g;
let m;
while ((m = re.exec(md)) !== null) {
  try { entries.push(JSON.parse(m[1])); } catch (e) { /* ignore malformed */ }
}

const failed = entries.filter(e => e.status !== 'processed');
const done = entries.filter(e => e.status === 'processed');
const shaky = done.filter(e => Number(e.confidence) < 95);

function esc(s) {
  return String(s === undefined || s === null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
// 15000555 -> 15,000,555.00
function money(n) {
  const num = Number(n) || 0;
  const parts = Math.abs(num).toFixed(2).split('.');
  const grouped = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return (num < 0 ? '-' : '') + grouped + '.' + parts[1];
}
function fileCell(e) {
  const name = esc(e.file);
  const link = e.link
    ? '<a href="' + esc(e.link) + '" target="_blank" rel="noopener">' + name + '</a>'
    : name;
  return '<div class="fname">' + link + '</div>'
       + '<div class="loc">' + esc(e.folder || 'location unknown') + '</div>';
}

const stamp = new Date().toISOString().replace('T', ' ').substring(0, 16);

let failHtml = '';
for (const e of failed) {
  failHtml += '<tr>'
    + '<td>' + fileCell(e) + '</td>'
    + '<td class="tag-cell"><span class="tag">' + esc(e.sourceType || 'unknown') + '</span></td>'
    + '<td class="reason">' + esc(e.reason || '') + '</td>'
    + '</tr>';
}

let okHtml = '';
for (const e of done) {
  const conf = Number(e.confidence) || 0;
  const rows = Array.isArray(e.rows) ? e.rows : [];
  const cls = conf < 95 ? ' class="warn"' : '';
  const dot = conf < 95 ? 'amber' : 'green';
  for (let i = 0; i < Math.max(rows.length, 1); i++) {
    const r = rows[i] || {};
    okHtml += '<tr' + cls + '>'
      + (i === 0
          ? '<td rowspan="' + Math.max(rows.length, 1) + '">' + fileCell(e) + '</td>'
          : '')
      + '<td class="seller">' + esc(r['Seller / Service Provider'] || '') + '</td>'
      + '<td class="desc">' + esc(r['Description'] || '')
        + (r['Project'] ? '<span class="proj">' + esc(r['Project']) + '</span>' : '')
      + '</td>'
      + '<td class="num">' + money(r['Net Cost']) + '</td>'
      + '<td class="num">' + money(r['VAT']) + '</td>'
      + '<td class="date">' + esc(r['Date'] || '') + '</td>'
      + (i === 0
          ? '<td rowspan="' + Math.max(rows.length, 1) + '" class="conf">'
            + '<span class="dot ' + dot + '"></span>' + conf + '%'
            + '<div class="note">' + esc(e.notes || '') + '</div></td>'
          : '')
      + '</tr>';
  }
}

const css = `
:root{--ink:#16181d;--muted:#6b7280;--line:#e8eaed;--bg:#fff;--soft:#f7f8fa;
--red:#c0272d;--redbg:#fdf2f2;--redline:#f2c9c9;--amber:#a35b06;--amberbg:#fffaf0;--green:#137a4b;--accent:#1a3d6d}
*{box-sizing:border-box}
body{margin:0;padding:40px 44px 64px;background:var(--bg);color:var(--ink);
font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto}
header{border-bottom:3px solid var(--accent);padding-bottom:18px;margin-bottom:28px;
display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap}
h1{margin:0;font-size:30px;letter-spacing:-.02em;font-weight:650}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
margin:0 0 6px;font-weight:600}
.meta{font-size:13px;color:var(--muted);text-align:right;line-height:1.7}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px;margin-bottom:36px}
.stat{border:1px solid var(--line);border-radius:10px;padding:16px 18px;background:var(--soft)}
.stat .v{font-size:24px;font-weight:640;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat .k{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
margin-top:5px;font-weight:600}
.stat.total{background:var(--accent);border-color:var(--accent)}
.stat.total .v{color:#fff}.stat.total .k{color:#b9cbe4}
.stat.alert{background:var(--redbg);border-color:var(--redline)}
.stat.alert .v{color:var(--red)}.stat.alert .k{color:var(--red);opacity:.85}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
margin:0 0 12px;font-weight:700;display:flex;align-items:center;gap:9px}
h2 .count{background:var(--soft);border:1px solid var(--line);border-radius:20px;
padding:1px 9px;font-size:11px;letter-spacing:0;color:var(--ink)}
h2.danger{color:var(--red)}h2.danger .count{background:var(--redbg);border-color:var(--redline);color:var(--red)}
section{margin-bottom:38px}
table{border-collapse:collapse;width:100%;font-size:14px}
th{text-align:left;padding:9px 12px;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
color:var(--muted);font-weight:700;border-bottom:1.5px solid var(--line);white-space:nowrap}
td{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:last-child td{border-bottom:none}
.fname{font-weight:560;word-break:break-word}
.fname a{color:var(--ink);text-decoration:none;border-bottom:1px solid #c9d3e0}
.fname a:hover{border-bottom-color:var(--accent)}
.loc{color:var(--muted);font-size:12px;margin-top:3px}
.seller{font-weight:560;max-width:230px}
.desc{color:#3d434d;max-width:330px}
.proj{display:block;margin-top:5px;font-size:11px;font-weight:600;color:var(--accent);
background:#eef3fa;border-radius:4px;padding:2px 7px;width:fit-content;letter-spacing:.02em}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:560}
.date{white-space:nowrap;color:#3d434d;font-variant-numeric:tabular-nums}
.conf{white-space:nowrap;font-variant-numeric:tabular-nums;font-weight:600;min-width:190px}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;vertical-align:1px}
.dot.green{background:var(--green)}.dot.amber{background:#d18616}
.note{font-weight:400;color:var(--muted);font-size:12px;margin-top:5px;white-space:normal;max-width:260px}
tr.warn td{background:var(--amberbg)}tr.warn .conf{color:var(--amber)}
.fail table{background:var(--redbg);border:1px solid var(--redline);border-radius:10px;overflow:hidden}
.fail th{color:var(--red);border-bottom-color:var(--redline);padding-left:14px}
.fail td{border-bottom-color:var(--redline);padding-left:14px}
.fail .reason{color:var(--red);font-weight:500}
.tag{display:inline-block;font-size:11px;font-weight:600;background:#fff;border:1px solid var(--redline);
color:var(--red);border-radius:4px;padding:2px 7px;white-space:nowrap}
.empty{color:var(--muted);font-style:italic;padding:14px;border:1px dashed var(--line);border-radius:10px}
tfoot td{border-top:2px solid var(--ink);border-bottom:none;padding-top:13px;font-weight:680}
tfoot .lbl{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);
font-size:12px;color:var(--muted)}
@media print{body{padding:0}.stat{background:#fff!important}
.stat.total{background:#fff!important;border-color:var(--ink)}.stat.total .v{color:var(--ink)}
.stat.total .k{color:var(--muted)}section{break-inside:avoid}
.fname a{color:var(--ink);border:none}}
`;

const netCell = money(totals.netTotal), vatCell = money(totals.vatTotal), grossCell = money(totals.grossTotal);

const html = '<!doctype html><html lang="en"><head><meta charset="utf-8">'
+ '<meta name="viewport" content="width=device-width,initial-scale=1">'
+ '<title>' + esc(ctx.projectName) + ' - Expense Report</title><style>' + css + '</style></head><body><div class="wrap">'
+ '<header><div><p class="eyebrow">Expense processing report</p><h1>' + esc(ctx.projectName) + '</h1></div>'
+ '<div class="meta">Generated ' + stamp + ' UTC<br>' + entries.length + ' document(s) examined</div></header>'

+ '<div class="stats">'
+ '<div class="stat total"><div class="v">' + netCell + '</div><div class="k">Net total</div></div>'
+ '<div class="stat"><div class="v">' + vatCell + '</div><div class="k">VAT total</div></div>'
+ '<div class="stat"><div class="v">' + grossCell + '</div><div class="k">Gross total</div></div>'
+ '<div class="stat"><div class="v">' + totals.rowCount + '</div><div class="k">Rows in spreadsheet</div></div>'
+ '<div class="stat' + (failed.length ? ' alert' : '') + '"><div class="v">' + failed.length
  + '</div><div class="k">Need manual review</div></div>'
+ '</div>'

+ '<section class="fail"><h2' + (failed.length ? ' class="danger"' : '') + '>Needs manual review'
+ (failed.length ? '<span class="count">' + failed.length + '</span>' : '') + '</h2>'
+ (failed.length
    ? '<table><thead><tr><th>File and location</th><th>Read as</th><th>Why it failed</th></tr></thead><tbody>'
      + failHtml + '</tbody></table>'
    : '<div class="empty">Nothing outstanding - every document was processed.</div>')
+ '</section>'

+ '<section><h2>Processed'
+ (done.length ? '<span class="count">' + done.length + '</span>' : '')
+ (shaky.length ? '<span class="count">' + shaky.length + ' below 95%</span>' : '') + '</h2>'
+ (done.length
    ? '<table><thead><tr><th>File and location</th><th>Seller</th><th>Description</th>'
      + '<th class="num">Net</th><th class="num">VAT</th><th>Date</th><th>Confidence</th></tr></thead><tbody>'
      + okHtml + '</tbody>'
      + '<tfoot><tr><td colspan="3" class="lbl">Total written to spreadsheet</td>'
      + '<td class="num">' + netCell + '</td><td class="num">' + vatCell + '</td><td colspan="2"></td></tr></tfoot>'
      + '</table>'
    : '<div class="empty">No documents were processed.</div>')
+ '</section>'

+ '<footer>Amounts as written to <strong>' + esc(ctx.projectName) + '.xlsx</strong>, which remains the source of truth. '
+ 'Anything listed above as needing review was moved to <strong>' + esc(ctx.projectName)
+ ' - UNCOMPLETED</strong> and is not included in these totals.</footer>'
+ '</div></body></html>';

return [{
  json: { reportBytes: html.length, failedCount: failed.length, processedCount: done.length },
  binary: { data: {
    data: Buffer.from(html, 'utf-8').toString('base64'),
    mimeType: 'text/html',
    fileName: ctx.projectName + ' - report.html',
    fileExtension: 'html'
  } }
}];
