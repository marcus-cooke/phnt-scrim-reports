# Changelog

## 0.1.3.1 — 9 November 2026

- Confirm the added recording as 8 November 2026 against RMNT and HTD, using WDL fixture #114 and user confirmation. Show the date and opponents in the selector, heading and downloads, retaining its existing share URL.
- Add the fixture's 19:00 GMT start, Ozeti map, Default zone, DayEarlyFog lighting, RMNT host and under-review league status. Keep league-listed faction assignments separate from the recorded round's colours and preserve observed player tags.

## 0.1.3.0 — 9 November 2026

- Add the undated WDL / Phantom scrim 2 recording from another PHNT POV, calibrated from its 1920 × 804 source. Verify PHNT as Blue / Lonestar and the 100–75–88 Blue–Red–Green result.
- Include five-second HUD sampling, two feed observations per second, 29 reviewed ticket anchors, 12 map snapshots, ten manually read PHNT scoreboard rows and ten visually reviewed feed examples.
- Require agreement between two English recognizers for player counts. Keep ambiguous Green 3/5 readings unavailable; verify sampled peaks of Blue 45, Red 41 and Green 41 against native footage.
- Correct sampling-bin offsets, retain source fingerprints and uncertainty, and distinguish sampled feed display episodes from final kills. The recording date and POV identity remain unconfirmed.
- Support additional matches in comparisons and targeted packaging without reprocessing the existing reports.

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
