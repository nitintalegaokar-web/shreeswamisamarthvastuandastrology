// Classic-script PDF.js bundles also work when index.html is opened from disk.
function localPdfAsset(name){const encoded=window.vastuPdfAssets?.[name];if(!encoded)throw Error('Missing bundled PDF font or CMap: '+name);const decoded=atob(encoded),bytes=new Uint8Array(decoded.length);for(let i=0;i<decoded.length;i++)bytes[i]=decoded.charCodeAt(i);return bytes}
class LocalCMapReader{async fetch({name}){return {cMapData:localPdfAsset(name+'.bcmap'),compressionType:1}}}
class LocalStandardFontReader{async fetch({filename}){return localPdfAsset(filename)}}
async function ensurePdfRuntime(){if(!window.pdfjs?.getDocument||!window.pdfjsWorker?.WorkerMessageHandler||!window.vastuPdfAssets)throw Error('PDF support files are missing. Extract the complete updated ZIP, including its vendor folder, then reopen index.html.');return window.pdfjs}
function pdfDocumentOptions(bytes){return {data:bytes,CMapReaderFactory:LocalCMapReader,StandardFontDataFactory:LocalStandardFontReader,useWorkerFetch:false,isEvalSupported:false}}
