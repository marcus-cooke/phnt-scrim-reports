"""Dependency-free checks for the published static data and local asset links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,re,csv
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';errors=[]
class Links(HTMLParser):
    def __init__(self,path):super().__init__();self.path=path
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k not in ['src','href','poster'] or not v or v.startswith(('#','http:','https:','data:','mailto:')):continue
            if '__' in v:errors.append(f'Unexpanded placeholder: {self.path} {v}');continue
            target=(self.path.parent/unquote(urlsplit(v).path)).resolve()
            if not target.is_relative_to(DOCS.resolve()):errors.append(f'Asset outside site: {target}')
            elif not target.exists():errors.append(f'Missing asset: {target}')
for p in DOCS.rglob('*.html'):
    text=p.read_text(encoding='utf-8');Links(p).feed(text)
    if re.search(r'127\.0\.0\.1|localhost|file:///|C:\\\\Users',text):errors.append(f'Local-only URL/path in {p}')
catalog=json.loads((DOCS/'catalog.json').read_text())
configured={m['id']:m for m in json.loads((ROOT/'matches.json').read_text(encoding='utf-8'))}
assert {m['meta']['id'] for m in catalog}==set(configured)
for m in catalog:
    folder=DOCS/'matches'/m['meta']['id'];d=json.loads((folder/'data/match-data.json').read_text())
    flags=0
    for r in d['strength']['rows']:
        for team in ['blue','red','green']:
            value=r[team];expected=None if value is None else value>33
            assert r[team+'_over_33'] is expected,'Threshold flags inconsistent'
            if expected:flags+=1
        assert (folder/r['source_image']).is_file()
    assert flags==sum(s['over_33_readings'] for s in d['strength']['summary'])
    for e in d['events']:assert (folder/e['source_image']).is_file()
    if d.get('feed_method',{}).get('version')==2:
        known_clans=set(d['feed_method'].get('clan_teams',{'PHNT':'','PV':'','AK-P':'','AK':''}))
        gap=d['summary']['feed_sample_gap_seconds']
        assert d['summary']['feed_frames']==round((d['summary']['feed_end_seconds']-d['summary']['feed_start_seconds'])/gap)+1
        if m['meta']['id']=='2026-10-25':assert d['summary']['feed_frames']==24622 and gap==.25
        assert len({e['event_id'] for e in d['events']})==len(d['events'])
        for e in d['events']:
            observations=e['observation_times']
            assert len(set(observations))==len(observations)==e['observations'],'Count source frames, not recognizer invocations'
            assert min(observations)==e['first_seen_seconds'] and max(observations)==e['last_seen_seconds']
            assert e['evidence_seconds'] in observations,'Screenshot must come from an actual track observation'
            expected=(e['observations']>=3 and e['ocr_confidence']>=.8) or (e['observations']>=2 and e['strong_model_agreement_observations']>=2)
            for name in [e['attacker'],e['target']]:
                if name.upper() in known_clans:expected=False
                if ('[' in name or ']' in name) and not re.match(r'^\[[^\[\]\s]{1,12}\].+',name):expected=False
            if e['status']=='rejected_duplicate':
                assert e.get('review_decision')=='exclude_duplicate'
                assert any(p['event_id']==e.get('duplicate_of') and p['accepted_feed_entry'] for p in d['events'])
                expected=False
            assert e['accepted_feed_entry']==expected or e['status']=='reviewed'
            if e['included_in_charts']:
                assert e['accepted_feed_entry'] and e['event_kind']=='pair' and e['attacker_team']!='Unknown' and e['target_team']!='Unknown'
        assert d['summary']['charted_events']==sum(e['included_in_charts'] for e in d['events'])
        assert d['summary']['accepted_feed_entries']==sum(e['accepted_feed_entry'] for e in d['events'])
    def evidence_paths(value):
        if isinstance(value,dict):
            for key,v in value.items():
                if key in ['source_file','source_image','snapshot','peak_source_image'] and isinstance(v,str) and v:
                    assert v.startswith('assets/'),f'Nonpublic evidence path: {v}'
                    assert (folder/v).is_file(),f'Broken evidence reference: {v}'
                evidence_paths(v)
        elif isinstance(value,list):
            for item in value:evidence_paths(item)
    evidence_paths(d)
    for path in (folder/'data').glob('*.csv'):
        with path.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                for key in ['source_file','source_image','snapshot','peak_source_image']:
                    v=row.get(key)
                    if v:assert v.startswith('assets/') and (folder/v).is_file(),f'Broken CSV evidence reference in {path}: {v}'
    for clip in d['clips']:
        assert (folder/clip['src']).is_file();assert (folder/clip['poster']).is_file()
        assert (folder/clip['src']).stat().st_size<30_000_000
    if m['meta']['id']=='2026-10-25':
        assert m['meta']['phnt_team']=='Blue'
        assert min(r['video_seconds'] for r in d['tickets'])>=300
        assert min(r['video_seconds'] for r in d['strength']['rows'])>=300
        assert all(e['first_seen_seconds']>=300 for e in d['events'])
        assert all(c['start_seconds']>=300 for c in d['clips'])
        assert m['meta']['final_scores']=={'Blue':100,'Red':80,'Green':62}
        assert d['scoreboard']==[], 'Never reuse the first recording scoreboard'
    else:assert m['meta']['phnt_team']==configured[m['meta']['id']]['phnt_team']
    if d.get('source_recording') and m['meta']['id']=='wdl-phantom-scrim-2':
        provenance=json.loads((folder/'data/recording-provenance.json').read_text())
        assert m['meta']['date_iso']==provenance['recording_date']=='2026-11-08'
        assert m['meta']['opponents']==provenance['opponents']==['RMNT','HTD']
        assert m['meta']['league']['fixture_number']==114
        assert m['meta']['league']['result_status']=='Under review'
        assert (provenance['source_video_width'],provenance['source_video_height'])==(1920,804)
        assert provenance['verified_result']['Blue']==100 and provenance['verified_result']['Green']==88 and provenance['verified_result']['Red']==75
        assert d['summary']['feed_frames']==13420 and d['summary']['feed_sample_gap_seconds']==.5
        assert len(d['scoreboard'])==10 and len({r['player'] for r in d['scoreboard']})==10
        assert sum(e['status']=='reviewed' for e in d['events'])==10
        assert all(.25<=e['first_seen_seconds']<=e['last_seen_seconds']<=6709.75 for e in d['events'])
        assert {s['team']:s['peak'] for s in d['strength']['summary']}=={'Blue':45,'Red':41,'Green':41}
        with (folder/'data/strength-model-reads.csv').open(encoding='utf-8-sig',newline='') as f:
            independent={(float(r['video_seconds']),r['team']):r for r in csv.DictReader(f)}
        for r in d['strength']['rows']:
            for team in ['Blue','Red','Green']:
                key=team.lower();audit=independent[(r['video_seconds'],team)]
                if r[key+'_status']=='machine_read':
                    assert audit['decision']=='machine_consensus'
                    assert int(audit['english_v4'])==int(audit['english_v5'])==r[key]
                    assert min(float(audit['v4_confidence']),float(audit['v5_confidence']))>=.92
                if '3-versus-5' in audit['reason']:assert r[key] is None or r[key+'_status']=='reviewed'
        for team in ['blue','red','green']:
            values=[r[team] for r in d['tickets'] if r[team] is not None]
            assert values==sorted(values),'Accepted ticket progression must be monotonic'
    if m['meta']['id']=='2026-11-22':
        meta=m['meta'];assert meta['category']=='phnt' and meta['recording_owner']=='PHNT'
        assert meta['phnt_team']=='Blue' and meta['final_scores']=={'Blue':96,'Red':100,'Green':96}
        assert meta['result']=='2nd place' and meta['opponents']==['AK','PMF']
        assert min(r['video_seconds'] for r in d['tickets'])>=370
        assert min(r['video_seconds'] for r in d['strength']['rows'])>=370
        assert all(370<=e['first_seen_seconds']<=e['last_seen_seconds']<8205 for e in d['events'])
        assert all(c['start_seconds']>=370 for c in d['clips'])
        assert d['summary']['feed_frames']==31340 and d['summary']['feed_sample_gap_seconds']==.25
        assert d['summary']['feed_start_seconds']==370 and d['summary']['feed_end_seconds']==8204.75
        assert d['ticket_anchor_count']==29 and d['scoreboard']==[]
        provenance=json.loads((folder/'data/recording-provenance.json').read_text())
        assert d['feed_method']['clan_teams']==provenance['clan_factions']
        assert provenance['recording_date']=='2026-11-22' and provenance['category']=='phnt'
        assert provenance['verified_result']==meta['final_scores']
        assert (provenance['source_video_width'],provenance['source_video_height'])==(3440,1440)
        with (folder/'data/strength-model-reads.csv').open(encoding='utf-8-sig',newline='') as f:
            reads={(float(r['video_seconds']),r['team']):r for r in csv.DictReader(f)}
        for r in d['strength']['rows']:
            for team in ['Blue','Red','Green']:
                if r[team.lower()+'_status']=='machine_read':
                    audit=reads[(r['video_seconds'],team)]
                    assert audit['decision']=='machine_consensus'
                    assert int(audit['english_v4'])==int(audit['english_v5'])==r[team.lower()]
                    assert min(float(audit['v4_confidence']),float(audit['v5_confidence']))>=.92
        for team in ['blue','red','green']:
            values=[r[team] for r in d['tickets'] if r[team] is not None]
            assert values==sorted(values),'Accepted tickets must be monotonic'
    print(m['meta']['id'],len(d['tickets']),'ticket rows;',len(d['events']),'feed candidates;',flags,'strength flags;',len(d['clips']),'clips')
for p in DOCS.rglob('*'):
    if p.is_file() and p.stat().st_size>50_000_000:errors.append(f'Oversized file {p}')
if errors:raise SystemExit('\n'.join(errors))
size=sum(p.stat().st_size for p in DOCS.rglob('*') if p.is_file())
assert not list(DOCS.rglob('*.mp4')),'Video clips stay offline; publish screenshots and data only'
assert size<950*1024**2,'Public package exceeds the 950 MiB budget; keep video media offline before publishing'
print(f'PASS: static links, no local server dependencies, threshold >33, faction mapping, new-round boundary; {size/1024**2:.1f} MiB total')
