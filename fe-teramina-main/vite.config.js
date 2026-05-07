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
    globPatterns: ["**/*.{html,js,css,ico,png,gif,woff2,svg}"],
    globIgnores: ["**/laptop.svg"],
  },
});
const ALIAS = {
  components: resolve(__dirname, "./src/components"),
  containers: resolve(__dirname, "./src/features"),
  hoc: resolve(__dirname, "./src/hoc"),
  pages: resolve(__dirname, "./src/pages"),
  routes: resolve(__dirname, "./src/routes"),
  theme: resolve(__dirname, "./src/theme"),
  libraries: resolve(__dirname, "./src/libraries"),
  helper: resolve(__dirname, "./src/helper"),
  widgets: resolve(__dirname, "./src/widgets"),
  hooks: resolve(__dirname, "./src/hooks"),
  store: resolve(__dirname, "./src/store"),
  locales: resolve(__dirname, "./src/locales"),
  features: resolve(__dirname, "./src/features"),
  lib: resolve(__dirname, "./src/lib"),
};
const OUTPUT = {
  manualChunks: (id) => {
    if (id.includes("node_modules")) {
      if (id.includes("@mui/icons-material")) {
        return "vendor_mui_icons_material";
      }

      if (id.includes("@mui/material")) {
        return "vendor_mui_material";
      }

      if (id.includes("@mui/styles")) {
        return "vendor_mui_styles";
      }

      if (id.includes("@mui/x-data-grid")) {
        return "vendor_mui_x_data_grid";
      }

      if (id.includes("@mui/x-date-pickers")) {
        return "vendor_mui_x_date_pickers";
      }

      if (id.includes("react-icons")) {
        return "vendor_react_icons";
      }

      if (id.includes("firebase")) {
        return "vendor_firebase";
      }

      if (id.includes("classnames")) {
        return "vendor_classnames";
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

      if (id.includes("@fontsource")) {
        return "vendor_fontsource";
      }

      if (id.includes("universal-cookie")) {
        return "vendor_universal_cookie";
      }

      if (id.includes("remix")) {
        return "vendor_remix";
      }

      if (id.includes("jss")) {
        return "vendor_jss";
      }

      if (id.includes("scheduler")) {
        return "vendor_scheduler";
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
