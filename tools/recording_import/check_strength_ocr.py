"""Independent English-model reads of small person counts, with raw disagreement."""
import argparse,json,time,cv2
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();root=Path(a.output)
models=[RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,use_cls=False,rec_use_dml=True,
    rec_batch_num=96,rec_model_path=str(root/'feed-v2/models'/f'en_PP-OCRv{v}_rec.onnx')) for v in [4,5]]
raw=[json.loads(s) for s in (root/'strength-raw.jsonl').read_text().splitlines()]
out=[]
for off in range(0,len(raw),64):
    part=raw[off:off+64];crops=[]
    for r in part:
        im=cv2.imread(str(root/'keyframes'/r['source_file']))
        crops.extend(cv2.resize(im[698:715,x:x2],None,fx=5,fy=5,interpolation=cv2.INTER_CUBIC) for x,x2 in [(124,151),(238,265),(352,379)])
    results=[ocr.text_rec(crops)[0] for ocr in models]
    for i,r in enumerate(part):
        r['english_v4']=results[0][i*3:i*3+3];r['english_v5']=results[1][i*3:i*3+3];out.append(r)
    print('Strength reread',len(out),flush=True)
(root/'strength-independent.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in out))
