// Unified auth + request client for cookie-based sessions
(function(){
  const BASE = (window.MMS_CONFIG && MMS_CONFIG.API_BASE_URL) || 'https://api.mapmystandards.ai';
  class AuthClient {
    constructor(){
      this.baseUrl = BASE;
      this._refreshInFlight = null;
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
      const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`;
      const opts = Object.assign({ credentials:'include', headers: this.headers(options.headers) }, options);

      let res = await this._attemptWithBackoff(url, opts, 3);
      if (res.status === 401){
        await this.silentRefresh();
        const retry = await this._attemptWithBackoff(url, opts, 2);
        if (!retry.ok){
          if (retry.status === 401) throw new Error('Authentication required');
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
          let r = await fetch(`${this.baseUrl}/api/auth/refresh`, { method:'POST', credentials:'include' });
          if (!r.ok && r.status === 404){
            r = await fetch(`${this.baseUrl}/auth/refresh`, { method:'POST', credentials:'include' });
          }
          if (!r.ok) throw new Error('refresh_failed');
          await r.json().catch(()=>({}));
        } finally {
          this._refreshInFlight = null;
        }
      })();
      return this._refreshInFlight;
    }

    async me(){
      try{
        const r = await fetch(`${this.baseUrl}/api/auth/me`, { credentials:'include' });
        if (r.ok) return await r.json();
      }catch(_){ }
      return { ok:false };
    }

    async logout(){
      try{
        const r = await fetch(`${this.baseUrl}/api/auth/logout`, { method:'POST', credentials:'include' });
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
