/* ===== 媒体长效缓存 =====
   GitHub Pages 对一切资源只给 cache-control: max-age=600（10 分钟）。
   那个 8.6 MB 的莲花视频因此每 10 分钟就被重下一次 —— 这是首页"卡"的根因。
   这个 Service Worker 用 Cache API 把媒体长期留在浏览器里：首次下载，之后读本地。
   范围严格限定在下面的名单内：HTML / JS / CSS 一律不接管，避免整站被冻结在旧版本。 */
const CACHE = 'gs-media-v3';
const MEDIA = [
  '/geosandbox/assets/flower-bloom.mp4',
  '/geosandbox/assets/flower-bloom-poster.jpg',
  '/geosandbox/assets/memorial-bg.mp4',
  '/geosandbox/assets/bgm-audio.mp4',
  '/geosandbox/assets/hero-base.webp',
  '/geosandbox/assets/hero-reveal.webp',
  '/geosandbox/assets/memorial-poster.jpg',
  '/geosandbox/assets/NotoTitleVF.woff2'
];

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch (_) { return; }
  if (url.origin !== self.location.origin) return;
  if (MEDIA.indexOf(url.pathname) === -1) return;   /* 名单外一律走网络 */

  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    /* 缓存键用带 ?v= 的完整 URL —— 换版本号即自动失效，不会卡住旧文件 */
    const hit = await cache.match(req);
    if (hit) return hit;
    try {
      const res = await fetch(req);
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    } catch (err) {
      const fb = await cache.match(req);
      if (fb) return fb;
      throw err;
    }
  })());
});
