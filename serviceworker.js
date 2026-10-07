/* ASRAMAku service worker
 *
 * What it does:
 *   - Static files (CSS, JS, images, fonts and the CDN libraries) are kept in a cache,
 *     served from it instantly, and refreshed in the background.
 *   - Pages are always fetched live from the server. If the device is offline,
 *     the offline page is shown instead.
 *   - Logins, forms, API calls and uploaded photos are never cached.
 *
 * Change VERSION whenever you change CSS/JS/images, so every device drops its old copies.
 */
const VERSION = 'v1';
const STATIC_CACHE = 'asramaku-static-' + VERSION;
const OFFLINE_URL = '/offline/';

const PRECACHE_URLS = [
    OFFLINE_URL,
    '/static/app/css/style.css',
    '/static/app/js/base.js',
    '/static/app/img/asramaku_logo_wide.png',
    '/static/app/img/icons/icon-192.png',
];

const CDN_HOSTS = ['cdnjs.cloudflare.com', 'fonts.googleapis.com', 'fonts.gstatic.com'];

// Install: store the offline page and core files. One missing file must not break the install.
self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(function (cache) {
                return Promise.all(PRECACHE_URLS.map(function (url) {
                    return cache.add(new Request(url, { cache: 'reload' })).catch(function (error) {
                        console.warn('[sw] could not precache', url, error);
                    });
                }));
            })
            .then(function () { return self.skipWaiting(); })
    );
});

// Activate: remove caches left by older versions, then take control of open pages.
self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys()
            .then(function (keys) {
                return Promise.all(keys
                    .filter(function (key) { return key !== STATIC_CACHE; })
                    .map(function (key) { return caches.delete(key); }));
            })
            .then(function () { return self.clients.claim(); })
    );
});

function isCacheable(response) {
    return response && (response.ok || response.type === 'opaque');
}

// Answer from the cache when possible, and refresh the cached copy in the background.
function staleWhileRevalidate(event) {
    const request = event.request;
    return caches.open(STATIC_CACHE).then(function (cache) {
        return cache.match(request).then(function (cached) {
            const refresh = fetch(request).then(function (response) {
                if (isCacheable(response)) cache.put(request, response.clone());
                return response;
            });

            if (cached) {
                event.waitUntil(refresh.catch(function () {}));
                return cached;
            }
            return refresh;
        });
    });
}

self.addEventListener('fetch', function (event) {
    const request = event.request;

    // Never touch form submissions, logins or anything else that changes data.
    if (request.method !== 'GET') return;

    const url = new URL(request.url);

    if (CDN_HOSTS.indexOf(url.hostname) !== -1) {
        event.respondWith(staleWhileRevalidate(event));
        return;
    }

    if (url.origin !== self.location.origin) return;

    if (url.pathname.indexOf('/static/') === 0) {
        event.respondWith(staleWhileRevalidate(event));
        return;
    }

    // Pages: live from the server, offline page as the fallback. Nothing is stored.
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(function () {
                return caches.match(OFFLINE_URL).then(function (page) {
                    return page || new Response('You are offline.', {
                        status: 503,
                        headers: { 'Content-Type': 'text/plain' },
                    });
                });
            })
        );
    }

    // Everything else (API calls, live updates, uploaded photos) goes straight to the network.
});
