# WDL / Phantom scrim 2 import

These scripts record the adaptations used for the **undated 1920 × 804 POV**.
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
final kills and leave recording date / POV identity unconfirmed.
