(() => {
  if (document.getElementById('globalNavContainer')) return;

  const links = [
    { text: 'AI Dashboard', path: '/ai-dashboard' },
    { text: 'Standards', path: '/standards' },
    { text: 'Evidence Mapping', path: '/evidence-mapping' },
    { text: 'Reports', path: '/reports' },
    { text: 'Org Chart', path: '/org-chart' },
    { text: 'Upload', path: '/upload' }
  ];

  const pathname = window.location.pathname.replace(/\/$/, '');
  const origin = window.location.origin;

  const ensureStyle = () => {
    if (document.getElementById('mms-global-nav-style')) return;
    const s = document.createElement('style');
    s.id = 'mms-global-nav-style';
    s.textContent = `
      .mms-global-nav{background:#fff;border-bottom:1px solid #e5e7eb;}
      .mms-gn-inner{max-width:1200px;margin:0 auto;padding:8px 16px;}
      .mms-gn-nav{display:flex;gap:8px;flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch}
      .mms-gn-nav a{display:inline-block;padding:6px 10px;border-radius:6px;font-size:14px;color:#374151;text-decoration:none;white-space:nowrap}
      .mms-gn-nav a:hover{background:#f3f4f6;color:#111827}
      .mms-gn-nav a[aria-current="page"]{color:#1d4ed8;background:#eff6ff;font-weight:600}
      .mms-gn-nav::-webkit-scrollbar{height:6px}
      .mms-gn-nav::-webkit-scrollbar-thumb{background:#e5e7eb;border-radius:3px}
    `;
    document.head.appendChild(s);
  };

  const makeLink = (l) => {
    const a = document.createElement('a');
    a.href = origin + l.path;
    a.textContent = l.text;
    if (pathname === l.path) a.setAttribute('aria-current', 'page');
    return a;
  };

  const renderNav = () => {
    ensureStyle();
    const bar = document.createElement('div');
    bar.className = 'mms-global-nav';
    bar.innerHTML = '<div class="mms-gn-inner"><nav class="mms-gn-nav" id="globalNavContainer"></nav></div>';
    const header = document.querySelector('header');
    if (header && header.parentNode) {
      header.parentNode.insertBefore(bar, header.nextSibling);
    } else {
      document.body.insertBefore(bar, document.body.firstChild);
    }
    const nav = bar.querySelector('#globalNavContainer');
    links.forEach(l => nav.appendChild(makeLink(l)));
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderNav);
  else renderNav();
})();
