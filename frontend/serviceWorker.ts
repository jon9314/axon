/// <reference lib="webworker" />
// frontend/serviceWorker.ts
const CACHE_NAME = 'axon-cache-v1';
const OFFLINE_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/vite.svg',
];

const sw = self as unknown as ServiceWorkerGlobalScope;

sw.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(OFFLINE_URLS))
      .then(() => sw.skipWaiting())
  );
});

sw.addEventListener('activate', (event: ExtendableEvent) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.map((key) => (key !== CACHE_NAME ? caches.delete(key) : Promise.resolve())))
      )
      .then(() => sw.clients.claim())
  );
});

sw.addEventListener('fetch', (event: FetchEvent) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
