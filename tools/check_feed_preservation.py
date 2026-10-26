"""Capture/compare unrelated report data around a feed-only rebuild."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--capture',action='store_true');a=p.parse_args()
values={}
for day in ['2026-10-24','2026-10-25']:
    d=json.loads((ROOT/f'docs/matches/{day}/data/match-data.json').read_text())
    keys=['tickets','maps','positions','scoreboard','strength']
    if day=='2026-10-24':keys+=['events','summary']
    for key in keys:
        if key in d:values[day+'/'+key]=hashlib.sha256(json.dumps(d[key],sort_keys=True).encode()).hexdigest()
snapshot=ROOT/'qa/feed-preservation.json'
if a.capture:
    if snapshot.exists():
        prior=json.loads(snapshot.read_text())
        assert all(values.get(k)==v for k,v in prior.items()),'Existing captured metrics changed; never replace their baseline'
        assert set(values)>set(prior),'No new metric keys to capture'
    snapshot.parent.mkdir(exist_ok=True);snapshot.write_text(json.dumps(values,indent=2))
    print('Captured unrelated metrics and complete older-game feed')
else:
    expected=json.loads(snapshot.read_text());assert values==expected,'A metric outside the latest-game feed changed'
    print('PASS: tickets, maps, symbols, scoreboard, strength, and older-game feed unchanged')
