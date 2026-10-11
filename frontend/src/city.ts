import type { Progress, Theme } from "./types";
type State = {
  theme: Theme;
  scores: Record<string, number | null>;
  statuses: Map<string, Progress>;
  focused: string;
  busy: boolean;
};
type Window = {
  x: number;
  y: number;
  country: number;
  delay: number;
  cool: boolean;
  flicker: number;
};
function seeded(seed: number) {
  return () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
}
export class City {
  private ctx: CanvasRenderingContext2D;
  private staticLayer = document.createElement("canvas");
  private windows: Window[] = [];
  private width = 0;
  private height = 0;
  private dpr = 1;
  private reduced = matchMedia("(prefers-reduced-motion: reduce)");
  private frame = 0;
  private last = 0;
  private elapsed = 0;
  private intro = true;
  private dirty = true;
  private samples: number[] = [];
  private litBridge = document.createElement("canvas");
  private names = [
    "United States",
    "United Kingdom",
    "France",
    "Germany",
    "Japan",
    "India",
  ];
  constructor(
    private canvas: HTMLCanvasElement,
    private countries: string[],
    private state: () => State,
    private choose: (c: string) => void,
    private hover: (c: string) => void,
  ) {
    this.ctx = canvas.getContext("2d", { alpha: false })!;
    try {
      this.intro = sessionStorage.getItem("newsbridge-intro") !== "seen";
    } catch {
      this.intro = true;
    }
    if (this.reduced.matches) this.intro = false;
    new ResizeObserver(() => {
      this.resize();
      this.invalidate();
    }).observe(canvas);
    document.addEventListener("visibilitychange", () => {
      cancelAnimationFrame(this.frame);
      this.last = 0;
      if (!document.hidden) this.loop(performance.now());
    });
    this.reduced.addEventListener("change", () => {
      if (this.reduced.matches) this.skip();
      this.invalidate();
    });
    canvas.addEventListener("click", (e) => {
      if (this.intro) {
        this.skip();
        return;
      }
      const r = canvas.getBoundingClientRect();
      this.choose(
        this.countries[
          Math.min(
            this.countries.length - 1,
            Math.floor(
              ((e.clientX - r.left) / r.width) * this.countries.length,
            ),
          )
        ],
      );
    });
    canvas.addEventListener("mousemove", (e) => {
      if (this.intro) return;
      const r = canvas.getBoundingClientRect();
      this.hover(
        this.countries[
          Math.min(5, Math.floor(((e.clientX - r.left) / r.width) * 6))
        ],
      );
      canvas.title =
        this.countries[
          Math.min(5, Math.floor(((e.clientX - r.left) / r.width) * 6))
        ].toUpperCase() + " district · click to inspect evidence";
    });
    canvas.addEventListener("mouseleave", () => this.hover(""));
    document
      .getElementById("skip-intro")!
      .addEventListener("click", () => this.skip());
    document.addEventListener("keydown", (e) => {
      if (this.intro && !e.metaKey && !e.ctrlKey && !e.altKey) {
        this.skip();
      }
    });
    document.addEventListener(
      "pointerdown",
      (e) => {
        if (this.intro && (e.target as HTMLElement).id !== "skip-intro")
          this.skip();
      },
      { capture: true },
    );
  }
  start() {
    this.resize();
    if (this.intro) {
      document.body.classList.add("intro");
      document.getElementById("skip-intro")!.hidden = false;
    } else {
      this.elapsed = 6000;
      this.remember();
    }
    this.loop(performance.now());
  }
  invalidate() {
    this.dirty = true;
    if (!document.hidden) {
      cancelAnimationFrame(this.frame);
      this.loop(performance.now());
    }
  }
  private remember() {
    try {
      sessionStorage.setItem("newsbridge-intro", "seen");
    } catch {
      /* Storage disabled: the skip button still works. */
    }
  }
  private skip() {
    if (!this.intro) return;
    this.intro = false;
    this.elapsed = 6000;
    document.body.classList.remove("intro", "wordmark", "search-ready");
    document.getElementById("skip-intro")!.hidden = true;
    this.remember();
    this.dirty = true;
  }
  private resize() {
    const r = this.canvas.getBoundingClientRect();
    this.width = r.width;
    this.height = r.height;
    this.dpr = Math.min(devicePixelRatio || 1, 1.5);
    for (const c of [this.canvas, this.staticLayer, this.litBridge]) {
      c.width = Math.round(this.width * this.dpr);
      c.height = Math.round(this.height * this.dpr);
    }
    this.windows = [];
    this.build();
    this.dirty = true;
  }
  private build() {
    const c = this.staticLayer.getContext("2d")!;
    c.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    const w = this.width,
      h = this.height,
      water = h * 0.79;
    const rand = seeded(242);
    c.fillStyle = "#080f1c";
    c.fillRect(0, 0, w, h);
    const sky = c.createLinearGradient(0, 0, 0, water);
    sky.addColorStop(0, "#080f1c");
    sky.addColorStop(0.75, "#101b2b");
    sky.addColorStop(1, "#1a2435");
    c.fillStyle = sky;
    c.fillRect(0, 0, w, water);
    for (let i = 0; i < 70; i++) {
      c.fillStyle = `rgba(183,205,230,${rand() * 0.35})`;
      c.fillRect(rand() * w, rand() * h * 0.5, 1, 1);
    }
    for (let depth = 0; depth < 3; depth++) {
      let x = -15;
      while (x < w) {
        const bw = (18 + rand() * 35) * (depth === 2 ? 1.15 : 1),
          bh = 35 + rand() * 115 + depth * 13;
        const y = water - bh - depth * 8;
        c.fillStyle = ["#182438", "#111d30", "#0b1525"][depth];
        c.fillRect(x, y, bw, bh + depth * 8);
        c.fillStyle = ["#1c2940", "#172238", "#122038"][depth];
        c.fillRect(x, y, 2, bh);
        if (rand() > 0.7) {
          c.fillRect(x + bw * 0.35, y - 10, bw * 0.3, 10);
          c.fillRect(x + bw * 0.5, y - 20, 1, 20);
        } else if (rand() > 0.5) {
          c.beginPath();
          c.moveTo(x + bw * 0.5, y - 16);
          c.lineTo(x + bw * 0.15, y);
          c.lineTo(x + bw * 0.85, y);
          c.fill();
        }
        if (depth > 0) {
          for (let wx = x + 6; wx < x + bw - 4; wx += 7) {
            for (let wy = y + 8; wy < water - 5; wy += 10) {
              if (rand() > 0.36)
                this.windows.push({
                  x: wx,
                  y: wy,
                  country: Math.min(5, Math.max(0, Math.floor((wx / w) * 6))),
                  delay: ((wx / w) * 0.4 + rand() * 0.6) * 2800 + 500,
                  cool: rand() > 0.9,
                  flicker: rand(),
                });
            }
          }
        }
        x += bw + 3 + rand() * 7;
      }
    }
    [0.09, 0.29, 0.48, 0.66, 0.82, 0.94].forEach((fraction, i) => {
      const x = w * fraction;
      const tall = 110 + (i % 3) * 18;
      const y = water - tall;
      c.fillStyle = "#0b1525";
      if (i % 3 === 0) {
        c.fillRect(x - 5, y, 10, tall);
        c.fillRect(x - 15, y + 18, 30, 7);
        c.fillRect(x, y - 28, 1, 28);
      } else if (i % 3 === 1) {
        c.fillRect(x - 15, y + 20, 30, tall - 20);
        c.beginPath();
        c.arc(x, y + 20, 15, Math.PI, 0);
        c.fill();
        c.fillRect(x, y - 4, 1, 20);
      } else {
        for (let j = 0; j < 4; j++)
          c.fillRect(x - 16 + j * 3, y + j * 13, 32 - j * 6, tall - j * 13);
      }
    });
    c.fillStyle = "#070e18";
    c.fillRect(0, water, w, h - water);
    const waterGradient = c.createLinearGradient(0, water, 0, h);
    waterGradient.addColorStop(0, "#152338");
    waterGradient.addColorStop(1, "#080f1c");
    c.fillStyle = waterGradient;
    c.fillRect(0, water, w, h - water);
    this.bridge(c, 1, "#29354a");
    const bridgeContext = this.litBridge.getContext("2d")!;
    bridgeContext.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    bridgeContext.clearRect(0, 0, w, h);
    this.bridge(bridgeContext, 1, "#75dce5");
  }
  private bridge(c: CanvasRenderingContext2D, alpha: number, color: string) {
    const w = this.width,
      h = this.height;
    const road = h * 0.765,
      left = w * 0.16,
      right = w * 0.84,
      top = h * 0.4;
    c.save();
    c.globalAlpha = alpha;
    c.strokeStyle = color;
    c.lineWidth = 1;
    c.beginPath();
    c.moveTo(0, road);
    c.lineTo(w, road);
    c.stroke();
    c.lineWidth = 3;
    c.beginPath();
    c.moveTo(left, road + 30);
    c.lineTo(left, top);
    c.moveTo(right, road + 30);
    c.lineTo(right, top);
    c.stroke();
    c.lineWidth = 1;
    c.beginPath();
    c.moveTo(0, road - 10);
    c.quadraticCurveTo(left * 0.5, road - 35, left, top);
    c.quadraticCurveTo(w * 0.5, road + 36, right, top);
    c.quadraticCurveTo(w * 0.92, road - 35, w, road - 10);
    c.stroke();
    for (let x = left; x <= right; x += w / 44) {
      const t = (x - left) / (right - left),
        y = top + 4 * t * (1 - t) * (road + 36 - top) * 0.5;
      c.beginPath();
      c.moveTo(x, y);
      c.lineTo(x, road);
      c.stroke();
    }
    c.restore();
  }
  private loop = (now: number) => {
    if (document.hidden) return;
    const dt = this.last ? Math.min(now - this.last, 40) : 0;
    this.last = now;
    this.elapsed += dt;
    if (this.intro && this.elapsed > 5500) this.skip();
    if (this.intro && this.elapsed > 3300)
      document.body.classList.add("wordmark");
    if (this.intro && this.elapsed > 4400)
      document.body.classList.add("search-ready");
    const before = performance.now();
    if (!this.reduced.matches || this.dirty) this.draw(now);
    this.samples.push(performance.now() - before);
    if (this.samples.length > 180) this.samples.shift();
    (
      window as unknown as { newsBridgePerformance: unknown }
    ).newsBridgePerformance = {
      canvasDrawP95Ms:
        [...this.samples].sort((a, b) => a - b)[
          Math.floor(this.samples.length * 0.95)
        ] ?? 0,
      windows: this.windows.length,
      dpr: this.dpr,
      frameBudgetMs: 16.67,
    };
    this.dirty = false;
    if (!this.reduced.matches) this.frame = requestAnimationFrame(this.loop);
  };
  private draw(now: number) {
    const c = this.ctx,
      w = this.width,
      h = this.height,
      water = h * 0.79;
    const state = this.state();
    c.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    c.drawImage(this.staticLayer, 0, 0, w, h);
    const countryAlpha: number[] = [];
    this.countries.forEach((country, i) => {
      let intensity = 0.4;
      const s = state.statuses.get(country)?.stage;
      if (state.busy)
        intensity =
          s === "ready"
            ? 0.85
            : s === "analyzing" || s === "translating"
              ? 0.4 + Math.sin(now / 400) * 0.2
              : s === "fetching"
                ? 0.12
                : 0.03;
      else if (
        state.scores[country] !== null &&
        state.scores[country] !== undefined
      )
        intensity = 0.12 + (state.scores[country]! / 100) * 0.88;
      if (state.focused && state.focused !== country) intensity *= 0.35;
      countryAlpha.push(intensity);
      if (!this.intro) {
        const glow = c.createRadialGradient(
          ((i + 0.5) * w) / 6,
          water - 45,
          5,
          ((i + 0.5) * w) / 6,
          water - 45,
          w / 6,
        );
        glow.addColorStop(0, `rgba(245,187,103,${intensity * 0.055})`);
        glow.addColorStop(1, "rgba(245,187,103,0)");
        c.fillStyle = glow;
        c.fillRect((i * w) / 6, 0, w / 6, water);
      }
    });
    c.fillStyle = "#f5bb67";
    for (const win of this.windows) {
      let alpha = countryAlpha[win.country];
      if (this.intro) {
        const t = Math.max(0, Math.min(1, (this.elapsed - win.delay) / 950));
        alpha = t * t * 0.8;
      }
      if (!this.reduced.matches && win.flicker > 0.985)
        alpha *= 0.7 + 0.3 * Math.sin(now / 630 + win.delay);
      c.globalAlpha = alpha;
      c.fillStyle = win.cool ? "#b8dae7" : "#f5bb67";
      c.fillRect(win.x, win.y, 2.4, 3.7);
      if (win.flicker > 0.94 && alpha > 0.15) {
        c.globalAlpha = alpha * 0.12;
        const reflected = water + (water - win.y) * 0.3;
        c.fillRect(
          win.x + (this.reduced.matches ? 0 : Math.sin(now / 1400 + win.x) * 2),
          reflected,
          3,
          6,
        );
      }
    }
    c.globalAlpha = 1;
    const bridgeProgress = this.intro
      ? Math.max(0, Math.min(1, (this.elapsed - 2300) / 2000))
      : 1;
    if (bridgeProgress > 0) {
      c.save();
      c.beginPath();
      c.rect(0, 0, w * bridgeProgress, h);
      c.clip();
      c.globalAlpha = this.intro ? 0.7 : 0.5;
      c.drawImage(this.litBridge, 0, 0, w, h);
      c.restore();
    }
    if (!this.reduced.matches && (!this.intro || this.elapsed > 3300)) {
      c.fillStyle = "#f5bb67";
      for (let i = 0; i < 12; i++) {
        const x =
          (((now * 0.022 * (i % 2 ? 1 : -1) + (i * w) / 12) % w) + w) % w;
        c.globalAlpha = 0.65;
        c.fillRect(x, h * 0.765 + (i % 2 ? 2 : -2), 3, 1);
      }
    }
    c.globalAlpha = 1;
    if (!this.intro) {
      c.textAlign = "center";
      c.font = '9px "Bricolage Grotesque", sans-serif';
      this.countries.forEach((country, i) => {
        c.fillStyle = state.focused === country ? "#f5bb67" : "#a3adbd";
        c.fillText(
          w < 700 ? country.toUpperCase() : this.names[i],
          ((i + 0.5) * w) / 6,
          h * 0.965,
        );
      });
    }
    if (this.intro) {
      c.fillStyle = `rgba(2,5,12,${Math.max(0, 1 - this.elapsed / 1500) * 0.95})`;
      c.fillRect(0, 0, w, h);
    }
  }
}
