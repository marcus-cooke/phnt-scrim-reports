from pathlib import Path
from PIL import Image,ImageDraw
import math,argparse,os
p=argparse.ArgumentParser();p.add_argument('--folder',default='validation-1440');a=p.parse_args()
ROOT=Path(os.environ.get('PHNT_ANALYSIS_ROOT',str(Path(__file__).parent)))/'feed-v2';folder=ROOT/a.folder
files=[p for p in sorted(folder.glob('*.png')) if int(p.stem)%1000==0]
for offset in range(0,len(files),10):
    part=files[offset:offset+10];sheet=Image.new('RGB',(1250,360*math.ceil(len(part)/2)),'#101518');d=ImageDraw.Draw(sheet)
    for i,path in enumerate(part):
        im=Image.open(path).crop((25,10,650,340));x=i%2*625;y=i//2*360;sheet.paste(im,(x,y));t=int(path.stem)/1000
        d.text((x+5,y+334),f'{int(t)//60:02}:{int(t)%60:02} / {t:.2f}s',fill='white')
    sheet.save(ROOT/f'{a.folder}-sheet-{offset}.png')
print(len(files),'one-second frames in independent manual-review sheets')
