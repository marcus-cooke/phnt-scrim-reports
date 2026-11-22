"""Log recording provenance and evaluate automatic tracks against native references."""
import argparse,json,csv,hashlib,re,difflib,unicodedata,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();root=Path(a.output)
cfg=json.loads((root/'import-config.json').read_text());meta=json.loads((root/'metadata.json').read_text());d=json.loads((root/'data/match-data.json').read_text())
tracks=json.loads((root/'feed-v2/tracks-automatic.json').read_text())
def accepted(e):
 for n in [e['attacker'],e['target']]:
  if n.upper() in cfg['clan_teams']:return False
  if ('[' in n or ']' in n) and not re.match(r'^\[[^\[\]\s]{1,12}\].+',n):return False
 return (e['count']>=3 and e['confidence']>=.8) or (e['count']>=2 and sum(o.get('model_agreement',False) and o['confidence']>=.92 for o in e['observations'])>=2)
def key(n):
 n=n.split(']',1)[-1] if n.startswith('[') else n
 n=''.join(c for c in unicodedata.normalize('NFKD',n) if not unicodedata.combining(c))
 return re.sub(r'\W','',n).lower()
def sim(a,b):return difflib.SequenceMatcher(None,key(a),key(b)).ratio()
references=list(csv.DictReader((root/'manual-feed-reference.csv').open(encoding='utf-8-sig')));results=[]
for start in sorted({int(r['window_start']) for r in references}):
 truth=[r for r in references if int(r['window_start'])==start];events=[e for e in tracks if accepted(e) and e['first']<start+40 and e['last']>=start];used=set();matches=[];misses=[]
 for r in truth:
  options=[]
  for i,e in enumerate(events):
   if i in used or not e['first']-10<=float(r['seen_seconds'])<=e['last']+1:continue
   sa=sim(r['attacker'],e['attacker']);sb=sim(r['target'],e['target'])
   if min(sa,sb)>=.6 and (sa+sb)/2>=.8:options.append(((sa+sb)/2,i,e))
  if options:
   score,i,e=max(options,key=lambda v:v[0]);used.add(i);matches.append(dict(reference=r,event_id=e['id'],attacker=e['attacker'],target=e['target'],name_similarity=score))
  else:misses.append(r)
 extras=[dict(event_id=e['id'],first=e['first'],last=e['last'],attacker=e['attacker'],target=e['target']) for i,e in enumerate(events) if i not in used and e['first']<start+30]
 results.append(dict(start_seconds=start,duration_seconds=30,reference_pairs=len(truth),matched=len(matches),matches=matches,missed=misses,unmatched_predictions=extras))
validation=json.loads((root/'data/feed-validation.json').read_text());validation.update(reference_pairs=len(references),sample_seconds=90,matched=sum(r['matched'] for r in results),unmatched_predictions=sum(len(r['unmatched_predictions']) for r in results),windows=results,unsupported_notice='One readable Shaddy single-name notice at 7800s is excluded from paired evaluation; single-name notices are not classified in this import.',limitations='Three selected development spot-check windows, not a held-out test or whole-match accuracy estimate. Matching tolerates OCR spelling differences and measures episode recovery, not exact name accuracy. Automatic results precede separately logged visual corrections.')
validation['review_windows_seconds']=[[r['start_seconds'],r['start_seconds']+r['duration_seconds']] for r in results]
validation['match_timing_tolerance']='A readable source sample may precede reliable OCR by up to ten seconds; matching includes ten seconds of context after each window. Unmatched predictions are restricted to tracks observed before the window end.'
validation['limitations']+=' Reference images are sampled at one-second intervals with an additional quarter-second window-end check. Unmatched predictions may be fragments or additional displays; they are not all proven false positives.'
d['feed_sample_check']={k:validation[k] for k in ['reference_pairs','sample_seconds','matched','unmatched_predictions','limitations']}
(root/'data/match-data.json').write_text(json.dumps(d,separators=(',',':')))
(root/'data/feed-validation.json').write_text(json.dumps(validation,indent=2));shutil.copyfile(root/'manual-feed-reference.csv',root/'data/manual-feed-reference.csv')
fingerprint=json.loads((root/'video-sha256.json').read_text())
provenance=dict(recording=Path(meta['source']).name,recording_date='2026-11-22',category='phnt',recording_owner='PHNT',source_video_sha256=fingerprint['sha256'],source_video_bytes=fingerprint['bytes'],source_video_width=meta['width'],source_video_height=meta['height'],source_fps=meta['fps'],duration_seconds=meta['duration_seconds'],opponents=cfg['opponents'],clan_factions=cfg['clan_teams'],verified_result=cfg['final_scores'],result_screen_seconds=cfg['result_seconds'],analysis_start_seconds=cfg['start_seconds'],active_hud_end_seconds=cfg['end_seconds'],score_anchors=d['ticket_anchor_count'],reviewed_scoreboard_rows=0,reviewed_feed_entries=d['summary']['reviewed_events'],sampling=dict(feed_hz=4,hud_gap_seconds=5,feed_frames=d['summary']['feed_frames']),source_timing_checks=json.loads((root/'source-timing-check.json').read_text()),strength='Two English recognizers agree on two digits at >=0.92 each; visible ticket HUD required. Missing data stays unavailable. Values strictly above 33 are flagged; selected extrema separately reviewed.',limits='PHNT clan recording supplied by user. Opponent names are visible tags, not independently confirmed full clan names. Feed rows are display episodes, not verified final kills. Single-name notices remain unresolved. No per-player final scoreboard totals were transcribed. Anonymous map markers do not identify continuous routes.',models=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((root/'feed-v2/models').glob('*.onnx'))])
(root/'data/recording-provenance.json').write_text(json.dumps(provenance,indent=2))
print('Automatic source-window check:',validation['matched'],'/',len(references),'pairs;',validation['unmatched_predictions'],'unmatched accepted candidates')
