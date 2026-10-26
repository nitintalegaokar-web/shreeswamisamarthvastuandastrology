const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
(async () => {
  const opened = [], messages = [], handlers = {};
  let ready, fail = false;
  const electron = {
    app: { setPath() {}, getPath: () => '/tmp', requestSingleInstanceLock: () => true,
      on() {}, whenReady: () => ({ then: fn => ready = fn }), getVersion: () => '1.3.1' },
    BrowserWindow: class {
      constructor() { this.webContents = {
        setWindowOpenHandler: fn => handlers.open = fn,
        on: (name, fn) => handlers[name] = fn
      }; }
      once() {} loadFile() {}
    },
    Menu: { setApplicationMenu() {}, buildFromTemplate: x => x },
    session: { defaultSession: { setPermissionRequestHandler() {} } },
    dialog: { showMessageBox: (_window, message) => messages.push(message) },
    shell: { openExternal: async url => { if (fail) throw Error('No handler'); opened.push(url); } }
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../main.cjs'), 'utf8'), {
    require: name => name === 'electron' ? electron : name === './whatsapp.cjs' ? require('../whatsapp.cjs') : require(name),
    __dirname: path.join(__dirname, '..'), URL
  });
  await ready();
  const url = 'whatsapp://send?phone=919000000000&text=Namaste';
  assert.deepEqual(handlers.open({url}).action, 'deny');
  assert.equal(opened[0], url);
  for (const blocked of ['https://wa.me/919000000000', 'https://web.whatsapp.com', 'file:///tmp/test', 'whatsapp://call?text=x']) handlers.open({url: blocked});
  assert.equal(opened.length, 1);
  let prevented = false;
  handlers['will-navigate']({preventDefault: () => prevented = true}, url);
  assert(prevented); assert.equal(opened.length, 2);
  fail = true; handlers.open({url}); await new Promise(resolve => setImmediate(resolve));
  assert.equal(messages.length, 1); assert(messages[0].message.includes('Install WhatsApp'));
  assert.equal(opened.length, 2);
  console.log('PASS desktop routing opens app URLs, blocks web and unrelated links, and explains missing WhatsApp without browser fallback.');
})().catch(error => { console.error(error); process.exit(1); });
