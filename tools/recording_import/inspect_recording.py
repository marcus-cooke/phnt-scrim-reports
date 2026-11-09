"""Inspect a new POV without assuming the original recording's resolution."""
import argparse, json, math
from pathlib import Path
import cv2
from PIL import Image, ImageDraw

p = argparse.ArgumentParser()
p.add_argument('video')
p.add_argument('output')
p.add_argument('--times', nargs='*', type=float)
a = p.parse_args()
out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
cap = cv2.VideoCapture(a.video)
fps = cap.get(5); duration = cap.get(7) / fps
meta = dict(source=a.video, width=cap.get(3), height=cap.get(4), fps=fps,
            duration_seconds=duration, frames=cap.get(7))
(out/'metadata.json').write_text(json.dumps(meta, indent=2))
times = a.times or sorted(set([0, 30, 120, 300, 600] + list(range(900, int(duration), 600)) + [duration-30, duration-5]))
w = 640; h = round(w*meta['height']/meta['width']); cell=h+26
sheet = Image.new('RGB', (w*3, cell*math.ceil(len(times)/3)), '#141820')
draw = ImageDraw.Draw(sheet)
for i,t in enumerate(times):
    cap.set(cv2.CAP_PROP_POS_MSEC, t*1000); ok, bgr=cap.read()
    if not ok: continue
    im=Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    im.save(out/f'sample-{t:.3f}.jpg', quality=95)
    x=i%3*w; y=i//3*cell; sheet.paste(im.resize((w,h)), (x,y))
    draw.text((x+8,y+h+5), f'{int(t)//3600:02}:{int(t)//60%60:02}:{t%60:06.3f} ({t:.3f}s)', fill='white')
sheet.save(out/'overview.jpg', quality=92)
cap.release()
print(json.dumps(meta)); print(out/'overview.jpg')
