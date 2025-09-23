// Unified auth + request client for cookie-based sessions
(function(){
  const BASE = (window.MMS_CONFIG && MMS_CONFIG.API_BASE_URL) || '/api';
  const PLATFORM_BASE = (window.MMS_CONFIG && MMS_CONFIG.PLATFORM_BASE_URL) || window.location.origin;
  function redirectToLogin(withReturn=true){
    try{
      const ret = withReturn ? `?return=${encodeURIComponent(window.location.pathname + window.location.search)}` : '';
      const dest = PLATFORM_BASE.replace(/\/$/, '') + '/login' + ret;
      window.location.replace(dest);
    }catch(_){ window.location.href = "/login-enhanced-v2.html"; }
  }
  class AuthClient {
    constructor(){
      this.baseUrl = BASE;
      this._refreshInFlight = null;
    }

    buildUrl(path){
      if (path.startsWith('http')) return path;
      const base = this.baseUrl || '';
      if (!base) return path;
      if (base === '/api' && path.startsWith('/api/')) return path;
      if (base.endsWith('/api') && path.startsWith('/api/')) return base + path.slice(4);
      return base + (path.startsWith('/') ? path : '/' + path);
    }

    headers(extra){
      return Object.assign({ 'Content-Type': 'application/json' }, extra||{});
    }

    async _attemptWithBackoff(url, options, tries=3){
      let last;
      for (let i=0;i<tries;i++){
        try{
          const r = await fetch(url, options);
          if (r.status >= 500 && r.status <= 504) throw new Error(`upstream_${r.status}`);
          return r;
        }catch(e){ last=e; await new Promise(r=>setTimeout(r, 300*Math.pow(2,i))); }
      }
      if (last) throw last;
    }

    async request(path, options={}){
      const url = this.buildUrl(path);
      const opts = Object.assign({ credentials:'include', headers: this.headers(options.headers) }, options);

      let res = await this._attemptWithBackoff(url, opts, 3);
      if (res.status === 401){
        try { await this.silentRefresh(); } catch(_){ redirectToLogin(true); throw new Error('Authentication required'); }
        const retry = await this._attemptWithBackoff(url, opts, 2);
        if (!retry.ok){
          if (retry.status === 401) { redirectToLogin(true); throw new Error('Authentication required'); }
          if (retry.status === 402) throw new Error('Active subscription required');
          if (retry.status === 404) throw new Error('Resource not found');
          throw new Error(`API Error: ${retry.status} ${retry.statusText}`);
        }
        return await retry.json();
      }
      if (!res.ok){
        if (res.status === 402) throw new Error('Active subscription required');
        if (res.status === 404) throw new Error('Resource not found');
        throw new Error(`API Error: ${res.status} ${res.statusText}`);
      }
      return await res.json();
    }

  async silentRefresh(){
      if (this._refreshInFlight) return this._refreshInFlight;
      this._refreshInFlight = (async ()=>{
        try{
          // Prefer /api/auth/refresh first (session router)
          let r = await fetch(this.buildUrl('/api/auth/refresh'), { method:'POST', credentials:'include' });
          if (!r.ok && r.status === 404){
            r = await fetch(this.buildUrl('/auth/refresh'), { method:'POST', credentials:'include' });
          }
          if (!r.ok) { redirectToLogin(true); throw new Error('refresh_failed'); }
          await r.json().catch(()=>({}));
        } finally {
          this._refreshInFlight = null;
        }
      })();
      return this._refreshInFlight;
    }

    async me(){
      try{
        // Prefer /api/auth/me (session router)
  const r = await fetch(this.buildUrl('/api/auth/me'), { credentials:'include' });
        if (r.ok) return await r.json();
      }catch(_){ }
      return { ok:false };
    }

    async logout(){
      try{
        // Prefer /api/auth/logout (session router)
  const r = await fetch(this.buildUrl('/api/auth/logout'), { method:'POST', credentials:'include' });
        if (r.ok) return await r.json();
      }catch(_){ }
      return { success:false };
    }

    clearLegacy(){
      try{
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('token');
        localStorage.removeItem('a3e_api_key');
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('auth_token');
      }catch(_){ }
    }
  }
  window.MMS_AUTH = new AuthClient();
})();
