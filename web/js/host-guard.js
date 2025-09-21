(() => {
  const PLATFORM_HOST = 'platform.mapmystandards.ai';
  const isPlatform = window.location.hostname === PLATFORM_HOST;
  const isMarketing = window.location.hostname === 'mapmystandards.ai' || window.location.hostname === 'www.mapmystandards.ai';
  const isVercel = window.location.hostname.endsWith('.vercel.app');

  if (!(isMarketing || isVercel)) return;

  const APP_PATHS = new Set([
    '/login',
    '/login-platform',
    '/login-platform.html',
    '/subscribe',
    '/ai-dashboard',
    '/org-chart',
    '/reports',
    '/standards',
    '/evidence-mapping',
  '/upload-modern',
  ]);

  const toPlatform = (path) => `https://${PLATFORM_HOST}${path}`;
  const CANONICAL = {
    '/login': '/login.html',
    '/login-platform': '/login.html',
    '/login-platform.html': '/login.html',
  };

  const rewriteLinks = () => {
    const anchors = document.querySelectorAll('a[href]');
    anchors.forEach((a) => {
      try {
        const href = a.getAttribute('href') || '';
        if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
        // Only rewrite root-relative app paths
        if (href.startsWith('/')) {
          const pathOnly = href.split('?')[0].split('#')[0];
          if (APP_PATHS.has(pathOnly)) {
            const canonicalPath = CANONICAL[pathOnly] || pathOnly;
            const suffix = href.slice(pathOnly.length);
            const newHref = canonicalPath + suffix;
            a.setAttribute('href', toPlatform(newHref));
          }
        }
      } catch (_) {}
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', rewriteLinks);
  } else {
    rewriteLinks();
  }
})();
// Redirect any vercel.app access to the custom domain
(function(){
  try {
    var host = window.location.hostname || '';
    if (host.endsWith('.vercel.app')) {
      var target = 'https://platform.mapmystandards.ai' + window.location.pathname + window.location.search + window.location.hash;
      window.location.replace(target);
    }
  } catch (_) {}
})();
