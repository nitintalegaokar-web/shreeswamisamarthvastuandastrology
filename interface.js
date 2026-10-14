// One action toolbar; view-specific controls retain only their unique operations.
const appHeader=document.querySelector('header'),settingsSidebar=document.querySelector('.layout > aside');
settingsSidebar.querySelector('h2').textContent='Geometry & direction';
const floorField=$('floorSelect').closest('.field');floorField.classList.add('header-floor');appHeader.append(floorField);
appHeader.append($('mapFile'));settingsSidebar.querySelector('.steps')?.remove();[...settingsSidebar.querySelectorAll('h3')].find(x=>x.textContent==='Steps')?.remove();
for(const button of document.querySelectorAll('button')){const action=button.getAttribute('onclick')||'';if(action==="showTab('report')"&&button.closest('header'))button.remove();if(settingsSidebar.contains(button)&&["setMode('center')","setMode('boundary')","undo('center')","undo('boundary')","showTab('chart')"].includes(action))button.remove();if(action==='undo()'||action==='resetMarks()'||action==='downloadMap()')button.remove();if(action==="setMode('view')"&&button.closest('#markingPanel'))button.remove();if(action==='printReport()'&&button.closest('#downloadTab'))button.remove();if(action==="showTab('report')"&&button.closest('#downloadTab'))button.remove()}
$('emptyMap').querySelectorAll('button').forEach(b=>b.remove());
$('workspaceOverview').style.display='none';
const quietOverview=updateOverview;updateOverview=function(){quietOverview();$('workspaceOverview').style.display='none'};
const actions=document.createElement('div');actions.className='global-actions';actions.innerHTML='<button id="globalUndo" onclick="globalUndo()">↶ Undo</button><button id="globalRedo" onclick="buildRedo()">↷ Redo</button><button onclick="globalExport()">Export SVG</button><button onclick="globalClear()">Clear marks</button><button onclick="newProject()">New project</button><button onclick="loadDemo()">Sample</button>';
appHeader.append(actions);
function globalUndo(){if(tab==='builder')buildUndo();else undo()}
function globalClear(){if(tab==='builder'&&!floor().builder)return notify('Create a drawing floor first.');if(tab==='builder'){if(!confirm('Clear all drawing features on this floor?'))return;rememberBuild();const f=floor();f.boundary=[];f.center=[];f.rooms=[];f.objects=[];f.entrances=[];f.builder.walls=[];f.builder.doors=[];f.builder.labels=[];buildSelected=null;buildDraft=[];updateBuilderImage();render();renderBuilder()}else resetMarks()}
function globalExport(){if(tab==='entry'||tab==='devta')downloadReference(tab,$(`${tab}Canvas`)?.querySelector('.diagram-footer input')?.checked!==false);else if(tab==='chart')download(new Blob([distributionSVG()],{type:'image/svg+xml'}),'Vastu_Zone_Distribution.svg');else downloadMap()}
function deduplicateView(){document.querySelectorAll('.diagram-footer').forEach(el=>el.innerHTML='<label class="check"><input type="checkbox" checked> Include legend in SVG export</label>');$('distributionPanel')?.querySelector('.plot-header button')?.remove();$('builderTab').querySelectorAll('[onclick="buildUndo()"],[onclick="buildRedo()"],[onclick="downloadMap()"],[onclick="showTab(\'chart\')"]').forEach(b=>b.remove());$('builderTab').querySelector('[onclick="finishBuild()"]')?.classList.toggle('hidden',!['boundary','room'].includes(buildMode));document.querySelectorAll('.builder-feature-list button').forEach(b=>b.textContent='Remove');$('globalRedo').disabled=tab!=='builder'||!floor().builder;$('globalUndo').disabled=['entry','devta','compass','download','report'].includes(tab)}
const uniqueBuilder=renderBuilder;renderBuilder=function(){uniqueBuilder();deduplicateView();$('buildWidth')?.closest('.field')?.classList.toggle('hidden',buildMode!=='boundary')};
const uniqueEntry=renderEntries;renderEntries=function(){uniqueEntry();deduplicateView()};
const uniqueDevtas=renderDevtas;renderDevtas=function(){uniqueDevtas();deduplicateView()};
const uniqueChart=renderChart;renderChart=function(){uniqueChart();deduplicateView()};
const uniqueTab=showTab;showTab=function(id){uniqueTab(id);deduplicateView()};
// Analyse Map uses one click to enter a mode; no separate Start button.
const startControl=analysisPanel.querySelector('[onclick="analysisMode(analysisFeature)"]');startControl?.remove();
// Floor setup and feature modes are shown once in the relevant workspace.
const editorOptions=$('editorTab').querySelector('.row');editorOptions.querySelectorAll('button').forEach(b=>{if(['Room','Object','Entrance'].includes(b.textContent.trim()))b.remove()});
const uniqueMode=setMode;setMode=function(m){uniqueMode(m);$('markingPanel').classList.toggle('hidden',tab!=='editor'||!['room','object','entrance'].includes(m))};
const newEditorTab=showTab;showTab=function(id){newEditorTab(id);$('markingPanel').classList.toggle('hidden',id!=='editor'||!['room','object','entrance'].includes(mode))};
appHeader.querySelector('h1').textContent='◈ Vastu Master Studio';
// Keyboard navigation is scoped to the active drawing workflow.
window.addEventListener('keydown',e=>{if(tab!=='builder'||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||dialog.open)return;if(e.key==='Escape'){buildDraft=[];buildSelected=null;renderBuilder()}if((e.ctrlKey||e.metaKey)&&e.key==='y'){e.preventDefault();buildRedo()}if(e.key==='Delete'&&buildSelected)deleteBuilderSelected();if(e.key.startsWith('Arrow')){e.preventDefault();const delta={ArrowLeft:[-40,0],ArrowRight:[40,0],ArrowUp:[0,-40],ArrowDown:[0,40]}[e.key];buildPan(...delta)}},true);
// Prevent older editor shortcuts from acting on the builder's floor history.
window.addEventListener('keydown',e=>{if(tab==='builder'&&!/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)&&!dialog.open&&(e.key==='Enter'||((e.ctrlKey||e.metaKey)&&e.key==='z'))){e.preventDefault();e.stopImmediatePropagation();if(e.key==='Enter')finishBuild();else buildUndo()}},true);
deduplicateView();
document.body.dataset.studioTab=tab;

$('downloadTab').querySelector('.panel').insertAdjacentHTML('beforeend','<p class="hint">Choose the sections here, then open Premium Report to preview and print / save as PDF.</p>');
$('devtaTab').querySelector('.hint').textContent='Schematic concentric reference: 1 center, 4 inner, 8 middle and 32 outer regions. Verify traditional placements against your chosen reference before interpretation.';
