"""Make native-source review sheets for anchors, round boundaries and names."""
import argparse, cv2, math
from pathlib import Path
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('video');p.add_argument('output');a=p.parse_args()
root=Path(a.output);dest=root/'review';dest.mkdir(exist_ok=True)
cap=cv2.VideoCapture(a.video)
def frame(t):
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,im=cap.read()
    return Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)) if ok else None
times=[0,120,180,300]+list(range(600,6601,300))+[6650,6680,6690,6700,6710]
w=600;h=190;sheet=Image.new('RGB',(w*3,h*math.ceil(len(times)/3)),'#141820');d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
    im=frame(t)
    if im is None:continue
    im.save(dest/f'native-{t}.jpg',quality=96)
    x=i%3*w;y=i//3*h;sheet.paste(im.crop((20,716,218,775)).resize((594,177)),(x,y))
    d.text((x+4,y+178),f'{t//60:02}:{t%60:02} / {t}s / Blue-Red-Green',fill='white')
sheet.save(dest/'ticket-anchors.jpg',quality=95)
times=[6695,6700,6705,6710,6715,6720,6725,6730,6735,6740,6745,6750]
w=640;h=294;sheet=Image.new('RGB',(w*3,h*math.ceil(len(times)/3)),'#141820');d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
    im=frame(t)
    if im is None:continue
    im.save(dest/f'native-{t}.jpg',quality=97)
    x=i%3*w;y=i//3*h;sheet.paste(im.resize((640,268)),(x,y));d.text((x+4,y+271),f'{t//60:02}:{t%60:02} / {t}s',fill='white')
sheet.save(dest/'ending.jpg',quality=95)
cap.release()
print(dest)
