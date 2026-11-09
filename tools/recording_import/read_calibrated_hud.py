"""Read normalized HUD samples, keeping raw OCR and unavailable values."""
import argparse, cv2, json, time, re
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR

p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();root=Path(a.output)
ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,use_cls=False,
    det_limit_type='max',det_limit_side_len=736,det_use_dml=True,rec_use_dml=True,rec_batch_num=16)
ref=cv2.imread(str(root/'sample-5100.000.jpg'))
ref=cv2.cvtColor(cv2.resize(ref,(688,288))[256:267,230:500],cv2.COLOR_BGR2GRAY)
done=set()
if (root/'hud-raw.jsonl').exists():done={json.loads(s)['source_file'] for s in (root/'hud-raw.jsonl').read_text().splitlines()}
start=time.time();count=0
with (root/'hud-raw.jsonl').open('a') as f,(root/'strength-raw.jsonl').open('a') as sf:
    while True:
        files=[p for p in sorted((root/'keyframes').glob('*.jpg')) if p.name not in done]
        if not files:
            if (root/'complete.json').exists():break
            time.sleep(2);continue
        for path in files:
            im=cv2.imread(str(path));t=int(path.stem)/1000
            imgs=[cv2.resize(im[680:720,x:x2],None,fx=2,fy=2) for x,x2 in [(45,115),(158,230),(272,345)]]
            numbers,_=ocr.text_rec(imgs)
            vals=[int(txt.strip()) if re.fullmatch(r'\d{3}',txt.strip()) and int(txt)<=100 and score>=.85 else None for txt,score in numbers]
            ctrl,_=ocr(im[720:750,40:380],use_det=False,use_cls=False)
            region=cv2.cvtColor(im[1016:1027,230:500],cv2.COLOR_BGR2GRAY)
            rec=dict(video_seconds=t,source_file=path.name,ticket_raw=numbers,tickets=vals,
                     control_raw=ctrl,feed_ocr=[],map_template_score=float(cv2.matchTemplate(region,ref,cv2.TM_CCOEFF_NORMED)[0,0]))
            imgs=[cv2.resize(im[698:715,x:x2],None,fx=5,fy=5,interpolation=cv2.INTER_CUBIC) for x,x2 in [(124,151),(238,265),(352,379)]]
            people,_=ocr.text_rec(imgs)
            sr=dict(video_seconds=t,source_file=path.name,reads=people,hud_tickets=vals)
            f.write(json.dumps(rec)+'\n');sf.write(json.dumps(sr)+'\n');f.flush();sf.flush()
            done.add(path.name);count+=1
            if count%100==0:print(f'HUD {count}: {t/60:.1f}min, {time.time()-start:.0f}s elapsed',flush=True)
print('HUD OCR complete',len(done),flush=True)
