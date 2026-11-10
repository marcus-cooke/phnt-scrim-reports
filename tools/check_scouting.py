"""Validate the separate opponent route, evidence, curation and public exports."""
from pathlib import Path
import csv
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "docs/scouting"
data = json.loads((PUBLIC / "data/scouting-report.json").read_text(encoding="utf-8"))
assert data == json.loads((ROOT / "site/scouting/report.json").read_text(encoding="utf-8"))
html = (PUBLIC / "index.html").read_text(encoding="utf-8")
inline = re.search(r'<script id="scouting-data" type="application/json">(.*?)</script>', html, re.S)[1]
assert json.loads(inline.replace('<\\/', '</')) == data
assert "__SCOUTING_DATA__" not in html
for file in [ROOT / "site/index.html", ROOT / "docs/index.html"]:
    assert 'href="scouting/"' in file.read_text(encoding="utf-8"), "Scouting must be discoverable from the report shell"
evidence = {e["id"]: e for e in data["evidence"]}
assert len(evidence) == len(data["evidence"])
assert set(t["id"] for t in data["teams"]) == {"blue", "red", "green"}
assert data["source"]["match_date"] is None, "Do not substitute upload date for match date"
for record in evidence.values():
    assert 0 <= record["seconds"] < data["source"]["duration_seconds"]
    path = (PUBLIC / record["image"]).resolve()
    assert path.is_relative_to(PUBLIC.resolve()) and path.is_file()
    assert (PUBLIC / record['thumbnail']).is_file()
    assert record["basis"] and record["image_alt"]
    if record.get("clip"):
        clip = record["clip"]
        assert 0 <= clip["start_seconds"] <= record["seconds"] <= clip["end_seconds"] <= data["source"]["duration_seconds"]
        path = (PUBLIC / clip["src"]).resolve()
        assert path.is_relative_to(PUBLIC.resolve()) and path.is_file()
        assert 0 < path.stat().st_size < 30_000_000
for finding in data["findings"]:
    assert finding["team"] in {"blue", "red", "green"}
    assert finding["type"] in {"strength", "weakness", "adaptation"}
    assert finding["confidence"] in {"High", "Moderate"}
    assert all(finding[key] for key in ["observation", "interpretation", "response", "limitation"])
    assert finding["evidence_ids"] and set(finding["evidence_ids"]) <= set(evidence)
with (PUBLIC / "data/findings.csv").open(encoding="utf-8-sig", newline="") as stream:
    exported = list(csv.DictReader(stream))
assert len(exported) == len(data["findings"])
for row, source in zip(exported, data["findings"]):
    for key in row:
        assert row[key] == (" | ".join(source[key]) if key == "evidence_ids" else source[key])
assert len(data["score_anchors"]) == data["coverage"]["score_anchors"]
previous = None
for row in data["score_anchors"]:
    assert row["evidence_id"] in evidence
    assert row["seconds"] == evidence[row["evidence_id"]]["seconds"]
    for side in ["blue", "red", "green"]:
        assert row[side] is None or isinstance(row[side], int) and 0 <= row[side] <= 100
        if previous and row[side] is not None and previous[side] is not None:
            assert row[side] >= previous[side], "Review score regressions rather than silently smoothing"
    previous = row
assert {k: data["score_anchors"][-1][k] for k in ["blue", "red", "green"]} == data["result"]["scores"]
assert data["result"]["evidence_id"] in evidence
review = json.loads((PUBLIC / "data/review-log.json").read_text())
assert {e["id"] for e in review["reviewed_evidence"]} == set(evidence)
assert not data["coverage"]["continuous_visual_watch"] and not data["coverage"]["manual_human_review"]
for record in review["reviewed_evidence"]:
    assert abs(record["seconds"] - record["decoded_seconds"]) < .04
for event in data["timeline"]:
    assert 0 <= event["start_seconds"] < event["end_seconds"] <= data["source"]["duration_seconds"]
    assert set(event["evidence_ids"]) <= set(evidence)
for file in PUBLIC.rglob('*'):
    if file.is_file() and file.suffix in {'.html', '.json', '.js', '.csv'}:
        text = file.read_text(encoding='utf-8-sig')
        assert not re.search(r'C:\\Users|file:///|googlevideo\.com|expire=|__SCOUTING_DATA__',text), f'Local path or signed source leaked: {file}'
assert not list(PUBLIC.rglob('source.*')), "Full recording and raw download metadata stay offline"
print(f"PASS: scouting route, {len(data['findings'])} bounded findings, {len(evidence)} evidence records, {len(data['score_anchors'])} score anchors and matching exports")
