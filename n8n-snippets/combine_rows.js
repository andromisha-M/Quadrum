// A..F are the data columns, G..J are spacers, K holds the running total.
const DATA_COLUMNS = ['Seller / Service Provider', 'Description', 'Net Cost', 'VAT', 'Date', 'Project'];
const NUMERIC = new Set(['Net Cost', 'VAT']);
const SPACER_COLUMNS = 4;
const TOTAL_HEADER = 'TOTAL NET';

function num(v) {
  if (typeof v === 'number') return v;
  if (v === undefined || v === null || v === '') return 0;
  return Number(String(v).replace(/\s/g, '').replace(/,/g, '')) || 0;
}

const existing = $input.all()
  .map(i => i.json)
  .filter(r => r && !r.__placeholder && Object.keys(r).length > 0)
  .map(r => {
    const row = {};
    for (const c of DATA_COLUMNS) {
      if (NUMERIC.has(c)) row[c] = num(r[c]);
      else row[c] = r[c] === undefined || r[c] === null ? '' : String(r[c]);
    }
    return row;
  });

const newRows = $('Format Rows For Spreadsheet').first().json.newRows || [];
const all = existing.concat(newRows);
const totalNet = Number(all.reduce((s, r) => s + num(r['Net Cost']), 0).toFixed(2));

return all.map((row, index) => {
  const out = {};
  for (const c of DATA_COLUMNS) out[c] = row[c];
  for (let i = 0; i < SPACER_COLUMNS; i++) out[' '.repeat(i + 1)] = '';
  out[TOTAL_HEADER] = index === 0 ? totalNet : '';
  return { json: out };
});
