"""Apply separately reviewed 22 November decisions without changing the raw audit."""
import argparse,json,csv,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();root=Path(a.output)
cfg=json.loads((root/'import-config.json').read_text());assert cfg['id']=='2026-11-22'
data=root/'data';d=json.loads((data/'match-data.json').read_text());events=d['events'];byid={e['event_id']:e for e in events}
assert d['summary']['accepted_feed_entries']==2128 and d['summary']['reviewed_events']==7,'Apply once to the documented automatic/base-review export'
shutil.copyfile(data/'match-data.json',root/'feed-v2/match-before-extra-visual-decisions.json')
decisions=list(csv.DictReader((data/'feed-manual-decisions.csv').open(encoding='utf-8-sig')))
spec=json.loads((root/'feed-curation-decisions.json').read_text())
def tc(t):return f'{int(t)//3600:02}:{int(t)//60%60:02}:{t%60:06.3f}'
for decision in spec['duplicates']:
    child,parent=byid[decision['event_id']],byid[decision['duplicate_of']]
    assert child['accepted_feed_entry'] and parent['accepted_feed_entry']
    assert not set(child['observation_times'])&set(parent['observation_times']),'Never merge co-observed source rows'
    times=sorted(set(child['observation_times'])|set(parent['observation_times']))
    assert times[-1]-times[0]<=10.5,'Reviewed fragment must fit one display lifetime'
    parent.update(observation_times=times,observations=len(times),first_seen_seconds=times[0],last_seen_seconds=times[-1],timecode=tc(times[0]),ocr_confidence=max(parent['ocr_confidence'],child['ocr_confidence']))
    for key in ['model_agreement_observations','strong_model_agreement_observations']:parent[key]+=child[key]
    parent['notes']+=' Separate visual review merged source observations from '+child['event_id']+'.'
    child.update(status='rejected_duplicate',review_decision='exclude_duplicate',duplicate_of=parent['event_id'],accepted_feed_entry=False,included_in_charts=False)
    child['notes']+=' Visually confirmed fragment of '+parent['event_id']+'; retained for audit, excluded from accepted totals.'
    decisions.append(dict(event_id=child['event_id'],decision='exclude_duplicate',duplicate_of=parent['event_id'],reviewed_at_seconds=decision['reviewed_at_seconds'],source_image=child['source_image'],note=decision['note']))
promote=spec['recovery'];e=byid[promote['event_id']]
assert not e['accepted_feed_entry'] and e['evidence_seconds']==7812.75 and e['observations']==1
e.update(attacker=promote['attacker'],target=promote['target'],attacker_team='Red',target_team='Green',attacker_team_source='visual review',target_team_source='visual review',status='reviewed',reviewed_at_seconds=7812.75,review_decision='recover_readable_pair',accepted_feed_entry=True,included_in_charts=True,icon_class='skull-marked',notes='Names, factions and skull appearance visually reviewed in native source at 7812.75s and surrounding frames. Automatic raw validation retains this miss; icon appearance is not verified final-kill telemetry.')
decisions.append(dict(event_id=e['event_id'],decision='recover_readable_pair',reviewed_at_seconds=7812.75,attacker=e['attacker'],target=e['target'],attacker_team='Red',target_team='Green',icon_class=e['icon_class'],source_image=e['source_image'],note=promote['note']))
d['events'].sort(key=lambda e:e['first_seen_seconds'])
d['summary'].update(accepted_feed_entries=sum(e['accepted_feed_entry'] for e in events),charted_events=sum(e['included_in_charts'] for e in events),reviewed_events=sum(e['status']=='reviewed' for e in events))
def write(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (data/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
write('feed-events.csv',d['events']);write('feed-review-queue.csv',[e for e in events if not e['accepted_feed_entry']]);write('feed-manual-decisions.csv',decisions)
validation=json.loads((data/'feed-validation.json').read_text());validation.update(visually_reviewed_entries=8,separate_visual_recoveries=1,separate_visual_duplicate_exclusions=4)
(data/'feed-validation.json').write_text(json.dumps(validation,indent=2));d['feed_sample_check'].update(visual_recoveries=1,visual_duplicate_exclusions=4)
provenance=json.loads((data/'recording-provenance.json').read_text());provenance.update(reviewed_feed_entries=8,visual_duplicate_exclusions=4,automatic_reference_recovery='25/26 before separate visual decisions')
(data/'recording-provenance.json').write_text(json.dumps(provenance,indent=2));(data/'match-data.json').write_text(json.dumps(d,separators=(',',':')));(data/'summary.json').write_text(json.dumps(d['summary'],indent=2))
print('Curated:',d['summary']['accepted_feed_entries'],'accepted,',d['summary']['charted_events'],'charted,8 reviewed,4 duplicate exclusions; raw automatic25/26 retained')
