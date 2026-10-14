/* Read-only DOCX topic import; never used by astrology calculations. */
(()=>{'use strict';
function init(){const node=document.getElementById('kp-kaal-resource-data');if(!node||!window.KPResources?.importTopics)return;const data=JSON.parse(node.textContent);window.KPResources.importTopics(data.topics,data.source.sha256);window.KPKaalResources=Object.freeze({topicCount:data.topicCount,paragraphCount:data.paragraphCount,source:data.source});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else setTimeout(init,0);
})();
