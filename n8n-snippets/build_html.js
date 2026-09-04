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
function money(n) {
  return (Number(n) || 0).toFixed(2);
}
function fileCell(e) {
  const name = esc(e.file);
  const link = e.link ? '<a href="' + esc(e.link) + '" target="_blank">' + name + '</a>' : name;
  return link + '<div class="loc">' + esc(e.folder || '(folder unknown)') + '</div>';
}

const stamp = new Date().toISOString().replace('T', ' ').substring(0, 19);

let rowsHtml = '';
for (const e of failed) {
  rowsHtml += '<tr class="bad"><td>' + fileCell(e) + '</td><td>' + esc(e.sourceType || '')
    + '</td><td class="reason">' + esc(e.reason || '') + '</td></tr>';
}

let okHtml = '';
for (const e of done) {
  const cls = Number(e.confidence) < 95 ? 'warn' : '';
  const rows = Array.isArray(e.rows) ? e.rows : [];
  const detail = rows.map(r =>
    esc(r['Seller / Service Provider']) + ' &middot; ' + esc(r['Description'])
    + ' &middot; net ' + money(r['Net Cost']) + ' &middot; VAT ' + money(r['VAT'])
    + ' &middot; ' + esc(r['Date'])).join('<br>');
  okHtml += '<tr class="' + cls + '"><td>' + fileCell(e) + '</td>'
    + '<td class="conf">' + esc(e.confidence) + '%</td>'
    + '<td>' + detail + '</td>'
    + '<td class="note">' + esc(e.notes || '') + '</td></tr>';
}

const html = '<!doctype html><html><head><meta charset="utf-8">'
+ '<title>' + esc(ctx.projectName) + ' - Expense Report</title><style>'
+ 'body{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:32px;color:#1a1a1a;background:#fff}'
+ 'h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 10px}'
+ '.sub{color:#666;margin-bottom:24px}'
+ '.cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px}'
+ '.card{border:1px solid #e0e0e0;border-radius:8px;padding:12px 16px;min-width:130px}'
+ '.card .n{font-size:22px;font-weight:600}.card .l{color:#666;font-size:12px}'
+ '.card.red{border-color:#e5484d;background:#fff5f5}.card.red .n{color:#c62a2f}'
+ 'table{border-collapse:collapse;width:100%;margin-top:6px}'
+ 'th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #ececec;vertical-align:top}'
+ 'th{background:#fafafa;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#555}'
+ 'tr.bad td{background:#fff5f5;color:#c62a2f}tr.bad .reason{font-weight:500}'
+ 'tr.warn td{background:#fffaf0}tr.warn .conf{color:#b45309;font-weight:600}'
+ '.loc{color:#777;font-size:12px;margin-top:2px}'
+ '.note{color:#555;font-size:13px}.conf{white-space:nowrap}'
+ 'a{color:#0b62d0}.empty{color:#666;font-style:italic;padding:10px 0}'
+ '@media print{body{padding:0}a{color:#000;text-decoration:none}}'
+ '</style></head><body>'
+ '<h1>' + esc(ctx.projectName) + '</h1>'
+ '<div class="sub">Expense processing report &middot; generated ' + stamp + ' UTC</div>'
+ '<div class="cards">'
+ '<div class="card"><div class="n">' + totals.rowCount + '</div><div class="l">rows in spreadsheet</div></div>'
+ '<div class="card"><div class="n">' + money(totals.netTotal) + '</div><div class="l">net total</div></div>'
+ '<div class="card"><div class="n">' + money(totals.vatTotal) + '</div><div class="l">VAT total</div></div>'
+ '<div class="card"><div class="n">' + money(totals.grossTotal) + '</div><div class="l">gross total</div></div>'
+ '<div class="card' + (failed.length ? ' red' : '') + '"><div class="n">' + failed.length + '</div><div class="l">need manual review</div></div>'
+ '</div>'
+ '<h2>Needs manual review</h2>'
+ (failed.length
    ? '<table><tr><th>File and location</th><th>Read as</th><th>Why it failed</th></tr>' + rowsHtml + '</table>'
    : '<div class="empty">Nothing - every document was processed.</div>')
+ '<h2>Processed' + (shaky.length ? ' <span style="color:#b45309;font-weight:400;font-size:13px">(' + shaky.length + ' below 95% - shaded)</span>' : '') + '</h2>'
+ (done.length
    ? '<table><tr><th>File and location</th><th>Conf.</th><th>Written to spreadsheet</th><th>Notes</th></tr>' + okHtml + '</table>'
    : '<div class="empty">No documents were processed.</div>')
+ '</body></html>';

return [{
  json: { reportBytes: html.length, failedCount: failed.length, processedCount: done.length },
  binary: { data: {
    data: Buffer.from(html, 'utf-8').toString('base64'),
    mimeType: 'text/html',
    fileName: ctx.projectName + ' - report.html',
    fileExtension: 'html'
  } }
}];
