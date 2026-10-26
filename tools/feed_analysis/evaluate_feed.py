"""One-to-one visible-episode evaluation against independently read source sheets."""
from pathlib import Path
import csv,json,re,difflib,unicodedata
from track_dense_feed import run,ROOT,accepted

def key(n):
    # Evaluate player text separately from clan OCR; report exact spelling below.
    if n.startswith('[') and ']' in n:n=n.split(']',1)[1]
    n=re.sub(r'\[BRO\]?','',n,flags=re.I)
    n=''.join(c for c in unicodedata.normalize('NFKD',n) if not unicodedata.combining(c))
    return re.sub(r'\W','',n).lower()
def sim(a,b):return difflib.SequenceMatcher(None,key(a),key(b)).ratio()
results=[]
baseline=json.loads((ROOT/'baseline-events.json').read_text())
full_path=ROOT/'tracks-final.json'
full=json.loads(full_path.read_text()) if full_path.exists() else []
for start in [1440,2400,5880,4320,3300]:
    duration=30 if start==3300 else 60
    truth=list(csv.DictReader((ROOT/f'manual-{start}.csv').open()))
    pairs=truth
    native=run(ROOT/f'validation-{start}-native.jsonl')
    methods={'native_v2':[e for e in native if accepted(e)],
             'baseline_included':[e for e in baseline if e['included_in_charts'] and e['first_seen_seconds']<start+duration and e['last_seen_seconds']>=start]}
    combined=ROOT/f'validation-{start}-combined.jsonl'
    if combined.exists():methods['combined_v2']=[e for e in run(combined) if accepted(e)]
    if full:methods['whole_game_v2']=[e for e in full if accepted(e) and e['first']<start+duration and e['last']>=start]
    for method,events in methods.items():
        used=set();matches=[];misses=[]
        for m in pairs:
            opts=[]
            for i,e in enumerate(events):
                if i in used:continue
                first=e.get('first',e.get('first_seen_seconds'));last=e.get('last',e.get('last_seen_seconds'))
                # Reference time is the first readable one-second sheet sample,
                # not an exact event birth. Later OCR can recover that episode.
                if not first-10<=float(m['seen_seconds'])<=last+1:continue
                sa=sim(m['attacker'],e['attacker']);sb=sim(m['target'],e['target'])
                if min(sa,sb)>=.6 and (sa+sb)/2>=.80:opts.append(((sa+sb)/2,i,e))
            if opts:
                score,i,e=max(opts,key=lambda x:x[0]);used.add(i)
                matches.append(dict(manual=m,prediction={k:v for k,v in e.items() if k!='observations'},name_similarity=score))
            else:misses.append(m)
        extras=[{k:v for k,v in e.items() if k!='observations'} for i,e in enumerate(events) if i not in used]
        result=dict(window=start,duration=duration,method=method,reference_entries=len(pairs),reference_pairs=sum(bool(m['attacker']) for m in pairs),reference_notices=sum(not m['attacker'] for m in pairs),matched=len(matches),missed=misses,unmatched_predictions=extras,recall=len(matches)/len(pairs),precision=len(matches)/len(events) if events else None,matches=matches)
        results.append(result)
        print(start,method,'reference',len(pairs),'matched',len(matches),'extra',len(extras),'missed',len(misses))
        if method!='baseline_included':
            for m in misses:print(' MISS',m['seen_seconds'],m['attacker'],'->',m['target'])
            for e in extras:print(' EXTRA',e.get('first',e.get('first_seen_seconds')),e['attacker'],'->',e['target'])
(ROOT/'evaluation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
