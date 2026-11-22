"""Archive hosted excerpts offline and retain screenshot/data-only reports.

Run only when removing clips is requested. The archive must be outside docs.
Structured gameplay readings and screenshot bytes are preserved.
"""
from pathlib import Path
import argparse,json,re,zipfile,shutil,hashlib
from build_scouting import render_page
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--original-scouting-backup');a=p.parse_args()
archive=Path(a.archive).resolve();assert not archive.is_relative_to(DOCS.resolve());archive.mkdir(parents=True,exist_ok=True)
originals=Path(a.original_scouting_backup).resolve() if a.original_scouting_backup else None
manifest=json.loads((archive/'manifest.json').read_text(encoding='utf-8')) if (archive/'manifest.json').exists() else []
for path in sorted(DOCS.rglob('*.mp4')):
    resolved=path.resolve();assert resolved.is_relative_to(DOCS.resolve())
    if path.name.endswith('.compact.mp4'):
        path.unlink();continue
    rel=path.relative_to(DOCS);source=path
    if originals and rel.parts[0]=='scouting' and (originals/Path(*rel.parts[1:])).is_file():source=originals/Path(*rel.parts[1:])
    target=archive/rel;target.parent.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if not target.exists():shutil.copyfile(source,target)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==digest,'Archive must verify before removal'
    manifest.append(dict(path=rel.as_posix(),bytes=target.stat().st_size,sha256=digest))
    (archive/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    path.unlink()
for folder in sorted((DOCS/'matches').iterdir()):
    data=folder/'data/match-data.json'
    if not data.is_file():continue
    d=json.loads(data.read_text(encoding='utf-8'));d['clips']=[]
    payload=json.dumps(d,ensure_ascii=True,separators=(',',':'));data.write_text(payload,encoding='utf-8')
    html=(folder/'index.html').read_text(encoding='utf-8')
    html=re.sub(r'(<script id="match-data" type="application/json">).*?(</script>)',lambda m:m[1]+payload.replace('</','<\\/')+m[2],html,flags=re.S)
    html=re.sub(r'<button\b[^>]*\bid="tab-clips"[^>]*>.*?</button>','',html,flags=re.S)
    html=re.sub(r'<section\b[^>]*\bid="clips"[^>]*>.*?</section>','',html,flags=re.S)
    html=html.replace('<button id="play-source"','<button hidden id="play-source"')
    html=html.replace('Only selected excerpts are included; original videos are not hosted.','Timestamped screenshots are included; video excerpts and originals stay offline.')
    html=html.replace('Original video remains offline. Selected excerpts and screenshots are included.','Original video and excerpts remain offline. Timestamped screenshots are included.')
    (folder/'index.html').write_text(html,encoding='utf-8')
    notes=folder/'data/README.txt'
    notes.write_text(notes.read_text(encoding='utf-8').replace('Only selected excerpts are included; original videos are not hosted.','Timestamped screenshots are included; video excerpts and originals stay offline.'),encoding='utf-8')
    with zipfile.ZipFile(folder/'match-data.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted((folder/'data').iterdir()):z.write(f,f.name)
catalog=json.loads((DOCS/'catalog.json').read_text(encoding='utf-8'))
for row in catalog:row['clips']=0
(DOCS/'catalog.json').write_text(json.dumps(catalog,separators=(',',':')),encoding='utf-8')
reports=[('',ROOT/'site/scouting/report.json')]+[(f.stem,f) for f in sorted((ROOT/'site/scouting/reports').glob('*.json'))]
for slug,source in reports:
    report=json.loads(source.read_text(encoding='utf-8'))
    for item in report['evidence']:item.pop('clip',None)
    payload=json.dumps(report,indent=2,ensure_ascii=False)
    source.write_text(payload,encoding='utf-8');folder=DOCS/'scouting'/slug
    (folder/'data/scouting-report.json').write_text(payload,encoding='utf-8')
    (folder/'index.html').write_text(render_page(report,slug),encoding='utf-8')
with zipfile.ZipFile(DOCS/'all-match-data.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted((DOCS/'matches').glob('*/data/*')):z.write(f,f.relative_to(DOCS/'matches').as_posix())
assert not list(DOCS.rglob('*.mp4'))
print('Archived and removed',len(manifest),'hosted clips. Gameplay readings and native screenshots retained.')
