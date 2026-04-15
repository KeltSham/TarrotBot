// =============================================
// SERVICE WORKER — Tarot Universe
// Стратегии кэширования:
//   • Статика (HTML/CSS/JS)    → network-first, fallback на кэш
//   • Изображения              → cache-first, runtime-cache при первом запросе
//   • Google Fonts             → cache-first (шрифты стабильны)
//   • API /api/*               → network-only (динамические данные)
//   • Telegram SDK             → network-only (всегда свежий)
// =============================================

const CACHE_VER    = 'v9';
const STATIC_CACHE = `tarot-static-${CACHE_VER}`;
const IMAGE_CACHE  = `tarot-images-${CACHE_VER}`;
const FONT_CACHE   = `tarot-fonts-v1`;   // версия шрифтов меняется редко

// ── Критические файлы: кэшируем при установке ──
const STATIC_PRECACHE = [
  './',
  './index.html',
  './style.css',
  './script.js',
  './manifest.json',
];

// ── UI-изображения: нужны сразу ──
// bg_mystic оставлен в PNG (WebP вышел на 3% больше оригинала)
const UI_IMAGES = [
  './images/tarot_back_1774882589907.webp',      // -14% vs PNG
  './images/tarot_front_blank_1774882898806.webp', // -13% vs PNG
  './images/bg_mystic_1774882343565.png',
];

// ── Все 78 карт Таро ──
// Оригинальные JPEG уже хорошо сжаты (~25-40 KB); WebP не даёт выигрыша.
// Рубашка и бланк конвертированы в WebP (−13..14%), фон оставлен PNG (+3% при WebP).
const CARD_IMAGES = [
  // Старшие Арканы (0–21)
  'ar00','ar01','ar02','ar03','ar04','ar05','ar06','ar07','ar08','ar09',
  'ar10','ar11','ar12','ar13','ar14','ar15','ar16','ar17','ar18','ar19',
  'ar20','ar21',
  // Жезлы (14 карт)
  'waac','wa02','wa03','wa04','wa05','wa06','wa07','wa08','wa09','wa10',
  'wapa','wakn','waqu','waki',
  // Кубки (14 карт)
  'cuac','cu02','cu03','cu04','cu05','cu06','cu07','cu08','cu09','cu10',
  'cupa','cukn','cuqu','cuki',
  // Мечи (14 карт)
  'swac','sw02','sw03','sw04','sw05','sw06','sw07','sw08','sw09','sw10',
  'swpa','swkn','swqu','swki',
  // Пентакли (14 карт)
  'peac','pe02','pe03','pe04','pe05','pe06','pe07','pe08','pe09','pe10',
  'pepa','pekn','pequ','peki',
].map(f => `./images/${f}.jpg`);

const ALL_PRECACHE = [...STATIC_PRECACHE, ...UI_IMAGES, ...CARD_IMAGES];

// ─────────────────────────────────────────────
// INSTALL: прекэшируем всё
// ─────────────────────────────────────────────
self.addEventListener('install', event => {
  console.log('[SW] Installing, cache version:', CACHE_VER);
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache =>
        // addAll падает если хоть один ресурс недоступен —
        // используем allSettled, чтобы SW установился даже при частичных 404
        Promise.allSettled(
          ALL_PRECACHE.map(url =>
            cache.add(url).catch(err =>
              console.warn('[SW] Precache miss:', url, err.message)
            )
          )
        )
      )
      .then(() => {
        console.log('[SW] Precache complete, skipping waiting');
        return self.skipWaiting();
      })
  );
});

// ─────────────────────────────────────────────
// ACTIVATE: удаляем старые кэши
// ─────────────────────────────────────────────
self.addEventListener('activate', event => {
  const KEEP = new Set([STATIC_CACHE, IMAGE_CACHE, FONT_CACHE]);
  event.waitUntil(
    caches.keys()
      .then(keys =>
        Promise.all(
          keys
            .filter(k => !KEEP.has(k))
            .map(k => {
              console.log('[SW] Deleting old cache:', k);
              return caches.delete(k);
            })
        )
      )
      .then(() => {
        console.log('[SW] Activated, claiming clients');
        return self.clients.claim();
      })
  );
});

// ─────────────────────────────────────────────
// FETCH: маршрутизация запросов
// ─────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // 1. Только GET
  if (req.method !== 'GET') return;

  // 2. API-запросы к боту → network-only (динамика, не кэшировать)
  if (url.pathname.includes('/api/')) return;

  // 3. Telegram Web App SDK → network-only
  if (url.hostname === 'telegram.org') return;

  // 4. Google Fonts → cache-first (шрифты не меняются, CDN надёжен)
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(fontFirst(req));
    return;
  }

  // 5. Изображения → cache-first + runtime-cache (WebP/PNG/JPG/SVG)
  if (/\.(webp|png|jpg|jpeg|gif|svg|ico)$/i.test(url.pathname)) {
    event.respondWith(imageFirst(req));
    return;
  }

  // 6. Всё остальное (HTML, CSS, JS) → network-first, fallback на кэш
  event.respondWith(networkFirst(req));
});

// ─────────────────────────────────────────────
// Вспомогательные стратегии
// ─────────────────────────────────────────────

/** Cache-first для шрифтов */
function fontFirst(req) {
  return caches.open(FONT_CACHE).then(cache =>
    cache.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(resp => {
        if (resp.ok) cache.put(req, resp.clone());
        return resp;
      });
    })
  );
}

/** Cache-first для изображений, runtime-cache при первом запросе */
function imageFirst(req) {
  return caches.match(req).then(cached => {
    if (cached) return cached;

    // Нет в кэше — идём в сеть и сохраняем
    return caches.open(IMAGE_CACHE).then(cache =>
      fetch(req)
        .then(resp => {
          if (resp.ok) cache.put(req, resp.clone());
          return resp;
        })
        .catch(() => {
          // Сеть недоступна и кэша нет — вернём пустой 404
          console.warn('[SW] Image not cached and offline:', req.url);
          return new Response('', { status: 404, statusText: 'Offline' });
        })
    );
  });
}

/** Network-first для HTML/CSS/JS — актуальность важнее скорости */
function networkFirst(req) {
  return fetch(req)
    .then(resp => {
      // Обновляем кэш свежей версией
      if (resp.ok) {
        caches.open(STATIC_CACHE).then(c => c.put(req, resp.clone()));
      }
      return resp;
    })
    .catch(() => {
      // Сеть недоступна → отдаём из кэша
      return caches.match(req).then(cached => {
        if (cached) return cached;
        // Последний резерв: cached index.html для офлайн-навигации
        return caches.match('./index.html');
      });
    });
}
