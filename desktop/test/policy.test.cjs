const test = require('node:test');
const assert = require('node:assert/strict');
const {isExternal,isPreview,safeFilename} = require('../policy.cjs');
test('Only web account links can open the external browser', () => {
  assert.equal(isExternal('https://accounts.example.com/#account'),true);
  assert.equal(isExternal('http://localhost:8080/#account'),true);
  for (const url of ['javascript:alert(1)','file:///C:/secret.txt','ms-settings:','http://example.com','bad url']) assert.equal(isExternal(url),false);
});
test('Local report preview windows work without allowing network pages', () => {
  for (const url of ['','about:blank','about:blank#preview','blob:file:///report']) assert.equal(isPreview(url),true);
  for (const url of ['https://example.com','file:///C:/secret.txt']) assert.equal(isPreview(url),false);
});
test('Download file names cannot escape the selected save directory', () => {
  for (const filename of ['../../report.pdf','C:\\secret.pdf','report?.pdf','']) {
    const safe=safeFilename(filename);
    assert.ok(safe.length>0);
    assert.equal(/[<>:"/\\|?*\x00-\x1f]/.test(safe),false);
  }
});
