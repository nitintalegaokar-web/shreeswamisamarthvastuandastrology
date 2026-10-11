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
})();
