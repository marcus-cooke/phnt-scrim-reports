"""Two recognizers share detector boxes; observations still count source frames."""
import argparse,cv2,json,time,numpy as np
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--batch',type=int,default=24);a=p.parse_args()
root=Path(a.output)/'feed-v2'
def create(model):
    return RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,use_cls=False,
        det_limit_type='max',det_limit_side_len=960,det_use_dml=True,rec_use_dml=True,
        rec_batch_num=64,rec_model_path=str(root/'models'/model))
v4=create('en_PP-OCRv4_rec.onnx');v5=create('en_PP-OCRv5_rec.onnx')
outputs=[root/'ocr-en-native.jsonl',root/'ocr-en-v5-rerec.jsonl']
done=[]
for path in outputs:
    done.append({json.loads(s)['frame'] for s in path.read_text().splitlines()} if path.exists() else set())
start=time.time();count=0
with outputs[0].open('a') as f4,outputs[1].open('a') as f5:
    while True:
        pending=[p for p in sorted((root/'frames').glob('*.png')) if any(p.name not in d for d in done)]
        if not pending:
            if (root/'frames/complete.json').exists():break
            time.sleep(2);continue
        for off in range(0,len(pending),a.batch):
            paths=pending[off:off+a.batch];records=[];all_crops=[]
            for path in paths:
                im=cv2.imread(str(path));boxes,_=v4(im,use_rec=False)
                boxes=boxes or []
                crops=v4.get_crop_img_list(im,np.array(boxes,dtype=np.float32)) if boxes else []
                records.append((path,boxes,len(all_crops),len(crops)));all_crops.extend(crops)
            for i,(ocr,f) in enumerate([(v4,f4),(v5,f5)]):
                result,_=ocr.text_rec(all_crops) if all_crops else ([],0)
                for path,boxes,begin,n in records:
                    if path.name in done[i]:continue
                    entries=[[b,str(txt),float(score)] for b,(txt,score) in zip(boxes,result[begin:begin+n]) if score>=.5]
                    f.write(json.dumps(dict(t=int(path.stem)/1000,frame=path.name,ocr=entries,scale=1,
                        recognizer='English PP-OCRv4' if i==0 else 'English PP-OCRv5',batch_frames=a.batch))+'\n')
                    done[i].add(path.name)
                f.flush()
            count+=len(paths)
            if count%240==0:print(f'Both models {len(done[1])} frames; source {int(paths[-1].stem)/60000:.1f}min; elapsed {time.time()-start:.0f}s',flush=True)
print('Two-model recognition complete',list(map(len,done)),flush=True)
