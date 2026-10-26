import argparse,hashlib,json,shutil
from pathlib import Path
from track_dense_feed import ROOT
p=argparse.ArgumentParser();p.add_argument('start',type=int);p.add_argument('--duration',type=int,default=30);a=p.parse_args()
folder=ROOT/f'validation-{a.start}';folder.mkdir(exist_ok=True)
for model,source in [('native','ocr-en-native.jsonl'),('v5-rerec','ocr-en-v5-rerec.jsonl')]:
    rows=[]
    for line in (ROOT/source).read_text().splitlines():
        r=json.loads(line)
        if a.start<=r['t']<a.start+a.duration:
            rows.append(r)
            if model=='native':shutil.copyfile(ROOT/'frames'/r['frame'],folder/r['frame'])
    assert len(rows)==4*a.duration
    (ROOT/f'validation-{a.start}-{model}.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
(folder/'complete.json').write_text('{}')
policy=Path(__file__).parent/'track_dense_feed.py'
(ROOT/f'validation-{a.start}-frozen-policy.json').write_text(json.dumps(dict(policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),start=a.start,duration=a.duration)))
