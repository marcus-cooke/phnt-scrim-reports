"""Select count readings supported by two English models, keeping disagreement."""
import argparse,csv,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();root=Path(a.output)
rows=[json.loads(s) for s in (root/'strength-independent.jsonl').read_text().splitlines()]
audit=[]
for r in rows:
    r['original_reads']=r['reads'];effective=[]
    for i,team in enumerate(['Blue','Red','Green']):
        (v4,s4),(v5,s5)=r['english_v4'][i],r['english_v5'][i]
        reason=''
        if v4!=v5:reason='English recognizers disagree'
        elif not re.fullmatch(r'\d{2}',v4.strip()):reason='Not an exact two-digit reading'
        elif min(s4,s5)<.92:reason='Below 0.92 in an English recognizer'
        elif team=='Green' and v4.startswith('5'):reason='Unresolved 3-versus-5 first digit in small green HUD; withheld for visual review'
        effective.append([v4,min(s4,s5)] if not reason else ['',0.])
        audit.append(dict(video_seconds=r['video_seconds'],team=team,original_text=r['original_reads'][i][0],
            english_v4=v4,v4_confidence=s4,english_v5=v5,v5_confidence=s5,
            decision='unavailable' if reason else 'machine_consensus',reason=reason,
            source_image='keyframes/'+r['source_file']))
    r['reads']=effective
(root/'strength-raw.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
with (root/'data/strength-model-reads.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(audit[0]));w.writeheader();w.writerows(audit)
print('Selected',sum(r['decision']=='machine_consensus' for r in audit),'count readings;',sum('3-versus-5' in r['reason'] for r in audit),'ambiguous green counts withheld')
