/**
 * Service Worker for Personal AI Career Co-Pilot PWA
 * Handles caching, offline functionality, and background sync
 */

const CACHE_NAME = 'career-copilot-v1.0.0';
const STATIC_CACHE_NAME = 'career-copilot-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'career-copilot-dynamic-v1.0.0';

// Static assets to cache immediately
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
    '/css/style.css',
    '/css/themes.css',
    '/js/app.js',
    '/js/api.js',
    '/js/pdf-generator.js',
    '/js/utils.js',
    '/icons/icon-192x192.png',
    '/icons/icon-512x512.png',
    '/icons/apple-touch-icon.png',
    '/favicon.ico',
    // External dependencies
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'
];

// Dynamic assets to cache when accessed
const DYNAMIC_CACHE_URLS = [
    '/api/',
    'https://us-central1-personal-ai-career-copilot.cloudfunctions.net/'
];

// Assets that should always be fetched from network
const NETWORK_ONLY_URLS = [
    '/generate_application_http',
    '/job_scout',
    '/health_check'
];

/**
 * Service Worker Installation
 * Cache static assets during installation
 */
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Service Worker: Static assets cached successfully');
                return self.skipWaiting(); // Force activation of new service worker
            })
            .catch((error) => {
                console.error('Service Worker: Failed to cache static assets', error);
            })
    );
});

/**
 * Service Worker Activation
 * Clean up old caches and claim clients
 */
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Delete old caches that don't match current version
                    if (cacheName !== STATIC_CACHE_NAME && 
                        cacheName !== DYNAMIC_CACHE_NAME &&
                        cacheName.startsWith('career-copilot-')) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Activated and claiming clients');
            return self.clients.claim(); // Take control of all pages
        })
    );
});

/**
 * Fetch Event Handler
 * Implement caching strategies for different types of requests
 */
self.addEventListener('fetch', (event) => {
    const requestURL = new URL(event.request.url);
    
    // Handle different request types with appropriate strategies
    if (isStaticAsset(event.request)) {
        event.respondWith(cacheFirstStrategy(event.request));
    } else if (isAPIRequest(event.request)) {
        event.respondWith(networkFirstStrategy(event.request));
    } else if (isDocumentRequest(event.request)) {
        event.respondWith(staleWhileRevalidateStrategy(event.request));
    } else {
        event.respondWith(networkFirstStrategy(event.request));
    }
});

/**
 * Cache First Strategy
 * Serve from cache first, fallback to network
 * Best for static assets that don't change often
 */
async function cacheFirstStrategy(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.status === 200) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Cache First Strategy failed:', error);
        
        // Return offline fallback if available
        if (request.destination === 'document') {
            return caches.match('/offline.html') || new Response('Offline');
        }
        
        throw error;
    }
}

/**
 * Network First Strategy
 * Try network first, fallback to cache
 * Best for API requests and dynamic content
 */
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful API responses for offline access
        if (networkResponse.status === 200 && isAPIRequest(request)) {
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network request failed, trying cache:', error);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline response for API requests
        if (isAPIRequest(request)) {
            return new Response(JSON.stringify({
                success: false,
                error: 'Offline - please check your internet connection',
                offline: true
            }), {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        throw error;
    }
}

/**
 * Stale While Revalidate Strategy
 * Serve from cache immediately, update cache in background
 * Best for documents and pages that need to be fast but can be updated
 */
async function staleWhileRevalidateStrategy(request) {
    const cachedResponse = await caches.match(request);
    
    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.status === 200) {
            const cache = caches.open(DYNAMIC_CACHE_NAME);
            cache.then(cache => cache.put(request, networkResponse.clone()));
        }
        return networkResponse;
    }).catch(() => {
        // Ignore network errors in stale-while-revalidate
        return null;
    });
    
    // Return cached version immediately if available
    if (cachedResponse) {
        // Still fetch from network to update cache
        fetchPromise;
        return cachedResponse;
    }
    
    // Wait for network if no cached version
    return fetchPromise || new Response('Offline');
}

/**
 * Check if request is for a static asset
 */
function isStaticAsset(request) {
    const url = new URL(request.url);
    
    return url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/) ||
           STATIC_ASSETS.includes(url.pathname) ||
           url.hostname === 'fonts.googleapis.com' ||
           url.hostname === 'fonts.gstatic.com' ||
           url.hostname === 'cdnjs.cloudflare.com';
}

/**
 * Check if request is for an API endpoint
 */
function isAPIRequest(request) {
    const url = new URL(request.url);
    
    return url.pathname.startsWith('/api/') ||
           url.hostname.includes('cloudfunctions.net') ||
           DYNAMIC_CACHE_URLS.some(pattern => url.href.includes(pattern));
}

/**
 * Check if request is for a document/HTML page
 */
function isDocumentRequest(request) {
    return request.destination === 'document' ||
           request.headers.get('accept').includes('text/html');
}

/**
 * Background Sync for offline document generation
 * Queue document generation requests when offline
 */
self.addEventListener('sync', (event) => {
    console.log('Service Worker: Background sync triggered', event.tag);
    
    if (event.tag === 'document-generation') {
        event.waitUntil(syncDocumentGeneration());
    }
});

/**
 * Handle background sync for document generation
 */
async function syncDocumentGeneration() {
    try {
        // Get queued requests from IndexedDB or local storage
        const queuedRequests = await getQueuedRequests();
        
        for (const request of queuedRequests) {
            try {
                // Attempt to process the queued request
                const response = await fetch(request.url, {
                    method: request.method,
                    headers: request.headers,
                    body: request.body
                });
                
                if (response.ok) {
                    // Remove from queue on success
                    await removeQueuedRequest(request.id);
                    
                    // Notify user of successful sync
                    self.registration.showNotification('Document Generated', {
                        body: 'Your career document has been generated successfully!',
                        icon: '/icons/icon-192x192.png',
                        badge: '/icons/badge-72x72.png',
                        tag: 'document-generated',
                        requireInteraction: true,
                        actions: [
                            {
                                action: 'view',
                                title: 'View Document'
                            }
                        ]
                    });
                }
            } catch (error) {
                console.error('Failed to sync document generation:', error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

/**
 * Handle notification clicks
 */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'view') {
        // Open the app and navigate to results
        event.waitUntil(
            clients.openWindow('/?view=results')
        );
    } else {
        // Default action - just open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

/**
 * Handle push notifications (future feature)
 */
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    const data = event.data.json();
    
    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: '/icons/icon-192x192.png',
            badge: '/icons/badge-72x72.png',
            tag: data.tag || 'general',
            data: data.data || {}
        })
    );
});

/**
 * Utility functions for managing queued requests
 * These would integrate with IndexedDB for persistent storage
 */
async function getQueuedRequests() {
    // Placeholder - would implement IndexedDB integration
    return [];
}

async function removeQueuedRequest(requestId) {
    // Placeholder - would implement IndexedDB integration
    console.log('Removing queued request:', requestId);
}

/**
 * Handle messages from the main thread
 */
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});
