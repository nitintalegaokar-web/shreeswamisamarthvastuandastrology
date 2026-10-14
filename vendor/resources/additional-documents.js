(() => {
'use strict';
function init(){const d=JSON.parse(document.getElementById('kp-additional-document-data').textContent);KPResources.importTopics(d.topics,d.sources.map(s=>s.sha256).join(':'));window.KPDocumentReferences=Object.freeze({sources:d.sources,numbers:d.numbers});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();
})();
