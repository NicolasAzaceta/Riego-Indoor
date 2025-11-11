const CACHE_NAME = 'riegum-cache-v1';
const urlsToCache = [
  '/',
  '/dashboard/',
  '/add/',
  '/static/css/variables.css',
  '/static/css/styles.css',
  '/static/js/auth.js',
  '/static/js/api.js',
  '/static/js/plants.js',
  '/static/js/google-places.js',
  '/static/assets/img/icono.png',
  '/static/assets/img/RIEGUMICONO.png',
  '/static/assets/animaciones/plantjump.json',
  '/static/assets/animaciones/water.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
  'https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js',
  // Agrega aquí todas las URLs de tus activos estáticos que quieras cachear
  // ¡Importante! Asegúrate de que estas URLs sean accesibles y existan.
];

// Evento 'install': Se dispara cuando el Service Worker se instala por primera vez.
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalando...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Cacheando archivos estáticos');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.error('[Service Worker] Falló el cacheo durante la instalación:', error);
      })
  );
});

// Evento 'activate': Se dispara cuando el Service Worker se activa.
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activando...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Eliminando caché antigua:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Reclama a los clientes para que el nuevo Service Worker tome el control inmediatamente.
  return self.clients.claim();
});

// Evento 'fetch': Se dispara cada vez que el navegador intenta cargar un recurso.
self.addEventListener('fetch', (event) => {
  // Solo cacheamos solicitudes GET
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Si el recurso está en caché, lo devolvemos.
        if (response) {
          console.log('[Service Worker] Sirviendo desde caché:', event.request.url);
          return response;
        }
        // Si no está en caché, intentamos obtenerlo de la red.
        console.log('[Service Worker] Obteniendo de la red:', event.request.url);
        return fetch(event.request)
          .then((networkResponse) => {
            // Si la respuesta de la red es válida, la cacheamos y la devolvemos.
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
            return networkResponse;
          })
          .catch((error) => {
            console.error('[Service Worker] Falló la solicitud de red:', error);
            // Aquí podrías servir una página de "offline" si la solicitud falla.
            // Por ejemplo: return caches.match('/offline.html');
            throw error; // Re-lanza el error para que el navegador lo maneje
          });
      })
  );
});