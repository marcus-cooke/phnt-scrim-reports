"""Second recognizer on original detector boxes; no synthetic image restoration."""
from pathlib import Path
import argparse,json,time,os
import cv2,numpy as np
from rapidocr_onnxruntime import RapidOCR
ROOT=Path(os.environ.get('PHNT_ANALYSIS_ROOT',str(Path(__file__).parent)))/'feed-v2'
p=argparse.ArgumentParser();p.add_argument('--input',default='ocr-en-native.jsonl');p.add_argument('--output',default='ocr-en-v5-rerec.jsonl');p.add_argument('--folder',default='frames');p.add_argument('--expected',type=int,default=24622);a=p.parse_args()
ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,use_cls=False,det_use_dml=True,rec_use_dml=True,rec_batch_num=32,rec_model_path=str(ROOT/'models/en_PP-OCRv5_rec.onnx'))
out=ROOT/a.output;done=set()
if out.exists():
    for line in out.read_text().splitlines():
        try:done.add(json.loads(line)['frame'])
        except json.JSONDecodeError:pass
start=time.time();count=0
with out.open('a',encoding='utf-8') as f:
    while True:
        source=[]
        for line in (ROOT/a.input).read_text(encoding='utf-8').splitlines():
            try:source.append(json.loads(line))
            except json.JSONDecodeError:pass
        pending=[r for r in source if r['frame'] not in done]
        for r in pending:
            im=cv2.imread(str(ROOT/a.folder/r['frame']));boxes=[o[0] for o in r['ocr']]
            results=[]
            if boxes:
                crops=ocr.get_crop_img_list(im,np.array(boxes,dtype=np.float32))
                results,_=ocr.text_rec(crops)
            r['ocr']=[[b,str(text),float(score)] for b,(text,score) in zip(boxes,results)]
            r['recognizer']='en_PP-OCRv5_rec_mobile';f.write(json.dumps(r)+'\n');f.flush();done.add(r['frame']);count+=1
            if count%300==0:print(f'V5 reread {count}; source {r["t"]/60:.1f} min; elapsed {time.time()-start:.0f}s',flush=True)
        if len(done)>=a.expected:break
        time.sleep(2)
print('V5 rerecognition complete',len(done),flush=True)
