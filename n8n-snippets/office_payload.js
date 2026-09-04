const f = $('Process Files One By One').first().json;
const origin = $('Text Extracted OK?').first().json || {};
const resp = $input.first().json || {};
const images = Array.isArray(resp.images) ? resp.images : [];
const urls = images.map(img => 'data:' + (img.mimeType || 'image/png') + ';base64,' + img.base64);

let why = '';
if (urls.length === 0) {
  const sent = $('Office Binary To Base64').first().json || {};
  if (!sent.officeBytes) {
    why = 'the file could not be downloaded from Google Drive';
  } else if (resp.error) {
    why = 'the conversion request failed: '
        + (typeof resp.error === 'string' ? resp.error : JSON.stringify(resp.error)).substring(0, 400);
  } else if (resp.detail) {
    why = 'LibreOffice could not convert it: ' + JSON.stringify(resp.detail).substring(0, 400);
  } else {
    why = 'the converter gave no usable answer: ' + JSON.stringify(resp).substring(0, 400);
  }
}

const originalReason = origin.extractionNote || 'it could not be read as text';

return [{ json: {
  fileId: f.id, fileName: f.name, mimeType: f.mimeType,
  // Keep the original classification when nothing worked, so the report stays honest.
  sourceType: urls.length > 0 ? 'office-converted' : (origin.sourceType || 'unknown'),
  imageDataUrls: urls,
  imageOk: urls.length > 0,
  imageNote: urls.length > 0
    ? ('Could not be read as text, so it was converted to ' + urls.length
       + ' page image(s) and read by the vision model.')
    : ('Two attempts failed. Text extraction: ' + originalReason
       + ' Conversion to images: ' + why + '.')
} }];
