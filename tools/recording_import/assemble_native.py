"""Assemble a native-layout import from explicit, recording-specific review files.

Review config, ticket anchors and manual decisions belong to this recording.
Existing reports and earlier recordings' decisions are never loaded.
"""
import argparse,csv,json,hashlib
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--legacy',required=True);a=p.parse_args()
root=Path(a.output).resolve();legacy=Path(a.legacy);cfg=json.loads((root/'import-config.json').read_text());meta=json.loads((root/'metadata.json').read_text())
for name in ['data','charts','evidence']:(root/name).mkdir(exist_ok=True)
def run_legacy(name):
 s=(legacy/name).read_text(encoding='utf-8').replace('ROOT=Path(__file__).parent',f'ROOT=Path({str(root)!r})')
 if name=='prepare_data.py':
  s=s.replace("TEAM={'PHNT':'Green','26TH':'Red','TLL':'Blue','1G':'Blue','N1':'Blue'}",'TEAM='+repr(cfg['clan_teams']))
  s=s.replace('green_phnt_points','green_points').replace(r'C:\Users\marcu\Videos\2026-10-24 20-01-17.mp4',meta['source'])
  s=s.replace('video_seconds=6201.583333,fps=60',f'video_seconds={meta["duration_seconds"]},fps={meta["fps"]}')
  start=s.index('    scoreboard=[');end=s.index('    included=',start);s=s[:start]+'    scoreboard=[]\n'+s[end:]
  s=s.replace('mask=cv2.inRange(hsv,np.array([35,100,90]),np.array([92,255,255]))','mask=cv2.inRange(hsv,np.array([90,100,90]),np.array([135,255,255]))')
  s=s.replace('green symbol candidate','blue symbol candidate').replace('green_pixels','blue_pixels')
 else:
  s=s.replace("team=='Green'","team=='Blue'").replace('xlim=(8,104)','xlim=(6,139)').replace('ax.text(104,33','ax.text(139,33')
  s=s.replace('approximately 4.167-second sampling','5-second sampling').replace('plus 25 manually reviewed low-confidence candidates','plus separately logged visual reviews')
  s=s.replace('Two-digit OCR confidence >=0.92 with visible ticket HUD','Two English recognizers agree on two digits at confidence >=0.92 in both, with visible ticket HUD')
  s=s.replace('Initial run starts and peaks were inspected visually; entire series is not manually verified.','Selected peaks are checked separately; entire series is not manually verified.').replace('Sample spacing ≈4.17 seconds','Sample spacing 5 seconds')
 exec(compile(s,str(root/('adapted-'+name)),'exec'),{'__name__':'__main__','__file__':str(legacy/name)})
run_legacy('prepare_data.py');run_legacy('build_strength.py')
d=json.loads((root/'data/match-data.json').read_text())
for r in d['tickets']:
 r['control_raw']=r.get('control_raw','').strip()
 if r['status']=='reviewed':
  t=r['video_seconds'];src=root/'review'/f'native-{int(t)}.jpg'
  if not src.exists():src=root/f'native-{int(t)}.jpg'
  target=root/'evidence'/f'ticket-anchor-{int(t)}.jpg';Image.open(src).save(target,quality=96);r['source_image']='evidence/'+target.name;r['source_file']=''
for m in d['maps']:
 if not m.get('native_snapshot'):m['snapshot']=None
def write(name,rows,fields):
 with (root/'data'/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
write('tickets.csv',d['tickets'],['video_seconds','timecode','blue','red','green','control','status','source_file','source_image','control_raw'])
write('map-appearances.csv',d['maps'],['map_id','timecode','first_seen_seconds','last_seen_seconds','representative_seconds','sample_count','best_score','status','source_image','snapshot','native_snapshot','symbol_candidates'])
write('scoreboard-visible-phnt.csv',[],['player','kills','assists','deaths','revives','status'])
d['summary']['phnt_team']=cfg['phnt_team'];d['ticket_anchor_count']=sum(r['status']=='reviewed' for r in d['tickets'])
d['source_recording']=dict(width=meta['width'],height=meta['height'],fps=meta['fps'],duration_seconds=meta['duration_seconds'],pov='PHNT clan recording; supplied by clan member',layout='Native 3440x1440; no coordinate enlargement',timing='Recording timestamps; 4Hz feed and 5-second HUD samples use upward-rounded source bins, within one source frame (0.017s).')
(root/'data/match-data.json').write_text(json.dumps(d,separators=(',',':')))
print('Assembled native match',d['summary'],flush=True)
