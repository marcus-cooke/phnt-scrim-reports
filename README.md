# PHNT scrim reports

Static, evidence-linked reports for PHNT's recorded War Dogs scrims.

[Open the clan report](https://marcus-cooke.github.io/phnt-scrim-reports/) · [Release notes](CHANGELOG.md)

[Opponent scouting](https://marcus-cooke.github.io/phnt-scrim-reports/scouting/) adds a separate evidence-linked briefing for non-PHNT recordings. The first dossier covers Black Sails vs BNT / III vs OOPS / Merc, with 11 bounded tactical findings, 21 visually reviewed score anchors and a verified 100–98–99 Blue victory. Team filters, timestamped screenshots and data exports keep each interpretation inspectable. It is sampled agent review from one POV, not complete clan telemetry. See [scouting workflow and source fingerprints](tools/scouting/README.md).

Choose a match to inspect ticket progression, sampled control, feed exchanges, team strength, map snapshots and source screenshots. The comparison view keeps PHNT's faction identity correct across all four recordings, shows the verified result screens and provides a combined CSV/JSON download. Share links preserve the selected match and report section.

The report uses the [official Phantom Regiment branding](https://phantomwardogs.com/): original SVG emblem and wordmark, self-hosted Oxanium and Instrument Sans fonts, signal-red accents and graphite surfaces. The shared assets and source fingerprints are documented in [the brand notes](site/brand/README.md); faction colours retain their data meaning. Run `python tools/apply_brand.py` to apply brand-only updates without reprocessing footage, and `python tools/check_brand.py` to verify the assets and styling links.

| Recording | PHNT faction | Verified result | Report window |
| --- | --- | --- | --- |
| 24 October 2026 | Green / Manticore | Third place; 21 points | HUD scan from 08:00, plus earlier reviewed zero-score anchors |
| 25 October 2026 | Blue / Lonestar | Victory; 100 points | From video **05:00**, at 0–0–0 |
| 8 November 2026 · vs RMNT / HTD | Blue / Lonestar | Victory; 100 points | From recording start; active HUD through about 1:51:48 |
| 22 November 2026 · vs AK / PMF | Blue / Lonestar | Second place; 96 points | Active HUD from **06:10** to 2:16:45; result at 2:17:00 |

The 25 October recording begins with the tail of a preceding game, a round transition and setup. Everything before **300 seconds (05:00)** is excluded from that match's charts, statistics, downloads and evidence.

## Reading the reports

The separate [opponent scouting collection](docs/scouting/index.html) contains
five recordings, including Adversary's Humvee POV, WOUF's Tower 2 defence, Silk's
competitive pilot POV and two Black Sails frontline recordings. Each dossier links
observations, interpretations and proposed responses to native screenshots,
reviewed score anchors and CSV/JSON exports. The
[cross-recording preparation themes](docs/scouting/patterns/index.html) link back
to their evidence. These games do not enter PHNT's match-comparison catalog.

The four added recordings have 33 bounded findings and 57 reviewed score anchors.
Silk's competitive evidence starts at 1:24:00; preceding public play and setup are
excluded. Coverage is sampled agent review, not continuous telemetry. Match dates
and transfer to current rosters/patches remain unverified. See the
[scouting workflow](tools/scouting/README.md) for acquisition and review details.

- **Team strength** means the small person-icon HUD count. A value **greater than 33** is flagged: 34 and above qualify; exactly 33 does not. Click a flagged observation or peak to inspect its screenshot.
- Timestamps are elapsed **recording time**, rather than wall time or an exact server-event clock. The comparison ticket curves align to the first observed non-zero score for any faction within each report window.
- Missing or unreadable readings remain unavailable. Gaps can split observed runs above 33; a run is not a measured continuous duration above the threshold.
- Feed charts contain manually reviewed sample entries and qualifying machine candidates. They measure extracted feed entries, **not verified final-kill totals**. OCR errors, missed rows and merged combat-state changes can affect the results.
- Map markers are anonymous observations from one POV. They do not establish continuous named-player routes. Faction colours can change between games.
- Sampling and extraction coverage differ between recordings. Do not treat the sampled feed totals as an overall performance comparison. Review flags and source evidence are retained alongside the data.

## WDL / Phantom scrim 2

The additional member recording is **1920 × 804**, about 1 hour 53 minutes long. The [WDL fixture #114](https://wardogsleague.net/matches/cmw7udybd00mzp701dzl4rk0l) identifies **8 November 2026**, **19:00 GMT**, **PHNT vs Remnant (RMNT) and HaiiTeD (HTD)**: a friendly on **Ozeti**, Default zone, DayEarlyFog, hosted by RMNT. The league result was **under review** when checked on 9 November. Its listed faction assignments differ from this recorded round; report charts follow the footage. POV identity remains unconfirmed. The result screen verifies **Blue 100, Red 75, Green 88**. The report includes 29 visually checked score anchors, five-second HUD observations, two feed observations per second, 12 map snapshots and ten clear PHNT scoreboard rows from the final screens.

Small HUD text is enlarged to align the existing coordinate layout; enlargement creates no new detail. Player counts require agreement between two English recognizers at confidence ≥0.92 in both. Ambiguous first-digit 3/5 readings on Green remain unavailable. Selected source frames verify sampled peaks of **Blue 45, Red 41 and Green 41**. Sampling-bin timing offsets are corrected, with about one source frame of remaining uncertainty.

Ten feed entries were checked visually in selected source windows, with decisions logged separately from automatic output. This is a spot check, not a whole-match accuracy estimate. Unreadable pairs and isolated one-name notices stay unresolved. Feed episodes are not verified final kills.

- [Recording provenance and calibration](docs/matches/wdl-phantom-scrim-2/data/recording-provenance.json)
- [Count recognizer agreement and disagreements](docs/matches/wdl-phantom-scrim-2/data/strength-model-reads.csv)
- [Visual feed review decisions](docs/matches/wdl-phantom-scrim-2/data/feed-manual-decisions.csv)
- [Recording-specific processing scripts](tools/recording_import/README.md)

## 22 November PHNT recording

The native **3440 × 1440, 60 FPS** recording runs for 8316.683 seconds. The report excludes the preceding round and transition before **370 seconds (06:10)**. Active-round sampling covers 370–8205 seconds; the final screen at **8220 seconds (2:17:00)** verifies **Blue 96, Red 100, Green 96**, with PHNT awarded second place. Visible tags and glyphs identify PHNT as Blue, AK/AKP as Red and PMF as Green. No per-player final scoreboard totals were transcribed.

Coverage includes **31,340 feed frames at 4 Hz**, **1,567 five-second HUD samples**, **29 reviewed ticket anchors** and **12 map snapshots**. Of 6,611 feed candidates, **2,125 display episodes** are accepted and **2,064 paired entries** enter faction charts; eight entries are individually reviewed. These are feed displays, not verified final kills. The automatic pass recovered **25 of 26 readable paired episodes** across three 30-second development windows. Tolerant name matching does not establish exact spelling or whole-match accuracy. One manual recovery and four duplicate exclusions are logged separately and do not change that automatic result.

There are **112 accepted strength observations strictly above 33**, with reviewed peaks of **Blue 47, Red 41 and Green 42**. Machine readings require two English recognizers to agree at confidence ≥0.92 in both; unknown readings remain gaps.

- [Recording provenance](docs/matches/2026-11-22/data/recording-provenance.json) and [count recognition audit](docs/matches/2026-11-22/data/strength-model-reads.csv)
- [Feed candidates and decisions](docs/matches/2026-11-22/data/feed-events.csv), [automatic validation](docs/matches/2026-11-22/data/feed-validation.json) and [manual reference](docs/matches/2026-11-22/data/manual-feed-reference.csv)
- [Separate visual decisions](docs/matches/2026-11-22/data/feed-manual-decisions.csv) and [native processing workflow and review inputs](tools/recording_import/README.md#22-november-phnt-clan-recording)

## 25 October feed audit

The **25 October feed** uses 24,622 native observations at **four frames per second**, from recording time **300 to 6455.25 seconds**. Two English recognizers and temporal row tracking read the feed independently of ticket visibility. The earlier game's extraction retains its original sampling.

The 25 October export contains **1,610 accepted display episodes**: **1,540 paired entries** with known factions enter the charts, **43 single-name notices** remain separately labelled, and **27 paired entries** retain unresolved factions. Four entries are individually reviewed. These are extracted feed episodes, not verified final kills.

In 4.5 minutes of manually logged, readable reference footage, the automatic whole-game pipeline recovered **110 of 111 entries**, with **three duplicate fragments before separate visual corrections**. These development/diagnostic windows were used during refinement. Tolerant name matching measures episode recovery, not exact spelling, and this result is not a held-out test or a whole-game accuracy estimate. Three fragments were subsequently merged or excluded visually and one distorted entry was recovered manually; those decisions are logged separately from the automatic evaluation.

The 25 October feed audit preserved the entire 24 October dataset and both October games' tickets, maps, map-symbol positions, scoreboard data and team-strength series, including every strictly-above-33 flag.

- [Accepted feed episodes CSV](docs/matches/2026-10-25/data/feed-events.csv)
- [Automatic validation JSON](docs/matches/2026-10-25/data/feed-validation.json) and [manual reference CSV](docs/matches/2026-10-25/data/manual-feed-reference.csv)
- [Visual review decisions CSV](docs/matches/2026-10-25/data/feed-manual-decisions.csv) and [extraction provenance JSON](docs/matches/2026-10-25/data/feed-provenance.json)
- [Dense-feed pipeline, dependencies and model provenance](tools/feed_analysis/README.md)

## Evidence and downloads

The public site contains compact screenshots with native feed and HUD strips, native row evidence, map snapshots and result screens. All 61 previously hosted MP4 excerpts have been removed; reports distribute screenshots and data only. The original recordings, archived excerpts and local OCR environments remain offline. All 12,789 older screenshots and older non-clip gameplay data are preserved.

Per-match data is under `docs/matches/<match-id>/data/`; each match also has a `match-data.zip`. `docs/all-match-data.zip` combines all four PHNT recordings' exports. `source_image` and public `source_file` paths are relative to the corresponding match report. The exports distinguish accepted readings, manual records and unresolved review queues.

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

The dependency-free checker verifies local asset links, absence of local-only URLs in HTML, evidence availability, strict strength-threshold flags, faction mapping, absence of hosted MP4s, the 950 MiB package budget, and recording-specific round boundaries. Browser behaviour and visual layout are checked separately.

## Optional: repackage local analysis

The published site needs no packaging dependencies. To regenerate it, `tools/build_site.py` requires Python, Pillow, OpenCV and imageio-ffmpeg:

```sh
python -m pip install Pillow opencv-python imageio-ffmpeg
```

Supply each selected match's existing analysis folder and original video, plus the report templates (`report-template.html`, `strength-panel.html`, `strength-ui.js`). Analysis folders must already contain their structured `data/match-data.json`, CSV exports, keyframes and selected evidence images. OCR extraction itself is not performed by this packager.

The optional **`--feed-data MATCH_ID=PATH`** argument supplies a staged replacement export for that match, including its dense-feed CSVs, validation and provenance. To retain the audited 25 October feed when rebuilding, pass its `feed-v2/staged-data/` folder. Omitting this argument uses the original analysis folder's dataset instead. The [dense-feed instructions](tools/feed_analysis/README.md) describe how to produce the staged export and keep automatic evaluation separate from visual decisions.

The packager defaults to screenshot-only reports. Its legacy `--include-clips` option requires NVIDIA CUDA/NVENC for encoding and is incompatible with the current public-site checks. Use repeatable `--only MATCH_ID` arguments to rebuild selected recordings while retaining existing reports; without `--only`, inputs are required for every match in `matches.json`.

All CLI input paths resolve from the current working directory. For example, from this repository root, with inputs stored outside the checkout:

```sh
python tools/build_site.py --only 2026-10-24 --only 2026-10-25 --templates ../report-templates --analysis 2026-10-24=../analysis/24-oct --analysis 2026-10-25=../analysis/25-oct --video 2026-10-24=../recordings/24-oct.mp4 --video 2026-10-25=../recordings/25-oct.mp4 --feed-data 2026-10-25=../analysis/25-oct/feed-v2/staged-data
python tools/check_site.py
```

Review regenerated data and screenshots before publishing. The site shell source is `site/index.html`; match metadata and verified result values are in `matches.json`.
