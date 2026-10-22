// electron-builder 26.15.3 normally executes the NSIS uninstaller stub with Wine
// on Linux. Its own UninstallerReader extracts exactly that embedded executable
// natively (the same implementation used by the builder on macOS).
// Use that parser only for this project's expected uninstaller-generation call.
// Use the builder's supported x86 executable compression filter.
// This changes compression only; the installed files remain identical.
process.env.ELECTRON_BUILDER_7Z_FILTER ??= 'BCJ2';
const path = require('node:path');
const { build, Platform, Arch } = require('electron-builder');
const { WineVmManager } = require('app-builder-lib/out/vm/WineVm');
const { UninstallerReader } = require('app-builder-lib/out/targets/nsis/nsisUtil');
const { version } = require('./package.json');
const setup = path.join(__dirname, 'release', `KP-Master-Setup-${version}.exe`);
const uninstaller = setup.slice(0, -3) + '__uninstaller.exe';
const original = WineVmManager.prototype.exec;
if (process.platform === 'linux') {
  WineVmManager.prototype.exec = function(file, args, options, ...rest) {
    if (path.resolve(file) === setup && (!args || args.length === 0) && options?.env?.__COMPAT_LAYER === 'RunAsInvoker') {
      console.log('Extracting the NSIS uninstaller using electron-builder native parser.');
      return UninstallerReader.exec(setup, uninstaller);
    }
    return original.call(this, file, args, options, ...rest);
  };
}
build({
  projectDir: __dirname,
  targets: Platform.WINDOWS.createTarget(['nsis'], Arch.x64),
  publish: 'never',
  ...(process.argv.includes('--prepackaged') ? { prepackaged: path.join(__dirname, 'release', 'win-unpacked') } : {})
}).catch(error => { console.error(error); process.exitCode = 1; });
