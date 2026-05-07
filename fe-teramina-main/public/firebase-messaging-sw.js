// Firebase Messaging Service Worker — handles background push notifications
importScripts("https://www.gstatic.com/firebasejs/10.0.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.0.0/firebase-messaging-compat.js");

// Config injected at runtime via firebaseConfig (uses same project as main app)
// Service worker reads config from URL search params passed during registration
self.addEventListener("activate", () => {});

firebase.initializeApp({
  apiKey: self.location.search.includes("apiKey")
    ? new URLSearchParams(self.location.search).get("apiKey")
    : "",
  // NOTE: in production, these values should be injected at build time
  // For now, this service worker shows the notification directly
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const { title, body } = payload.notification || {};
  self.registration.showNotification(title || "Teramina Alert", {
    body: body || "",
    icon: "/assets/images/logo.png",
    badge: "/assets/images/logo.png",
    data: payload.data,
  });
});
