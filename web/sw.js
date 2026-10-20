// 发布新版本时改这里的 VERSION，activate 阶段会自动清掉旧缓存。
const VERSION = "v3";
const CACHE = `2048-mobile-${VERSION}`;
const PRECACHE = ["./", "./index.html", "./style.css", "./app.mjs", "./game.mjs",
  "./storage.mjs", "./sound.mjs", "./dialog.mjs", "./render.mjs", "./input.mjs",
  "./manifest.webmanifest", "./icon.svg", "./audio_review/win_A.wav"];

const isOurRequest = request =>
  request.method === "GET" && new URL(request.url).origin === self.location.origin;

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE);
      await cache.put(request, response.clone());
    }
    return response;
  } catch {
    // 断网时退回缓存的页面壳，保证同一网址仍能打开。
    return (await caches.match("./index.html")) || Response.error();
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE);
      await cache.put(request, response.clone());
    }
    return response;
  } catch {
    return Response.error();
  }
}

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith("2048-mobile-") && key !== CACHE).map(key => caches.delete(key))
  )));
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  if (!isOurRequest(event.request)) return;
  // 页面本身走网络优先，避免改了 HTML 后用户还拿着旧缓存；
  // JS/CSS/图标等带内容校验的静态资源走缓存优先，保证离线可用。
  event.respondWith(event.request.mode === "navigate"
    ? networkFirst(event.request)
    : cacheFirst(event.request));
});
