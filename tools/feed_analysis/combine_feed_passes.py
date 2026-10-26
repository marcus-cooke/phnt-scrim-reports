"""Combine recognizers per source row without counting model reads as frames."""
from pathlib import Path
import argparse,collections,json,re
from track_dense_feed import ROOT,names,parse_frame,similarity

def read(path):
    rows=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        try:rows.append(json.loads(line))
        except json.JSONDecodeError:raise ValueError(f'Incomplete JSON line in {path}')
    return rows

def norm(s):return re.sub(r'\W','',s).casefold()
def combine(native,alternate,out,expected=None):
    a=read(native);b=read(alternate);other={r['frame']:r for r in b}
    assert len(other)==len(b),'Duplicate reread frames'
    if expected is not None:assert len(a)==len(b)==expected,'Full-game OCR is incomplete; do not publish partial data'
    assert {r['frame'] for r in a}==set(other),'Recognition passes cover different frames'
    roster=collections.Counter()
    for r in a+b:
        for box,text,score in r['ocr']:
            if score>=.92:
                for n in names(text):roster[n]+=1
    trusted={norm(n) for n,c in roster.items() if c>=20}
    aliases={}
    frequent=[n for n,c in roster.most_common() if c>=20]
    for n,c in roster.items():
        candidates=[m for m in frequent if roster[m]>=max(20,c*3) and n.split(']')[0]==m.split(']')[0]] if c<20 else []
        candidates=[m for m in candidates if similarity(n,m)>=.92]
        if candidates:aliases[n]=max(candidates,key=lambda m:(similarity(n,m),roster[m]))
    window=re.search(r'validation-\d+',native.name);folder=ROOT/window[0] if window else ROOT/'frames'
    with out.open('w',encoding='utf-8') as f:
        for r in a:
            options=collections.defaultdict(list)
            for model,record in [('v4',r),('v5',other[r['frame']])]:
                for o in parse_frame(record,folder):
                    o['a']=aliases.get(o['a'],o['a']);o['b']=aliases.get(o['b'],o['b'])
                    o['trusted_names']=all(norm(n) in trusted for n in [o['a'],o['b']] if n)
                    o['recognizer']=model;options[o['row']].append(o)
            chosen=[]
            for row,opts in sorted(options.items()):
                # Roster support outranks raw confidence; scores from different
                # recognizers are not treated as calibrated probabilities.
                rank=lambda o:(sum(norm(n) in trusted for n in [o['a'],o['b']] if n),o['confidence'],o['recognizer']=='v5')
                best=max(opts,key=rank).copy()
                best['model_agreement']=any(o['recognizer']!=best['recognizer'] and min(similarity(o['a'],best['a']),similarity(o['b'],best['b']))>=.9 for o in opts)
                chosen.append(best)
            raw_rows=collections.defaultdict(set)
            for record in [r,other[r['frame']]]:
                for box,text,score in record['ocr']:
                    y=sum(p[1] for p in box)/4;row=round((y-36)/32)
                    if 0<=row<=8 and abs(y-36-32*row)<=12 and min(p[0] for p in box)<650:raw_rows[row].add(text)
            recovered={o['row'] for o in chosen}
            unparsed=[dict(row=row,raw_text=' | '.join(sorted(texts))) for row,texts in raw_rows.items() if row not in recovered]
            f.write(json.dumps(dict(t=r['t'],frame=r['frame'],parsed_rows=chosen,unparsed_rows=unparsed))+'\n')
    (out.parent/(out.stem+'-roster.json')).write_text(json.dumps(dict(names=dict(roster),aliases=aliases),indent=2),encoding='utf-8')
    return len(a)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',default='ocr-en-native.jsonl');p.add_argument('--alternate',default='ocr-en-v5-rerec.jsonl');p.add_argument('--output',default='combined-rows.jsonl');p.add_argument('--expected',type=int,default=24622);a=p.parse_args()
    print('Combined',combine(ROOT/a.native,ROOT/a.alternate,ROOT/a.output,a.expected),'distinct source frames')
