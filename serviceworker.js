var staticCacheName = 'django-pwa-v' + new Date().getTime();
var CDN_CACHE_NAME = 'cdn-cache-v' + new Date().getTime(); // Fixed spelling 'cdn-ache-v'

var dirToCache = ['/', '/dashboard/', '/self-register/', '/static/app/css/dashboard.css', '/static/app/css/index.css', '/static/app/css/style.css', '/static/app/img/asramaku_logo.png', '/static/app/js/dashboard.js', '/static/app/js/index.js', '/static/app/js/self_register.js'];

// ✅ FIXED: Added leading slashes to all paths so Django resolves them properly
const filesToCache = [
    "/manifest.json", 
    "/static/app/css/dashboard.css", 
    "/static/app/css/index.css",
    "/static/app/css/style.css", 
    "/static/app/img/asramaku_logo.png", 
    "/static/app/js/dashboard.js", 
    "/static/app/js/index.js", 
    "/static/app/js/self_register.js",  
    ...dirToCache
];

const CDN_URLS = [];

self.addEventListener('install', event => {
    event.waitUntil(
        Promise.all([
            caches.open(staticCacheName).then(cache => {
                return cache.addAll(filesToCache);
            }),

            caches.open(CDN_CACHE_NAME).then(cache => {
                return cache.addAll(CDN_URLS);
            })
        ])
    )
})

self.addEventListener('activate', event => {
    const cacheWhitelist = [staticCacheName, CDN_CACHE_NAME];

    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (!cacheWhitelist.includes(cacheName)) {
                        return caches.delete(cacheName);
                    }
                })
            )
        })
    )
})

self.addEventListener('fetch', event => {
    const url = event.request.url;

    if (url.protocol === 'http' || url.protocol === 'https') {
        if (CDN_URLS.some(cdnUrl => url.startsWith(cdnUrl))) {
            event.respondWith(
                (async () => {
                    try {
                        const networkResponse = await fetch(event.request);

                        if (networkResponse && networkResponse.status === 200) {
                            const cache = await caches.open(CDN_CACHE_NAME);
                            cache.put(event.request, networkResponse.clone());

                            return networkResponse;
                        }
                    } catch (error) {
                        const cacheResponse = await caches.match(event.request);

                        if (cacheResponse) {
                            return cacheResponse;
                        }
                        
                        // ✅ FIXED: Removed non-existent /offline.html fallback reference
                        return new Response("Offline connection error."); 
                    }
                })()
            )

            return;
        }

        event.respondWith(
            (async () => {
                try {
                    const networkResponse = await fetch(event.request);

                    if (networkResponse && networkResponse.status === 200) {
                        const cache = await caches.open(staticCacheName);

                        cache.put(event.request, networkResponse.clone());

                        return networkResponse;
                    }

                    return networkResponse;
                } catch (error) {
                    const cachedResponse = await caches.match(event.request);

                    if (cachedResponse) {
                        return cachedResponse;
                    }

                    // ✅ FIXED: Removed non-existent /offline.html fallback reference
                    return new Response("Offline connection error.");
                }
            })()
        )
    }
})