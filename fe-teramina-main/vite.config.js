import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vite";

const __dirname = dirname(fileURLToPath(import.meta.url));

const REACT = react();
const SERVICE_WORKER = VitePWA({
  registerType: "autoUpdate",
  injectRegister: "auto",
  workbox: {
    clientsClaim: true,
    skipWaiting: true,
    cleanupOutdatedCaches: true,
    globPatterns: ["**/*.{html,js,css,ico,png,gif,woff2,svg}"],
    globIgnores: ["**/laptop.svg"],
  },
});
const ALIAS = {
  components: resolve(__dirname, "./src/components"),
  pages: resolve(__dirname, "./src/pages"),
  routes: resolve(__dirname, "./src/routes"),
  theme: resolve(__dirname, "./src/theme"),
  libraries: resolve(__dirname, "./src/libraries"),
  helper: resolve(__dirname, "./src/helper"),
  widgets: resolve(__dirname, "./src/features/dashboard"),
  hooks: resolve(__dirname, "./src/hooks"),
  store: resolve(__dirname, "./src/store"),
  locales: resolve(__dirname, "./src/locales"),
  features: resolve(__dirname, "./src/features"),
  lib: resolve(__dirname, "./src/lib"),
};
const OUTPUT = {
  manualChunks: (id) => {
    if (id.includes("node_modules")) {
      if (
        id.includes("/node_modules/react/")
        || id.includes("/node_modules/react-dom/")
        || id.includes("/node_modules/scheduler/")
      ) {
        return "vendor_react_core";
      }

      if (id.includes("react-router")) {
        return "vendor_react_router";
      }

      if (id.includes("@tanstack")) {
        return "vendor_tanstack";
      }

      if (id.includes("react-hook-form") || id.includes("@hookform") || id.includes("zod")) {
        return "vendor_forms";
      }

      if (id.includes("i18next") || id.includes("react-i18next")) {
        return "vendor_i18n";
      }

      if (id.includes("@mui/icons-material")) {
        return "vendor_mui_icons_material";
      }

      if (id.includes("@mui/x-data-grid")) {
        return "vendor_mui_x_data_grid";
      }

      if (id.includes("@mui/x-date-pickers")) {
        return "vendor_mui_x_date_pickers";
      }

      if (
        id.includes("@mui/")
        || id.includes("@emotion")
        || id.includes("tss-react")
        || id.includes("react-transition-group")
        || id.includes("clsx")
      ) {
        return "vendor_mui_core";
      }

      if (id.includes("react-icons")) {
        return "vendor_react_icons";
      }

      if (id.includes("firebase")) {
        return "vendor_firebase";
      }

      if (id.includes("zrender")) {
        return "vendor_zrender";
      }

      if (id.includes("echarts")) {
        return "vendor_echarts";
      }

      if (id.includes("@testing-library")) {
        return "vendor_testing_library";
      }

      if (id.includes("axios")) {
        return "vendor_axios";
      }

      if (id.includes("@sentry")) {
        return "vendor_sentry";
      }

      if (
        id.includes("react-markdown")
        || id.includes("rehype")
        || id.includes("remark")
        || id.includes("unified")
        || id.includes("vfile")
        || id.includes("mdast")
        || id.includes("hast")
        || id.includes("micromark")
      ) {
        return "vendor_markdown";
      }

      if (id.includes("lodash") || id.includes("dayjs") || id.includes("zustand") || id.includes("classnames")) {
        return "vendor_utils";
      }

      if (id.includes("react-svg") || id.includes("react-dropzone") || id.includes("react-ga4")) {
        return "vendor_react_extras";
      }

      if (id.includes("@fontsource")) {
        return "vendor_fontsource";
      }

      if (id.includes("universal-cookie")) {
        return "vendor_universal_cookie";
      }

      return "vendor";
    }
  },
};

const CONFIG = {
  plugins: [],
  resolve: {
    alias: ALIAS,
  },
  build: {
    rollupOptions: {
      output: OUTPUT,
    },
  },
};

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  CONFIG.plugins.push(REACT);

  if (!(mode === "development")) {
    CONFIG.plugins.push(SERVICE_WORKER);
  }

  return CONFIG;
});
