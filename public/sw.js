// Killer SW to unregister any previously registered root-scoped service worker
// Version: 2025-09-20

self.addEventListener('install', () => {
  // Ensure this SW activates immediately
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    try {
      // Unregister this SW (and any prior root-scoped SW)
      await self.registration.unregister();
      // Nudge controlled clients to reload so they detach from SW control
      const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      for (const client of clients) {
        try { client.navigate(client.url); } catch (_) {}
      }
    } catch (_) {}
  })());
});

// No fetch handler — allow browser/network default
