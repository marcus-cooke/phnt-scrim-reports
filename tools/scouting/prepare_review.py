"""Prepare native evidence frames and contact sheets from an authorised recording.

This is sampling for visual review, not continuous event or player tracking.
Original media, captions and working sheets stay in the ignored analysis folder.
"""
import argparse
import json
import math
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont


def stamp(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--overview", action="store_true")
    parser.add_argument("--range", action="append", default=[], help="NAME:START:END:STEP, in seconds")
    parser.add_argument("--times", nargs="*", type=float, default=[])
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    captions = next(root.glob("*.en.json3"), None)
    if captions:
        events = json.loads(captions.read_text(encoding="utf-8"))["events"]
        rows = []
        for event in events:
            text = "".join(s.get("utf8", "") for s in event.get("segs", [])).strip()
            if text:
                rows.append(dict(start_seconds=event["tStartMs"] / 1000,
                                 duration_seconds=event.get("dDurationMs", 0) / 1000,
                                 text=text, source="YouTube automatic English captions; unverified"))
        (root / "captions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        (root / "captions.txt").write_text("\n".join(f"[{stamp(r['start_seconds'])}] {r['text']}" for r in rows), encoding="utf-8")
    if not args.video:
        return
    cap = cv2.VideoCapture(str(args.video.resolve()))
    if not cap.isOpened():
        raise RuntimeError("Cannot open recording")
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    metadata = dict(width=int(cap.get(3)), height=int(cap.get(4)), fps=fps,
                    duration_seconds=duration, frames=int(cap.get(7)),
                    source_filename=args.video.name)
    (root / "video-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    groups = {}
    if args.overview:
        groups["overview"] = list(range(0, int(duration), 60)) + [duration - 2]
    for spec in args.range:
        name, start, end, step = spec.split(":")
        groups[name] = list(range(int(start), int(end) + 1, int(step)))
    if args.times:
        groups["selected"] = args.times
    frame_dir = root / "frames"
    review_dir = root / "review"
    frame_dir.mkdir(exist_ok=True)
    review_dir.mkdir(exist_ok=True)
    index_file = root / "frame-index.json"
    index = json.loads(index_file.read_text()) if index_file.exists() else {}
    for name, times in groups.items():
        paths = []
        for t in times:
            if not 0 <= t < duration:
                raise ValueError(f"Out of range: {t}")
            key = f"{round(t * 1000):010d}"
            path = frame_dir / f"{key}.jpg"
            if not path.exists():
                cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                ok, bgr = cap.read()
                if not ok:
                    raise RuntimeError(f"Cannot decode {t}")
                actual = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).save(path, quality=94)
                index[key] = dict(requested_seconds=t, decoded_seconds=actual,
                                  source_frame=round(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1,
                                  source_image=f"frames/{key}.jpg")
            paths.append((t, path))
        for batch_no in range(math.ceil(len(paths) / 24)):
            batch = paths[batch_no * 24:(batch_no + 1) * 24]
            width, height = 480, round(metadata["height"] / metadata["width"] * 480)
            sheet = Image.new("RGB", (width * 4, (height + 30) * math.ceil(len(batch) / 4)), "#14171a")
            draw = ImageDraw.Draw(sheet)
            font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 19)
            for i, (t, path) in enumerate(batch):
                x, y = i % 4 * width, i // 4 * (height + 30)
                with Image.open(path) as frame:
                    sheet.paste(frame.resize((width, height)), (x, y))
                draw.text((x + 8, y + height + 2), f"{stamp(t)} / {t:g}s", fill="white", font=font)
            target = review_dir / f"{name}-{batch_no + 1:02}.jpg"
            sheet.save(target, quality=94)
            print(target, flush=True)
    index_file.write_text(json.dumps(index, indent=2), encoding="utf-8")
    cap.release()
    print(json.dumps(metadata), flush=True)


if __name__ == "__main__":
    main()
