"""Build this POV's feed, retaining automatic output and separate visual decisions."""
import argparse,os,sys,json,csv,re,collections,difflib
from pathlib import Path
import cv2
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--repo',required=True);a=p.parse_args()
analysis=Path(a.output).resolve();root=analysis/'feed-v2'
os.environ['PHNT_ANALYSIS_ROOT']=str(analysis);sys.path.insert(0,str(Path(a.repo)/'tools/feed_analysis'))
import track_dense_feed as tracker
import combine_feed_passes as combiner
from annotate_dense_feed import coloured_pixels
tracker.TEAM={'PHNT':'Blue','HTD':'Red','GIII':'Red'}
tracker.TAG=re.compile(r'(?:\[|\b)(PHNT|HTD|GIII)[\]\| ]*',re.I)
original_names=tracker.names;original_clean=tracker.clean
def clean(s):
    s=re.sub(r'^\[[\W_]{0,6}\]','',s)
    return original_clean(s)
tracker.clean=clean
def names(s):
    s=re.sub(r'\[(G[Il1]{2,4})\]', '[GIII]',s,flags=re.I)
    s=re.sub(r'^[I1LTFEd]?(HTD|PHNT)[Ij1L\]|]',r'[\1]',s)
    return original_names(s)
tracker.names=names;combiner.names=names
# An isolated OCR name does not establish that a one-name notice was displayed.
tracker.notice_kind=lambda path,row:None
native=root/'ocr-en-native.jsonl';alternate=root/'ocr-en-v5-rerec.jsonl'
records=[json.loads(s) for s in native.read_text().splitlines()]
assert len(records)==len({r['frame'] for r in records})
combiner.combine(native,alternate,root/'combined-rows-all.jsonl',expected=len(records))
records=[json.loads(s) for s in (root/'combined-rows-all.jsonl').read_text().splitlines() if json.loads(s)['t']<6710]
assert len(records)==13420 and records[0]['t']==.25 and records[-1]['t']==6709.75
(root/'combined-rows.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
tracks=tracker.run(root/'combined-rows.jsonl')
for e in tracks:
    votes={side:collections.Counter() for side in ['attacker','target']}
    for o in sorted(e['observations'],key=lambda o:-o['confidence'])[:12]:
        im=cv2.imread(str(root/'frames'/o['frame']));y=36+32*o['row']
        for side,x0,x1 in [('attacker',46,65),('target',int(o['target_end'])-8,int(o['target_end'])+26)]:
            if x1<=x0 or x0<0 or x1>900:continue
            team=coloured_pixels(im[max(0,y-10):y+11,x0:x1])
            if team:votes[side][team]+=1
    for side in votes:
        clan=e[side][1:].split(']')[0] if e[side].startswith('[') else ''
        known=tracker.TEAM.get(clan);vote=votes[side].most_common(1)
        glyph=vote[0][0] if vote and vote[0][1]>=3 and vote[0][1]>=.8*sum(votes[side].values()) else None
        e[side+'_team']=known or glyph or 'Unknown'
        e[side+'_team_source']='clan' if known else 'repeated glyph' if glyph else 'unresolved'
    e['glyph_team_votes']={side:dict(v) for side,v in votes.items()}
(root/'tracks-automatic.json').write_text(json.dumps(tracks))
events=[]
def tc(t):return f'{int(t)//3600:02}:{int(t)//60%60:02}:{t%60:06.3f}'
for e in tracks:
    o=max(e['observations'],key=lambda o:o['confidence']);accepted=tracker.accepted(e)
    events.append(dict(event_id=e['id'],first_seen_seconds=e['first'],last_seen_seconds=e['last'],
        timecode=tc(e['first']),attacker=e['attacker'],target=e['target'],attacker_team=e['attacker_team'],target_team=e['target_team'],
        attacker_team_source=e['attacker_team_source'],target_team_source=e['target_team_source'],
        observations=e['count'],observation_times=sorted(o['t'] for o in e['observations']),ocr_confidence=e['confidence'],
        evidence_seconds=o['t'],source_file='',source_image='feed-evidence/'+Path(o['frame']).stem+f'-r{o["row"]+1}.jpg',
        raw_text=o['raw'],status='machine_candidate',event_kind='pair',icon_class='unclassified',accepted_feed_entry=accepted,
        included_in_charts=accepted and e['attacker_team']!='Unknown' and e['target_team']!='Unknown',
        model_agreement_observations=sum(o.get('model_agreement',False) for o in e['observations']),
        strong_model_agreement_observations=sum(o.get('model_agreement',False) and o['confidence']>=.92 for o in e['observations']),
        notes='Two source observations per second from a 1920x804 POV. Temporal OCR names remain unverified. Visible feed display episodes, not verified final kills.'))
automatic_accepted=sum(e['accepted_feed_entry'] for e in events)
# Names, faction glyphs and icon appearances read directly from the three retained
# source contact sheets. These checks are separate from automatic acceptance.
manual=[(.25+900,'Spike','[PHNT]Jensen','Green','Blue',0,'skull-marked'),
 (.25+900,'Ivary','[HTD]Ceddy','Green','Red',1,'unclassified'),
 (.25+902,'hjp','[GIII]Falk','Green','Red',0,'skull-marked'),
 (.25+902,'[PHNT]BlackShadow','DuckPuncher','Blue','Green',3,'unclassified'),
 (.25+904,'[PHNT]Chamberz','[HTD]OhhMagxz','Blue','Red',0,'unclassified'),
 (.25+3304,'[PHNT]Silverhand','[HTD]K1SHO','Blue','Red',1,'unclassified'),
 (.25+3304,'[GIII]Bot Yuri','Zanshin','Red','Green',0,'unclassified'),
 (.25+3304,'hjp','[GIII]leeven.berlin','Green','Red',2,'unclassified'),
 (.25+3310,'j','[HTD]Kanonenfutter','Green','Red',0,'unclassified'),
 (.25+6004,'[PHNT]fishu','[HTD]D3rPhil','Blue','Red',0,'unclassified')]
decisions=[];used=set()
for t,attacker,target,ateam,bteam,row,icon in manual:
    matches=[e for e in events if e['event_id'] not in used and e['first_seen_seconds']-1<=t<=e['last_seen_seconds']+1 and
        min(tracker.similarity(attacker,e['attacker']),tracker.similarity(target,e['target']))>=.75]
    if matches:
        e=max(matches,key=lambda e:e['observations']);decision='correct_existing_candidate'
        # Choose an observed frame/row for the event's evidence; manual review time
        # can differ and is retained separately.
    else:
        e=dict(event_id=f'V{len(decisions)+1:05}',first_seen_seconds=t,last_seen_seconds=t,timecode=tc(t),
            observations=1,observation_times=[t],ocr_confidence=None,source_file='',evidence_seconds=t,
            source_image=f'feed-evidence/{round(t*1000):010d}-r{row+1}.jpg',raw_text='Manually read source row',
            event_kind='pair',model_agreement_observations=0,strong_model_agreement_observations=0)
        events.append(e);decision='add_visual_sample'
    used.add(e['event_id'])
    e.update(attacker=attacker,target=target,attacker_team=ateam,target_team=bteam,
        attacker_team_source='visual review',target_team_source='visual review',icon_class=icon,status='reviewed',
        reviewed_at_seconds=t,accepted_feed_entry=True,included_in_charts=True,
        notes='Names, faction glyphs and icon appearance visually reviewed at the separately logged sample time. Icon appearance does not establish final-kill semantics.')
    decisions.append(dict(event_id=e['event_id'],decision=decision,reviewed_at_seconds=t,attacker=attacker,target=target,
        attacker_team=ateam,target_team=bteam,icon_class=icon,source_image=e['source_image']))
evidence=analysis/'feed-evidence';evidence.mkdir(exist_ok=True)
for e in events:
    path=analysis/e['source_image']
    frame=f'{round(e["evidence_seconds"]*1000):010d}.png'
    original=Image.open(root/'frames'/frame).convert('RGB')
    panel=Image.new('RGB',(900,380),'#141820');draw=ImageDraw.Draw(panel)
    draw.text((12,10),'ENLARGED SOURCE FEED / '+tc(e['evidence_seconds'])+' / '+e['event_id'],fill='white')
    panel.paste(original,(0,40));row=int(re.search(r'-r(\d+)',path.stem)[1])-1
    draw.rectangle((0,40+22+32*row,3,40+50+32*row),fill='#d52b27');panel.save(path,quality=93)
d=json.loads((analysis/'data/match-data.json').read_text());d['events']=sorted(events,key=lambda e:e['first_seen_seconds'])
d['summary'].update(candidate_events=len(events),charted_events=sum(e['included_in_charts'] for e in events),
    reviewed_events=len(manual),accepted_feed_entries=sum(e['accepted_feed_entry'] for e in events),single_name_notices=0,
    feed_frames=len(records),feed_start_seconds=.25,feed_end_seconds=6709.75,feed_sample_gap_seconds=.5)
d['feed_method']=dict(version=2,sampling_hz=2,recognizers=['English PP-OCRv4','English PP-OCRv5'],
    inclusion='At least 3 distinct source frames and OCR score >=0.80, or 2 source frames with both recognizers agreeing at >=0.92; separate visual reviews.',
    limits='Small compressed source text. Unreadable and isolated single-name rows are not automatically classified. No whole-match accuracy or final-kill claim.',
    validation_file='feed-validation.json')
def write(name,rows,fields=None):
    with (analysis/'data'/name).open('w',encoding='utf-8-sig',newline='') as f:
        fields=fields or list(dict.fromkeys(k for r in rows for k in r))
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
write('feed-events.csv',d['events']);write('feed-review-queue.csv',[e for e in events if not e['accepted_feed_entry']],list(events[0]))
write('feed-manual-decisions.csv',decisions)
unparsed=[dict(video_seconds=r['t'],row=o['row'],raw_text=o['raw_text'],reason='No supported paired row recovered') for r in records for o in r.get('unparsed_rows',[])]
write('unparsed-feed-rows.csv',unparsed,['video_seconds','row','raw_text','reason'])
roster=json.loads((root/'combined-rows-all-roster.json').read_text())
write('name-aliases.csv',[dict(ocr_name=k,canonical_name=v,method='Same-clan temporal frequency and similarity; unreviewed') for k,v in roster['aliases'].items()],['ocr_name','canonical_name','method'])
(analysis/'data/feed-validation.json').write_text(json.dumps(dict(source_frames=len(records),sampling_hz=2,
    automatic_accepted_before_visual_review=automatic_accepted,visually_reviewed_entries=len(manual),
    visual_additions=sum(r['decision']=='add_visual_sample' for r in decisions),
    review_windows_seconds=[[900.25,910.25],[3300.25,3310.25],[6000.25,6010.25]],
    limitations='Selected visual spot checks only. Not a complete reference census, held-out evaluation, spelling accuracy or whole-match recovery estimate.'),indent=2))
(analysis/'data/match-data.json').write_text(json.dumps(d,separators=(',',':')))
(analysis/'data/summary.json').write_text(json.dumps(d['summary'],indent=2))
print(json.dumps(d['summary'],indent=2));print('Manual decisions',collections.Counter(x['decision'] for x in decisions))
