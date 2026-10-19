(() => {
  'use strict';

  const STORAGE_KEY = 'kpAboutPortraitV1';
  const MAX_INPUT_BYTES = 12 * 1024 * 1024;
  const MAX_OUTPUT_BYTES = 320 * 1024;
  const START_MAX_WIDTH = 720;
  const START_MAX_HEIGHT = 900;
  const ACCEPTED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
  let currentPortrait = '';
  let selectionVersion = 0;

  const byId = id => document.getElementById(id);
  const notify = (message, type) => {
    if (typeof window.showToast === 'function') window.showToast(message, type);
  };

  function setStatus(message, state = '') {
    const status = byId('about-photo-status');
    if (!status) return;
    status.textContent = message;
    status.dataset.state = state;
  }

  function dataUrlBytes(source) {
    if (typeof source !== 'string' || !/^data:image\/(?:jpeg|webp);base64,/i.test(source)) return 0;
    const payload = source.slice(source.indexOf(',') + 1);
    if (!/^[A-Za-z0-9+/]+={0,2}$/.test(payload)) return 0;
    return Math.floor(payload.length * 3 / 4) - ((payload.endsWith('==') ? 2 : payload.endsWith('=') ? 1 : 0));
  }

  function readFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ''));
      reader.onerror = () => reject(new Error('The selected portrait could not be read.'));
      reader.readAsDataURL(file);
    });
  }

  function decodeImage(source) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => {
        if (image.naturalWidth > 0 && image.naturalHeight > 0) resolve(image);
        else reject(new Error('The selected portrait has no readable image data.'));
      };
      image.onerror = () => reject(new Error('Choose a valid JPG, PNG or WebP portrait.'));
      image.src = source;
    });
  }

  function canvasBlob(canvas, quality) {
    return new Promise((resolve, reject) => {
      canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('The portrait could not be compressed.')), 'image/jpeg', quality);
    });
  }

  async function blobDataUrl(blob) {
    return readFile(new File([blob], 'about-portrait.jpg', {type: 'image/jpeg'}));
  }

  async function compressPortrait(source) {
    const image = await decodeImage(source);
    let scale = Math.min(1, START_MAX_WIDTH / image.naturalWidth, START_MAX_HEIGHT / image.naturalHeight);
    let width = Math.max(1, Math.round(image.naturalWidth * scale));
    let height = Math.max(1, Math.round(image.naturalHeight * scale));
    let quality = .86;
    let best = null;

    for (let attempt = 0; attempt < 8; attempt++) {
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext('2d', {alpha: false});
      if (!context) throw new Error('This computer cannot prepare the portrait image.');
      context.imageSmoothingEnabled = true;
      context.imageSmoothingQuality = 'high';
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, width, height);
      context.drawImage(image, 0, 0, width, height);
      const blob = await canvasBlob(canvas, quality);
      best = {blob, width, height};
      if (blob.size <= MAX_OUTPUT_BYTES || Math.max(width, height) <= 420) break;
      if (quality > .68) quality -= .08;
      else {
        width = Math.max(1, Math.round(width * .84));
        height = Math.max(1, Math.round(height * .84));
      }
    }
    const sourceUrl = await blobDataUrl(best.blob);
    return {source: sourceUrl, width: best.width, height: best.height, bytes: best.blob.size};
  }

  function renderPortrait(source) {
    const slot = byId('about-developer-photo');
    if (!slot) return;
    slot.replaceChildren();
    if (source) {
      const image = document.createElement('img');
      image.alt = 'Shri. Nitin R Talegaonkar';
      image.decoding = 'async';
      image.src = source;
      slot.append(image);
      slot.setAttribute('aria-label', 'Portrait of Shri. Nitin R Talegaonkar');
    } else {
      const initials = document.createElement('span');
      initials.className = 'about-photo-initials';
      initials.dataset.noLocalize = 'true';
      initials.textContent = 'NRT';
      slot.append(initials);
      slot.setAttribute('aria-label', 'Developer portrait placeholder');
    }
    currentPortrait = source;
    const remove = byId('remove-about-photo');
    if (remove) remove.hidden = !source;
  }

  function persistPortrait(record) {
    try {
      if (record) localStorage.setItem(STORAGE_KEY, JSON.stringify(record));
      else localStorage.removeItem(STORAGE_KEY);
      return true;
    } catch (_) {
      return false;
    }
  }

  async function selectPortrait(event) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    const version = ++selectionVersion;
    if (!file) return;
    setStatus('Preparing a compact portrait…', 'working');
    try {
      if (file.size <= 0 || file.size > MAX_INPUT_BYTES) throw new Error('Choose a portrait smaller than 12 MB.');
      if (!ACCEPTED_TYPES.has(file.type)) throw new Error('Choose a JPG, PNG or WebP portrait.');
      const original = await readFile(file);
      const result = await compressPortrait(original);
      if (version !== selectionVersion) return;
      renderPortrait(result.source);
      const saved = persistPortrait({version: 1, source: result.source, width: result.width, height: result.height});
      const size = Math.max(1, Math.round(result.bytes / 1024));
      setStatus(saved ? `Portrait saved on this computer · ${size} KB` : `Portrait ready for this session · ${size} KB`, saved ? 'saved' : 'session');
      notify(saved ? 'About portrait saved.' : 'Portrait added for this session. Browser storage is unavailable.', saved ? 'success' : 'warning');
      window.dispatchEvent(new CustomEvent('about-portrait-change', {detail: {ready: true, saved}}));
      return result.source;
    } catch (error) {
      if (version === selectionVersion) {
        setStatus(error.message, 'error');
        notify(error.message, 'error');
      }
    } finally {
      input.value = '';
    }
  }

  // The owner's portrait is fixed; presentation controls cannot clear it.
  function removePortrait() { return false; }

  async function restorePortrait() {
    let parsed = null;
    try { parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null'); } catch (_) { /* Ignore a damaged local record. */ }
    const source = parsed?.version === 1 && dataUrlBytes(parsed.source) <= MAX_OUTPUT_BYTES + 4096 ? parsed.source : '';
    if (!source) {
      
      renderPortrait('');
      setStatus('No portrait selected. Choose a photo to store it offline.');
      return;
    }
    try {
      await decodeImage(source);
      renderPortrait(source);
      setStatus(`Portrait stored on this computer · ${Math.max(1, Math.round(dataUrlBytes(source) / 1024))} KB`, 'saved');
    } catch (_) {
      renderPortrait('');
      setStatus('The saved portrait could not be read. Please choose it again.', 'error');
    }
  }

  function enhanceAbout() {
    const card = document.querySelector('#about .about-card');
    const profile = card?.querySelector('.developer-profile');
    const slot = byId('about-developer-photo');
    if (!card || !profile || !slot || card.dataset.brandingReady === 'true') return false;
    card.dataset.brandingReady = 'true';
    card.classList.add('about-branding-card');

    const heading = profile.querySelector('h2');
    if (heading) {
      heading.textContent = 'Shri. Nitin R Talegaonkar — B.Sc-Maths/MCA';
      heading.dataset.noLocalize = 'true';
    }

    const role = profile.querySelector('.developer-role');
    if (role && !profile.querySelector('.about-advisor')) {
      const advisor = document.createElement('p');
      advisor.className = 'about-advisor';
      advisor.dataset.noLocalize = 'true';
      const label = document.createElement('span');
      label.className = 'about-advisor-label';
      label.textContent = 'KP Advisor:';
      const name = document.createElement('strong');
      name.textContent = 'Mr. Anil Deshmukh';
      const title = document.createElement('span');
      title.textContent = '— KP astrologer';
      advisor.append(label, name, title);
      role.after(advisor);
    }

    const wrap = document.createElement('div');
    wrap.className = 'developer-photo-wrap';
    slot.before(wrap);
    wrap.append(slot);
    restorePortrait();
    window.KPLanguage?.localize?.(card);
    return true;
  }

  window.KPAboutBranding = Object.freeze({
    storageKey: STORAGE_KEY,
    getPortrait: () => currentPortrait,
    selectFile: file => selectPortrait({currentTarget:{files:[file],value:''}}),
    clearPortrait: removePortrait,
    refresh: enhanceAbout
  });

  function initialize() {
    if (enhanceAbout()) return;
    const observer = new MutationObserver(() => {
      if (enhanceAbout()) observer.disconnect();
    });
    observer.observe(document.documentElement, {childList: true, subtree: true});
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, {once: true});
  else initialize();
})();
