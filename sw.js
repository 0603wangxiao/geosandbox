/* ===== 已停用 =====
   原用途：绕过 GitHub Pages 的 cache-control: max-age=600，把媒体长期留在浏览器。
   停用原因：作者真机实测视频 readyState 停在 0（HAVE_NOTHING），一帧都没解码。
   视频元素一律走 HTTP Range 请求，而旧版实现会把整份 200 响应回给 Range 请求 ——
   部分移动端浏览器 / WebView 遇到这种情况会直接卡住。本地复现不出来（SW 未接管），
   无法证实也无法排除，故按「撤掉未验证的新机制、恢复已知可用基线」处理。

   本文件保留（不删）是为了让仍装着旧版 SW 的浏览器能拉到这一版，
   然后在 activate 里把自己注销并把媒体缓存放掉 —— 访客无需手动清缓存。 */
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(
        keys.filter((k) => k.indexOf('gs-media') === 0).map((k) => caches.delete(k))
      );
    } catch (_) {}
    try { await self.registration.unregister(); } catch (_) {}
  })());
});
