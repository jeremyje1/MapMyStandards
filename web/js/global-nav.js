(() => {
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

  const makeLink = (l) => {
    const a = document.createElement('a');
    a.href = origin + l.path;
    a.textContent = l.text;
    a.className = 'px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50';
    if (pathname === l.path) {
      a.className += ' text-blue-600 bg-blue-50';
      a.setAttribute('aria-current', 'page');
    }
    return a;
  };

  const renderNav = () => {
    const header = document.querySelector('header');
    if (!header) return;
    const container = header.querySelector('.max-w-7xl, .header-content') || header;
    const bar = document.createElement('div');
    bar.style.borderTop = '1px solid #e5e7eb';
    bar.style.background = '#fff';
    bar.innerHTML = '<div class="px-4 sm:px-6 lg:px-8"><nav class="flex flex-wrap items-center gap-2 py-2" id="globalNavContainer"></nav></div>';
    container.appendChild(bar);
    const nav = bar.querySelector('#globalNavContainer');
    links.forEach(l => nav.appendChild(makeLink(l)));
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderNav);
  } else {
    renderNav();
  }
})();
