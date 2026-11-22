"""Sample an explicitly bounded native 3440x1440 recording without bin offsets."""
import argparse,json,subprocess,time
from pathlib import Path
import imageio_ffmpeg,cv2
p=argparse.ArgumentParser();p.add_argument('video');p.add_argument('output');p.add_argument('--start',type=float,required=True);p.add_argument('--end',type=float,required=True);a=p.parse_args()
root=Path(a.output).resolve();video=str(Path(a.video).resolve())
cap=cv2.VideoCapture(video);assert (cap.get(3),cap.get(4))==(3440,1440);cap.release()
for folder in ['keyframes','feed-v2/frames','data','evidence','charts']:(root/folder).mkdir(parents=True,exist_ok=True)
ff=imageio_ffmpeg.get_ffmpeg_exe()
base=[ff,'-hide_banner','-y','-hwaccel','cuda','-hwaccel_output_format','cuda','-ss',str(a.start),'-t',str(a.end-a.start),'-i',video,'-an']
# Round up chooses the frame at the bin boundary for this exact 60fps source.
# FPS is selected on GPU frames before transfer; output PTS is recording time.
feed=f'fps=4:round=up,setpts=PTS+{a.start}/TB,hwdownload,format=nv12,crop=900:340:0:640'
hud=f'fps=1/5:round=up,setpts=PTS+{a.start}/TB,hwdownload,format=nv12,split=2[a][b];[a]crop=760:760:0:640[h];[b]scale=688:288,pad=760:288:0:0[m];[h][m]vstack[out]'
commands=[base+['-vf',feed,'-fps_mode','passthrough','-enc_time_base','1/1000','-frame_pts','1',str(root/'feed-v2/frames/%010d.png')],base+['-filter_complex',hud,'-map','[out]','-fps_mode','passthrough','-enc_time_base','1/1000','-frame_pts','1','-q:v','3',str(root/'keyframes/%010d.jpg')]]
(root/'calibration.json').write_text(json.dumps(dict(source=Path(video).name,native_size=[3440,1440],start_seconds=a.start,end_seconds=a.end,feed_fps=4,hud_gap_seconds=5,rounding='up; recording PTS; no bin-offset correction'),indent=2))
for name,cmd in zip(['feed','hud'],commands):
 with (root/f'{name}-decode.log').open('w') as f:
  t=time.time();task=subprocess.Popen(cmd,stdout=f,stderr=f)
  while task.poll() is None:
   time.sleep(5);folder=root/('feed-v2/frames' if name=='feed' else 'keyframes');print(name,len(list(folder.glob('*.png' if name=='feed' else '*.jpg'))),round(time.time()-t),'s',flush=True)
 if task.returncode:raise SystemExit(task.returncode)
 dest=root/'feed-v2/frames' if name=='feed' else root
 (dest/'complete.json').write_text(json.dumps(dict(start=a.start,end=a.end,elapsed_seconds=time.time()-t)))
