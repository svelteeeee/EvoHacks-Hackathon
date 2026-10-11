import "@fontsource/bricolage-grotesque/400.css";
import "@fontsource/bricolage-grotesque/600.css";
import "@fontsource/bricolage-grotesque/700.css";
import "@fontsource/source-serif-4/400.css";
import "@fontsource/source-serif-4/400-italic.css";
import "./style.css";
import {
  themes,
  themeNames,
  type Config,
  type Report,
  type Outlet,
  type Theme,
  type Progress,
} from "./types";

const app = document.querySelector<HTMLDivElement>("#app")!;
const esc = (s: unknown) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ]!,
  );
let config: Config;
let report: Report | undefined;
let selectedTheme: Theme = "diplomacy";
let selectedCountry = "";
let hoveredCountry = "";
const focusDistrict = (country: string) => {
  hoveredCountry = country;
  document.querySelectorAll<HTMLElement>(".outlet-row").forEach((row) => {
    const outlet = outlets().find((o) => "outlet-" + o.article.id === row.id);
    row.classList.toggle(
      "dimmed",
      !!country && outlet?.article.country !== country,
    );
    row.classList.toggle("district-focus", outlet?.article.country === country);
  });
  cityUpdate?.();
};
let busy = false;
let simple = false;
let original = false;
let language = "en";
let mode = "demo";
let controller: AbortController | undefined;
let focusedElement: HTMLElement | null = null;
const statuses = new Map<string, Progress>();
let cityUpdate: (() => void) | undefined;

app.innerHTML = `
<a class="skip-link" href="#main">Skip to content</a>
<header class="masthead"><a href="/" class="brand" aria-label="News Bridge home"><svg viewBox="0 0 34 26" aria-hidden="true"><path d="M2 21H32M8 21V5M26 21V5M2 16Q17 3 32 16M8 8Q17 21 26 8"/></svg>news<span>bridge</span><sup>β</sup></a><nav aria-label="Main"><button id="about-btn" class="text-button">The idea <span>↗</span></button><span class="edition">A DIFFERENT VIEW OF THE WORLD</span></nav><label class="language-control"><span class="sr-only">Summary language</span><span aria-hidden="true">◎</span><select id="language"><option value="en">English</option><option value="es">Español</option><option value="fr">Français</option></select></label></header>
<main id="main">
<section class="hero" aria-labelledby="hero-title"><div class="hero-copy"><p class="eyebrow"><span class="live-dot"></span> ONE STORY. SIX PERSPECTIVES.</p><h1 id="hero-title">The same world.<br><em>A different story.</em></h1><p class="hero-description">Cross borders. Read between the headlines.<br>See how the world sees your news.</p></div>
<div class="skyline-wrap"><canvas id="city" aria-hidden="true"></canvas><div class="intro-wordmark" aria-hidden="true">news<span>bridge</span></div><div class="city-caption"><span>THE WORLD, IN SIX DISTRICTS</span><span>EVERY WINDOW IS A PERSPECTIVE</span></div></div>
<div class="search-zone"><form id="search-form"><label for="query" class="sr-only">News event to compare</label><span class="search-icon" aria-hidden="true">⌕</span><input id="query" name="query" placeholder="What’s happening in the world?" required minlength="3" maxlength="160" autocomplete="off"><kbd id="shortcut">⌘ K</kbd><button type="submit" class="primary" id="search-btn">Bridge the story <span aria-hidden="true">↗</span></button></form><div class="search-under"><div class="mode-control"><button data-mode="demo" class="active" aria-pressed="true">Cached demo</button><button data-mode="live" aria-pressed="false">Live search</button></div><span id="key-note">No sign-in. All perspectives welcome.</span></div><div id="suggestions" class="suggestions" aria-label="Cached event suggestions"></div></div>
</section>
<div id="message" role="status" aria-live="polite"></div>
<section id="pipeline" class="pipeline" hidden aria-label="Analysis progress"><div class="section-heading"><p class="eyebrow">BUILDING YOUR BRIDGE</p><p id="pipeline-stage" role="status">Finding coverage</p></div><div id="country-statuses"></div><button id="cancel" class="text-button">Cancel analysis</button></section>
<section id="welcome" class="welcome"><div class="welcome-heading"><p class="eyebrow">START WITH A STORY</p><h2>Big events. Different lenses.</h2><p>Three real stories, captured and ready to explore.</p></div><div id="demo-stories" class="story-list"></div><div class="how"><div><span>01 / FIND</span><p>Coverage across six<br>country editions.</p></div><div><span>02 / UNDERSTAND</span><p>Translate the text.<br>Trace the framing.</p></div><div><span>03 / CONNECT</span><p>Common ground.<br>Not a single “truth.”</p></div><p class="how-note">Not a bias detector.<br>A better starting point.</p></div></section>
<section id="results" hidden></section>
</main>
<footer><a href="/" class="footer-brand">newsbridge</a><p>AI analysis of headlines and excerpts, not ground truth.<br>One outlet never speaks for a whole country.</p><span>BUILT TO BRING US CLOSER ↗</span></footer>
<dialog id="palette" aria-labelledby="palette-title"><div class="dialog-heading"><h2 id="palette-title">Find a story</h2><button data-close="palette" aria-label="Close search">×</button></div><label class="sr-only" for="palette-input">Search cached events</label><input id="palette-input" placeholder="Type an event…"><div id="palette-list"></div><p class="muted">↑ ↓ to move · Enter to choose · Esc to close</p></dialog>
<dialog id="evidence" aria-labelledby="evidence-title"></dialog>
<dialog id="about" aria-labelledby="about-title"><div class="dialog-heading"><p class="eyebrow">WHY NEWS BRIDGE</p><button data-close="about" aria-label="Close explanation">×</button></div><h2 id="about-title">Your feed is a window.<br>Not the whole city.</h2><p>News Bridge automates the work of reading foreign coverage: finding stories, translating headlines and excerpts, tracing claims, and comparing emphasis.</p><p>Our city makes those perspectives visible. A brighter district means more emphasis on the selected theme in the retrieved sample—not more truth, and not what an entire country believes.</p><p>Every score links back to evidence. Missing voices are questions worth asking, not accusations of censorship.</p><a class="source-link" href="/docs">Explore the pipeline API ↗</a></dialog>
<button id="skip-intro" class="skip-intro" hidden>Skip intro ↗</button>
`;
const el = <T extends HTMLElement = HTMLElement>(id: string) =>
  document.getElementById(id) as T;
const notice = (message: string, error = false) => {
  el("message").innerHTML = message
    ? `<div class="notice ${error ? "error" : ""}"><span>${error ? "!" : "↗"}</span>${esc(message)}</div>`
    : "";
};
const outlets = () => report?.countries.flatMap((c) => c.outlets) ?? [];
const countryName = (c: string) => config.countries[c]?.name ?? c;
const restoreCity = () => {
  const skyline = document.querySelector<HTMLElement>(".skyline-wrap");
  if (skyline) {
    document.querySelector(".hero")!.append(skyline);
    skyline.classList.remove("result-city");
  }
};
const score = (c: string, t: Theme) => {
  const items = report?.countries.find((x) => x.country === c)?.outlets ?? [];
  return items.length
    ? Math.round(
        items.reduce(
          (n, o) =>
            n + (o.framing.themes.find((s) => s.theme === t)?.score ?? 0),
          0,
        ) / items.length,
      )
    : null;
};
const sourceLinks = (ids: string[]) =>
  ids
    .map((id) => {
      const o = outlets().find((x) => x.article.id === id);
      return o
        ? `<a href="${esc(o.article.url)}" target="_blank" rel="noopener noreferrer" class="citation" title="${esc(o.article.headline)}">${esc(o.article.outlet)} ↗</a>`
        : "";
    })
    .join(" ");
function renderDemos() {
  el("welcome").querySelector(".welcome-heading>p:last-child")!.textContent =
    `${config.demos.length} real stories, captured and ready to explore.`;
  el("suggestions").innerHTML =
    `<span>TRY A STORY</span>` +
    config.demos
      .map(
        (d) =>
          `<button data-demo="${d.id}">${esc(d.query)} <span>↗</span></button>`,
      )
      .join("");
  el("demo-stories").innerHTML = config.demos
    .map(
      (d, i) =>
        `<button class="story" data-demo="${d.id}"><span class="story-number">0${i + 1}</span><div><span class="eyebrow">${esc(d.tag)}</span><h3>${esc(d.title)}</h3><span class="story-date">${esc(d.date)} · 6 country editions</span></div><span class="story-arrow">↗</span></button>`,
    )
    .join("");
  renderPalette("");
}
function renderPalette(query: string) {
  el("palette-list").innerHTML =
    config.demos
      .filter((d) =>
        (d.title + " " + d.query).toLowerCase().includes(query.toLowerCase()),
      )
      .map(
        (d) =>
          `<button data-demo="${d.id}"><span>${esc(d.query)}</span><small>${esc(d.title)}</small><span>↵</span></button>`,
      )
      .join("") || "<p>No cached match. Use live search for another story.</p>";
}
function setMode(value: string) {
  mode = value;
  document.querySelectorAll<HTMLButtonElement>("[data-mode]").forEach((b) => {
    b.classList.toggle("active", b.dataset.mode === mode);
    b.setAttribute("aria-pressed", String(b.dataset.mode === mode));
  });
  el("key-note").textContent =
    mode === "demo"
      ? !config.keys.groq || !config.keys.news
        ? "Keys missing · cached demo still works."
        : "Captured sources. Cached AI. No network required."
      : !config.keys.groq || !config.keys.news
        ? "Keys missing. Choose a cached story to continue."
        : "Live feeds can be incomplete. Sources stay visible.";
}
function statusRender() {
  el("country-statuses").innerHTML = Object.keys(config.countries)
    .map((c) => {
      const s = statuses.get(c);
      return `<div class="status-chip ${s?.stage ?? "waiting"}"><span class="status-light"></span><span>${esc(countryName(c))}</span><small>${esc(s?.stage === "ready" ? "Ready" : s?.stage === "failed" ? "Unavailable" : (s?.stage ?? "Waiting"))}</small>${s ? `<span class="status-detail">${esc(s.message)}</span>` : ""}</div>`;
    })
    .join("");
  cityUpdate?.();
}
async function analyze(query: string, demo: boolean) {
  if (busy) return;
  restoreCity();
  document.body.classList.remove("has-report");
  busy = true;
  el<HTMLSelectElement>("language").disabled = true;
  controller = new AbortController();
  report = undefined;
  selectedCountry = "";
  statuses.clear();
  el("pipeline-stage").textContent = "Finding coverage";
  el("results").hidden = true;
  el("welcome").hidden = true;
  el("pipeline").hidden = false;
  el<HTMLButtonElement>("search-btn").disabled = true;
  el("search-btn").innerHTML = 'Connecting <span class="spinner"></span>';
  notice("");
  statusRender();
  el<HTMLInputElement>("query").value = query;
  try {
    const response = await fetch("/api/analyze/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, language, demo }),
      signal: controller.signal,
    });
    if (!response.ok)
      throw new Error(
        "The request could not start. Check your query and try again.",
      );
    const reader = response.body?.getReader();
    if (!reader) throw new Error("Streaming is unavailable. Try again.");
    let buffer = "";
    const decoder = new TextDecoder();
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";
      for (const chunk of chunks) {
        if (!chunk.startsWith("data: ")) continue;
        const update: Progress = JSON.parse(chunk.slice(6));
        if (update.stage === "error") throw new Error(update.message);
        if (update.stage === "complete" && update.report) {
          report = update.report;
          renderResults();
        } else if (update.country) {
          statuses.set(update.country, update);
          statusRender();
        } else {
          el("pipeline-stage").textContent = update.message;
        }
      }
      if (done) break;
    }
    if (!report)
      throw new Error(
        "The analysis ended without a report. Try a cached story.",
      );
  } catch (error) {
    if ((error as Error).name !== "AbortError")
      notice((error as Error).message, true);
    else notice("Analysis cancelled. Pick a story when you’re ready.");
    if (!report) el("welcome").hidden = false;
  } finally {
    busy = false;
    el<HTMLSelectElement>("language").disabled = false;
    controller = undefined;
    el("pipeline").hidden = true;
    el<HTMLButtonElement>("search-btn").disabled = false;
    el("search-btn").innerHTML =
      'Bridge the story <span aria-hidden="true">↗</span>';
    cityUpdate?.();
  }
}
function translatedHeadline(o: Outlet) {
  const text = original ? o.article.headline : o.framing.translated_headline;
  if (original) return esc(text);
  let cursor = 0;
  const words = o.framing.loaded_words
    .map((w) => ({ ...w, index: text.indexOf(w.word) }))
    .filter((w) => w.index >= 0)
    .sort((a, b) => a.index - b.index);
  let html = "";
  for (const w of words) {
    if (w.index < cursor) continue;
    html +=
      esc(text.slice(cursor, w.index)) +
      `<mark tabindex="0" class="loaded" aria-label="${esc(w.word + ": " + w.explanation + ". Neutral wording: " + w.neutral)}">${esc(w.word)}<span class="word-tip">${esc(w.explanation)}<br><strong>Neutral: ${esc(w.neutral)}</strong></span></mark>`;
    cursor = w.index + w.word.length;
  }
  return html + esc(text.slice(cursor));
}
function outletCard(o: Outlet) {
  const f = o.framing;
  const prominent = [...f.themes]
    .sort((a, b) => b.score - a.score)
    .filter((t) => t.score > 0)
    .slice(0, 2);
  return `<article class="outlet-row" id="outlet-${esc(o.article.id)}"><div class="outlet-origin"><span class="flag">${config.countries[o.article.country].flag}</span><div><p>${esc(countryName(o.article.country))}</p><a href="${esc(o.article.url)}" target="_blank" rel="noopener noreferrer">${esc(o.article.outlet)} ↗</a></div></div><div class="outlet-content"><div class="outlet-meta"><span>${esc(f.tone.replaceAll("_", " "))}</span><span>${esc(o.article.coverage.replaceAll("_", " "))} evidence</span></div><h3 lang="${original ? o.article.language : "en"}">${translatedHeadline(o)}</h3><p class="original-headline" lang="${o.article.language}">${esc(original ? f.translated_headline : o.article.headline)}</p><div class="tags">${prominent.map((t) => `<button data-evidence="${o.article.country}:${t.theme}">${themeNames[t.theme]} <b>${t.score}</b></button>`).join("")}</div></div><div class="outlet-confidence"><span class="eyebrow">EVIDENCE CONFIDENCE*</span><div class="confidence-track"><span style="width:${f.confidence * 100}%"></span></div><strong>${Math.round(f.confidence * 100)}%</strong><button class="text-button" data-evidence="${o.article.country}:${selectedTheme}">See evidence ↗</button></div></article>`;
}
function renderResults() {
  if (!report) return;
  restoreCity();
  document.body.classList.add("has-report");
  const count = outlets().length;
  const ready = report.countries.filter((c) => c.outlets.length).length;
  el("welcome").hidden = true;
  el("results").hidden = false;
  el("results").innerHTML = `
 <div class="report-heading"><div><p class="eyebrow"><span class="live-dot"></span> ${report.mode === "live" ? "LIVE ANALYSIS" : report.mode === "demo" ? "CACHED DEMO · REAL SOURCES" : "CACHED LIVE ANALYSIS"}</p><h2>${esc(report.query)}<span class="report-period">.</span></h2><p>${count} sources · ${ready} country editions · ${esc(new Date(report.created_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }))}</p></div><div class="report-actions"><button class="outline" id="share">Copy report link ↗</button><button class="outline" id="export">Print report ↗</button></div></div>
 <div class="sample-note"><span>ⓘ</span><p>${esc(report.notices[0] ?? "AI analysis, not ground truth.")} ${esc(report.notices[1] ?? "")}</p></div>
 <section class="summary-section" aria-labelledby="summary-title"><div class="section-label"><span>01</span><p class="eyebrow">THE COMMON GROUND</p><h3 id="summary-title">What connects<br>the coverage.</h3><label class="simple-control"><input id="simple" type="checkbox" ${simple ? "checked" : ""}> Explain it simply</label><button class="text-button" id="audio-summary">Listen to the briefing <span>▷</span></button><div id="audio-player"></div></div><div class="summary-copy">${(simple ? report.synthesis.simple_summary : report.synthesis.summary).map((s) => `<div><p>${esc(s.text)}</p><div class="citations">${sourceLinks(s.source_ids)}</div></div>`).join("")}<p class="summary-caveat">${esc(report.synthesis.caveat)}</p></div></section>
 <section class="comparison" aria-labelledby="comparison-title"><div class="section-heading"><div><p class="eyebrow">02 / THE PERSPECTIVE MAP</p><h3 id="comparison-title">What gets the spotlight?</h3></div><p>Choose a theme. Watch the districts respond.<br>Brighter means more emphasis—not more truth.</p></div><div class="theme-switcher" role="group" aria-label="Compare theme">${themes.map((t) => `<button data-theme="${t}" aria-pressed="${t === selectedTheme}" class="${t === selectedTheme ? "active" : ""}">${themeNames[t]}</button>`).join("")}</div><div id="results-city" class="results-city" aria-label="City district emphasis visualization"></div><div class="districts">${Object.keys(
   config.countries,
 )
   .map((c) => {
     const n = score(c, selectedTheme);
     return `<button class="district ${selectedCountry === c ? "selected" : ""}" data-district="${c}" data-evidence="${c}:${selectedTheme}" style="--intensity:${(n ?? 0) / 100}"><span class="district-mark">${config.countries[c].flag}</span><span>${esc(countryName(c))}</span><strong>${n ?? "—"}<small>${n === null ? "no sample" : "/ 100"}</small></strong><span class="district-meter"><i style="width:${n ?? 0}%"></i></span><span class="district-foot">${n === null ? "No coverage" : "Trace the evidence ↗"}</span></button>`;
   })
   .join(
     "",
   )}</div><details class="matrix" open><summary>Accessible emphasis matrix <span>0 = not visible · 100 = dominant</span></summary><div class="table-scroll"><table><caption class="sr-only">Theme emphasis across country-edition samples, zero to one hundred. Each cell opens evidence.</caption><thead><tr><th scope="col">Country edition</th>${themes.map((t) => `<th scope="col">${themeNames[t]}</th>`).join("")}</tr></thead><tbody>${Object.keys(
   config.countries,
 )
   .map(
     (c) =>
       `<tr><th scope="row">${config.countries[c].flag} ${esc(countryName(c))}</th>${themes
         .map((t) => {
           const n = score(c, t);
           return `<td><button data-evidence="${c}:${t}" style="--score:${(n ?? 0) / 100}" ${n === null ? "disabled" : ""} aria-label="${esc(countryName(c))}, ${themeNames[t]}, ${n ?? "no sample"}. Show evidence.">${n ?? "—"}</button></td>`;
         })
         .join("")}</tr>`,
   )
   .join("")}</tbody></table></div></details></section>
 <section class="coverage-section" aria-labelledby="coverage-title"><div class="section-heading"><div><p class="eyebrow">03 / SAME STORY, DIFFERENT LENS</p><h3 id="coverage-title">Read the windows.</h3></div><label class="simple-control"><input id="original" type="checkbox" ${original ? "checked" : ""}> Original headlines</label></div><div class="country-filter" role="group" aria-label="Filter sources"><button data-filter="" class="${!selectedCountry ? "active" : ""}">All perspectives</button>${report.countries
   .filter((c) => c.outlets.length)
   .map(
     (c) =>
       `<button data-filter="${c.country}" class="${selectedCountry === c.country ? "active" : ""}">${esc(countryName(c.country))}</button>`,
   )
   .join("")}</div><div id="outlet-list">${outlets()
   .filter((o) => !selectedCountry || o.article.country === selectedCountry)
   .map(outletCard)
   .join("")}</div>${report.countries
   .filter((c) => c.status !== "ready")
   .map(
     (c) =>
       `<p class="error-inline">${esc(countryName(c.country))}: ${esc(c.message)}</p>`,
   )
   .join(
     "",
   )}<p class="muted small">Amber words were flagged by AI. Hover or focus them for context. All headline translations are English; briefing language is selectable. *Confidence is an AI evidence-sufficiency estimate, not calibrated factual certainty.</p></section>
 <section class="insights" aria-labelledby="insights-title"><div class="section-heading"><div><p class="eyebrow">04 / GO ONE QUESTION DEEPER</p><h3 id="insights-title">Agreement isn’t the whole story.</h3></div><span class="ai-label">AI-ASSISTED · SOURCE-LINKED</span></div><div class="insight-columns"><div><h4>Where claims connect <span>↔</span></h4>${report.synthesis.clusters.map((c) => `<article class="claim"><span class="claim-status ${c.status}">${esc(c.status.replaceAll("_", " "))}</span><h5>${esc(c.claim)}</h5><p>${esc(c.note)}</p><div class="citations">${sourceLinks(c.source_ids)}</div></article>`).join("")}<p class="muted small">Shared reporting is not independent verification.</p></div><div><h4>Who isn’t in the room? <span>?</span></h4><p class="muted">Perspectives not visible in these excerpts—not proof of intentional omission.</p>${report.synthesis.missing_voices.map((v) => `<article class="missing"><h5>${esc(v.perspective)}</h5><p>${esc(v.why_it_matters)}</p><div class="citations">${sourceLinks(v.source_ids)}</div></article>`).join("")}</div></div></section>`;
  const skyline = document.querySelector<HTMLElement>(".skyline-wrap")!;
  el("results-city").append(skyline);
  skyline.classList.add("result-city");
  history.replaceState(null, "", `?report=${encodeURIComponent(report.id)}`);
  cityUpdate?.();
}
function openDialog(id: string) {
  focusedElement = document.activeElement as HTMLElement;
  el<HTMLDialogElement>(id).showModal();
}
function closeDialog(id: string) {
  el<HTMLDialogElement>(id).close();
  focusedElement?.focus();
}
function evidence(country: string, theme: Theme) {
  if (!report) return;
  selectedCountry = country;
  cityUpdate?.();
  const items = outlets().filter((o) => o.article.country === country);
  el("evidence").innerHTML =
    `<div class="dialog-heading"><p class="eyebrow">EVIDENCE LOCK / ${esc(countryName(country))}</p><button data-close="evidence" aria-label="Close evidence">×</button></div><h2 id="evidence-title">${themeNames[theme]} <span class="amber">${score(country, theme) ?? "—"}</span></h2><p class="muted">A qualitative emphasis score in the retrieved sample. Not a measurement of national opinion.</p>${
      items.length
        ? items
            .map((o) => {
              const t = o.framing.themes.find((x) => x.theme === theme)!;
              return `<article class="evidence-source"><p class="eyebrow">${esc(o.article.outlet)} · ${esc(o.article.coverage)} · ${Math.round(o.framing.confidence * 100)}% CONFIDENCE</p><blockquote lang="${o.article.language}">${t.quote ? `“${esc(t.quote)}”` : "No supporting mention in this sample."}</blockquote><p>${esc(t.rationale)}</p><a href="${esc(o.article.url)}" target="_blank" rel="noopener noreferrer" class="source-link">Read the original source ↗</a><details><summary>Claims, actors, and missing context</summary>${o.framing.key_claims.map((c) => `<p>${esc(c.text)}</p><blockquote lang="${o.article.language}">${esc(c.quote)}</blockquote>`).join("")}<p><strong>Blamed:</strong> ${esc(o.framing.blamed.join(", ") || "No explicit blame")}</p><p><strong>Praised:</strong> ${esc(o.framing.praised.join(", ") || "No explicit praise")}</p><p><strong>Not visible:</strong> ${esc(o.framing.omitted.join("; ") || "No further gap inferred")}</p></details><button class="text-button" data-audio="${country}">Hear this perspective ▷</button></article>`;
            })
            .join("")
        : "<p>No coverage was retrieved for this district.</p>"
    }<div id="district-audio"></div><button class="outline" id="focus-outlets" data-country="${country}">Focus these outlet cards ↗</button>`;
  openDialog("evidence");
}
async function playAudio(country: string) {
  if (!report) return;
  const target =
    country === "summary" ? el("audio-player") : el("district-audio");
  if (!target) return;
  target.innerHTML = '<p class="muted">Preparing cached narration…</p>';
  try {
    const response = await fetch(`/api/reports/${report.id}/audio/${country}`, {
      method: "POST",
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail ?? "Narration unavailable.");
    target.innerHTML = `<audio controls preload="metadata" src="${esc(data.url)}" aria-label="${esc(country === "summary" ? "Neutral briefing" : countryName(country) + " perspective")}"></audio><p class="small muted">${esc(data.cached ? "Cached ElevenLabs narration" : "ElevenLabs narration; now cached")} · Transcript below</p><p class="audio-transcript">${esc(data.transcript)}</p>`;
  } catch (e) {
    target.innerHTML = `<p class="error-inline">${esc((e as Error).message)}</p>`;
  }
}
document.addEventListener("pointerover", (e) => {
  const district = (e.target as HTMLElement).closest<HTMLElement>(
    "[data-district]",
  );
  if (district) focusDistrict(district.dataset.district!);
});
document.addEventListener("pointerout", (e) => {
  const district = (e.target as HTMLElement).closest<HTMLElement>(
    "[data-district]",
  );
  if (district && !district.contains((e as PointerEvent).relatedTarget as Node))
    focusDistrict("");
});
document.addEventListener("focusin", (e) => {
  const district = (e.target as HTMLElement).closest<HTMLElement>(
    "[data-district]",
  );
  if (district) focusDistrict(district.dataset.district!);
});
document.addEventListener("focusout", (e) => {
  if ((e.target as HTMLElement).closest("[data-district]")) focusDistrict("");
});
document.addEventListener("click", (event) => {
  const button = (event.target as HTMLElement).closest<HTMLElement>("button");
  if (!button) return;
  if (button.dataset.close) {
    closeDialog(button.dataset.close);
    return;
  }
  if (button.dataset.demo) {
    const d = config.demos.find((d) => d.id === button.dataset.demo)!;
    if (el<HTMLDialogElement>("palette").open) closeDialog("palette");
    setMode("demo");
    void analyze(d.query, true);
    return;
  }
  if (button.dataset.mode) {
    setMode(button.dataset.mode);
    return;
  }
  if (button.dataset.theme) {
    selectedTheme = button.dataset.theme as Theme;
    renderResults();
    document
      .querySelector<HTMLButtonElement>(`[data-theme="${selectedTheme}"]`)
      ?.focus();
    return;
  }
  if (button.dataset.evidence) {
    const [c, t] = button.dataset.evidence.split(":");
    evidence(c, t as Theme);
    return;
  }
  if (button.dataset.filter !== undefined) {
    selectedCountry = button.dataset.filter;
    renderResults();
    document
      .querySelector<HTMLButtonElement>(`[data-filter="${selectedCountry}"]`)
      ?.focus();
    return;
  }
  if (button.dataset.audio) {
    void playAudio(button.dataset.audio);
    return;
  }
  if (button.id === "focus-outlets") {
    selectedCountry = button.dataset.country!;
    closeDialog("evidence");
    renderResults();
    el("outlet-list").scrollIntoView({
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
    return;
  }
  if (button.id === "about-btn") {
    openDialog("about");
    return;
  }
  if (button.id === "audio-summary") {
    void playAudio("summary");
    return;
  }
  if (button.id === "cancel") {
    controller?.abort();
    return;
  }
  if (button.id === "export") {
    window.print();
    return;
  }
  if (button.id === "share") {
    if (!navigator.clipboard) {
      notice("Copy the URL from your address bar to share this report.");
      return;
    }
    void navigator.clipboard
      .writeText(location.href)
      .then(() =>
        notice(
          "Report link copied. It works while this server keeps its disk cache.",
        ),
      )
      .catch(() =>
        notice("Copy the URL from your address bar to share this report."),
      );
  }
});
document.addEventListener("change", (event) => {
  const input = event.target as HTMLInputElement;
  if (input.id === "simple") {
    simple = input.checked;
    renderResults();
    el("simple").focus();
  }
  if (input.id === "original") {
    original = input.checked;
    renderResults();
    el("original").focus();
  }
});
el("search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  void analyze(el<HTMLInputElement>("query").value.trim(), mode === "demo");
});
el<HTMLSelectElement>("language").addEventListener("change", async () => {
  language = el<HTMLSelectElement>("language").value;
  if (report) {
    const demo = config.demos.find((d) => d.query === report?.query);
    if (report.mode === "demo" && demo) {
      await analyze(demo.query, true);
    } else {
      notice(
        "Language changed. Run the search again to generate a source-linked briefing in this language.",
      );
    }
  }
});
el("palette-input").addEventListener("input", () =>
  renderPalette(el<HTMLInputElement>("palette-input").value),
);
document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    openDialog("palette");
    el("palette-input").focus();
  }
  if (
    el<HTMLDialogElement>("palette").open &&
    (e.key === "ArrowDown" || e.key === "ArrowUp")
  ) {
    e.preventDefault();
    const buttons = [
      ...el("palette-list").querySelectorAll<HTMLButtonElement>("button"),
    ];
    const idx = buttons.indexOf(document.activeElement as HTMLButtonElement);
    buttons[
      (idx + (e.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length
    ]?.focus();
  }
  if (
    el<HTMLDialogElement>("palette").open &&
    e.key === "Enter" &&
    document.activeElement === el("palette-input")
  ) {
    e.preventDefault();
    el("palette-list").querySelector<HTMLButtonElement>("button")?.click();
  }
});
for (const d of document.querySelectorAll<HTMLDialogElement>("dialog")) {
  d.addEventListener("click", (e) => {
    if (e.target === d) {
      const r = d.getBoundingClientRect();
      if (
        e.clientX < r.left ||
        e.clientX > r.right ||
        e.clientY < r.top ||
        e.clientY > r.bottom
      )
        d.close();
    }
  });
  d.addEventListener("close", () => focusedElement?.focus());
}
async function init() {
  try {
    const response = await fetch("/api/config");
    if (!response.ok)
      throw new Error("Backend unavailable. Start FastAPI on port 8000.");
    config = await response.json();
    renderDemos();
    setMode("demo");
    const { City } = await import("./city");
    const city = new City(
      el<HTMLCanvasElement>("city"),
      Object.keys(config.countries),
      () => ({
        theme: selectedTheme,
        scores: Object.fromEntries(
          Object.keys(config.countries).map((c) => [
            c,
            score(c, selectedTheme),
          ]),
        ),
        statuses,
        focused: hoveredCountry || selectedCountry,
        busy,
      }),
      (c) => report && evidence(c, selectedTheme),
      focusDistrict,
    );
    cityUpdate = () => city.invalidate();
    city.start();
    const id = new URLSearchParams(location.search).get("report");
    if (id) {
      const r = await fetch(`/api/reports/${encodeURIComponent(id)}`);
      if (r.ok) {
        report = await r.json();
        language = report!.language;
        el<HTMLSelectElement>("language").value = language;
        renderResults();
      } else
        notice(
          "This report is not cached on this server. Choose a story below.",
        );
    }
  } catch (e) {
    notice((e as Error).message, true);
  }
}
void init();
