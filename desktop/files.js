(() => {
  'use strict';
  if (!window.KPDesktopFiles) return;
  const name = chart => {
    const fields = chart.fields || {};
    const native = String(fields.name?.value || 'kundali').replace(/[^\p{L}\p{N}_-]+/gu, '-').slice(0,65);
    return native + '-' + (fields['chart-kind']?.value || 'natal') + '.lkp';
  };
  window.KPChartFiles = Object.freeze({
    directory:async () => null,
    save:async chart => {
      const saved = await KPDesktopFiles.save(JSON.stringify(chart,null,2), name(chart));
      if (!saved) throw new DOMException('Save cancelled.', 'AbortError');
      return 'Saved ' + saved;
    },
    open:async () => {
      const selected = await KPDesktopFiles.open();
      return selected ? new File([selected.text], selected.name, {type:'application/json'}) : null;
    }
  });
  if (window.KPLicensing?.importControl) {
    const menu=document.querySelector('.backup-options'),button=document.createElement('button');
    button.id='kp-import-license-status';button.type='button';
    const label=()=>{button.textContent=window.KPPreferences?.get().language==='marathi'?'परवाना स्थिती आयात करा · Import license status':'Enter Activate / Deactivate key';};
    label();window.addEventListener('kp-preferences-changed',label);menu?.append(button);
    button.addEventListener('click',async()=>{
      button.disabled=true;
      try{const result=await KPLicensing.enterKey();if(result)window.showToast?.(window.KPPreferences?.get().language==='marathi'?'परवान्याची स्थिती लागू झाली.':'Paste the owner status key on the activation screen.','success');}
      catch(error){window.showToast?.(error.message.replace(/^Error invoking remote method '[^']+': (Error: )?/,''),'error');}
      finally{button.disabled=false;document.querySelector('.backup-menu').open=false;}
    });
  }
})();
