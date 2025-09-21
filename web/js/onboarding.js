(function(){
  const STYLE_ID = 'mms-onboarding-style';
  const MODAL_ID = 'mmsOnboardingModal';

  function ensureStyles(){
    if (document.getElementById(STYLE_ID)) return;
    const s = document.createElement('style');
    s.id = STYLE_ID;
    s.textContent = `
      .mms-modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;z-index:1000}
      .mms-modal{background:#fff;border-radius:12px;box-shadow:0 20px 40px rgba(0,0,0,.2);width:min(680px,92vw);max-height:90vh;overflow:auto}
      .mms-modal header{padding:16px 20px;border-bottom:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center}
      .mms-modal h2{margin:0;font-size:18px}
      .mms-modal .mms-body{padding:16px 20px;display:grid;gap:12px}
      .mms-field{display:grid;gap:6px}
      .mms-field label{font-size:13px;color:#374151}
      .mms-field input,.mms-field select{padding:10px 12px;border:1px solid #e5e7eb;border-radius:8px;font-size:14px}
      .mms-modal footer{padding:14px 20px;border-top:1px solid #e5e7eb;display:flex;gap:8px;justify-content:flex-end}
      .mms-btn{padding:10px 14px;border-radius:8px;border:1px solid #e5e7eb;background:#f9fafb;cursor:pointer}
      .mms-btn-primary{background:#1e40af;border-color:#1e40af;color:#fff}
      .mms-helper{font-size:12px;color:#6b7280}
      @media (prefers-reduced-motion: no-preference){.mms-modal{animation:mmsFade .12s ease-out}}
      @keyframes mmsFade{from{opacity:.8;transform:translateY(2px)}to{opacity:1;transform:translateY(0)}}
    `;
    document.head.appendChild(s);
  }

  function getAuthToken(){
    try{
      return localStorage.getItem('a3e_api_key') || sessionStorage.getItem('a3e_api_key') || localStorage.getItem('access_token') || localStorage.getItem('jwt_token') || '';
    }catch(_){ return ''; }
  }

  function apiBase(){
    const raw = (window.MMS_CONFIG && window.MMS_CONFIG.API_BASE_URL) || '';
    if (!raw) return '';
    return raw.replace(/\/$/, '');
  }

  async function loadSettings(){
    const t = getAuthToken();
    if (t){
      try{
        const res = await fetch(apiBase() + '/api/user/intelligence-simple/settings', { headers: { 'Authorization': `Bearer ${t}` }, credentials: 'include' });
        if (res.ok){
          const j = await res.json();
          return (j && j.organization !== undefined) ? j : (j && j.settings) || j || {};
        }
      }catch(_){ /* fall through */ }
    }
    // Cookie-based fetch (most production flows use httpOnly session cookies)
    try{
      const base = apiBase();
      const res = await fetch((base ? base : '') + '/api/user/intelligence-simple/settings', { credentials: 'include' });
      if (res.ok){
        const j = await res.json();
        return (j && j.organization !== undefined) ? j : (j && j.settings) || j || {};
      }
    }catch(_){ /* fall back to local */ }
    try{ return JSON.parse(localStorage.getItem('mms:onboarding')||'{}') || {}; }catch(_){ return {}; }
  }

  async function saveSettings(values){
    const t = getAuthToken();
    let saved = values;
    if (t){
      try{
        const res = await fetch(apiBase() + '/api/user/intelligence-simple/settings', { method:'POST', headers:{ 'Authorization': `Bearer ${t}`, 'Content-Type':'application/json' }, body: JSON.stringify(values), credentials: 'include' });
        if (res.ok){ const j = await res.json(); saved = (j && j.settings) || values; }
      }catch(_){ /* fall back to local only */ }
    }
    try{ localStorage.setItem('mms:onboarding', JSON.stringify(saved)); }catch(_){}
    window.dispatchEvent(new CustomEvent('mms:onboarding-updated', { detail: saved }));
    return saved;
  }

  function shouldPrompt(settings){
    try { if (localStorage.getItem('mms:onboarding-complete') === '1') return false; } catch(_) {}
    if (!settings) return true;
    const org = settings.organization || settings.institution_name || '';
    const accr = settings.primary_accreditor || '';
    return !(org && accr);
  }

  function closeModal(){
    const el = document.getElementById(MODAL_ID);
    if (el && el.parentNode) el.parentNode.remove();
    // restore focus
    if (closeModal._lastFocus && closeModal._lastFocus.focus) { try{ closeModal._lastFocus.focus(); }catch(_){} }
  }

  function openWizard(prefill){
    ensureStyles();
    closeModal();
    closeModal._lastFocus = document.activeElement;
    const backdrop = document.createElement('div');
    backdrop.className = 'mms-modal-backdrop';
    backdrop.innerHTML = `
      <div class="mms-modal" id="${MODAL_ID}" role="dialog" aria-modal="true" aria-labelledby="mmsObTitle">
        <header>
          <h2 id="mmsObTitle">Welcome! Let’s set up your account</h2>
          <button class="mms-btn" aria-label="Close" id="mmsObClose">✕</button>
        </header>
        <div class="mms-body">
          <div class="mms-field">
            <label for="mmsOrg">Institution name</label>
            <input id="mmsOrg" type="text" autocomplete="organization" />
          </div>
          <div class="mms-field">
            <label for="mmsState">State/Province</label>
            <input id="mmsState" type="text" autocomplete="address-level1" />
          </div>
          <div class="mms-field">
            <label for="mmsRegion">Accreditation region</label>
            <select id="mmsRegion">
              <option value="">Select region</option>
              <option>SACSCOC</option>
              <option>HLC</option>
              <option>MSCHE</option>
              <option>NECHE</option>
              <option>NWCCU</option>
              <option>WSCUC</option>
            </select>
          </div>
          <div class="mms-field">
            <label for="mmsAccr">Primary accreditor</label>
            <select id="mmsAccr">
              <option value="">Choose accreditor</option>
              <option value="SACSCOC">SACSCOC</option>
              <option value="HLC">HLC</option>
              <option value="MSCHE">MSCHE</option>
              <option value="NECHE">NECHE</option>
              <option value="NWCCU">NWCCU</option>
              <option value="WSCUC">WSCUC</option>
            </select>
          </div>
          <div class="mms-field">
            <label for="mmsEnroll">Approximate enrollment</label>
            <input id="mmsEnroll" type="number" min="0" step="1" inputmode="numeric" />
            <div class="mms-helper">Helps personalize your recommendations.</div>
          </div>
        </div>
        <footer>
          <button class="mms-btn" id="mmsObCancel">Cancel</button>
          <button class="mms-btn mms-btn-primary" id="mmsObSave">Save</button>
        </footer>
      </div>
    `;
    document.body.appendChild(backdrop);
    const modal = document.getElementById(MODAL_ID);
    const org = modal.querySelector('#mmsOrg');
    const state = modal.querySelector('#mmsState');
    const region = modal.querySelector('#mmsRegion');
    const accr = modal.querySelector('#mmsAccr');
    const enroll = modal.querySelector('#mmsEnroll');
    const saveBtn = modal.querySelector('#mmsObSave');
    const cancelBtn = modal.querySelector('#mmsObCancel');
    const closeBtn = modal.querySelector('#mmsObClose');

    // Prefill
    const s = prefill || {};
    org.value = s.organization || s.institution_name || '';
    state.value = s.state || '';
    region.value = s.region || s.accreditation_region || '';
    accr.value = s.primary_accreditor || '';
    enroll.value = s.institution_size || s.enrollment || '';

    // Basic focus management
    setTimeout(()=>{ try{ org.focus(); }catch(_){ } }, 0);
    backdrop.addEventListener('click', (e)=>{ if (e.target === backdrop) closeModal(); });
    cancelBtn.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('keydown', (e)=>{ if (e.key === 'Escape') closeModal(); });

    saveBtn.addEventListener('click', async () => {
      const values = {
        organization: org.value.trim(),
        state: state.value.trim(),
        accreditation_region: region.value.trim(),
        primary_accreditor: accr.value.trim(),
        institution_size: enroll.value.trim()
      };
      await saveSettings(values);
      closeModal();
    });
  }

  function isOnboardingRoute(){
    try{
      const p = String(location.pathname || '').replace(/\/$/, '');
      return p === '/onboarding' || p === '/onboarding.html';
    }catch(_){ return false; }
  }

  async function maybePrompt(){
    if (isOnboardingRoute()) return; // don't prompt while user is on the onboarding page
    try{
      const s = await loadSettings();
      if (shouldPrompt(s)) openWizard(s);
    }catch(_){ /* ignore */ }
  }

  window.MMS_ONBOARDING = { loadSettings, saveSettings, shouldPrompt, openWizard, maybePrompt };
})();
