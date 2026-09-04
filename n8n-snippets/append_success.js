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
const d = $('Format Rows For Spreadsheet').first().json;
const f = $('Process Files One By One').first().json;
const rows = d.newRows || [];

let entry = '### ' + d.fileName + '\n\n';
entry += '- **Status:** processed (' + d.confidence + '% confidence)\n';
entry += '- **Location:** ' + (f.folderPath || '(folder unknown)') + '\n';
entry += '- **Read as:** ' + d.sourceType + '\n';
for (const r of rows) {
  entry += '- **Row written:** ' + r['Seller / Service Provider'] + ' | ' + r['Description']
        + ' | net ' + r['Net Cost'] + ' | VAT ' + r['VAT'] + ' | ' + r['Date'] + '\n';
}
entry += '- **Notes:** ' + (d.notes || 'Processed correctly, no issues found.') + '\n';
entry += '- **Moved to:** ' + ctx.projectName + ' - PROCESSED / Processed Invoices\n\n';

// Machine-readable copy for the HTML report (invisible in rendered markdown)
entry += '<!--DATA ' + JSON.stringify({
  status: 'processed',
  file: d.fileName,
  folder: f.folderPath || '',
  link: f.driveLink || '',
  sourceType: d.sourceType,
  confidence: Number(d.confidence) || 0,
  notes: d.notes || 'Processed correctly, no issues found.',
  rows: rows
}) + '-->\n\n';

const updated = current + entry;
return [{
  json: { mdLength: updated.length },
  binary: { data: {
    data: Buffer.from(updated, 'utf-8').toString('base64'),
    mimeType: 'text/markdown',
    fileName: ctx.projectName + '.md',
    fileExtension: 'md'
  } }
}];
