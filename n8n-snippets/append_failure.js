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
const d = $('Merge Failure Paths').first().json;
const f = $('Process Files One By One').first().json;

let entry = '### ' + d.fileName + '  -  NEEDS MANUAL REVIEW\n\n';
entry += '- **Status:** NOT processed\n';
entry += '- **Location:** ' + (f.folderPath || '(folder unknown)') + '\n';
entry += '- **Read as:** ' + (d.sourceType || 'unknown') + '\n';
entry += '- **Reason:** ' + (d.reason || 'Unknown problem.') + '\n';
if (d.bestGuess) {
  entry += '- **Best guess (NOT written to the spreadsheet):** '
        + (d.bestGuess.seller || '?') + ' | ' + (d.bestGuess.description || '?')
        + ' | net ' + (d.bestGuess.net_cost !== undefined ? d.bestGuess.net_cost : '?')
        + ' | VAT ' + (d.bestGuess.vat !== undefined ? d.bestGuess.vat : '?')
        + ' | ' + (d.bestGuess.date || '?') + '\n';
}
entry += '- **Moved to:** ' + ctx.projectName + ' - UNCOMPLETED\n\n';

// Machine-readable copy for the HTML report (invisible in rendered markdown)
entry += '<!--DATA ' + JSON.stringify({
  status: 'failed',
  file: d.fileName,
  folder: f.folderPath || '',
  link: f.driveLink || '',
  sourceType: d.sourceType || 'unknown',
  reason: d.reason || 'Unknown problem.',
  bestGuess: d.bestGuess || null
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
