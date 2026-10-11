# News Bridge — 2:30 demo script

**Record locally.** Use 1440×900, zoom 100%, notifications off. Start both servers. Open a fresh tab/session or remove `newsbridge-intro` from sessionStorage before recording. Pick COP28 in English. Use captured data, openly labeled; no pretend live progress. Have the editor open at `backend/pipeline.py`, `backend/analysis.py`, and `frontend/src/city.ts`. Never show `.env` or terminals containing credentials. Test audio and keep its clip under five seconds.

| Time | Screen / action | Narration |
|---|---|---|
| **0:00–0:15** | Darkness → windows light → bridge. Let the 5.5-second intro breathe. | “Your news feed is one window into the world. But the same event can look completely different from another window. News Bridge lights up those perspectives—and builds a bridge between them.” |
| **0:15–0:30** | Search and cached story suggestions. | “Reading foreign coverage means finding sources, translating, and comparing what each emphasizes. Almost nobody does that by hand. Our AI pipeline does it for students, teachers, and anyone trying to understand beyond their feed.” |
| **0:30–0:50** | Select COP28. Show six editions, cited summary. | “Here’s COP28. This is a captured demo of real source headlines and Groq analysis, so it works without a feed or API call. The neutral briefing only uses claims linked to these sources. We call them news editions—not the opinions of whole countries.” |
| **0:50–1:15** | Money shot: select diplomacy → accountability → economy. Move over districts. | “The city is the comparison. Each district’s brightness follows its emphasis on the selected theme. Diplomacy, accountability, economy: one event, different editorial attention. Scores are qualitative and based only on the text we actually retrieved.” |
| **1:15–1:35** | Click nonzero heatmap cell. Show original quote, rationale, confidence, original link. | “A pretty chart isn’t enough. Evidence Lock opens the original quote behind every score. This demo uses headlines, so confidence is deliberately limited. You can read the source, switch the headline language, and question the AI’s interpretation.” |
| **1:35–1:50** | Show claim cross-check and missing voices; optionally 3-second voice clip. | “We separate shared claims from different emphasis, and ask whose perspective isn’t visible. Absence in an excerpt isn’t proof of censorship. The briefing can also be explained simply, translated, or heard through cached multi-voice narration.” |
| **1:50–2:20** | **30-second code tour**. Pipeline → prompts/schema/evidence checks → Canvas. | “Here’s the code. FastAPI runs country workers concurrently, with timeouts and disk caches. Feeds fall back to RSS; trafilatura extracts readable text when available. Groq returns strict Pydantic JSON. We reject quotes missing from the source and unknown citations before displaying results. The city is our own seeded Canvas renderer: static layers are cached, reduced motion is supported, and hidden tabs pause.” |
| **2:20–2:30** | Return to city and neutral briefing. | “News Bridge doesn’t tell you what to believe. It makes it easier to see what you haven’t read. Media literacy starts when one window becomes a whole city.” |

## If a feature fails during rehearsal
- No sound: show written transcript; do not spend time fixing device output on camera.
- No live API: use cached events, as planned. Explain the real captured pipeline and show code.
- City slow: enable reduced motion/static skyline. The comparison remains in the labeled numeric matrix.
- No disagreement: say “different emphasis,” not “these sources contradict each other.”

## What to show judges in code
- `backend/pipeline.py`: country workers, `asyncio.gather`, timeouts, independent failure.
- `backend/models.py` + `backend/prompts/`: real schema and AI instructions.
- `backend/analysis.py`: `validate_evidence`, `validate_references`.
- `backend/cache.py`: stable keying, atomic replace, TTL.
- `frontend/src/city.ts`: seeded rendering, static layer, accessibility/motion lifecycle.

Target spoken word count ~340; rehearse against the clock. Video file/link is still to be recorded by the team.
