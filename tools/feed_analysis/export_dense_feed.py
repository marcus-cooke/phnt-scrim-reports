"""Stage a complete replacement feed dataset; keep other metrics byte-identical."""
from pathlib import Path
import argparse,collections,copy,csv,json
from PIL import Image,ImageDraw
from track_dense_feed import ROOT,run,accepted,similarity
from annotate_dense_feed import annotate

ANALYSIS=ROOT.parent
def tc(t):return f'{int(t)//3600:02}:{int(t)//60%60:02}:{t%60:06.3f}'
def csvwrite(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',default='combined-rows.jsonl');a=p.parse_args()
    records=[json.loads(line) for line in (ROOT/a.input).read_text().splitlines()]
    times=[r['t'] for r in records]
    assert len(records)==24622 and len(set(times))==24622,'Incomplete dense source observations'
    assert min(times)==300 and max(times)==6455.25 and max(b-a for a,b in zip(times,times[1:]))==.25
    tracks=run(ROOT/a.input);annotate(tracks,ROOT/'frames')
    (ROOT/'tracks-final.json').write_text(json.dumps(tracks,indent=2),encoding='utf-8')
    # These names/factions/icons were rechecked directly in native frame 441.25.
    manual=[('[PHNT]Hanthy','[AK]Sneaky Rafiki','Blue','Green','unclassified'),
            ('[PV]Hal9000','[AK]Woxy','Red','Green','skull-marked'),
            ('[AK-P]Curze','[PV]Hal9000','Green','Red','unclassified')]
    reviewed={}
    for item in manual:
        candidates=[e for e in tracks if e['first']<=441.25<=e['last'] and min(similarity(item[0],e['attacker']),similarity(item[1],e['target']))>=.9]
        assert candidates,f'Missing previously reviewed event: {item}'
        winner=max(candidates,key=lambda e:e['count']);assert winner['id'] not in reviewed
        reviewed[winner['id']]=item
    events=[];evidence=ANALYSIS/'feed-evidence';evidence.mkdir(exist_ok=True)
    for i,e in enumerate(sorted(tracks,key=lambda e:e['first'])):
        obs=max(e['observations'],key=lambda o:o['confidence'])
        good=accepted(e);pair=e['kind']=='pair'
        event=dict(event_id=f'D{i+1:05}',first_seen_seconds=e['first'],last_seen_seconds=e['last'],
            timecode=tc(e['first']),attacker=e['attacker'],target=e['target'],
            attacker_team=e['attacker_team'],target_team=e['target_team'],
            attacker_team_source=e['attacker_team_source'],target_team_source=e['target_team_source'],
            observations=e['count'],ocr_confidence=e['confidence'],
            observation_times=sorted(o['t'] for o in e['observations']),
            source_file='',source_image='feed-evidence/'+Path(obs['frame']).stem+f'-r{obs["row"]+1}.jpg',
            evidence_seconds=obs['t'],raw_text=obs['raw'],status='machine_candidate',
            reviewed_at_seconds=None,
            event_kind=e['kind'],icon_class=e['icon_class'] if pair else e['kind'],
            accepted_feed_entry=good,included_in_charts=good and pair and e['attacker_team']!='Unknown' and e['target_team']!='Unknown',
            model_agreement_observations=sum(o.get('model_agreement',False) for o in e['observations']),
            strong_model_agreement_observations=sum(o.get('model_agreement',False) and o['confidence']>=.92 for o in e['observations']),
            notes='Visible HUD display episode; four source observations per second. Names use temporal OCR consensus and remain unverified. Icon labels describe appearance, not confirmed final-kill semantics.')
        if not good:event['notes']+=' Retained for review; insufficient recognition support.'
        if e['id'] in reviewed:
            attacker,target,attacker_team,target_team,icon=reviewed[e['id']]
            event.update(attacker=attacker,target=target,attacker_team=attacker_team,target_team=target_team,
                attacker_team_source='manual visual review',target_team_source='manual visual review',
                icon_class=icon,status='reviewed',accepted_feed_entry=True,included_in_charts=True,
                reviewed_at_seconds=441.25,
                notes='Names, factions and icon appearance rechecked in native frame 441.25. Dense first/last observations retain automatic timing; icon semantics are not a validated final-kill classification.')
        events.append(event)
        out=ANALYSIS/event['source_image']
        if not out.exists():
            original=Image.open(ROOT/'frames'/obs['frame']).convert('RGB')
            panel=Image.new('RGB',(900,380),'#14171a');draw=ImageDraw.Draw(panel)
            draw.text((14,10),'NATIVE FEED / RECORDING '+tc(obs['t'])+' / highlighted row '+str(obs['row']+1),fill='#f1f1ed')
            panel.paste(original,(0,40));draw.rectangle((0,40+22+32*obs['row'],3,40+50+32*obs['row']),fill='#d52b27')
            panel.save(out,quality=91)
    d=json.loads((ANALYSIS/'data/match-data.json').read_text(encoding='utf-8'))
    baseline=copy.deepcopy(d);d['events']=events
    accepted_events=[e for e in events if e['accepted_feed_entry']]
    summary=d['summary'];summary.update(candidate_events=len(events),charted_events=sum(e['included_in_charts'] for e in events),reviewed_events=len(reviewed),
        accepted_feed_entries=len(accepted_events),single_name_notices=sum(e['event_kind']!='pair' for e in accepted_events),
        feed_frames=len(records),feed_start_seconds=min(times),feed_end_seconds=max(times),feed_sample_gap_seconds=.25)
    d['feed_method']=dict(version=2,sampling_hz=4,recognizers=['English PP-OCRv4','English PP-OCRv5'],
        grouping='Feed-row continuity and temporal name consensus; simultaneous rows preserved',
        inclusion='At least 3 source observations and paired OCR score >=0.80, or 2 observations with both models agreeing and score >=0.92',
        limits='One recorded POV. Hidden feed, distortion, short rows and unreadable names can still be missed. Counts are visible display episodes, not validated final kills.',
        validation_file='feed-validation.json')
    for key in ['tickets','maps','positions','scoreboard','strength']:
        if key in baseline:assert d[key]==baseline[key],f'Unrelated metric changed: {key}'
    stage=ROOT/'staged-data';stage.mkdir(exist_ok=True)
    (stage/'match-data.json').write_text(json.dumps(d,ensure_ascii=True,separators=(',',':')),encoding='utf-8')
    csvwrite(stage/'feed-events.csv',events,list(events[0]))
    csvwrite(stage/'feed-review-queue.csv',[e for e in events if not e['accepted_feed_entry']],list(events[0]))
    unresolved=[dict(video_seconds=r['t'],native_frame=r['frame'],row=o['row'],raw_text=o['raw_text'],reason='Could not recover a supported pair or single-name notice') for r in records for o in r.get('unparsed_rows',[])]
    csvwrite(stage/'unparsed-feed-rows.csv',unresolved,['video_seconds','native_frame','row','raw_text','reason'])
    roster_path=(ROOT/a.input).with_name(Path(a.input).stem+'-roster.json')
    roster=json.loads(roster_path.read_text())
    csvwrite(stage/'name-aliases.csv',[dict(ocr_name=n,canonical_name=m,method='Same-clan similarity >=0.92 to a frequent reading across both recognizers; unreviewed') for n,m in roster['aliases'].items()],['ocr_name','canonical_name','method'])
    (stage/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (stage/'feed-validation.json').write_text((ROOT/'evaluation.json').read_text(),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    print('STAGED ONLY: preserve manual reviewed entries and validate evidence before replacing published data')
