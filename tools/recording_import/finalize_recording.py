"""Add separately transcribed final scoreboard rows and recording provenance."""
import argparse,json,csv,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();root=Path(a.output)
d=json.loads((root/'data/match-data.json').read_text())
rows=[('fishu',11,5,9,22,6745),('Raz1els',10,10,16,10,6745),('Grynd',7,3,11,4,6745),
 ('A Randy Gypsy',14,19,18,6,6745),('RobbinAK',22,7,17,8,6745),
 ('BlackShadow',31,11,19,8,6750),('Chamberz',26,14,20,3,6750),
 ('Tourist',25,18,22,14,6750),('a cactus',24,7,14,0,6750),('Aseiton',24,1,5,1,6750)]
scoreboard=[]
for name,kills,assists,deaths,revives,t in rows:
    src=f'evidence/scoreboard-{t}.jpg';shutil.copyfile(root/f'review/native-{t}.jpg',root/src)
    scoreboard.append(dict(player='[PHNT]'+name,kills=kills,assists=assists,deaths=deaths,revives=revives,
        video_seconds=t,coverage='Ten clear PHNT rows from two visible final scoreboard screens; incomplete roster',source_image=src,status='reviewed'))
d['scoreboard']=sorted(scoreboard,key=lambda r:-r['kills']);d['ticket_anchor_count']=29
d['source_recording']['timing']='Sampling-bin offsets corrected: HUD +2.5 seconds, feed +0.25 seconds; within one source frame (0.034 seconds). Result/scoreboard review uses native source timestamps.'
with (root/'data/scoreboard-visible-phnt.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(d['scoreboard'][0]));w.writeheader();w.writerows(d['scoreboard'])
meta=json.loads((root/'metadata.json').read_text())
provenance=dict(recording=Path(meta['source']).name,source_video_sha256=hashlib.file_digest(open(meta['source'],'rb'),'sha256').hexdigest(),
    source_video_bytes=Path(meta['source']).stat().st_size,source_video_width=1920,source_video_height=804,
    source_fps=meta['fps'],duration_seconds=meta['duration_seconds'],recording_date='2026-11-08',opponents=['RMNT','HTD'],match_details_source='WDL fixture 114; user confirmation',opponent_faction_mapping=None,pov_identity=None,
    verified_result=dict(phnt_faction='Blue',Blue=100,Red=75,Green=88,result_screen_seconds=6722.163),
    sampling=dict(hud_gap_seconds=5,feed_gap_seconds=.5,feed_start_seconds=.25,feed_end_seconds=6709.75),
    calibration='Bicubic enlargement to the existing 3440x1440 layout; no new image detail is created. Source times corrected for nearest-rounding sampling bins; uncertainty about 0.034 seconds.',
    strength='Two English recognizers agree, exact two digits, confidence >=0.92 in both, visible ticket HUD. Ambiguous first-digit 5 on Green is withheld for 3-versus-5 review. Three selected faction peaks visually verified; other observations remain machine reads.',
    score_anchors=29,reviewed_scoreboard_rows=len(rows),reviewed_feed_entries=d['summary']['reviewed_events'],
    limits='Member POV identity unconfirmed. League-listed factions differ from the recorded round; charts follow the footage. Feed samples are display episodes, not verified final kills. Selected visual checks do not establish whole-match accuracy. Anonymous map symbols do not identify player routes.',
    models=[dict(file=p.name,sha256=hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()) for p in sorted((root/'feed-v2/models').glob('*.onnx'))])
if (root/'data/league-fixture.json').exists():provenance['league']=json.loads((root/'data/league-fixture.json').read_text())
(root/'data/recording-provenance.json').write_text(json.dumps(provenance,indent=2))
(root/'data/match-data.json').write_text(json.dumps(d,separators=(',',':')))
print('Finalized',len(rows),'scoreboard rows and source provenance.')
