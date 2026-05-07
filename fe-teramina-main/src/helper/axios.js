import axios from "axios";
import { getAuth, signOut } from "firebase/auth";
import { useLocalStorage } from "hooks/useLocalStorage";
import { useToastStore } from "store/toast.store";

const AXIOS = axios.create({
  withCredentials: true,
  baseURL: import.meta.env.VITE_ENDPOINT,
  headers: {
    "Content-Type": "application/json",
  }
});

const DEV_TOKEN = import.meta.env.VITE_DEV_TOKEN;

AXIOS.interceptors.request.use(
  (config) => {
    const { get } = useLocalStorage();
    const token = DEV_TOKEN || get("authentication");
    if (token) {
      config.headers["Authorization"] = "Bearer " + token;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
)

AXIOS.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { get, set, removeItem } = useLocalStorage();
    const originalRequest = error.config;
    const showToast = useToastStore.getState().setToast;

    // No response at all — network failure or timeout
    if (!error.response) {
      showToast({ open: true, variant: "error", text: "Network error. Please check your connection." });
      return Promise.reject(error);
    }

    const { status } = error.response;

    if (status === 401) {
      try {
        const new_access_token = await AXIOS.get("/user/verify-with-refresh-token", {
          headers: { Authorization: `Bearer ${get("refresh_token")}` },
        });
        if (!new_access_token) throw new_access_token;
        set("authentication", new_access_token.payload.token);
        set("refresh_token", new_access_token.payload.refresh_token);
        return AXIOS(originalRequest);
      } catch {
        const auth = getAuth();
        await signOut(auth);
        removeItem("authentication");
        removeItem("refresh_token");
        return (window.location.href = "/");
      }
    }

    if (status === 429) {
      showToast({ open: true, variant: "info", text: "Too many requests. Please wait a moment and try again." });
      return Promise.reject(error);
    }

    if (status >= 500) {
      showToast({ open: true, variant: "error", text: "Something went wrong on the server. Please try again later." });
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);


export { AXIOS as axios }