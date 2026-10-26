// Only the WhatsApp app's send action may be passed to the operating system.
function isWhatsAppAppUrl(value) {
  try {
    const url = new URL(value);
    if (url.protocol !== 'whatsapp:' || url.hostname !== 'send' ||
        !['', '/'].includes(url.pathname) || url.username || url.password || url.port || url.hash) return false;
    if ([...url.searchParams.keys()].some(key => !['phone', 'text'].includes(key))) return false;
    if (url.searchParams.getAll('text').length !== 1 || url.searchParams.getAll('phone').length > 1) return false;
    const phone = url.searchParams.get('phone');
    return !!url.searchParams.get('text') && (phone === null || /^[1-9]\d{6,14}$/.test(phone));
  } catch { return false; }
}
module.exports = { isWhatsAppAppUrl };
