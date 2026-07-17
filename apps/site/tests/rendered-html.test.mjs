import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the CUTED public page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>CUTED \| Cortes de vídeo com IA no Windows<\/title>/i);
  assert.match(html, /Baixar para Windows/);
  assert.match(html, /CUTED Now/);
  assert.match(html, /Falar com o desenvolvedor/);
  assert.match(html, /edubertin85@gmail\.com/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("keeps public links and release assets explicit", async () => {
  const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  const layout = await readFile(new URL("../app/layout.tsx", import.meta.url), "utf8");

  assert.match(page, /github\.com\/edubertin\/CUTED/);
  assert.match(page, /v2026\.07\.17-beta\.1\/CUTED-Setup\.exe/);
  assert.match(page, /CUTED-Setup\.exe\.sha256/);
  assert.match(page, /tiktok\.com\/@cutednow/);
  assert.match(layout, /lang="pt-BR"/);
  assert.match(layout, /\/og\.png/);
});
