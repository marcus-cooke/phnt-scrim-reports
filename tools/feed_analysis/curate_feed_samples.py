"""Apply separately logged visual decisions; retain untouched automatic results."""
import csv,json,re
from track_dense_feed import ROOT,similarity
from export_dense_feed import csvwrite,tc
stage=ROOT/'staged-data';path=stage/'match-data.json';d=json.loads(path.read_text())
assert not d.get('feed_curation'),'Already curated; regenerate the automatic stage before reapplying'
events=d['events'];decisions=[]
rules=[(2436.0,'[PV]Vittex','[PHNT]10080','[PV]Vittex','MAX'),
       (4349.0,'IPHNA','[AK-P]Trigga','[PHNT]Chicodi','Trigga'),
       (3310.25,'[PV]sonsays','[PV]MandreV|aim.exe','[PV]s1monsays','Mandre')]
for t,a,b,parent_actor,parent_target in rules:
    candidates=[e for e in events if e['first_seen_seconds']==t and e['attacker']==a and e['target']==b]
    assert len(candidates)==1,(t,a,b,len(candidates))
    duplicate=candidates[0]
    parents=[e for e in events if e['accepted_feed_entry'] and e is not duplicate and abs(e['first_seen_seconds']-t)<11 and similarity(e['attacker'],parent_actor)>=.85 and parent_target.casefold() in e['target'].casefold()]
    assert parents,(t,parent_actor,parent_target)
    parent=max(parents,key=lambda e:e['observations'])
    parent['observation_times']=sorted(set(parent['observation_times']+duplicate['observation_times']))
    parent['first_seen_seconds']=min(parent['observation_times']);parent['last_seen_seconds']=max(parent['observation_times']);parent['observations']=len(parent['observation_times'])
    parent['timecode']=tc(parent['first_seen_seconds'])
    parent['ocr_confidence']=max(parent['ocr_confidence'],duplicate['ocr_confidence'])
    # Counts below remain a conservative lower bound after manual grouping.
    parent['manually_merged_fragments']=[duplicate['event_id']]
    parent['notes']+=' Visual review joined an OCR fragment of the same displayed row; name spelling is still machine-read.'
    duplicate.update(status='rejected_duplicate',accepted_feed_entry=False,included_in_charts=False,
        duplicate_of=parent['event_id'],review_decision='exclude_duplicate',reviewed_at_seconds=t,
        notes='Manually checked against the native feed: OCR fragment of '+parent['event_id']+'. Retained for audit and excluded from accepted counts.')
    decisions.append(dict(event_id=duplicate['event_id'],decision='exclude_duplicate',parent_event_id=parent['event_id'],video_seconds=t,source_image=duplicate['source_image'],notes='Same visible feed row; native source inspected'))
    print('Excluded duplicate',duplicate['event_id'],'of',parent['event_id'])

# Native 4351.75 visibly reads PHNT ZioWillY -> PV Vittex, aircraft/impact icon.
candidates=[e for e in events if e['first_seen_seconds']==4351.75 and 'ZIO' in e['attacker'].upper()]
assert len(candidates)==1,len(candidates)
e=candidates[0]
assert e['evidence_seconds']==4351.75 and not e['accepted_feed_entry']
e.update(attacker='[PHNT]ZioWillY',target='[PV]Vittex',attacker_team='Blue',target_team='Red',
    attacker_team_source='manual visual review',target_team_source='manual visual review',
    status='reviewed',accepted_feed_entry=True,included_in_charts=True,reviewed_at_seconds=4351.75,
    icon_class='aircraft / impact',review_decision='recover_readable_entry',
    notes='Names, factions and aircraft/impact icon manually read in native frame 4351.75 after automatic recognition failed. This single supported observation is a manual override. Final-kill semantics remain unvalidated.')
decisions.append(dict(event_id=e['event_id'],decision='recover_readable_entry',parent_event_id='',video_seconds=4351.75,source_image=e['source_image'],notes='Both names/factions visually read in the source frame'))
d['feed_curation']=dict(automatic_results_file='feed-validation.json',decisions=len(decisions),notes='Automatic validation precedes these visual decisions; it is not replaced by the corrected result.')
s=d['summary'];s.update(accepted_feed_entries=sum(e['accepted_feed_entry'] for e in events),charted_events=sum(e['included_in_charts'] for e in events),reviewed_events=sum(e['status']=='reviewed' for e in events),single_name_notices=sum(e['accepted_feed_entry'] and e['event_kind']!='pair' for e in events))
path.write_text(json.dumps(d,ensure_ascii=True,separators=(',',':')))
fields=list(dict.fromkeys(k for e in events for k in e))
csvwrite(stage/'feed-events.csv',events,fields)
csvwrite(stage/'feed-review-queue.csv',[e for e in events if not e['accepted_feed_entry']],fields)
csvwrite(stage/'feed-manual-decisions.csv',decisions,list(decisions[0]))
(stage/'summary.json').write_text(json.dumps(s,indent=2))
(stage/'feed-validation.json').write_text((ROOT/'evaluation.json').read_text())
print(json.dumps(s,indent=2))
