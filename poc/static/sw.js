// Service Worker — İstanbul Türkçesi Diksiyon PWA
// Strateji:
//   /static/*       → cache-first (uygulama kabuğu, offline çalışır)
//   /reference/*    → cache-first (referans sesleri telefonda saklansın)
//   /exercises      → network-first (alıştırma havuzu güncel kalsın)
//   /assess (POST)  → her zaman ağdan, asla cache (mikrofon kaydı analizi)

const CACHE_NAME = 'diksiyon-v5-clean';

const APP_SHELL = [
  '/static/',
  '/static/index.html',
  '/static/manifest.webmanifest',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon-maskable.png',
  '/static/icons/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // POST /assess → her zaman fresh, cache yok
  if (event.request.method !== 'GET') return;

  // /exercises → network-first (alıştırmalar güncel kalsın)
  if (url.pathname.endsWith('/exercises')) {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
          return res;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // /reference/ ve /static/ → cache-first
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/reference/')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
          }
          return res;
        });
      })
    );
    return;
  }

  // Diğer her şey: default behavior
});
