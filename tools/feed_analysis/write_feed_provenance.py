import hashlib,json
from track_dense_feed import ROOT
rows={}
for name in ['ocr-en-native.jsonl','ocr-en-v5-rerec.jsonl','combined-rows.jsonl']:
    path=ROOT/name;rows[name]=dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),frames=sum(1 for _ in path.open()))
result=dict(recording='2026-10-25 19-29-14.mp4',analysis_start_seconds=300,last_frame_seconds=6455.25,sampling_hz=4,frames=24622,native_crop=dict(width=900,height=340,source_x=0,source_y=640),recognition_streams=rows,
    model_sha256={name:hashlib.sha256((ROOT/'models'/name).read_bytes()).hexdigest() for name in ['en_PP-OCRv4_rec.onnx','en_PP-OCRv5_rec.onnx']},
    caveats='Recording observations, not server-event time. Automatic sample validation precedes separately recorded visual decisions. Frames, original video and OCR streams remain offline.')
(ROOT/'staged-data/feed-provenance.json').write_text(json.dumps(result,indent=2))
print('Wrote complete-frame provenance and model fingerprints')
