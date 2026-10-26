from pathlib import Path
import argparse,cv2,json,time,os
from rapidocr_onnxruntime import RapidOCR
ROOT=Path(os.environ.get('PHNT_ANALYSIS_ROOT',str(Path(__file__).parent)))/'feed-v2'
p=argparse.ArgumentParser();p.add_argument('--folder',default='frames');p.add_argument('--output',default='ocr-en-native.jsonl');p.add_argument('--scale',type=float,default=1);p.add_argument('--step',type=int,default=1);p.add_argument('--model',default='en_PP-OCRv4_rec.onnx');a=p.parse_args()
folder=ROOT/a.folder;out=ROOT/a.output
ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,use_cls=False,det_limit_type='max',det_limit_side_len=960 if a.scale==1 else 1536,det_use_dml=True,rec_use_dml=True,rec_batch_num=32,rec_model_path=str(ROOT/'models'/a.model))
done=set()
if out.exists():
    for s in out.read_text().splitlines():
        try:done.add(json.loads(s)['frame'])
        except json.JSONDecodeError:pass
count=0;start=time.time();idle=0
with out.open('a',encoding='utf-8') as f:
    while True:
        files=[p for i,p in enumerate(sorted(folder.glob('*.png'))) if i%a.step==0 and p.name not in done]
        if not files:
            if (folder/'complete.json').exists():break
            idle+=1;time.sleep(2);continue
        for path in files:
            im=cv2.imread(str(path))
            if im is None:continue
            if a.scale!=1:im=cv2.resize(im,None,fx=a.scale,fy=a.scale,interpolation=cv2.INTER_CUBIC)
            r,elapsed=ocr(im)
            if a.scale!=1 and r:
                for box,_,_ in r:
                    for pt in box:pt[0]/=a.scale;pt[1]/=a.scale
            rec=dict(t=int(path.stem)/1000,frame=path.name,ocr=r or [],scale=a.scale)
            f.write(json.dumps(rec,ensure_ascii=True)+'\n');f.flush();done.add(path.name);count+=1
            if count%300==0:print(f'OCR {count} frames; source {rec["t"]/60:.1f}min; elapsed {time.time()-start:.0f}s',flush=True)
print('Dense OCR complete',count,flush=True)
