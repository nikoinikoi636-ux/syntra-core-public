
const CACHE='mindcopy-202508190523';
const ASSETS=['./','./index.html','./styles.css','./script.js','./manifest.json',
'./icons/icon-192.png','./icons/icon-512.png',
'./data/HEART_CORE_v3_1.md','./data/HEART_CORE_FreeLayer_v1.md','./data/SevenDay_Cahetel_Ritual.md'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.map(k=>k!==CACHE?caches.delete(k):null)))));
self.addEventListener('fetch',e=>e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request))));
