import json
from track_dense_feed import ROOT
from export_dense_feed import tc,csvwrite
stage=ROOT/'staged-data';path=stage/'match-data.json';d=json.loads(path.read_text());by_id={e['event_id']:e for e in d['events']}
evaluation=json.loads((ROOT/'evaluation.json').read_text())
final=[r for r in evaluation if r['method']=='whole_game_v2'];baseline=[r for r in evaluation if r['method']=='baseline_included']
d['feed_validation_summary']=dict(reference_entries=sum(r['reference_entries'] for r in final),matched=sum(r['matched'] for r in final),unmatched_predictions=sum(len(r['unmatched_predictions']) for r in final),baseline_matched=sum(r['matched'] for r in baseline),sample_seconds=sum(r['duration'] for r in final),manual_decisions=d['feed_curation']['decisions'])
for e in d['events']:
    if e.get('manually_merged_fragments'):
        e['timecode']=tc(e['first_seen_seconds'])
        e['ocr_confidence']=max([e['ocr_confidence']]+[by_id[ident]['ocr_confidence'] for ident in e['manually_merged_fragments']])
path.write_text(json.dumps(d,ensure_ascii=True,separators=(',',':')))
csvwrite(stage/'feed-events.csv',d['events'],list(dict.fromkeys(k for e in d['events'] for k in e)))
print('Refreshed manually grouped timestamp labels and confidence maxima')
