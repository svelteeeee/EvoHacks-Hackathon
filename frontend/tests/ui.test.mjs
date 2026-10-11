/** DOM interaction tests, not a substitute for an actual browser/performance test. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { Window } from "happy-dom";
import { build } from "esbuild";

await build({
  entryPoints: ["src/main.ts"],
  bundle: true,
  format: "esm",
  outfile: ".test/main.mjs",
  loader: { ".css": "empty" },
  logLevel: "silent",
});
const fixture = JSON.parse(
  await readFile("../data/demo/cop28-en.json", "utf8"),
);
const config = {
  countries: {
    us: { name: "United States", flag: "🇺🇸", language: "en" },
    gb: { name: "United Kingdom", flag: "🇬🇧", language: "en" },
    fr: { name: "France", flag: "🇫🇷", language: "fr" },
    de: { name: "Germany", flag: "🇩🇪", language: "de" },
    jp: { name: "Japan", flag: "🇯🇵", language: "ja" },
    in: { name: "India", flag: "🇮🇳", language: "hi" },
  },
  languages: { en: "English" },
  keys: { groq: false, news: false, audio: false },
  demos: [
    {
      id: "cop28",
      query: "COP28",
      title: "The fossil fuel turning point",
      tag: "CLIMATE & DIPLOMACY",
      date: "13 Dec 2023",
      languages: ["en"],
    },
  ],
};
const window = new Window({ url: "http://localhost:3000" });
for (const key of [
  "window",
  "document",
  "navigator",
  "HTMLElement",
  "HTMLCanvasElement",
  "HTMLDialogElement",
  "ResizeObserver",
  "sessionStorage",
  "history",
  "location",
])
  Object.defineProperty(globalThis, key, {
    value: key === "window" ? window : window[key],
    configurable: true,
    writable: true,
  });
globalThis.devicePixelRatio = 1;
const media = { matches: false, addEventListener() {} };
globalThis.matchMedia = () => media;
globalThis.requestAnimationFrame = () => 1;
globalThis.cancelAnimationFrame = () => {};
const gradient = { addColorStop() {} };
const context = new Proxy(
  {},
  {
    get(_target, name) {
      if (name === "createLinearGradient" || name === "createRadialGradient")
        return () => gradient;
      return () => {};
    },
    set() {
      return true;
    },
  },
);
window.HTMLCanvasElement.prototype.getContext = () => context;
window.HTMLElement.prototype.getBoundingClientRect = () => ({
  width: 1200,
  height: 440,
  left: 0,
  right: 1200,
  top: 0,
  bottom: 440,
});
window.HTMLElement.prototype.scrollIntoView = () => {};
window.HTMLDialogElement.prototype.showModal = function () {
  this.open = true;
};
window.HTMLDialogElement.prototype.close = function () {
  this.open = false;
  this.dispatchEvent(new window.Event("close"));
};
const calls = [];
globalThis.fetch = async (url, options) => {
  calls.push([url, options]);
  if (url === "/api/config") return Response.json(config);
  if (url === "/api/analyze/stream")
    return new Response(
      "data: " +
        JSON.stringify({ stage: "complete", report: fixture }) +
        "\n\n",
      { headers: { "Content-Type": "text/event-stream" } },
    );
  if (url.includes("/audio/"))
    return Response.json({ detail: "Narration not cached" }, { status: 503 });
  if (url.startsWith("/api/reports/")) return Response.json(fixture);
  throw Error("Unexpected request " + url);
};
document.body.innerHTML = '<div id="app"></div>';
await import("../.test/main.mjs");
const wait = async (predicate) => {
  for (let i = 0; i < 100; i++) {
    if (predicate()) return;
    await new Promise((r) => setTimeout(r, 10));
  }
  throw Error("DOM did not reach expected state");
};
await wait(() => document.querySelector("[data-demo]"));

test("first-visit intro can be skipped; missing keys clearly labeled", () => {
  assert(document.body.classList.contains("intro"));
  document.getElementById("skip-intro").click();
  assert(!document.body.classList.contains("intro"));
  assert.equal(sessionStorage.getItem("newsbridge-intro"), "seen");
  assert.match(document.getElementById("key-note").textContent, /Keys missing/);
});
test("event selection renders six actual outlet rows and evidence-linked summary", async () => {
  document.querySelector('[data-demo="cop28"]').click();
  await wait(() => !document.getElementById("results").hidden);
  assert.equal(
    document.querySelectorAll(".outlet-row").length,
    fixture.countries.reduce((n, c) => n + c.outlets.length, 0),
  );
  assert.equal(document.querySelectorAll("tbody tr").length, 6);
  assert.equal(document.querySelectorAll("tbody td button").length, 36);
  assert(document.querySelector(".summary-copy .citation"));
  assert(document.querySelector(".results-city canvas"));
  assert.equal(
    JSON.parse(calls.find((c) => c[0] === "/api/analyze/stream")[1].body).demo,
    true,
  );
});
test("theme selection and heatmap cell open exact original evidence", () => {
  document.querySelector('[data-theme="diplomacy"]').click();
  assert.equal(
    document
      .querySelector('[data-theme="diplomacy"]')
      .getAttribute("aria-pressed"),
    "true",
  );
  document.querySelector('tbody button[data-evidence="us:diplomacy"]').click();
  assert(document.getElementById("evidence").open);
  const quote = fixture.countries[0].outlets[0].framing.themes.find(
    (t) => t.theme === "diplomacy",
  ).quote;
  assert(
    document.querySelector("#evidence blockquote").textContent.includes(quote),
  );
  assert(document.querySelector("#evidence a").href.startsWith("https://"));
  document.querySelector('[data-close="evidence"]').click();
});
test("translation toggle, simple summary, and source filtering work", () => {
  document.getElementById("original").checked = true;
  document
    .getElementById("original")
    .dispatchEvent(new window.Event("change", { bubbles: true }));
  const row = document.querySelector(".outlet-content h3");
  assert.equal(
    row.textContent,
    fixture.countries[0].outlets[0].article.headline,
  );
  document.getElementById("simple").checked = true;
  document
    .getElementById("simple")
    .dispatchEvent(new window.Event("change", { bubbles: true }));
  assert(
    document
      .querySelector(".summary-copy")
      .textContent.includes(fixture.synthesis.simple_summary[0].text),
  );
  document.querySelector('[data-filter="fr"]').click();
  assert.equal(
    document.querySelectorAll(".outlet-row").length,
    fixture.countries.find((c) => c.country === "fr").outlets.length,
  );
  assert.equal(document.querySelector(".outlet-content h3").lang, "fr");
});
test("command palette keyboard shortcut works and respects Esc/close control", () => {
  document.dispatchEvent(
    new window.KeyboardEvent("keydown", {
      key: "k",
      ctrlKey: true,
      bubbles: true,
    }),
  );
  assert(document.getElementById("palette").open);
  assert.equal(document.activeElement.id, "palette-input");
  document.querySelector('[data-close="palette"]').click();
  assert(!document.getElementById("palette").open);
});
test("district hover focuses matching outlet rows and leaves no stale dimming", () => {
  document.querySelector('[data-filter=""]').click();
  const district = document.querySelector('[data-district="fr"]');
  district.dispatchEvent(
    new window.PointerEvent("pointerover", { bubbles: true }),
  );
  assert.equal(
    document.querySelectorAll(".outlet-row.dimmed").length,
    fixture.countries
      .filter((c) => c.country !== "fr")
      .reduce((n, c) => n + c.outlets.length, 0),
  );
  assert.equal(
    document.querySelectorAll(".outlet-row.district-focus").length,
    fixture.countries.find((c) => c.country === "fr").outlets.length,
  );
  district.dispatchEvent(
    new window.PointerEvent("pointerout", {
      bubbles: true,
      relatedTarget: document.body,
    }),
  );
  assert.equal(document.querySelectorAll(".outlet-row.dimmed").length, 0);
});
test("unsafe headline HTML is escaped rather than executed", async () => {
  fixture.countries[0].outlets[0].framing.translated_headline =
    "<img src=x onerror=alert(1)> headline";
  document.getElementById("original").checked = false;
  document
    .getElementById("original")
    .dispatchEvent(new window.Event("change", { bubbles: true }));
  document.querySelector('[data-demo="cop28"]').click();
  await wait(() => !document.getElementById("results").hidden);
  assert.equal(document.querySelectorAll("#results img").length, 0);
  assert(
    document.querySelector(".outlet-content h3").textContent.includes("<img"),
  );
});
