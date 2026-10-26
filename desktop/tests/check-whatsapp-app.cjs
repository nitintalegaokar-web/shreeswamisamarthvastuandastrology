const assert = require('node:assert/strict');
const { isWhatsAppAppUrl } = require('../whatsapp.cjs');
for (const url of ['whatsapp://send?phone=919000000000&text=Hello%20customer', 'whatsapp://send?text=Remedy%0Aमराठी']) assert.equal(isWhatsAppAppUrl(url), true);
for (const url of ['https://wa.me/919000000000?text=Hi','https://web.whatsapp.com','file:///etc/passwd','whatsapp://call?text=Hi','whatsapp://send/other?text=Hi','whatsapp://send?phone=abc&text=Hi','whatsapp://send?text=Hi&other=x','whatsapp://send?text=a&text=b','whatsapp://send?text=']) assert.equal(isWhatsAppAppUrl(url), false, url);
console.log('PASS: WhatsApp send deep links only; web URLs and other protocols/actions rejected.');
