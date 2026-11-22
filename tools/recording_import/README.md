# WDL / Phantom scrim 2 import

These scripts record the adaptations used for the **8 November 2026, 1920 × 804 POV against RMNT and HTD**.
They are recording-specific analysis tools, not an automatic upload service.
Date, player identity, faction, round window, anchors and visual decisions must
be reviewed again for other footage. No previous match's manual feed decisions,
scoreboard rows or validation result is reused.

The tested local environment is the existing Windows Python 3.13 analysis venv
with OpenCV, Pillow, NumPy, Matplotlib, imageio-ffmpeg, RapidOCR and DirectML.
The English v4/v5 model files and checksums are documented in
[`../feed_analysis/README.md`](../feed_analysis/README.md). Place them under the
external output folder's `feed-v2/models/`. Full video, PNG frames, OCR streams
and weights remain outside the public repository.

Processing stages, in order:

1. `inspect_recording.py VIDEO OUTPUT` and `review_calibrated.py VIDEO OUTPUT`
   create metadata, overview, native anchor and final-screen sheets.
2. `extract_calibrated.py VIDEO OUTPUT --end 6710 --fps-round near` creates
   normalized HUD crops every five seconds and feed crops twice per second.
   Enlargement aligns existing coordinates; it adds no image detail.
3. `read_calibrated_hud.py OUTPUT` and `read_batched_feed.py OUTPUT` read the
   crops. The latter shares detector boxes across English v4/v5 recognizers,
   while observations still count distinct source images. Completed rows resume.
4. `check_strength_ocr.py OUTPUT` independently rereads the small person counts.
5. **After extraction and both recognition streams finish**, run
   `align_sample_times.py OUTPUT` exactly once. With nearest rounding, FFmpeg's
   output timestamps label bins rather than the retained source-frame times:
   this import adds 2.5 seconds for HUD and 0.25 seconds for feed. Source-time
   uncertainty is about one frame (0.034 seconds). The extractor also supports
   `--fps-round up`; do **not** apply this correction to an up-rounded run.
6. `select_strength_consensus.py OUTPUT` requires two English models to agree
   on two digits at confidence ≥0.92 each. Ambiguous Green first-digit 5 readings
   are withheld for visual review of the 3/5 confusion. Raw disagreements remain
   in `data/strength-model-reads.csv`.
7. `assemble_calibrated.py OUTPUT --legacy LEGACY_ANALYSIS` adapts the existing
   original analysis's `prepare_data.py` and `build_strength.py`. These remain
   external inputs, as described in the main README. Its 29 anchors are read
   from the new source sheets. Review overrides belong in the external
   `data/team-strength-reviewed.csv`: the three verified peaks are Blue 45 at
   6287.5, Red 41 at 6517.5 and Green 41 at 797.5 seconds.
8. `assemble_feed.py OUTPUT --repo REPOSITORY` uses shared temporal row tracking
   with this recording's clan mapping and separately logged visual checks.
   It selects 13,420 source observations, 0.25–6709.75 seconds. No one-name row
   is automatically labelled without a verified icon template. The automatic
   tracks are retained before the ten visual decisions; three visual examples
   required added sample records. This is not a full reference census or an
   estimate of whole-match recall.
9. `finalize_recording.py OUTPUT` adds ten clear final scoreboard rows and the
   original video's SHA256, source dimensions, timing and calibration limits.

Use `tools/build_site.py --only wdl-phantom-scrim-2` with the existing template,
`--analysis ID=OUTPUT` and `--video ID=VIDEO` arguments to package only this
recording. Existing report files stay intact. Validate with `tools/check_site.py`
and `tools/check_brand.py`, then review the browser behavior and source evidence.

The public exports distinguish sampled feed display episodes from verified
final kills. Date and opponents are confirmed by WDL fixture #114 and the user.
The fixture snapshot is in `data/league-fixture.json`. Its faction assignments
differ from the recorded round, so the report retains both sources separately.
POV identity remains unconfirmed. Visible HTD/GIII player tags stay as observed.

## 22 November PHNT clan recording

The native **3440 × 1440, 60 FPS** recording belongs in the main PHNT match
catalog, not opponent scouting. Its ID is `2026-11-22`. PHNT is Blue / Lonestar,
AK/AKP is Red and PMF is Green, from visible tags and faction glyphs. The final
screen at 8220 seconds awards PHNT second place: Blue 96, Red 100, Green 96.
The date follows the supplied recording filename; no league fixture is inferred.

Recording-specific review inputs are in `reference/2026-11-22/`. Copy the JSON
config, ticket anchors, manual paired reference, visual decisions and curation decisions into a fresh
external analysis folder. Put `team-strength-reviewed.csv` in its `data/` folder.
Use `inspect_recording.py` to record metadata, and retain native source shots at
each ticket-anchor time under `review/native-SECONDS.jpg` (the final result may
also be `native-8220.jpg` at the analysis root). These decisions are specific to
this footage and must not be inherited by another recording.

Processing order:

1. `extract_native.py VIDEO OUTPUT --start 370 --end 8205` samples 31,340 feed
   images at 4 Hz and 1,567 HUD images at five-second intervals. The preceding
   round and loading transition are excluded. Up-rounded sampling retains the
   recording timestamps; do not apply the older import's bin-offset adjustment.
2. Put the documented English v4/v5 model files in `feed-v2/models/`, then run
   `read_batched_feed.py OUTPUT` and `read_native_hud.py OUTPUT --map-reference
   OUTPUT/review/native-1200.jpg`. Both readers resume completed observations.
   Recognizers share detector boxes; model calls never count as extra frames.
3. After the HUD reader completes, run `check_strength_ocr.py OUTPUT`, then
   `select_strength_consensus.py OUTPUT`, then `assemble_native.py OUTPUT
   --legacy LEGACY_ANALYSIS`. The legacy analysis provides the previously
   documented ticket/map/strength algorithms. Native reviewed peaks are Blue 47
   at 6255s, Red 41 at 5145s and Green 42 at 7530s. Gaps remain unknown.
4. After both complete feed streams exist, run `assemble_native_feed.py OUTPUT
   --repo REPOSITORY`. It requires the full bounded coverage and uses this
   recording's clan mapping. A delimiter prevents `AK` inside names such as
   `[PMF][EGO]Aky` from being mistaken for another clan prefix. Public evidence
   retains the selected native feed row at its original pixel scale; the full
   feed crops stay offline. Single-name rows remain unresolved.
5. Record the original video's SHA256 and bytes in external `video-sha256.json`,
   plus the native timing comparisons in `source-timing-check.json`, then run
   `finalize_native.py OUTPUT`. It evaluates automatic tracks before the seven
   separate visual decisions against 26 readable paired episodes across three
   30-second source windows. This development check tolerates spelling errors;
   it is not held-out validation or a whole-match accuracy estimate. A visible
   Shaddy single-name notice is outside the paired evaluation. Then run
   `curate_native_feed.py OUTPUT` once to recover the separately reviewed MaTej
   row and exclude four verified fragments. This yields eight reviewed entries
   and keeps the raw automatic 25/26 recovery unchanged.
6. Package using `build_site.py --only 2026-11-22`, with the existing templates,
   analysis and video inputs. Existing match datasets and scouting dossiers are
   preserved. Run the static, branding, scouting and browser checks.

The public package is limited to **950 MiB** to leave room below GitHub Pages'
[published-site size limit](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
Reports publish charts, timestamped screenshots and CSV/JSON exports. Hosted video
clips were removed at the user's request; originals and archived excerpts remain
offline. The match packager defaults to screenshots-only.
