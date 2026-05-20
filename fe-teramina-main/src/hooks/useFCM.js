// Custom hook to register FCM token on login
// Uses Firebase Messaging API to get token
// On mount: request notification permission, get token, POST to /user/fcm-token
// Only runs once (stores "fcm_registered" in sessionStorage to avoid duplicate calls)

import { useEffect } from "react";
import { getMessaging, getToken } from "firebase/messaging";
import { getApp } from "firebase/app";
import { axios } from "helper/axios";

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY;

export function useFCM() {
  useEffect(() => {
    if (sessionStorage.getItem("fcm_registered")) return;
    if (!("Notification" in window)) return;

    Notification.requestPermission().then((permission) => {
      if (permission !== "granted") return;
      try {
        const app = getApp();
        const messaging = getMessaging(app);
        getToken(messaging, { vapidKey: VAPID_KEY }).then((token) => {
          if (token) {
            axios.post("/user/fcm-token", { token }).then(() => {
              sessionStorage.setItem("fcm_registered", "1");
            });
          }
        });
      } catch {
        // FCM not available in this environment
      }
    });
  }, []);
}
