# PHNT scrim reports

Static, evidence-linked reports for PHNT's recorded War Dogs scrims.

[Open the clan report](https://marcus-cooke.github.io/phnt-scrim-reports/) · [Release notes](CHANGELOG.md)

Choose a match to inspect ticket progression, sampled control, feed exchanges, team strength, map snapshots and selected source excerpts. The comparison view keeps PHNT's faction identity correct across both games, shows the verified result screens and provides a combined CSV/JSON download. Share links preserve the selected match and report section.

The report uses the [official Phantom Regiment branding](https://phantomwardogs.com/): original SVG emblem and wordmark, self-hosted Oxanium and Instrument Sans fonts, signal-red accents and graphite surfaces. The shared assets and source fingerprints live in `site/brand/`; faction colours retain their data meaning. Run `python tools/apply_brand.py` to apply brand-only updates without reprocessing footage, and `python tools/check_brand.py` to verify the assets and styling links.

| Recording | PHNT faction | Verified result | Report window |
| --- | --- | --- | --- |
| 24 October 2026 | Green / Manticore | Third place; 21 points | HUD scan from 08:00, plus earlier reviewed zero-score anchors |
| 25 October 2026 | Blue / Lonestar | Victory; 100 points | From video **05:00**, at 0–0–0 |

The 25 October recording begins with the tail of a preceding game, a round transition and setup. Everything before **300 seconds (05:00)** is excluded from that match's charts, statistics, downloads and hosted excerpts.

## Reading the reports

- **Team strength** means the small person-icon HUD count. A value **greater than 33** is flagged: 34 and above qualify; exactly 33 does not. Click a flagged observation or peak to inspect its screenshot.
- Timestamps are elapsed **recording time**, rather than wall time or an exact server-event clock. The comparison ticket curves align to the first observed non-zero score for any faction within each report window.
- Missing or unreadable readings remain unavailable. Gaps can split observed runs above 33; a run is not a measured continuous duration above the threshold.
- Feed charts contain manually reviewed sample entries and qualifying machine candidates. They measure extracted feed entries, **not verified final-kill totals**. OCR errors, missed rows and merged combat-state changes can affect the results.
- Map markers are anonymous observations from one POV. They do not establish continuous named-player routes. Faction colours can change between games.
- Sampling and extraction coverage differ between recordings. Do not treat the sampled feed totals as an overall performance comparison. Review flags and source evidence are retained alongside the data.

## Latest-game feed audit

The **25 October feed** uses 24,622 native observations at **four frames per second**, from recording time **300 to 6455.25 seconds**. Two English recognizers and temporal row tracking read the feed independently of ticket visibility. The earlier game's extraction retains its original sampling.

The latest export contains **1,610 accepted display episodes**: **1,540 paired entries** with known factions enter the charts, **43 single-name notices** remain separately labelled, and **27 paired entries** retain unresolved factions. Four entries are individually reviewed. These are extracted feed episodes, not verified final kills.

In 4.5 minutes of manually logged, readable reference footage, the automatic whole-game pipeline recovered **110 of 111 entries**, with **three duplicate fragments before separate visual corrections**. These development/diagnostic windows were used during refinement. Tolerant name matching measures episode recovery, not exact spelling, and this result is not a held-out test or a whole-game accuracy estimate. Three fragments were subsequently merged or excluded visually and one distorted entry was recovered manually; those decisions are logged separately from the automatic evaluation.

This release changes only the latest game's feed. The entire older-game dataset and both games' tickets, maps, map-symbol positions, scoreboard data and team-strength series remain unchanged, including every strictly-above-33 flag.

- [Accepted feed episodes CSV](docs/matches/2026-10-25/data/feed-events.csv)
- [Automatic validation JSON](docs/matches/2026-10-25/data/feed-validation.json) and [manual reference CSV](docs/matches/2026-10-25/data/manual-feed-reference.csv)
- [Visual review decisions CSV](docs/matches/2026-10-25/data/feed-manual-decisions.csv) and [extraction provenance JSON](docs/matches/2026-10-25/data/feed-provenance.json)
- [Dense-feed pipeline, dependencies and model provenance](tools/feed_analysis/README.md)

## Evidence and downloads

The public site contains compact screenshots with native feed and HUD strips, native row evidence for the latest feed, map snapshots, result screens, and selected ten-second H.264 excerpts with posters. Other timestamps retain screenshot evidence even when no hosted excerpt covers them. The original multi-gigabyte recordings and local OCR environments remain offline.

Per-match data is under `docs/matches/<date>/data/`; each match also has a `match-data.zip`. `docs/all-match-data.zip` combines both matches' exports. `source_image` and public `source_file` paths are relative to the corresponding match report. The exports distinguish accepted readings, manual records and unresolved review queues.

## Publish with GitHub Pages

This repository belongs to the personal account **[marcus-cooke](https://github.com/marcus-cooke)**. In repository **Settings → Pages**, select **Deploy from a branch**, branch **main**, folder **/docs**. The checked-in `docs/` folder is ready to serve, with `.nojekyll` and relative asset paths for the project-site URL. No application server, npm install or runtime video conversion is required.

The expected site address is `https://marcus-cooke.github.io/phnt-scrim-reports/`. The separate **Check static reports** workflow validates pushes to `main` and pull requests; it is not the publishing workflow.

## Preview and validate

From the repository root, using Python 3.13:

```sh
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000/`. Use an HTTP server rather than opening `index.html` directly, so embedded report navigation and origin checks behave consistently.

```sh
python tools/check_site.py
```

The dependency-free checker verifies local asset links, absence of local-only URLs in HTML, evidence availability, strict strength-threshold flags, faction mapping, clip sizes, and the 25 October round boundary. Browser behaviour and visual layout are checked separately.

## Optional: repackage local analysis

The published site needs no packaging dependencies. To regenerate it, `tools/build_site.py` requires Python, Pillow, OpenCV and imageio-ffmpeg, plus an NVIDIA CUDA/NVENC-capable setup for its selected clip-encoding command:

```sh
python -m pip install Pillow opencv-python imageio-ffmpeg
```

Supply two existing analysis folders, both original videos, and the report templates (`report-template.html`, `strength-panel.html`, `strength-ui.js`). Analysis folders must already contain their structured `data/match-data.json`, CSV exports, keyframes and selected evidence images. OCR extraction itself is not performed by this packager.

The optional **`--feed-data MATCH_ID=PATH`** argument supplies a staged replacement export for that match, including its dense-feed CSVs, validation and provenance. To retain the audited latest-game feed when rebuilding, pass its `feed-v2/staged-data/` folder. Omitting this argument uses the original analysis folder's dataset instead. The [dense-feed instructions](tools/feed_analysis/README.md) describe how to produce the staged export and keep automatic evaluation separate from visual decisions.

All CLI input paths resolve from the current working directory. For example, from this repository root, with inputs stored outside the checkout:

```sh
python tools/build_site.py --templates ../report-templates --analysis 2026-10-24=../analysis/24-oct --analysis 2026-10-25=../analysis/25-oct --video 2026-10-24=../recordings/24-oct.mp4 --video 2026-10-25=../recordings/25-oct.mp4 --feed-data 2026-10-25=../analysis/25-oct/feed-v2/staged-data
python tools/check_site.py
```

Review regenerated data and screenshots before publishing. The site shell source is `site/index.html`; match metadata and verified result values are in `matches.json`.
