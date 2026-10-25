"""Dependency-free checks for the published static data and local asset links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,re
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
assert {m['meta']['id'] for m in catalog}=={'2026-10-24','2026-10-25'}
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
    else:assert m['meta']['phnt_team']=='Green'
    print(m['meta']['id'],len(d['tickets']),'ticket rows;',len(d['events']),'feed candidates;',flags,'strength flags;',len(d['clips']),'clips')
for p in DOCS.rglob('*'):
    if p.is_file() and p.stat().st_size>50_000_000:errors.append(f'Oversized file {p}')
if errors:raise SystemExit('\n'.join(errors))
size=sum(p.stat().st_size for p in DOCS.rglob('*') if p.is_file())
print(f'PASS: static links, no local server dependencies, threshold >33, faction mapping, new-round boundary; {size/1024**2:.1f} MiB total')
