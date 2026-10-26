"""Recover HUD feed display episodes; retain raw observations and name votes.

This does not assert that every weapon/icon entry is a final kill.
"""
from pathlib import Path
import argparse,collections,difflib,json,re,os
import cv2

ROOT=Path(os.environ.get('PHNT_ANALYSIS_ROOT',str(Path(__file__).parent)))/'feed-v2'
TEAM={'PHNT':'Blue','PV':'Red','AK-P':'Green','AK':'Green'}
TAG=re.compile(r'(?:\[|\b)(PHNT|AK-P|AK|PV|III)[\]\| ]*',re.I)

def clean(s):
    s=s.replace('［','[').replace('］',']').strip()
    s=re.sub(r'\[?\d+\s*m\]?', '', s)
    s=re.sub(r'^[^A-Za-z0-9<\[]+','',s)
    return s.strip(' |.,:;')

def names(s):
    # OCR often turns the two brackets into I/L/1. Repair only known clan
    # prefixes at the start of a detector box; retain the original raw text.
    s=re.sub(r'^[I1LTFEd]?(AK-P|PHNT|PV|AK)[Ij1L\]|]',r'[\1]',s)
    matches=list(TAG.finditer(s));out=[]
    s=re.sub(r'\[AK\]P\]', '[AK-P]',s,flags=re.I)
    matches=list(TAG.finditer(s))
    if len(matches)==1:
        prefix=clean(s[:matches[0].start()])
        if re.fullmatch(r'[A-Za-z][A-Za-z0-9_. -]{2,25}',prefix) and prefix.upper() not in TEAM:out.append(prefix)
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(s)
        player=clean(s[m.end():end]).rstrip('[').strip()
        tag=m[1].upper()
        if tag=='AK' and player.startswith('P]'):tag='AK-P';player=player[2:]
        if len(player)>=2:out.append(f'[{tag}]{player}')
    if not out:
        m=re.search(r'\[([A-Za-z0-9_-]{1,12})\](.{2,40})',s)
        if m:
            tag=m[1].upper()
            if re.fullmatch(r'[IL1]{1,4}',tag):tag='III'
            out=[f'[{tag}]{clean(m[2])}']
    return out

def similarity(a,b):
    ca=a.split(']')[0] if a.startswith('[') and ']' in a else ''
    cb=b.split(']')[0] if b.startswith('[') and ']' in b else ''
    a=re.sub(r'\W','',a.split(']',1)[-1]).lower()
    b=re.sub(r'\W','',b.split(']',1)[-1]).lower()
    score=difflib.SequenceMatcher(None,a,b).ratio()
    if ca!=cb:
        # Temporally identical player text can repair a flickering clan read.
        return score*.96 if score>=.9 else 0
    return score

NOTICE_TEMPLATES=None
def notice_kind(path,row):
    global NOTICE_TEMPLATES
    if NOTICE_TEMPLATES is None:
        NOTICE_TEMPLATES={
            'single-name-skull':cv2.imread(str(ROOT/'validation-2400/0002445000.png'),0)[25:47,58:78],
            'single-name-hand':cv2.imread(str(ROOT/'validation-5880/0005931000.png'),0)[25:47,56:80]}
    im=cv2.imread(str(path),0)
    if im is None:return None
    y=36+row*32;crop=im[max(0,y-14):y+15,48:84]
    scores={k:float(cv2.minMaxLoc(cv2.matchTemplate(crop,v,cv2.TM_CCOEFF_NORMED))[1]) for k,v in NOTICE_TEMPLATES.items()}
    kind=max(scores,key=scores.get)
    return kind if scores[kind]>=.80 else None

def parse_frame(r,folder=None):
    rows=collections.defaultdict(list)
    for box,s,conf in r['ocr']:
        y=sum(p[1] for p in box)/4;x=min(p[0] for p in box)
        row=round((y-36)/32)
        if row<0 or row>8 or abs(y-(36+32*row))>12 or x>700:continue
        rows[row].append((x,s,conf,max(p[0] for p in box)))
    result=[]
    for row,parts in sorted(rows.items()):
        parts.sort();found=[]
        for x,s,conf,x1 in parts:
            for n in names(s):found.append((x,n,conf,x1))
        if len(found)==1 and found[0][0]<105:
            other=[(x,clean(s),conf,x1) for x,s,conf,x1 in parts if x>found[0][0]+85 and not names(s) and len(re.sub(r'\W','',clean(s)))>=3 and clean(s).upper() not in TEAM and not re.fullmatch(r'\[?\d+\s*m\]?',s)]
            if len(other)==1:found+=other
        elif len(found)==1 and found[0][0]>=150:
            other=[(x,clean(s),conf,x1) for x,s,conf,x1 in parts if x<105 and not names(s) and len(re.sub(r'\W','',clean(s)))>=3 and conf>=.6]
            if len(other)==1:found=other+found
        kind='pair'
        if len(found)==1 and 40<=found[0][0]<=105 and folder:
            kind=notice_kind(folder/r['frame'],row)
            if kind:found=[(0,'',found[0][2],0),found[0]]
        # Two tagged names may share a detector box; that is still a valid row.
        if len(found)==2 and found[0][0]<105:
            result.append(dict(row=row,a=found[0][1],b=found[1][1],kind=kind,attacker_x=found[0][0],target_x=found[1][0],target_end=found[1][3],confidence=min(x[2] for x in found),raw=' | '.join(p[1] for p in parts)))
    return result

def vote(counter):return counter.most_common(1)[0][0]

def accepted(e):
    # Distinct source observations, never a count of recognizer invocations.
    agreement=sum(o.get('model_agreement',False) and o['confidence']>=.92 for o in e['observations'])
    for n in [e['attacker'],e['target']]:
        if not n:continue
        if n.upper() in TEAM:return False
        if ('[' in n or ']' in n) and not re.match(r'^\[[^\[\]\s]{1,12}\].+',n):return False
    return (e['count']>=3 and e['confidence']>=.8) or (e['count']>=2 and agreement>=2)

def run(path):
    tracks=[];active=[];unparsed=[]
    m=re.search(r'validation-\d+',path.name);folder=ROOT/m[0] if m else ROOT/'frames'
    for line in path.open(encoding='utf-8'):
        r=json.loads(line);t=r['t'];seen=set()
        # Normal feed rows live about ten seconds; allow short OCR/menu gaps
        # only within that lifetime, and never move an existing row upwards.
        active=[e for e in active if t-e['last']<=6 and t-e['first']<=11]
        parsed=r.get('parsed_rows')
        if parsed is None:parsed=parse_frame(r,folder)
        # Feed entries are a queue: a new row pushes existing rows down together.
        # Estimate that shift from independently matching names, then use row
        # continuity to bridge poor text reads without creating duplicate events.
        shifts=collections.Counter()
        for obs in parsed:
            scores=[]
            for e in active:
                if t-e['last']>.75:continue
                sa=max(similarity(obs['a'],n) for n in e['a_votes']);sb=max(similarity(obs['b'],n) for n in e['b_votes'])
                delta=obs['row']-e['row']
                if 0<=delta<=5 and min(sa,sb)>=.8:scores.append(((sa+sb)/2,delta))
            if scores:
                score,delta=max(scores);shifts[delta]+=score
        shift=shifts.most_common(1)[0][0] if shifts else None
        projected={e['id']:e['row']+shift for e in active if shift is not None and t-e['last']<=.75}
        for obs in parsed:
            options=[]
            for e in active:
                if e['id'] in seen:continue
                sa=max(similarity(obs['a'],n) for n in e['a_votes']);sb=max(similarity(obs['b'],n) for n in e['b_votes'])
                aligned=projected.get(e['id'])==obs['row']
                if (min(sa,sb)>=.66 and (sa+sb)/2>=.82) or (aligned and max(sa,sb)>=.9):
                    options.append(((sa+sb)/2+.3*aligned-.008*abs(obs['row']-e['row']),e))
            if options:e=max(options,key=lambda p:p[0])[1]
            else:
                e=dict(id=f'D{len(tracks)+1:05}',first=t,last=t,row=obs['row'],a_votes=collections.Counter(),b_votes=collections.Counter(),observations=[],confidence=0)
                tracks.append(e);active.append(e)
            e['last']=t;e['row']=obs['row'];seen.add(e['id'])
            e['a_votes'][obs['a']]+=max(.01,obs['confidence'])**3
            e['b_votes'][obs['b']]+=max(.01,obs['confidence'])**3
            e['observations'].append(dict(t=t,frame=r['frame'],**obs))
            e['confidence']=max(e['confidence'],obs['confidence'])
        for e in active:
            if e['id'] not in seen and e['id'] in projected:e['row']=projected[e['id']]
    # Repair interleaved fragments only inside one HUD-row lifetime. Never merge
    # pair tracks that were simultaneously observed in different visible rows.
    merged=[]
    for e in tracks:
        match=None
        for prior in reversed(merged):
            if e['first']-prior['last']>6:continue
            if max(e['last'],prior['last'])-min(e['first'],prior['first'])>10.5:continue
            if min(similarity(vote(e['a_votes']),vote(prior['a_votes'])),similarity(vote(e['b_votes']),vote(prior['b_votes'])))<.9:continue
            if {o['t'] for o in e['observations']} & {o['t'] for o in prior['observations']}:continue
            match=prior;break
        if match:
            match['first']=min(e['first'],match['first']);match['last']=max(e['last'],match['last'])
            match['observations']+=e['observations'];match['a_votes'].update(e['a_votes']);match['b_votes'].update(e['b_votes']);match['confidence']=max(e['confidence'],match['confidence'])
        else:merged.append(e)
    tracks=merged
    for e in tracks:
        e['attacker']=vote(e['a_votes']);e['target']=vote(e['b_votes'])
        e['attacker_team']=TEAM.get(e['attacker'][1:].split(']')[0],'Unknown')
        e['target_team']=TEAM.get(e['target'][1:].split(']')[0],'Unknown')
        e['count']=len(e['observations'])
        e['kind']=collections.Counter(o['kind'] for o in e['observations']).most_common(1)[0][0]
    return tracks

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',default='tracks-native.json');a=p.parse_args()
    tracks=run(ROOT/a.input);(ROOT/a.output).write_text(json.dumps(tracks,indent=2),encoding='utf-8')
    for e in tracks:print(f'{e["id"]} {e["first"]:.2f}-{e["last"]:.2f} {e["count"]:3} {e["attacker"]} -> {e["target"]} {e["confidence"]:.3f}')
    print('Tracks',len(tracks))
