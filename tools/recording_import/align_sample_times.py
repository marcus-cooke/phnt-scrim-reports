"""Correct fps(round=near) sample labels to their source-frame bin centres.

The retained frame is the last input before the bin boundary: uncertainty is one
source frame. Output PTS alone labels the start, not the content's source time.
Run only once, after extraction and both recognition streams finish.
"""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();r=Path(a.output)
if (r/'time-aligned.json').exists():raise SystemExit('Already aligned')
def adjust(folder,extension,offset):
    for path in sorted(folder.glob('*.'+extension),reverse=True):
        path.rename(path.with_name(f'{int(path.stem)+offset:010d}.'+extension))
def stream(path,offset,timekey,filekey):
    records=[json.loads(s) for s in path.read_text().splitlines()]
    for item in records:
        item[timekey]+=offset/1000
        file=Path(item[filekey]);item[filekey]=f'{int(file.stem)+offset:010d}'+file.suffix
        item['source_time_uncertainty_seconds']=1/29.935
    path.write_text(''.join(json.dumps(item)+'\n' for item in records))
adjust(r/'keyframes','jpg',2500)
adjust(r/'feed-v2/frames','png',250)
for name in ['hud-raw.jsonl','strength-raw.jsonl','strength-independent.jsonl']:
    stream(r/name,2500,'video_seconds','source_file')
for name in ['ocr-en-native.jsonl','ocr-en-v5-rerec.jsonl']:
    stream(r/'feed-v2'/name,250,'t','frame')
(r/'time-aligned.json').write_text(json.dumps(dict(hud_offset_seconds=2.5,feed_offset_seconds=.25,
    uncertainty_seconds=1/29.935,note='Source times account for fps round=near bin selection. Retained images precede bin centres by at most one source frame.'),indent=2))
print('Aligned image names and raw observations to source content times.')
