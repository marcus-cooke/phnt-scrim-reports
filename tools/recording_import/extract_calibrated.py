"""Extract HUD samples and feed with an explicit virtual-layout calibration.

The source is never overwritten. Upsampling aligns coordinates; it adds no detail.
"""
import argparse, json, subprocess, time
from pathlib import Path
import imageio_ffmpeg

p=argparse.ArgumentParser()
p.add_argument('video'); p.add_argument('output')
p.add_argument('--end',type=float,default=6705)
p.add_argument('--feed-fps',type=float,default=2)
p.add_argument('--hud-gap',type=float,default=5)
p.add_argument('--fps-round',choices=['up','near'],default='up')
a=p.parse_args(); out=Path(a.output).resolve()
for folder in ['keyframes','feed-v2/frames']:(out/folder).mkdir(parents=True,exist_ok=True)
filters=(f'[0:v]scale=3440:1440:flags=bicubic,split=3[a][b][c];'
         f'[a]fps=1/{a.hud_gap}:round={a.fps_round},crop=760:760:0:640[h];'
         f'[b]fps=1/{a.hud_gap}:round={a.fps_round},scale=688:288,pad=760:288:0:0[m];'
         '[h][m]vstack[hud];'
         f'[c]fps={a.feed_fps}:round={a.fps_round},crop=900:340:0:640[feed]')
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-y','-hwaccel','cuda',
     '-t',str(a.end),'-i',str(Path(a.video).resolve()),'-an','-filter_complex',filters,
     '-map','[hud]','-fps_mode','passthrough','-enc_time_base','1/1000','-frame_pts','1','-q:v','3',str(out/'keyframes/%010d.jpg'),
     '-map','[feed]','-fps_mode','passthrough','-enc_time_base','1/1000','-frame_pts','1',str(out/'feed-v2/frames/%010d.png')]
(out/'calibration.json').write_text(json.dumps(dict(source=a.video,virtual_size=[3440,1440],
    native_size=[1920,804],feed_fps=a.feed_fps,hud_gap_seconds=a.hud_gap,end_seconds=a.end,
    note='Bicubic coordinate normalization only; native video remains the evidence source.',command=cmd),indent=2))
start=time.time()
with (out/'decode.log').open('w') as f:
    process=subprocess.Popen(cmd,stdout=f,stderr=f)
    while process.poll() is None:
        time.sleep(5)
        print(f'{len(list((out/"keyframes").glob("*.jpg")))} HUD / {len(list((out/"feed-v2/frames").glob("*.png")))} feed frames; {time.time()-start:.0f}s',flush=True)
if process.returncode:raise SystemExit(process.returncode)
for folder in [out,out/'feed-v2/frames']:
    (folder/'complete.json').write_text(json.dumps(dict(elapsed_seconds=time.time()-start)))
print('Extraction complete',flush=True)
