// Teramina PWA Service Worker
// Caches app shell for offline use; queues daily-log writes via Background Sync.

const CACHE_NAME = "teramina-shell-v1";
const SYNC_TAG = "daily-log-sync";

// App shell assets cached on install
const SHELL_ASSETS = [
  "/",
  "/index.html",
  "/manifest.json",
  "/favicon.ico",
];

// ── Lifecycle ────────────────────────────────────────────────────────────────

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch strategy ───────────────────────────────────────────────────────────
// API calls: network-first, fall through to error
// Shell assets: cache-first

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Pass through non-GET and cross-origin requests
  if (event.request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  // API routes: always network, no cache
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/agent/")) {
    return;
  }

  // Shell: cache-first with network fallback
  event.respondWith(
    caches.match(event.request).then(
      (cached) => cached || fetch(event.request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
    )
  );
});

// ── Background Sync — daily log writes ──────────────────────────────────────
// When offline, daily-log POST requests are stored in IndexedDB under "pending-notes".
// When connectivity returns, this handler flushes them.

self.addEventListener("sync", (event) => {
  if (event.tag === SYNC_TAG) {
    event.waitUntil(flushPendingNotes());
  }
});

async function flushPendingNotes() {
  const db = await openDB();
  const pending = await getAllPending(db);
  for (const item of pending) {
    try {
      const response = await fetch(item.url, {
        method: "POST",
        headers: item.headers,
        body: item.body,
      });
      if (response.ok) {
        await deletePending(db, item.id);
      }
    } catch {
      // Will retry on next sync event
    }
  }
}

// ── IndexedDB helpers ────────────────────────────────────────────────────────

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("teramina-offline", 1);
    req.onupgradeneeded = (e) => {
      e.target.result.createObjectStore("pending-notes", {
        keyPath: "id",
        autoIncrement: true,
      });
    };
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = (e) => reject(e.target.error);
  });
}

function getAllPending(db) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("pending-notes", "readonly");
    const req = tx.objectStore("pending-notes").getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function deletePending(db, id) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("pending-notes", "readwrite");
    const req = tx.objectStore("pending-notes").delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

// ── Push notifications ───────────────────────────────────────────────────────

self.addEventListener("push", (event) => {
  if (!event.data) return;
  let payload;
  try {
    payload = event.data.json();
  } catch {
    payload = { title: "Teramina Alert", body: event.data.text() };
  }
  event.waitUntil(
    self.registration.showNotification(payload.title || "Teramina Alert", {
      body: payload.body || "",
      icon: "/logo192.png",
      badge: "/favicon.png",
      data: payload.data || {},
      tag: payload.data?.alert_type || "teramina-alert",
      requireInteraction: payload.data?.severity === "critical",
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windowClients) => {
      const existing = windowClients.find((c) => c.url.includes(self.location.origin));
      if (existing) return existing.focus();
      return clients.openWindow("/dashboard/today");
    })
  );
});
