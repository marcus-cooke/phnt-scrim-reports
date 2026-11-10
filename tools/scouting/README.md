# Opponent scouting

The separate static route is `docs/scouting/`, published at `/phnt-scrim-reports/scouting/`.
It does not insert a non-PHNT game into `matches.json` or the PHNT comparison catalog.
The report source is `site/scouting/`; `report.json` contains the reviewed curation.

The collection now also includes four separate dossiers under
`site/scouting/reports/<slug>.json` and `docs/scouting/<slug>/`:

| Recording ID | Route | POV | Completed Blue / Red / Green result |
| --- | --- | --- | --- |
| bgnko5c07sA | adversary-warcats-easy | ScottE / Adversary Humvee | 56 / 100 / 26 |
| 32Pahm05pjI | wouf-wduk-gili | Djoula / WOUF Tower 2 | 100 / 79 / 12 |
| 8RAytkF3sA0 | silk-first-competitive | Silk / Red TAB air unit | 100 / 94 / 40 |
| tyN7Tu7TAW8 | black-sails-everything-wrong | Mike Well Played / Blue Black Sails | 99 / 72 / 100 |

The four additions contain 33 findings, 57 score anchors and 87 evidence records.
Faction mappings come from final scoreboard icons/tags where possible, or the
uploader's explicit coalition description. Only Clans alongside Green WDG is
reported in Silk's spoken introduction; separate coalition-member actions remain
unknown. The actual match dates remain unconfirmed.

Silk's competitive analysis begins at **5040 seconds (1:24:00), 0-0-0**, and runs
through the completed result at **11210 seconds (3:06:50)**. Public play and
lobby/setup are excluded from competitive anchors, findings and hosted excerpts.
The competitive overview was visually inspected at one-minute intervals, with
denser reviewed sequences. Full-source download does not mean continuous watching.

These sources differ in language and download formats. ScottE has automatic
translated audio tracks: select the original English `140-12` for this recording,
not the first matching audio format. WOUF's source is French; English automatic
translation supplies leads, with the French original checked for tactical wording.
Retain any successfully fetched original captions if an optional translated
caption request returns 429; resume media independently rather than redownloading it.

The first dossier uses video `EaqOp1Fh7D0`, uploaded 4 October 2026 by Mike Well Played.
The match date is unconfirmed. Blue is Black Sails, Red BNT / III, Green OOPS / Merc,
following the uploader's description. Coalition members are not measured separately.
The completed result screen verifies Blue 100, Red 98, Green 99.

## Source acquisition

For authorised footage, install `yt-dlp[default]`, a supported JavaScript runtime
(this run used Node 22.14.0), and FFmpeg. Inspect formats before selecting them:

```powershell
python -m yt_dlp --js-runtimes node --no-playlist --list-formats 'https://www.youtube.com/watch?v=EaqOp1Fh7D0'
```

This recording's format 299 is 1920 × 1080 at 59.94 fps; format 140 is audio.
The IDs are specific to this source and must be checked for each new video.
Separate files avoid the temporary duplicate disk space needed for a full mux:

```powershell
python -m yt_dlp --js-runtimes node --no-playlist -f '299,140' --write-info-json --write-subs --write-auto-subs --sub-langs en --sub-format json3 --newline --progress-delta 10 -o 'analysis/black-sails-EaqOp1Fh7D0/source.%(format_id)s.%(ext)s' 'https://www.youtube.com/watch?v=EaqOp1Fh7D0'
```

The completed download was 3,345,474,275 video bytes and 90,970,642 audio bytes.
Source fingerprints:

- Video SHA256: `bee3f4fd127dee49ef7322518001cc9a92a2e219c75317f987100fa55e1940d6`
- Audio SHA256: `1674bc37dddf208fca5d388fdaa8148159921a93a7fd06212b7321fc8c0af659`

Full media, download metadata (including temporary media URLs), automatic captions,
ASR working output and contact sheets remain in an ignored local analysis folder.
Do not publish the raw downloader metadata or claim upload date is match date.

## Review and package

`prepare_review.py ROOT --video FILE --overview` extracts native frames, an index
with actual decoded timestamps, and a one-minute overview. Add `--range NAME:START:END:STEP`
or `--times SECONDS ...` for closer inspection. It requires OpenCV and Pillow.
Caption normalisation is also supported when `*.en.json3` exists in `ROOT`.

Read the transcript for candidate decisions, then inspect their source sequences.
Review the result animation through its completed totals. Keep observations,
interpretations, proposed responses and visibility limits separate. This process
is sampled agent review; it is not complete video telemetry or independent human review.

For the first dossier, curation lives in `site/scouting/report.json`. Initial media
packaging accepts a local `curated-report.json`, `frame-index.json`, `frames/` and
the two source media files:

```powershell
python tools/build_scouting.py --analysis 'C:/local-analysis/black-sails-EaqOp1Fh7D0'
```

`imageio-ffmpeg` is needed only for packaging the selected H.264/AAC excerpts.
Once evidence is packaged, editing the page, styling or curation does not need the
full recording:

```powershell
python tools/build_scouting.py --data-only
python tools/check_site.py
python tools/check_brand.py
python tools/check_scouting.py
```

Changing an evidence timestamp requires returning to the source; `--data-only`
will refuse a time that differs from the retained review log.

For an additional dossier, use its own slug and source filenames declared in the
curated JSON (`source.video.mp4` and `source.audio.m4a` for the four additions):

```powershell
python tools/build_scouting.py --analysis 'C:/local-analysis/VIDEO_ID' --slug adversary-warcats-easy
python tools/build_scouting_catalog.py
python tools/check_scouting.py
```

Run the catalog builder after the source media/evidence is packaged for every
new report. It rebuilds navigation without replacing the original dossier, and
publishes `site/scouting/patterns.html` at `/scouting/patterns/`. The public JSON
contains source byte sizes and SHA256 fingerprints, but no raw downloader metadata,
signed media URLs, local storage paths or full captions.

The public dataset, CSV and review log carry evidence IDs and scope limitations.
The chart shows discrete score observations rather than interpolated control.
The evidence library omits extra score-only anchors, which remain inspectable
from the timeline table. Share URLs preserve the section, side/type filters and
open evidence dialog.

## Browser checks

`check_black_sails_browser.cjs` checks the route from the homepage, filtering,
direct evidence URLs, excerpt decoding/playback, data exports, desktop/mobile
layout, page errors and missing responses. It requires Playwright. If Playwright
or Chromium lives outside the standard install, set `PLAYWRIGHT_MODULE` and
`PLAYWRIGHT_CHROMIUM_EXECUTABLE` to those installed locations. It writes screenshots
and `browser-results.json` into the supplied ignored QA directory.

```powershell
node tools/scouting/check_black_sails_browser.cjs http://127.0.0.1:8027 qa/scouting
node tools/scouting/check_series_browser.cjs http://127.0.0.1:8027 qa/scouting-series
```

The series check covers every selector route, team/type filter including empty
results, persisted links, exported data, native images and each hosted excerpt's
decoding and playback. Desktop/mobile screenshots and browser results stay local.
