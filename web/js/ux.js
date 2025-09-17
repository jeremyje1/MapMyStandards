// UX helpers: tooltips, tutorial banner, high-contrast toggle, ARIA utilities
(function(){
  const s = document.createElement('style');
  s.textContent = `
    .mms-tooltip{position:relative;cursor:help}
    .mms-tooltip:hover .mms-tip{opacity:1;transform:translateY(0)}
    .mms-tip{position:absolute;z-index:100;background:#111827;color:#fff;border-radius:6px;padding:6px 8px;font-size:12px;line-height:1.2;white-space:nowrap;opacity:0;transform:translateY(-4px);transition:opacity .15s,transform .15s;top:100%;left:0;margin-top:6px}
    .mms-banner{background:#ecfeff;border:1px solid #a5f3fc;padding:10px 12px;border-radius:8px;margin:12px 0;display:flex;gap:10px;align-items:flex-start}
    .mms-banner strong{color:#0c4a6e}
    .high-contrast *, .high-contrast{color:#000 !important;background:#fff !important}
    .high-contrast a{color:#0000ee !important;text-decoration:underline}
    .visually-hidden{position:absolute!important;height:1px;width:1px;overflow:hidden;clip:rect(1px,1px,1px,1px);white-space:nowrap}
  `;
  document.head.appendChild(s);

  function attachTooltip(el, text){
    if (!el) return;
    el.classList.add('mms-tooltip');
    el.setAttribute('aria-label', text);
    const tip = document.createElement('span');
    tip.className = 'mms-tip';
    tip.textContent = text;
    el.appendChild(tip);
  }

  async function renderTutorialBanner(container){
    if (!container) return;
    try {
      const res = await fetch(`${(window.MMS_CONFIG&&MMS_CONFIG.API_BASE_URL)||''}/api/user/intelligence-simple/ui/tutorial`, { credentials: 'include' });
      if (!res.ok) return;
      const data = await res.json();
      const key = data.dismiss_key || 'mms_tutorial_dismissed';
      if (localStorage.getItem(key) === '1') return;
      const banner = document.createElement('div');
      banner.className = 'mms-banner';
      banner.setAttribute('role','region');
      banner.setAttribute('aria-label','Getting started tutorial');
      const cta = document.createElement('button');
      cta.textContent = 'Show Tutorial';
      cta.className = 'btn-tutorial';
      cta.setAttribute('aria-label','Show tutorial steps');
      const dismiss = document.createElement('button');
      dismiss.textContent = 'Dismiss';
      dismiss.setAttribute('aria-label','Dismiss tutorial banner');
      const msg = document.createElement('div');
      msg.innerHTML = '<strong>New here?</strong> Learn how to select standards, map evidence, review risk, and generate narratives. '+
        '<a href="/docs" target="_blank" rel="noopener">Docs</a> · <a href="/faq" target="_blank" rel="noopener">FAQ</a>';
      banner.appendChild(msg); banner.appendChild(cta); banner.appendChild(dismiss);
      container.prepend(banner);
      cta.addEventListener('click', () => {
        try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch {}
        alert('Tutorial:\n- Select Standards\n- Map Evidence\n- Review Risk\n- Generate Narrative');
      });
      dismiss.addEventListener('click', () => { localStorage.setItem(key, '1'); banner.remove(); });
    } catch {}
  }

  function toggleHighContrast(){
    document.documentElement.classList.toggle('high-contrast');
  }

  window.MMS_UX = { attachTooltip, renderTutorialBanner, toggleHighContrast };
})();
