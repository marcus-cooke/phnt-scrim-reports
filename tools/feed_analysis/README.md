# Dense feed audit scripts

These scripts reproduce the **25 October clip's feed analysis** alongside its
existing local analysis folder. They are not a general video-ingestion service.
The earlier report, ticket/strength extraction and report templates remain
separate inputs. Original videos, dense PNGs, OCR streams and model weights are
not committed or required to view the public site.

The tested environment is Python 3.13 on Windows, DirectML recognition and
NVIDIA CUDA decoding. Dependencies are pinned in `requirements.txt`.

RapidOCR's package dependency also pulls the CPU `onnxruntime` distribution,
which shares module files with DirectML. Finish a fresh installation in this
order so the intended runtime owns those files:

```powershell
python -m pip install -r tools/feed_analysis/requirements.txt
python -m pip uninstall -y onnxruntime
python -m pip install --no-deps --force-reinstall onnxruntime-directml==1.24.4
python -c "import onnxruntime as ort; print(ort.get_available_providers()); assert 'DmlExecutionProvider' in ort.get_available_providers()"
```

The provider assertion must pass before running the GPU recognition commands.

Set `PHNT_ANALYSIS_ROOT` to the existing latest-game analysis directory. Scripts
read and write its `feed-v2/` subdirectory and `feed-evidence/` folder. For example:

```powershell
$env:PHNT_ANALYSIS_ROOT='C:/local-analysis/25-oct'
python tools/feed_analysis/extract_dense_feed.py --video 'C:/recordings/25-oct.mp4'
python tools/feed_analysis/read_dense_feed.py
python tools/feed_analysis/rerecognize_feed.py
python tools/feed_analysis/combine_feed_passes.py
```

The extraction defaults deliberately require the known recording boundary:
300–6455.566667 seconds, four observations per second, 24,622 frames. The export
refuses incomplete coverage. It stages changes instead of replacing the local
analysis or publishing the site.

Copy `reference/*` into that external `feed-v2/` directory before evaluation.
The five reference CSVs were read from sequential source-image contact sheets;
their `seen_seconds` values are readable sample times, not exact event births.
`baseline-events.json` is the retained original sparse extraction.

After both full OCR streams exist, `prepare_validation.py START --duration N`
prepares a validation window. Use windows 1440, 2400, 5880 and 4320 for 60 seconds,
and 3300 for 30 seconds. `validation_sheets.py --folder validation-START` creates
the manual source sheets. For each window run `combine_feed_passes.py` with its
`--native validation-START-native.jsonl`,
`--alternate validation-START-v5-rerec.jsonl`,
`--output validation-START-combined.jsonl`, and `--expected 240` (120 for 3300).

Run `evaluate_feed.py`, then `export_dense_feed.py`, then `evaluate_feed.py`
again. The second evaluation includes the whole-game tracks with context across
window boundaries. `curate_feed_samples.py` applies the separately logged visual
decisions from this investigation; it asserts the expected records and must not
be reused blindly on other footage or changed recognition output.
`refresh_curated_exports.py` refreshes grouped timestamp labels and sample totals.
The resulting `feed-v2/staged-data/` can be passed to the report packager using
`--feed-data 2026-10-25=PATH`.

Both model files belong in external `feed-v2/models/`. They are listed in the
[official RapidAI model manifest](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/default_models.yaml):

| Local filename | Official model | SHA256 |
| --- | --- | --- |
| en_PP-OCRv4_rec.onnx | [English v4](https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv4/rec/en_PP-OCRv4_rec_mobile.onnx) | e8770c967605983d1570cdf5352041dfb68fa0c21664f49f47b155abd3e0e318 |
| en_PP-OCRv5_rec.onnx | [English v5](https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv5/rec/en_PP-OCRv5_rec_mobile.onnx) | c3461add59bb4323ecba96a492ab75e06dda42467c9e3d0c18db5d1d21924be8 |

The baseline reader gated feed recognition on ticket reads and sampled about
every 4.17 seconds. The new pass is independent, accepts merged text boxes,
repairs bracket errors, reads untagged names, uses row continuity and temporal
spelling votes, and retains single-name skull/hand notices. Model agreement is
counted per distinct source frame, never as two observations of the same frame.

The published validation records the automatic result before human corrections:
110/111 readable entries recovered in 4.5 reviewed minutes, with three duplicate
fragments. Those windows were used during iteration. Tolerant name matching
measures episode recovery, not exact spelling accuracy or whole-game completeness.
Three visual duplicate decisions and one recovered entry are logged separately.
Remaining names, icon semantics and grouping outside the reviewed samples are
machine-derived. No result should be read as verified final-kill telemetry.
