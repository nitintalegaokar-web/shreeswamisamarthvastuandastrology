const esbuild=require('esbuild'),fs=require('fs'),path=require('path');
esbuild.buildSync({stdin:{contents:"export {jsPDF} from 'jspdf'; export {default as html2canvas} from 'html2canvas';",resolveDir:path.resolve(__dirname,'..')},bundle:true,format:'iife',globalName:'ReportPDF',platform:'browser',target:'es2022',minify:true,outfile:'vendor/report-pdf.js',legalComments:'inline'});
for(const pkg of ['jspdf','html2canvas']){const base=path.dirname(require.resolve(pkg+'/package.json'));const license=fs.readdirSync(base).find(n=>/^licen[cs]e/i.test(n));if(license)fs.copyFileSync(path.join(base,license),'vendor/'+pkg+'-LICENSE.txt')}
console.log('Built offline report PDF runtime.');
