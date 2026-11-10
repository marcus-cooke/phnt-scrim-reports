"""Package reviewed opponent scouting without altering existing PHNT match data.

Usage: python tools/build_scouting.py --analysis PATH
The analysis folder contains curated-report.json, frame-index.json, frames/,
source.299.mp4 and source.140.m4a. Full media and working captions stay local.
"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess
import re
from html import escape

ROOT = Path(__file__).resolve().parents[1]


def recording_options(slug=''):
    catalog_file = ROOT / 'site/scouting/catalog.json'
    if not catalog_file.exists():
        return '<option value="./">Black Sails / BNT–III / OOPS–Merc</option>'
    prefix = '../' if slug else './'
    return ''.join(f'<option value="{escape(prefix + row["route"])}"'+
                   (' selected' if row['slug'] == slug else '')+
                   f'>{escape(row["label"])}</option>'
                   for row in json.loads(catalog_file.read_text(encoding='utf-8')))


def render_page(report, slug=''):
    data = json.dumps(report, ensure_ascii=True, separators=(',', ':'))
    html = (ROOT / 'site/scouting/index.html').read_text(encoding='utf-8')
    if slug:
        html = html.replace('href="../brand/', 'href="../../brand/').replace('src="../brand/', 'src="../../brand/')
        html = html.replace('href="../"', 'href="../../"').replace('href="./" aria-current', 'href="../" aria-current')
        html = html.replace('href="patterns/"', 'href="../patterns/"')
    return html.replace('__SCOUTING_DATA__', data.replace('</', '<\\/')).replace('__SCOUTING_OPTIONS__', recording_options(slug))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--analysis", type=Path)
    p.add_argument("--data-only", action="store_true", help="Rebuild page and exports using already-packaged evidence")
    p.add_argument('--slug', default='', help='Separate recording route; omitted for the original dossier')
    args = p.parse_args()
    if args.slug and (not re.fullmatch(r'[a-z0-9-]+', args.slug) or args.slug in {'assets','clips','data','patterns'}):
        p.error('Invalid recording slug')
    source_report = ROOT / ('site/scouting/reports/' + args.slug + '.json' if args.slug else 'site/scouting/report.json')
    if not args.analysis and not args.data_only:
        p.error("--analysis is required when packaging source media")
    analysis = args.analysis.resolve() if args.analysis else None
    report_file = analysis / "curated-report.json" if analysis else source_report
    if not report_file.exists():
        report_file = source_report
    report = json.loads(report_file.read_text(encoding="utf-8"))
    target = ROOT / 'docs/scouting' / args.slug
    frame_index = json.loads((analysis / "frame-index.json").read_text()) if not args.data_only else None
    previous_review = {r['id']: r for r in json.loads((target / "data/review-log.json").read_text())["reviewed_evidence"]} if args.data_only else {}
    (target / "assets").mkdir(parents=True, exist_ok=True)
    (target / "clips").mkdir(exist_ok=True)
    (target / "data").mkdir(exist_ok=True)
    review = []
    for item in report["evidence"]:
        item.setdefault('thumbnail', f"assets/thumb-{item['id']}.jpg")
        if args.data_only:
            record = previous_review[item['id']]
            assert record['seconds'] == item['seconds'], "Changed evidence time requires source review"
            assert (target / item['image']).is_file()
            if item.get('clip'):
                assert (target / item['clip']['src']).is_file()
            from PIL import Image
            with Image.open(target / item['image']) as source:
                source.thumbnail((640, 360))
                source.save(target / item['thumbnail'], quality=82)
            review.append({**record, 'basis': item['basis']})
            continue
        frame = frame_index[f"{round(item['seconds'] * 1000):010d}"]
        assert abs(frame["decoded_seconds"] - item["seconds"]) < 1 / report['source']['fps'] + .01, frame
        shutil.copy2(analysis / frame["source_image"], target / item["image"])
        from PIL import Image
        with Image.open(target / item['image']) as source:
            source.thumbnail((640, 360))
            source.save(target / item['thumbnail'], quality=82)
        review.append(dict(id=item["id"], seconds=item["seconds"],
                           decoded_seconds=frame["decoded_seconds"],
                           source_frame=frame["source_frame"],
                           review_method="Agent visual inspection of source frame and surrounding sampled sequence",
                           basis=item["basis"]))
        if item.get("clip"):
            clip = item["clip"]
            dest = target / clip["src"]
            video_file = report['source'].get('video_filename', 'source.299.mp4')
            audio_file = report['source'].get('audio_filename', 'source.140.m4a')
            spec = dict(start_seconds=clip["start_seconds"], end_seconds=clip["end_seconds"],
                        video=video_file, audio=audio_file,
                        output_size=[1280, 720], output_fps=30, audio_bitrate="96k",
                        crf=28, maxrate="1800k", bufsize="3600k")
            spec_path = analysis / (item["id"] + "-clip-spec.json")
            previous = json.loads(spec_path.read_text()) if spec_path.exists() else None
            if not dest.exists() or previous != spec:
                import imageio_ffmpeg
                command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
                           "-ss", str(clip["start_seconds"]), "-i", str(analysis / video_file),
                           "-ss", str(clip["start_seconds"]), "-i", str(analysis / audio_file),
                           "-t", str(clip["end_seconds"] - clip["start_seconds"]),
                           "-map", "0:v:0", "-map", "1:a:0", "-vf", "scale=1280:720,fps=30",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-threads", "8",
                           "-maxrate", "1800k", "-bufsize", "3600k",
                           "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(dest)]
                subprocess.run(command, check=True)
                spec_path.write_text(json.dumps(spec, indent=2))
            print("Packaged", item["id"], flush=True)
    html = render_page(report, args.slug)
    (target / "index.html").write_text(html, encoding="utf-8")
    for filename in ["scouting.css", "scouting.js"]:
        shutil.copy2(ROOT / "site/scouting" / filename, target / filename)
    (target / "data/scouting-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (target / "data/review-log.json").write_text(json.dumps(dict(
        reviewed_evidence=review, coverage=report["coverage"], rejected_claims=report["rejected_claims"],
        review_type="Agent-reviewed sampled footage; not independent human validation"), indent=2), encoding="utf-8")
    columns = ["id", "team", "type", "title", "observation", "interpretation", "response", "confidence", "limitation", "evidence_ids"]
    with (target / "data/findings.csv").open("w", newline="", encoding="utf-8-sig") as out:
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        for finding in report["findings"]:
            writer.writerow({**finding, "evidence_ids": " | ".join(finding["evidence_ids"])})
    # Keep the full reviewed source dataset under version control without local media paths.
    source_report.parent.mkdir(parents=True, exist_ok=True)
    source_report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Scouting route ready: {len(report['findings'])} findings / {len(review)} evidence records", flush=True)


if __name__ == "__main__":
    main()
