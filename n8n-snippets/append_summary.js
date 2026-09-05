let current = '';
try {
  const buffer = await this.helpers.getBinaryDataBuffer(0, 'data');
  current = buffer.toString('utf-8');
} catch (e) {
  current = '';
}
const ctx = $('Folder Context').first().json;
if (!current) {
  current = '# ' + ctx.projectName + ' - Expense Processing Report\n\n## Invoice log\n\n';
}

function fmt(num) {
  const n = Number(num) || 0;
  const parts = Math.abs(n).toFixed(2).split('.');
  return (n < 0 ? '-' : '') + parts[0] + '.' + parts[1];
}

const totals = $('Collect Final Rows').first().json;
const unc = $('Collect Uncompleted Files').first().json;
const stamp = new Date().toISOString().replace('T', ' ').substring(0, 19);

let entry = '\n---\n\n## Summary\n\n';
entry += 'Processing of **' + ctx.projectName + '** finished on ' + stamp + ' (UTC). ';
entry += 'A total of **' + totals.rowCount + ' expense row(s)** were written to `'
       + ctx.projectName + '.xlsx`, adding up to a net total of **' + fmt(totals.netTotal)
       + '**, VAT of **' + fmt(totals.vatTotal) + '**, and a gross total of **'
       + fmt(totals.grossTotal) + '**. ';
if (unc.uncompletedCount > 0) {
  entry += '**' + unc.uncompletedCount + ' file(s) could not be processed with enough certainty** '
        + 'and were moved to the ' + ctx.projectName + ' - UNCOMPLETED folder: '
        + unc.uncompletedNames.join(', ') + '. '
        + 'Each of them is listed above with the reason it failed, so they can be entered by hand '
        + 'or re-run after a fix. ';
} else {
  entry += 'Every document found in the project folder was processed successfully, with no files '
        + 'left for manual review. ';
}
entry += 'All figures above come straight from the rows written to the spreadsheet, so the '
       + 'spreadsheet remains the single source of truth.\n';

const updated = current + entry;
return [{
  json: { mdLength: updated.length, mdText: updated },
  binary: { data: {
    data: Buffer.from(updated, 'utf-8').toString('base64'),
    mimeType: 'text/markdown',
    fileName: ctx.projectName + '.md',
    fileExtension: 'md'
  } }
}];
