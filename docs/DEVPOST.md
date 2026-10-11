# News Bridge
**Tagline:** One story. A world of perspectives.

## Inspiration
Everyone gets a different version of the same news. A student following a major world event may never see how another country’s coverage frames it. Reading six foreign news editions, translating the coverage, and comparing it fairly is a workflow almost nobody performs by hand. We built a bridge through it.

## What it does — Impact & Utility (25%)
Enter an event. News Bridge finds coverage across six news editions, translates the available text, compares emphasis, and creates a neutral source-linked briefing in your language. It helps students, teachers and curious readers ask better questions—not outsource their judgment. The product makes its sample size, missing coverage and evidence limits visible. Three captured stories work even when Wi-Fi or API quotas fail.

## How we built it — Technical Execution (25%)
An async Python/FastAPI pipeline retrieves country feeds in parallel with bounded timeouts. GNews/NewsData and Google News RSS provide discovery; trafilatura extracts accessible article text, while paywalled or inaccessible pages retain headline/excerpt evidence. Groq translates and returns strict JSON validated through Pydantic. A second evidence-validation layer rejects fabricated quotes and unsupported source IDs. Separate prompts and typed models keep interpretation distinct from fetching and presentation. Disk caches use stable SHA-256 keys and atomic writes; retry/backoff handles rate limits. ElevenLabs narration is cached, with no runtime speech spending in demos. Parsing, analysis, API and DOM tests cover meaningful failure paths.

## What makes it different — Creativity (25%)
The world becomes a night city. Each news edition is a district; every lit window is a perspective. The bridge lights as the city wakes. During live analysis districts reflect pipeline progress, and in results their light follows the selected theme. The visual is functional—not decoration. Evidence Lock connects every score to its exact quote. Claim Cross-check distinguishes factual common ground from editorial emphasis, while Missing Voices turns unrepresented perspectives into questions rather than accusations.

## The experience — Presentation (25%)
An original Canvas skyline anchors a restrained editorial interface: ink blue, sodium amber and bridge cyan; Bricolage Grotesque paired with Source Serif 4. The first-visit intro is skippable, honors reduced motion and pauses in hidden tabs. A labeled numeric heatmap supports keyboard users. Original headlines, source links and a persistent AI disclaimer keep the story honest. The repository includes four-command setup, an architecture diagram, acceptance/verification notes and a 2:30 features-and-code demo script.

## Challenges and what we learned
Structured JSON is not enough: an AI can satisfy the schema while inventing evidence. We added verbatim quote validation. Country filters do not establish publisher nationality, and shared wire copy is not independent verification. We label editions and sample boundaries rather than claiming to measure “national bias.” Free-tier token limits made pre-capture, compact synthesis inputs and cached narration engineering requirements, not afterthoughts.

## What’s next
Broader local publisher samples, relevance screening, original-publication resolution for RSS redirects, multilingual query expansion, and syndication detection. Before public hosting: per-user API budgets and stronger hosting security. We will measure real-browser animation performance and conduct keyboard/screen-reader usability checks with students.

## Built with
Python, FastAPI, asyncio, Pydantic, HTTPX, trafilatura, Groq, ElevenLabs, GNews/NewsData.io, Google News RSS, TypeScript, Vite, Canvas 2D.

## Submission checklist
- Public GitHub URL: https://github.com/svelteeeee/EvoHacks-Hackathon — verify public visibility and push finalized changes before submission.
- Live URL: private development preview only so far; use local run steps unless a public Python deployment is explicitly approved.
- Video: record and attach the 2:30 walkthrough; script is not the video.
- Screenshots: capture the real interface after browser review; do not substitute a mockup for proof.
- Final counts/timings: use the verified final test output and `docs/http-verification.json`, not draft numbers.
