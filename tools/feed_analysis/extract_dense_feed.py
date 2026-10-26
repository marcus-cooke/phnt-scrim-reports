from pathlib import Path
import argparse,json,subprocess,time,imageio_ffmpeg,os
ROOT=Path(os.environ.get('PHNT_ANALYSIS_ROOT',str(Path(__file__).parent)))
p=argparse.ArgumentParser();p.add_argument('--video',required=True);p.add_argument('--start',type=float,default=300);p.add_argument('--end',type=float,default=6455.566667);p.add_argument('--fps',type=float,default=4);p.add_argument('--folder',default='frames');a=p.parse_args()
dest=ROOT/'feed-v2'/a.folder;dest.mkdir(parents=True,exist_ok=True)
video=str(Path(a.video).resolve())
filters=f'fps={a.fps}:start_time=0:round=near,setpts=PTS+{a.start}/TB,hwdownload,format=nv12,crop=900:340:0:640'
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-y','-hwaccel','cuda','-hwaccel_output_format','cuda','-ss',str(a.start),'-i',video,'-t',str(a.end-a.start),'-an','-vf',filters,'-fps_mode','passthrough','-enc_time_base','1/1000','-frame_pts','1',str(dest/'%010d.png')]
# -t is a duration before timestamp offset; use filter trim before offset so
# output timestamps remain original video time without shortening the window.
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-y','-hwaccel','cuda','-hwaccel_output_format','cuda','-ss',str(a.start),'-t',str(a.end-a.start),'-i',video,'-an','-vf',filters,'-fps_mode','passthrough','-enc_time_base','1/1000','-frame_pts','1',str(dest/'%010d.png')]
with (dest/'decode.log').open('w') as log:
    task=subprocess.Popen(cmd,stdout=log,stderr=log)
    (dest/'process.json').write_text(json.dumps(dict(pid=task.pid,start=a.start,end=a.end,fps=a.fps,source=video,command=cmd)))
    start=time.time()
    while task.poll() is None:
        time.sleep(5);files=list(dest.glob('*.png'));last=max((int(p.stem)/1000 for p in files),default=a.start)
        print(f'{len(files)} feed frames; source {last/60:.1f}min; elapsed {time.time()-start:.0f}s',flush=True)
if task.returncode:raise SystemExit(task.returncode)
files=list(dest.glob('*.png'))
(dest/'complete.json').write_text(json.dumps(dict(frames=len(files),first=min(p.name for p in files),last=max(p.name for p in files),elapsed_seconds=time.time()-start)))
print('Dense extraction complete',flush=True)
