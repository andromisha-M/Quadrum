const items = $input.all().map(i => i.json);
const newRows = items.map(e => ({
  'Seller / Service Provider': e.seller || '',
  'Description': e.description || '',
  'Net Cost': Number((Number(e.netCost) || 0).toFixed(2)),
  'VAT': Number((Number(e.vat) || 0).toFixed(2)),
  'Date': e.invoiceDate || '',
  'Project': e.project || ''
}));
const first = items[0] || {};
return [{ json: {
  fileId: first.fileId, fileName: first.fileName, sourceType: first.sourceType,
  confidence: first.confidence, notes: items.map(i => i.notes).filter(Boolean).join(' | '),
  entryCount: newRows.length,
  netTotal: items.reduce((s, i) => s + (Number(i.netCost) || 0), 0),
  vatTotal: items.reduce((s, i) => s + (Number(i.vat) || 0), 0),
  newRows: newRows
} }];
