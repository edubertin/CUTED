import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "src/index.ts"),
      fileName: () => "live-timeline.js",
      formats: ["iife"],
      name: "CuttedLiveTimeline"
    },
    outDir: "dist-lib",
    rollupOptions: {
      output: {
        assetFileNames: "live-timeline.[ext]",
        inlineDynamicImports: true
      }
    }
  }
});
