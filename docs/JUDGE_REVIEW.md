# Judge review — provisional, evidence-based

Scores are an engineering self-review, not actual judge results. Equal weighting as specified.

| Criterion | Score / 10 | Strength | Weakness |
|---|---:|---|---|
| Impact & Utility | 8 | Automates a difficult cross-language reading workflow; linked sources and useful questions | Small headline-only demo samples; no user study or relevance screening |
| Technical Execution | 8 | Actual Groq/NewsData/ElevenLabs calls, strict schemas plus evidence checks, async workers, disk caches and tests | Final full-text live run blocked by exhausted daily Groq quota; real-browser 60fps/audible playback unverified; quotas and source-nationality resolution not production-ready |
| Creativity | 9 | The city is intro, workflow state and emphasis map; Evidence Lock and Missing Voices reinforce the metaphor | No historical evolution or syndication fingerprint |
| Presentation | **6 before documentation** | Distinctive editorial direction and quiet surrounding UI | No README setup/code narrative, demo script, or submission checklist initially; actual screenshot/video still pending |

## Weakest criterion repaired: Presentation
Added four-command setup, architecture diagram, explicit AI workflow, limitations/provenance, a timed 2:30 feature-and-code script, judging-mapped Devpost draft, and a release checklist. Removed “country opinion” implications, made missing keys visible, labeled confidence as uncalibrated evidence sufficiency, and kept the same city in the result comparison rather than hiding the money shot above the fold. Both screenshot and actual video recording are tracked as pending instead of invented accomplishments.

**Revised Presentation: 8/10 if browser review confirms layout; actual media capture still needed.**

## Substance repair completed
The initial RSS sampling included UN/advocacy publishers and an English Reuters headline in the Japanese edition. Those were honestly labeled editions but weaken the pitch. The flagship demo refinement now has 11 linked headlines across six editions, including original Japanese and Hindi scripts, using local-language queries and up to two outlets per edition. It remains a sample, not national consensus. Recapture also exposed real free-tier token rate limits; compact synthesis inputs and low reasoning effort reduce output truncation without weakening validation.

## Submission blockers, not hidden failures
- Public repo visibility/commit/push has not been authorized or verified.
- Actual demo video and screenshot/GIF have not been recorded.
- Real-browser mobile/keyboard/audio review and mid-range laptop frame measurement are pending user checks.
- Exposed keys must be rotated. Before public live hosting, add visitor budgets/access control.

## Final verification limitations
Groq daily token quota exhausted during final full-text smoke verification. Full-article JSON output initially truncated; passage/output bounds were repaired, but the repaired live run cannot be confirmed until quota resets. Cached genuine Groq outputs all validate. ElevenLabs quota stopped generation at 9,889/10,000 characters; refined COP28 has four current tracks, Moon/Olympics seven each. No fake or mismatched audio is substituted. Revised Technical Execution is **7/10 pending the live rerun**, rather than claiming production reliability.
