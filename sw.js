const C='ld-v31',F=['./','index.html','editor.html','editor.js','app.js','core.js','vendor/cv.js','vendor/aruco.js','targets.json','drills.json','manifest.webmanifest','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>c.addAll(F))));
self.addEventListener('fetch',e=>e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r;}).catch(()=>caches.match(e.request))));
