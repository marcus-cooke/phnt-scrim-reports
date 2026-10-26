"""Evidence-based glyph colours and skull-marker scores, not game semantics."""
from pathlib import Path
import argparse,collections,json
import cv2,numpy as np
from track_dense_feed import ROOT,TEAM

def coloured_pixels(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV);h,s,v=cv2.split(hsv);mask=(s>100)&(v>95)
    counts={'Blue':int(np.sum(mask&(h>=90)&(h<=125))),
            'Green':int(np.sum(mask&(h>=38)&(h<=88))),
            'Red':int(np.sum(mask&((h<=9)|(h>=170))))}
    ranked=sorted(counts.items(),key=lambda x:-x[1])
    return ranked[0][0] if ranked[0][1]>=12 and ranked[0][1]>=ranked[1][1]*2 else None

def annotate(tracks,folder):
    skull=cv2.imread(str(ROOT/'validation-1440/0001445000.png'),0)[25:47,222:241]
    for e in tracks:
        team_votes={'attacker':collections.Counter(),'target':collections.Counter()};scores=[]
        # Spread observations; no inference from one brightest pixel.
        observations=sorted(e['observations'],key=lambda o:-o['confidence'])[:12]
        for o in observations:
            im=cv2.imread(str(folder/o['frame']))
            if im is None:continue
            y=36+32*o['row'];y0=max(0,y-13);y1=min(im.shape[0],y+14)
            if y1-y0<22:continue
            side=coloured_pixels(im[max(0,y-10):y+11,46:65])
            if side:team_votes['attacker'][side]+=1
            # Victim glyph follows its text. Locate the text box end, not any
            # coloured scenery inside the player name or the weapon gap.
            x=int(o['target_end'])
            if 100<x<700:
                side=coloured_pixels(im[max(0,y-10):y+11,max(0,x-8):min(im.shape[1],x+26)])
                if side:team_votes['target'][side]+=1
            crop=cv2.cvtColor(im[y0:y1,100:500],cv2.COLOR_BGR2GRAY)
            score=float(cv2.minMaxLoc(cv2.matchTemplate(crop,skull,cv2.TM_CCOEFF_NORMED))[1]);scores.append(score)
        e['glyph_team_votes']={k:dict(v) for k,v in team_votes.items()}
        for side in ['attacker','target']:
            tag=e[side][1:].split(']')[0] if e[side].startswith('[') else ''
            clan_team=TEAM.get(tag)
            vote=team_votes[side].most_common(1)
            glyph_team=vote[0][0] if vote and vote[0][1]>=3 and vote[0][1]>=sum(team_votes[side].values())*.8 else None
            e[side+'_team']=clan_team or glyph_team or 'Unknown'
            e[side+'_team_source']='clan' if clan_team else 'glyph' if glyph_team else 'unresolved'
            if clan_team and glyph_team and clan_team!=glyph_team:e[side+'_team_conflict']=True
        e['skull_scores']=[round(s,4) for s in scores]
        e['icon_class']='skull-marked' if sum(s>=.78 for s in scores)>=3 else 'unclassified'
    return tracks

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--folder',default='frames');p.add_argument('--output',default='tracks-annotated.json');a=p.parse_args()
    tracks=annotate(json.loads((ROOT/a.input).read_text()),ROOT/a.folder)
    (ROOT/a.output).write_text(json.dumps(tracks,indent=2),encoding='utf-8')
    print(collections.Counter(e['icon_class'] for e in tracks))
