'use strict';
function isExternal(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' ||
      (parsed.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(parsed.hostname));
  } catch { return false; }
}
function isPreview(url) {
  return url === '' || url === 'about:blank' || url.startsWith('about:blank#') || url.startsWith('blob:');
}
function safeFilename(name) {
  return String(name || 'KP-report.pdf').replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').replace(/[. ]+$/, '').slice(0,180) || 'KP-report.pdf';
}
module.exports = {isExternal, isPreview, safeFilename};
