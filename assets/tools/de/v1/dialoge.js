(() => {
  const specs = [
    ['tw-fonts-modal','Schriftstil auswählen','#tw-fonts-close'],
    ['tw-symbols-modal','Sonderzeichen auswählen','#tw-symbols-close'],
    ['tw-export-modal','Exportoptionen','#tw-export-close'],
    ['tw-result-modal','Exportergebnis','#tw-result-close'],
    ['bio-icon-picker','Bio-Symbole','button[onclick*="closeBioPicker"]'],
    ['bio-fonts-picker','Bio-Schriftstil','button[onclick*="closeBioFontsPicker"]'],
    ['lf194-cert-modal','Dekoratives Namenszertifikat','#lf194-cert-close'],
    ['lf194-icon-dropdown','Symbole und Leerzeichen','#lf194-icon-close']
  ];
  const visible = el => el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const panels = specs.map(([id,label,selector]) => {
    const el = document.getElementById(id), close = el.querySelector(selector);
    el.setAttribute('role','dialog'); el.setAttribute('aria-label',label);
    if(id!=='lf194-icon-dropdown')el.setAttribute('aria-modal','true');
    close.setAttribute('aria-label','Schließen');
    return {el,close,open:false};
  });
  let trigger,stack=[];
  document.addEventListener('click',e=>{const t=e.target.closest('button,a,select');if(t)trigger=t;},true);
  function update() {
    const opened=panels.filter(p=>!p.open && visible(p.el)),closed=stack.filter(p=>!visible(p.el));
    closed.forEach(p=>{p.open=false;}); stack=stack.filter(p=>p.open);
    opened.forEach(p=>{p.open=true;p.trigger=trigger;stack.push(p);});
    const top=stack.at(-1);
    if(opened.length)top.close.focus({preventScroll:true});
    else if(closed.length){const old=closed.at(-1).trigger;if(visible(old))old.focus({preventScroll:true});else if(top)top.close.focus({preventScroll:true});}
  }
  panels.forEach(p=>new MutationObserver(update).observe(p.el,{attributes:true,attributeFilter:['class','style','hidden']}));
  document.addEventListener('keydown',e=>{
    const p=stack.at(-1);if(!p || !visible(p.el))return;
    if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();p.close.click();return;}
    if(e.key!=='Tab')return;
    const controls=[...p.el.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]')].filter(visible);
    const first=controls[0],last=controls.at(-1),active=document.activeElement;
    if(first&&(!p.el.contains(active)||(e.shiftKey&&active===first)||(!e.shiftKey&&active===last))){e.preventDefault();(e.shiftKey?last:first).focus();}
  },true);
})();
