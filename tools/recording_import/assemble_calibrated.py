"""Adapt the legacy ticket/map/strength rules to this explicitly reviewed POV.

This does not reuse prior match decisions, anchors, scoreboards or feed validation.
"""
import argparse,json,csv,re
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--legacy',required=True);a=p.parse_args()
root=Path(a.output).resolve();legacy=Path(a.legacy)
meta=json.loads((root/'metadata.json').read_text());video=meta['source']
for name in ['data','charts','evidence']:(root/name).mkdir(exist_ok=True)
# Read directly from the native-source anchor sheet. 1200 is a map menu and is omitted.
anchors=[(0,0,0,0),(120,3,0,0),(180,4,0,1),(300,4,0,6),(600,4,0,17),
 (900,5,0,28),(1500,15,8,33),(1800,16,15,36),(2100,18,21,40),
 (2400,21,24,45),(2700,23,27,52),(3000,26,32,55),(3300,34,36,55),
 (3600,34,42,61),(3900,34,42,74),(4200,42,44,75),(4500,42,57,75),
 (4800,43,66,77),(5100,46,67,85),(5400,54,67,88),(5700,66,68,88),
 (6000,78,68,88),(6300,90,68,88),(6600,98,72,88),(6650,98,74,88),
 (6680,98,75,88),(6690,99,75,88),(6700,99,75,88),(6722.163,100,75,88)]
with (root/'ticket-samples.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['video_seconds','blue_points','red_points','green_points']);w.writerows(anchors)
(root/'sample-events.csv').write_text('last_absent_seconds,first_present_seconds,attacker,attacker_faction,target,target_faction,weapon_icon_visual,event_icon_visual,classification,evidence\n')
review=root/'data/team-strength-reviewed.csv'
if not review.exists():review.write_text('video_seconds,team,value,note\n')
# Use the existing vetted ticket consistency and anonymous-map algorithms.
source=(legacy/'prepare_data.py').read_text(encoding='utf-8')
source=source.replace("ROOT=Path(__file__).parent",f'ROOT=Path({str(root)!r})')
source=source.replace("TEAM={'PHNT':'Green','26TH':'Red','TLL':'Blue','1G':'Blue','N1':'Blue'}","TEAM={'PHNT':'Blue','HTD':'Red','GIII':'Red'}")
source=source.replace('green_phnt_points','green_points')
source=source.replace(r'C:\Users\marcu\Videos\2026-10-24 20-01-17.mp4',video)
source=source.replace("cv2.imwrite(str(dst),im[270:1210,1270:2170]", "im=cv2.resize(im,(3440,1440),interpolation=cv2.INTER_CUBIC)\n            cv2.imwrite(str(dst),im[270:1210,1270:2170]")
source=source.replace('if not dst.exists():','if True:')
source=source.replace('video_seconds=6201.583333,fps=60',f'video_seconds={meta["duration_seconds"]},fps={meta["fps"]}')
start=source.index('    scoreboard=[');end=source.index('    included=',start)
source=source[:start]+'    scoreboard=[]\n'+source[end:]
source=source.replace("mask=cv2.inRange(hsv,np.array([35,100,90]),np.array([92,255,255]))", "mask=cv2.inRange(hsv,np.array([90,100,90]),np.array([135,255,255]))")
source=source.replace('green symbol candidate','blue symbol candidate').replace('green_pixels','blue_pixels')
exec(compile(source,str(root/'adapted-prepare-data.py'),'exec'),{'__name__':'__main__','__file__':str(legacy/'prepare_data.py')})
source=(legacy/'build_strength.py').read_text(encoding='utf-8')
source=source.replace('ROOT=Path(__file__).parent',f'ROOT=Path({str(root)!r})')
source=source.replace("team=='Green'","team=='Blue'").replace('xlim=(8,104)','xlim=(0,113)').replace('ax.text(104,33','ax.text(113,33')
source=source.replace('approximately 4.167-second sampling','5-second sampling').replace('plus 25 manually reviewed low-confidence candidates','plus separately logged visual corrections')
source=source.replace('Two-digit OCR confidence >=0.92 with visible ticket HUD','Two English recognizers must agree on an exact two-digit value with confidence >=0.92 in both, with visible ticket HUD. Ambiguous first-digit 5 readings in the tiny green HUD are withheld for 3-versus-5 review')
source=source.replace('Initial run starts and peaks were inspected visually; entire series is not manually verified.','Selected peaks are visually reviewed; the entire series is not manually verified.').replace('Sample spacing ≈4.17 seconds','Sample spacing 5 seconds')
exec(compile(source,str(root/'adapted-strength.py'),'exec'),{'__name__':'__main__','__file__':str(legacy/'build_strength.py')})
# Give every manual anchor an actual evidence image, including the result proof.
d=json.loads((root/'data/match-data.json').read_text())
from PIL import Image
Image.open(root/'sample-6722.163.jpg').save(root/'evidence/final-result.jpg',quality=96)
for r in d['tickets']:
    if r['status']=='reviewed':
        if r['video_seconds']>6710:r['source_image']='evidence/final-result.jpg'
        else:
            t=r['video_seconds'];native=root/'review'/f'native-{int(t)}.jpg'
            target=root/'evidence'/f'ticket-anchor-{int(t)}.jpg'
            Image.open(native).save(target,quality=95)
            r['source_file']='';r['source_image']='evidence/'+target.name
def write(name,rows,fields=None):
    with (root/'data'/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),extrasaction='ignore');w.writeheader();w.writerows(rows)
write('tickets.csv',d['tickets'],['video_seconds','timecode','blue','red','green','control','status','source_file','source_image','control_raw'])
for m in d['maps']:
    if not m.get('native_snapshot'):m['snapshot']=None
write('map-appearances.csv',d['maps'],['map_id','timecode','first_seen_seconds','last_seen_seconds','representative_seconds','sample_count','best_score','status','source_image','snapshot','native_snapshot','symbol_candidates'])
d['summary']['phnt_team']='Blue'
d['source_recording']=dict(width=meta['width'],height=meta['height'],fps=meta['fps'],
    duration_seconds=meta['duration_seconds'],pov='Another PHNT member; identity unconfirmed',
    layout='1920x804 normalized to 3440x1440 for legacy HUD coordinates; upsampling adds no detail')
(root/'data/match-data.json').write_text(json.dumps(d,separators=(',',':')))
print('Base dataset assembled with new anchors and no inherited scoreboard/feed decisions.')
