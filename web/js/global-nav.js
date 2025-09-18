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
  const API_BASE = (window.MMS_CONFIG && window.MMS_CONFIG.API_BASE_URL) || '';

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
    a.innerHTML = `${l.text} ${l.path==='/standards'||l.path==='/evidence-mapping'?'<span class="mms-sel-badge" aria-label="Selected standards count" style="display:none;margin-left:6px;padding:0 6px;border-radius:999px;background:#1f2937;color:#fff;font-size:11px;line-height:18px;vertical-align:middle">0</span>':''}`;
    if (pathname === l.path) a.setAttribute('aria-current', 'page');
    return a;
  };

  const renderNav = () => {
    ensureStyle();
    const bar = document.createElement('div');
    bar.className = 'mms-global-nav';
    bar.innerHTML = '<div class="mms-gn-inner" style="display:flex;align-items:center;justify-content:space-between;gap:12px;"><nav class="mms-gn-nav" id="globalNavContainer"></nav><div id="mmsSessionArea" style="font-size:12px;color:#374151;position:relative;"></div></div>';
    const header = document.querySelector('header');
    if (header && header.parentNode) {
      header.parentNode.insertBefore(bar, header.nextSibling);
    } else {
      document.body.insertBefore(bar, document.body.firstChild);
    }
    const nav = bar.querySelector('#globalNavContainer');
    links.forEach(l => nav.appendChild(makeLink(l)));

    // Selection badge updater
    const updateBadge = async (fromEvent) => {
      try {
        let selected = [];
        // Prefer server-side selection if available
        try {
          const r = await fetch(`${API_BASE}/user/intelligence-simple/standards/selection/load`.replace(/\/api$/, '/api') , { credentials: 'include' });
          if (r.ok) {
            const j = await r.json();
            if (Array.isArray(j.selected)) selected = j.selected;
          }
        } catch(_) {}
        if (!Array.isArray(selected) || selected.length === 0) {
          try { selected = JSON.parse(localStorage.getItem('mms:selectedStandards') || '[]') || []; } catch(_) { selected = []; }
        }
        const n = (selected && selected.length) || 0;
        const badges = bar.querySelectorAll('.mms-sel-badge');
        badges.forEach(b => { b.style.display = n>0?'inline-block':'none'; b.textContent = String(n); });
      } catch(_) {}
    };
    updateBadge();
    window.addEventListener('mms:selected-standards-updated', (e) => updateBadge(true));
    window.addEventListener('storage', (e) => { if (e.key === 'mms:selectedStandards') updateBadge(true); });

    const sess = bar.querySelector('#mmsSessionArea');
  const renderSession = (info) => {
      const email = (info && (info.email || (info.user && info.user.email))) || '';
      const active = info && (info.ok === true || info.success === true);
      sess.innerHTML = `
        <div id="mmsSessBtn" style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;padding:6px 10px;border:1px solid #e5e7eb;border-radius:6px;background:#f9fafb;">
          <span style="font-weight:600;color:#111827;">${email || 'Guest'}</span>
          <span style="color:${active ? '#065f46' : '#92400e'};background:${active ? '#ecfdf5' : '#fffbeb'};border:1px solid ${active ? '#a7f3d0' : '#fde68a'};padding:2px 6px;border-radius:999px;">Session: ${active ? 'active' : 'inactive'}</span>
          <span aria-hidden="true" style="color:#6b7280;">▾</span>
        </div>
        <div id="mmsSessMenu" style="display:none;position:absolute;right:0;top:36px;background:#fff;border:1px solid #e5e7eb;border-radius:6px;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);min-width:200px;z-index:50;">
          <button id="mmsToggleContrast" style="display:block;width:100%;text-align:left;padding:8px 12px;font-size:13px;color:#111827;background:#fff;border:none;cursor:pointer;">Toggle High Contrast</button>
          <button id="mmsRefreshToken" style="display:block;width:100%;text-align:left;padding:8px 12px;font-size:13px;color:#111827;background:#fff;border:none;cursor:pointer;">Refresh Token</button>
          <button id="mmsLogout" style="display:block;width:100%;text-align:left;padding:8px 12px;font-size:13px;color:#b91c1c;background:#fff;border:none;cursor:pointer;">Log out</button>
        </div>
      `;
  const toggle = sess.querySelector('#mmsToggleContrast');
  if (toggle) toggle.addEventListener('click', () => { try { window.MMS_UX && MMS_UX.toggleHighContrast && MMS_UX.toggleHighContrast(); } catch(_){} menu.style.display='none'; });
      const btn = sess.querySelector('#mmsSessBtn');
      const menu = sess.querySelector('#mmsSessMenu');
      btn.addEventListener('click', () => {
        menu.style.display = (menu.style.display === 'none' || !menu.style.display) ? 'block' : 'none';
      });
      document.addEventListener('click', (e) => {
        if (!sess.contains(e.target)) menu.style.display = 'none';
      });
      sess.querySelector('#mmsRefreshToken').addEventListener('click', async () => {
        try {
          if (window.MMS_AUTH && typeof window.MMS_AUTH.silentRefresh === 'function') {
            await window.MMS_AUTH.silentRefresh();
            if (window.mmsAPI && window.mmsAPI.showSuccess) window.mmsAPI.showSuccess('Session refreshed');
          } else {
            // Prefer /api/auth/refresh
            let r = await fetch(`${API_BASE}/api/auth/refresh`, { method: 'POST', credentials: 'include' });
            if (!r.ok && r.status === 404) {
              r = await fetch(`${API_BASE}/auth/refresh`, { method: 'POST', credentials: 'include' });
            }
            if (r.ok) {
              if (window.mmsAPI && window.mmsAPI.showSuccess) window.mmsAPI.showSuccess('Session refreshed');
            } else {
              if (window.mmsAPI && window.mmsAPI.showError) window.mmsAPI.showError(new Error('Unable to refresh session'));
            }
          }
        } catch (e) {
          if (window.mmsAPI && window.mmsAPI.showError) window.mmsAPI.showError(e);
        }
        menu.style.display = 'none';
      });
      sess.querySelector('#mmsLogout').addEventListener('click', async () => {
        try {
          if (window.MMS_AUTH && typeof window.MMS_AUTH.logout === 'function') {
            await window.MMS_AUTH.logout();
          } else if (window.mmsAPI) {
            await window.mmsAPI.logout();
          } else {
            // Prefer /api/auth/logout
            await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST', credentials: 'include' });
          }
          if (window.mmsAPI) window.mmsAPI.clearAuth && window.mmsAPI.clearAuth();
          
          // Clear auth-bridge stored session
          if (window.MMS_AUTH_BRIDGE) {
            window.MMS_AUTH_BRIDGE.clearAuth();
          }
          
          window.location.href = origin + '/login-platform.html';
        } catch (e) {
          if (window.mmsAPI && window.mmsAPI.showError) window.mmsAPI.showError(e);
        }
      });
    };

    // Load session info
    (async () => {
      try {
        let info = { ok: false };
        
        // First check auth-bridge for stored session
        if (window.MMS_AUTH_BRIDGE) {
          const storedAuth = window.MMS_AUTH_BRIDGE.getStoredAuth();
          if (storedAuth && storedAuth.user) {
            info = { ok: true, data: storedAuth };
          }
        }
        
        // If no stored auth, try the regular auth methods
        if (!info.ok) {
          if (window.MMS_AUTH && typeof window.MMS_AUTH.me === 'function') {
            info = await window.MMS_AUTH.me();
          } else if (window.mmsAPI && window.mmsAPI.me) {
            info = await window.mmsAPI.me();
          } else {
            // Prefer /api/auth/me
            const r = await fetch(`${API_BASE}/api/auth/me`, { credentials: 'include' });
            if (r.ok) {
              info = await r.json();
              // Store successful auth for future use
              if (info.ok && window.MMS_AUTH_BRIDGE && info.data) {
                window.MMS_AUTH_BRIDGE.storeAuth(info.data);
              }
            }
          }
        }
        
        renderSession(info);
      } catch (_) {
        renderSession({ ok: false });
      }
    })();
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderNav);
  else renderNav();
})();
