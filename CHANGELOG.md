# Changelog

## 0.1.2.0 — 26 October 2026

- Re-extract the latest game's feed from 24,622 native observations at four frames per second, independently of ticket visibility, using two English recognizers and temporal row tracking.
- Show 1,610 accepted feed episodes: 1,540 paired exchanges enter the faction/activity charts, 43 single-name notices remain separately labelled, and 27 paired entries retain unresolved factions.
- Retain source-frame timestamps, native row evidence, OCR aliases, review queues, and separately logged visual decisions. Preserve the four individually reviewed entries.
- Add the sample-extraction comparison and downloadable automatic validation: 110 of 111 readable entries recovered in the 4.5 minutes used during refinement, with three duplicate fragments before visual correction. These are not final-kill totals or a whole-game accuracy estimate.
- Keep the earlier game's data and both games' tickets, maps, map-symbol positions, scoreboard data and team-strength series unchanged, including every strictly-above-33 flag.
- Include the analysis scripts, model provenance and manual reference samples for inspecting the method.

## 0.1.1 — 25 October 2026

- Match the official Phantom Regiment brand with its original SVG logo lockup, Oxanium headings and navigation, Instrument Sans body text, signal-red accents and graphite surfaces.
- Self-host the exact reference font files and retain their licence notices. Share one brand stylesheet across the report shell and both matches.
- Keep game-faction colours and all extracted match data intact. Keep report tabs visible when opening a shared link.

## 0.1.0 — 25 October 2026

- Browse both recorded scrims in one shareable report, with the correct PHNT faction and verified result for each match.
- Compare PHNT ticket progression and peak observed strength across matches.
- Inspect team-strength readings above 33, feed exchanges, map snapshots and supporting screenshots; play selected portable source excerpts.
- Download per-match or combined CSV/JSON data, with uncertainty and review status preserved.
- Exclude the preceding game's tail and transition from the 25 October report by starting its dataset at video 05:00 and 0–0–0.

### For contributors

- Serve the checked-in `docs/` package with GitHub Pages from `main` and `/docs`.
- Validate static assets, threshold flags, faction identity and the new-round boundary with the dependency-free Python checker and GitHub Actions workflow.
