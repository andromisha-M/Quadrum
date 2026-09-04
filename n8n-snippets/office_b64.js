const f = $('Process Files One By One').first().json;
let base64 = '';
try {
  const buffer = await this.helpers.getBinaryDataBuffer(0, 'data');
  base64 = buffer.toString('base64');
} catch (e) {
  base64 = '';
}
return [{ json: { officeBase64: base64, officeBytes: base64.length, fileName: f.name } }];
