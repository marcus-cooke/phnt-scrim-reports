"""Package existing local analysis into a buildless, self-contained clan site.

Local usage: python tools/build_site.py --templates PATH --analysis ID=PATH
  --analysis ID=PATH --video ID=PATH --video ID=PATH
No original video or analysis environment is copied into the public site.
"""
from pathlib import Path
import argparse,json,csv,copy,zipfile,re,subprocess,concurrent.futures,math
from PIL import Image,ImageDraw
import cv2,imageio_ffmpeg

REPO=Path(__file__).resolve().parents[1];DOCS=REPO/'docs'
COLORS={'Blue':'#59b9f3','Red':'#f4777d','Green':'#65d998'}
def mapping(values):return dict(s.split('=',1) for s in values)
def tc(t):return f'{int(t)//3600:02}:{int(t)//60%60:02}:{int(t)%60:02}'
def pack_match(meta,source,video,templates):
    dest=DOCS/'matches'/meta['id'];assets=dest/'assets';data=dest/'data';clipsdir=dest/'clips'
    for p in [assets,data,clipsdir]:p.mkdir(parents=True,exist_ok=True)
    d=json.loads((source/'data/match-data.json').read_text());d['meta']=meta
    d['summary']['phnt_team']=meta['phnt_team']
    images={}
    def register(s):
        if not isinstance(s,str):return s
        if s.startswith('keyframes/') and (source/s).is_file():
            rel='assets/hud-'+Path(s).stem+'.webp';images[s]=rel;return rel
        if (s.startswith('evidence/') or s.startswith('sample-')) and (source/s).is_file():
            rel='assets/'+Path(s).stem+'.webp';images[s]=rel;return rel
        if s.startswith('evidence/') or s.startswith('sample-'):return None
        return s
    def rewrite(obj):
        if isinstance(obj,dict):
            for k,v in list(obj.items()):
                if k=='source_file' and isinstance(v,str):obj[k]=register('keyframes/'+v) if v else ''
                elif isinstance(v,str):obj[k]=register(v)
                else:rewrite(v)
        elif isinstance(obj,list):
            for v in obj:rewrite(v)
    rewrite(d)
    # Public evidence preserves the native feed and ticket/person-count strips
    # with an overview thumbnail, dropping only unused terrain between them.
    def convert(item):
        old,rel=item;out=dest/rel
        if out.exists():return
        im=Image.open(source/old).convert('RGB')
        if old.startswith('keyframes/'):
            panel=Image.new('RGB',(760,685),'#101518');draw=ImageDraw.Draw(panel)
            draw.text((12,5),'RECORDED HUD / '+tc(int(Path(old).stem)/1000),fill='#cbd8d4')
            panel.paste(im.crop((0,0,760,225)),(0,25))
            draw.text((12,258),'POINTS AND PERSON-ICON COUNTS',fill='#cbd8d4')
            panel.paste(im.crop((35,640,395,755)),(12,278))
            panel.paste(im.crop((0,760,688,1048)),(36,397));im=panel
        im.save(out,'WEBP',quality=83,method=4)
    # Always retain native outcome proof, also available independently of clips.
    outcome=assets/'outcome.webp'
    if not outcome.exists():
        cap=cv2.VideoCapture(str(video));cap.set(cv2.CAP_PROP_POS_MSEC,meta['outcome_seconds']*1000);ok,bgr=cap.read();cap.release()
        if not ok:raise RuntimeError('Cannot extract outcome proof')
        Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)).save(outcome,'WEBP',quality=88)
    meta['outcome_image']='assets/outcome.webp'
    # Selected self-contained excerpts, rather than a dependency on a local
    # video server or uploads of the multi-gigabyte original recordings.
    highlights=[]
    for s in d['strength']['summary']:highlights.append((s['peak_seconds'],f"{s['team']} strength peak: {s['peak']}"))
    reviewed=[e for e in d['events'] if e['status']=='reviewed']
    if reviewed:highlights.append((reviewed[len(reviewed)//2]['first_seen_seconds'],'Reviewed feed sample'))
    native=[m for m in d['maps'] if m.get('native_snapshot')]
    for i in sorted(set([0,len(native)//2])):
        if native:highlights.append((native[i]['representative_seconds'],'Map observation'))
    highlights.append((meta['outcome_seconds'],'Final result'))
    clips=[];dur=d['summary']['video_seconds']
    for t,label in highlights:
        start=max(0,min(dur-10,t-3));end=min(dur,start+10);ident=f'{round(start*1000):010d}'
        rel=f'clips/{ident}.mp4';out=dest/rel;poster=f'clips/{ident}.webp'
        if not out.exists():
            command=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y','-hwaccel','cuda','-ss',str(start),'-i',str(video),'-t','10','-map','0:v:0','-map','0:a:0?','-vf','scale=1720:720,fps=30','-c:v','h264_nvenc','-preset','p4','-cq','28','-c:a','aac','-b:a','96k','-movflags','+faststart',str(out)]
            result=subprocess.run(command,capture_output=True,timeout=60)
            if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
        refs=list(sorted((source/'keyframes').glob('*.jpg')))
        near=min(refs,key=lambda p:abs(int(p.stem)/1000-t))
        if not (dest/poster).exists():Image.open(near).crop((0,760,688,1048)).save(dest/poster,'WEBP',quality=84)
        clips.append(dict(title=label,video_seconds=t,start_seconds=start,end_seconds=end,src=rel,poster=poster,timecode=tc(t)))
        print(meta['id'],label,'clip ready',flush=True)
    d['clips']=clips
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(convert,list(images.items())))
    (data/'match-data.json').write_text(json.dumps(d,ensure_ascii=True,separators=(',',':')),encoding='utf-8')
    # Export CSVs with public asset URLs; strip machine-specific local paths.
    for p in (source/'data').glob('*.csv'):
        with p.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames
            if not fields:continue
            rows=list(reader)
        with (data/p.name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
            for row in rows:
                for k,v in row.items():
                    if k=='source_file' and v:v=images.get('keyframes/'+v,v)
                    elif k in ['source_image','snapshot','peak_source_image'] and v and v.startswith(('keyframes/','evidence/','sample-')):v=images.get(v,'')
                    else:v=images.get(v,v)
                    row[k]=v
                writer.writerow(row)
    (data/'team-strength.json').write_text(json.dumps(d['strength'],separators=(',',':')))
    if not d['scoreboard']:
        (data/'scoreboard-visible-phnt.csv').write_text('player,kills,assists,deaths,revives,status\n',encoding='utf-8-sig')
    (data/'README.txt').write_text(f'''PHNT SCRIM - {meta['date']}
PHNT faction: {meta['phnt_team']}. Video: {meta['recording']}.
All times are elapsed recording seconds. {meta['notes']}
Tickets are point totals; person-icon counts are a separate HUD metric.
Strength flags use strictly >33 (34+). Blank readings remain unknown.
Feed charts include reviewed entries or repeated, high-confidence machine
candidates. These are observed feed entries, not confirmed final kills.
Sampling gaps, unknown clan mappings, OCR errors, state-change deduplication
and one-POV visibility limit completeness. Do not compare sampled feed totals
as a measure of overall team performance across matches.
Map symbols are anonymous observations; no continuous routes are inferred.
Public source_image/source_file fields refer to compact screenshots under
assets/, relative to the match report. Native feed and HUD strips are retained.
Only selected excerpts are included; original videos are not hosted.
Manual records and review queues remain separate. See the report's Data &
coverage section for sampling coverage and machine confidence rules.
''',encoding='utf-8')
    with zipfile.ZipFile(dest/'match-data.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in data.iterdir():z.write(p,p.name)
    html=(templates/'report-template.html').read_text(encoding='utf-8')
    strength=(templates/'strength-ui.js').read_text(encoding='utf-8')
    strength=strength.replace("const D=JSON.parse(document.getElementById('match-data').textContent).strength;","const rootData=JSON.parse(document.getElementById('match-data').textContent); const D=rootData.strength; const phntTeam=rootData.meta.phnt_team;")
    strength=strength.replace("team==='Green'","team===phntTeam").replace("s.team==='Green'","s.team===phntTeam")
    strength=strength.replace('const x=t=>62+(t-480)/(6240-480)*1000;', 'const start=rootData.meta.analysis_start_seconds,end=rootData.summary.video_seconds;const x=t=>62+(t-start)/(end-start)*1000;')
    strength=strength.replace('min="481" max="6198"',f'min="{meta["analysis_start_seconds"]}" max="{math.floor(dur)}"')
    panel=(templates/'strength-panel.html').read_text(encoding='utf-8')
    panel=panel.replace('min="481" max="6198"',f'min="{meta["analysis_start_seconds"]}" max="{math.floor(dur)}"')
    panel=panel.replace('Twenty-five ambiguous exceedance candidates were checked manually, correcting several OCR errors and restoring valid readings. Initial run starts and peaks were inspected visually. The entire series is not manually verified.','Selected peaks and sample records were checked visually. Manual corrections and unresolved reads are retained separately. The entire series is not manually verified.')
    nav='<button role="tab" id="tab-strength" aria-selected="false" aria-controls="strength" data-tab="strength">Team strength</button>'
    html=html.replace('<button role="tab" id="tab-feed"',nav+'<button role="tab" id="tab-feed"')
    html=html.replace('<section id="feed"',panel+'<section id="feed"')
    html=html.replace('filteredEvents:()=>filtered.length','filteredEvents:()=>filtered.length,inspect')
    html=html.replace('</body>','<script>'+strength+'</script></body>')
    # Remove duplicate masthead in the embedded report, retaining report tabs.
    aa=html.index('<header>');bb=html.index('<nav',aa);html=html[:aa]+'<header>'+html[bb:]
    html=html.replace('6201.583333',str(dur)).replace('max="6200"',f'max="{math.floor(dur)}"').replace('Math.min(6200,','Math.min('+str(math.floor(dur))+',')
    html=html.replace('min="480"',f'min="{meta["analysis_start_seconds"]}"').replace('Math.max(480,','Math.max('+str(meta['analysis_start_seconds'])+',')
    html=html.replace("e.attacker_team==='Green'","e.attacker_team===D.meta.phnt_team").replace("e.target_team==='Green'","e.target_team===D.meta.phnt_team")
    html=html.replace('Green · PHNT / Manticore','Green · '+('PHNT / ' if meta['phnt_team']=='Green' else '')+'Manticore')
    if meta['phnt_team']=='Blue':html=html.replace('Blue · Lonestar','Blue · PHNT / Lonestar')
    html=html.replace('All eight manually checked feed entries are included.',f'All {d["summary"]["reviewed_events"]} manually checked feed entries are included.')
    if meta['id']=='2026-10-25':
        html=html.replace('36 manually reviewed anchors','22 manually reviewed anchors')
        html=html.replace('Five visible PHNT rows at 1:43:15 · manually read','No verified per-player scoreboard totals extracted for this recording.')
        html=html.replace('These are scoreboard totals for the visible players. They are independent of the sampled feed counts and do not cover the full PHNT roster.','No per-player totals are carried over from the other match. The final result is independently verified from the result screen.')
        html=html.replace('PHNT → Green; 26TH → Red; TLL, 1G and N1 → Blue','PHNT → Blue; PV → Red; AK-P and AK → Green')
        html=html.replace('Green symbols','Friendly-coloured symbols').replace('Green components','Friendly-coloured components').replace('green symbol candidates','friendly-coloured symbol candidates')
    # Host only portable links and selected clips. No localhost or original file URL.
    a=html.index("$('play-source').onclick=");b=html.index('\nlet page=',a)
    html=html[:a]+'''$('play-source').onclick=()=>{const c=D.clips.find(c=>currentTime>=c.start_seconds&&currentTime<=c.end_seconds);if(!c)return;const v=$('source-video');v.pause();v.hidden=false;v.src=c.src;v.addEventListener('loadedmetadata',()=>{v.currentTime=Math.max(0,currentTime-c.start_seconds);v.play().catch(()=>{})},{once:true});v.load();};'''+html[b:]
    html=html.replace('currentTime=t;',"currentTime=t;const hostedClip=D.clips.find(c=>t>=c.start_seconds&&t<=c.end_seconds);$('play-source').hidden=!hostedClip;")
    html=html.replace('Play 12-second source excerpt','Play hosted source excerpt')
    html=html.replace('<a href="findings.txt">Original proof-of-concept notes</a>','<a href="data/README.txt">Data notes</a>')
    html=re.sub(r'<p>Original: C:.*?</p>','<p>Original video remains offline. Selected excerpts and screenshots are included.</p>',html)
    html=html.replace('<a href="charts/match-overview.png">Chart image</a>','<a href="data/match-data.json">Combined dataset</a>')
    html=html.replace('<a href="charts/team-strength.png">Chart image ↗</a>','')
    clipnav='<button role="tab" id="tab-clips" aria-selected="false" aria-controls="clips" data-tab="clips">Evidence clips</button>'
    html=html.replace('<button role="tab" id="tab-data"',clipnav+'<button role="tab" id="tab-data"')
    cliphtml='<section id="clips" role="tabpanel" aria-labelledby="tab-clips" hidden><h2>Selected source excerpts</h2><p class="muted">Portable H.264 excerpts · recording timestamps · original videos remain offline</p><div class="maps">'
    for c in clips:cliphtml+=f'<article><h3>{c["title"]} · {c["timecode"]}</h3><video controls preload="none" playsinline poster="{c["poster"]}" src="{c["src"]}" style="width:100%"></video></article>'
    cliphtml+='</div></section>';html=html.replace('<footer>',cliphtml+'<footer>')
    html=html.replace('<script id="match-data"', '<script id="match-data"')
    html=html.replace('__MATCH_DATA__',json.dumps(d,ensure_ascii=True,separators=(',',':')).replace('</','<\\/'))
    sync='''<script>document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('video').forEach(v=>v.pause());window.parent.postMessage({type:'report-tab',tab:b.dataset.tab},location.origin)}));const target=document.getElementById('tab-'+location.hash.slice(1));if(target)target.click();</script>'''
    html=html.replace('</body>',sync+'</body>')
    (dest/'index.html').write_text(html,encoding='utf-8')
    summary=dict(meta=meta,summary=d['summary'],strength=d['strength']['summary'],clips=len(clips),points=[{k:r[k] for k in ['video_seconds','blue','red','green']} for r in d['tickets']])
    print(meta['id'],'packaged',len(images),'screenshots',flush=True)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--templates',required=True);p.add_argument('--analysis',action='append',required=True);p.add_argument('--video',action='append',required=True);args=p.parse_args()
    analyses=mapping(args.analysis);videos=mapping(args.video);DOCS.mkdir(exist_ok=True)
    catalog=[]
    for m in json.loads((REPO/'matches.json').read_text()):catalog.append(pack_match(m,Path(analyses[m['id']]),Path(videos[m['id']]),Path(args.templates)))
    (DOCS/'catalog.json').write_text(json.dumps(catalog,separators=(',',':')))
    index=(REPO/'site/index.html').read_text(encoding='utf-8').replace('__CATALOG__',json.dumps(catalog,ensure_ascii=True,separators=(',',':')))
    (DOCS/'index.html').write_text(index,encoding='utf-8');(DOCS/'.nojekyll').write_text('')
    with zipfile.ZipFile(DOCS/'all-match-data.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((DOCS/'matches').glob('*/data/*')):z.write(p,str(p.relative_to(DOCS/'matches')))
    print('Static clan site ready',flush=True)
