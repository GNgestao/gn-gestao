const CACHE_NAME = 'gn-gestao-20260628';
const PRECACHE_URLS = ['/gn-gestao/index.html', '/gn-gestao/manifest.json'];
const N8N_ORIGIN = 'https://n8n.srv1610251.hstgr.cloud';

self.addEventListener('install', function(event){
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache){
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(event){
  event.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.filter(function(k){ return k !== CACHE_NAME; }).map(function(k){ return caches.delete(k); }));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function(event){
  const req = event.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);

  // Network-first para chamadas ao n8n
  if(url.origin === N8N_ORIGIN){
    event.respondWith(
      fetch(req).catch(function(){ return caches.match(req); })
    );
    return;
  }

  // Navegação (HTML) — cache-first com fallback offline para index.html
  if(req.mode === 'navigate'){
    event.respondWith(
      caches.match(req).then(function(cached){
        return cached || fetch(req).catch(function(){
          return caches.match('/gn-gestao/index.html');
        });
      })
    );
    return;
  }

  // Demais assets estáticos — cache-first
  event.respondWith(
    caches.match(req).then(function(cached){
      if(cached) return cached;
      return fetch(req).then(function(res){
        if(res && res.status === 200){
          const resClone = res.clone();
          caches.open(CACHE_NAME).then(function(cache){ cache.put(req, resClone); });
        }
        return res;
      }).catch(function(){
        return caches.match('/gn-gestao/index.html');
      });
    })
  );
});
