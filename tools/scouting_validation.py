"""Validate every scouting dossier, round boundaries and evidence exports."""
from pathlib import Path
import csv
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'docs/scouting'


def check_report(folder, source):
    data = json.loads((folder / 'data/scouting-report.json').read_text(encoding='utf-8'))
    assert data == json.loads(source.read_text(encoding='utf-8')), source
    html = (folder / 'index.html').read_text(encoding='utf-8')
    inline = re.search(r'<script id="scouting-data" type="application/json">(.*?)</script>', html, re.S)[1]
    assert json.loads(inline.replace('<\\/', '</')) == data
    assert '__SCOUTING_DATA__' not in html and '__SCOUTING_OPTIONS__' not in html
    evidence = {e['id']: e for e in data['evidence']}
    assert len(evidence) == len(data['evidence'])
    assert {t['id'] for t in data['teams']} == {'blue', 'red', 'green'}
    if data['source'].get('match_date'):
        assert data['source'].get('match_date_source'), 'Upload date alone is not a verified match date'
    duration = data['source']['duration_seconds']
    coverage = data['coverage']
    if coverage.get('source_files'):
        assert len(coverage['source_files']) == 2
        for source_file in coverage['source_files']:
            assert source_file['bytes'] > 0
            assert re.fullmatch('[0-9a-f]{64}', source_file['sha256'])
    if coverage.get('analysis_start_seconds') is not None:
        start, end = coverage['analysis_start_seconds'], coverage['analysis_end_seconds']
        assert 0 <= start < end <= duration
        assert all(start <= r['seconds'] <= end for r in data['score_anchors'])
        assert all(start <= f['start_seconds'] < f['end_seconds'] <= end for f in data['timeline'])
        assert all(e['seconds'] >= start and (not e.get('clip') or e['clip']['start_seconds'] >= start) for e in evidence.values()), 'Warmup evidence leaked into competitive dossier'
    for record in evidence.values():
        assert 0 <= record['seconds'] < duration
        for key in ['image', 'thumbnail']:
            path = (folder / record[key]).resolve()
            assert path.is_relative_to(folder.resolve()) and path.is_file(), path
        assert record['basis'] and record['image_alt']
        if record.get('clip'):
            clip = record['clip']
            assert 0 <= clip['start_seconds'] <= record['seconds'] <= clip['end_seconds'] <= duration
            path = (folder / clip['src']).resolve()
            assert path.is_relative_to(folder.resolve()) and path.is_file()
            assert 0 < path.stat().st_size < 30_000_000
    for finding in data['findings']:
        assert finding['team'] in {'blue', 'red', 'green'}
        assert finding['type'] in {'strength', 'weakness', 'adaptation'}
        assert finding['confidence'] in {'High', 'Moderate'}
        assert all(finding[key] for key in ['observation', 'interpretation', 'response', 'limitation'])
        assert finding['evidence_ids'] and set(finding['evidence_ids']) <= set(evidence)
    assert len({f['id'] for f in data['findings']}) == len(data['findings'])
    with (folder / 'data/findings.csv').open(encoding='utf-8-sig', newline='') as stream:
        exported = list(csv.DictReader(stream))
    assert len(exported) == len(data['findings'])
    for row, original in zip(exported, data['findings']):
        for key in row:
            assert row[key] == (' | '.join(original[key]) if key == 'evidence_ids' else original[key])
    assert len(data['score_anchors']) == data['coverage']['score_anchors']
    previous = {}
    rounds = {r['id']: r for r in data.get('rounds', [])}
    last_time = -1
    for row in data['score_anchors']:
        assert row['seconds'] > last_time, 'Sort anchors by recording time'
        last_time = row['seconds']
        assert row['evidence_id'] in evidence and row['seconds'] == evidence[row['evidence_id']]['seconds']
        round_id = row.get('round_id', 'match')
        if rounds:
            assert round_id in rounds
            assert rounds[round_id]['start_seconds'] <= row['seconds'] <= rounds[round_id]['end_seconds']
        for side in ['blue', 'red', 'green']:
            assert row[side] is None or isinstance(row[side], int) and 0 <= row[side] <= 100
            before = previous.get(round_id)
            if before and row[side] is not None and before[side] is not None:
                assert row[side] >= before[side], 'Review score regressions within the same round'
        previous[round_id] = row
    if data['result'].get('scores'):
        assert {k: data['score_anchors'][-1][k] for k in ['blue', 'red', 'green']} == data['result']['scores']
    assert data['result']['evidence_id'] in evidence
    review = json.loads((folder / 'data/review-log.json').read_text())
    assert {e['id'] for e in review['reviewed_evidence']} == set(evidence)
    assert not data['coverage']['continuous_visual_watch'] and not data['coverage']['manual_human_review']
    for record in review['reviewed_evidence']:
        assert abs(record['seconds'] - record['decoded_seconds']) < 1 / data['source']['fps'] + .01
    for event in data['timeline']:
        assert 0 <= event['start_seconds'] < event['end_seconds'] <= duration
        assert set(event['evidence_ids']) <= set(evidence)
    for record in rounds.values():
        assert 0 <= record['start_seconds'] < record['end_seconds'] <= duration
        if record.get('result_evidence_id'):
            assert record['result_evidence_id'] in evidence
    print(f"PASS {data['id']}: {len(data['findings'])} findings / {len(evidence)} evidence / {len(data['score_anchors'])} score anchors")


def main():
    check_report(PUBLIC, ROOT / 'site/scouting/report.json')
    for source in sorted((ROOT / 'site/scouting/reports').glob('*.json')):
        check_report(PUBLIC / source.stem, source)
    for file in [ROOT / 'site/index.html', ROOT / 'docs/index.html']:
        assert 'href="scouting/"' in file.read_text(encoding='utf-8')
    catalog_path = PUBLIC / 'catalog.json'
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
        assert catalog == json.loads((ROOT / 'site/scouting/catalog.json').read_text(encoding='utf-8'))
        assert len({r['video_id'] for r in catalog}) == len(catalog)
        for record in catalog:
            assert (PUBLIC / record['route'] / 'index.html').is_file()
        assert len(catalog) == 1 + len(list((ROOT / 'site/scouting/reports').glob('*.json')))
    patterns = PUBLIC / 'patterns/index.html'
    if patterns.exists():
        for route, evidence_id in re.findall(r'href="\.\./([^"?]*)(?:\?[^"#]*?evidence=)([^"&#]+)', patterns.read_text(encoding='utf-8')):
            report = json.loads((PUBLIC / route / 'data/scouting-report.json').read_text(encoding='utf-8'))
            assert evidence_id in {r['id'] for r in report['evidence']}, (route, evidence_id)
    for file in PUBLIC.rglob('*'):
        if file.is_file() and file.suffix in {'.html', '.json', '.js', '.csv'}:
            text = file.read_text(encoding='utf-8-sig')
            assert not re.search(r'[CF]:\\|file:///|googlevideo\.com|expire=|__SCOUTING_(?:DATA|OPTIONS)__', text), file
    assert not list(PUBLIC.rglob('source.*')), 'Full source media stays offline'
