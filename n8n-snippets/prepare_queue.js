const IMAGE = ['jpg','jpeg','png','webp','gif','bmp','tif','tiff','heic'];
const SHEET = ['xlsx','xls','csv','ods'];
const DOC   = ['docx','doc','rtf','odt','txt','md'];

// folder id -> readable path, from the folder walk
const folderPath = new Map();
for (const f of $('Find All Subfolders (Any Depth)').all()) {
  if (f.json && f.json.id) folderPath.set(f.json.id, f.json.path || f.json.name || '');
}

const items = $input.all().filter(i => i.json && i.json.id);
if (items.length === 0) {
  return [{ json: { hasFiles: false, fileCount: 0 } }];
}
const seen = new Set();
const out = [];
for (const item of items) {
  if (seen.has(item.json.id)) continue;
  seen.add(item.json.id);
  const name = String(item.json.name || '');
  const ext = name.includes('.') ? name.split('.').pop().toLowerCase() : '';
  let category = 'unsupported';
  if (ext === 'pdf') category = 'pdf';
  else if (IMAGE.includes(ext)) category = 'image';
  else if (SHEET.includes(ext)) category = 'spreadsheet';
  else if (DOC.includes(ext)) category = 'document';
  const parentId = (item.json.parents || [])[0] || '';
  out.push({ json: {
    id: item.json.id,
    name: name,
    mimeType: item.json.mimeType || '',
    fileExtension: ext,
    fileCategory: category,
    folderPath: folderPath.get(parentId) || '(folder unknown)',
    driveLink: 'https://drive.google.com/file/d/' + item.json.id + '/view',
    hasFiles: true
  } });
}
return out;
