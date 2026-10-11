# Browser performance — pending measurement

HTTP timings and DOM tests with mocked Canvas do not establish 60fps. Record on the intended mid-range laptop:

- Hardware / OS / browser:
- Viewport / DPR:
- Intro median / p95 frame duration / dropped frames:
- Results median / p95 frame duration / dropped frames:
- `window.newsBridgePerformance.canvasDrawP95Ms` (CPU draw only):
- Reduced motion and hidden-tab behavior checked:

Target: 16.67 ms total frame budget at 60 Hz. Current protections: capped DPR, bounded windows, cached skyline and lit bridge raster, hidden-tab cancellation, static reduced-motion rendering, no heavy dependencies. Actual browser visual, keyboard/screen-reader and audio checks are pending.
