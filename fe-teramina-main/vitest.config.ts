import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const alias = {
  components: resolve(__dirname, "./src/components"),

  hoc: resolve(__dirname, "./src/hoc"),
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

export default defineConfig({
  plugins: [react()],
  resolve: { alias },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/tests/setup.ts"],
    pool: "forks",
  },
});
