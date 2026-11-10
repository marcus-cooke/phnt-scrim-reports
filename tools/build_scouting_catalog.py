"""Connect completed dossiers without replacing the original scouting URL."""
import json
import shutil
from build_scouting import ROOT, render_page


if __name__ == '__main__':
    reports = [('', ROOT / 'site/scouting/report.json')]
    reports += [(p.stem, p) for p in sorted((ROOT / 'site/scouting/reports').glob('*.json'))]
    rows = []
    for slug, file in reports:
        d = json.loads(file.read_text(encoding='utf-8'))
        folder = ROOT / 'docs/scouting' / slug
        assert (folder / 'data/scouting-report.json').exists(), f'Package {slug} before adding navigation'
        rows.append(dict(slug=slug, route=slug + '/' if slug else './', id=d['id'],
                         video_id=d['source']['video_id'], label=d.get('presentation', {}).get('selector_label', 'Black Sails / first competitive war' if not slug else d['source']['title']),
                         findings=len(d['findings']), score_anchors=len(d['score_anchors']), evidence=len(d['evidence'])))
    for folder in [ROOT / 'site/scouting', ROOT / 'docs/scouting']:
        (folder / 'catalog.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
    for slug, file in reports:
        d = json.loads(file.read_text(encoding='utf-8'))
        folder = ROOT / 'docs/scouting' / slug
        (folder / 'index.html').write_text(render_page(d, slug), encoding='utf-8')
        for name in ['scouting.css', 'scouting.js']:
            shutil.copy2(ROOT / 'site/scouting' / name, folder / name)
    patterns = ROOT / 'docs/scouting/patterns'
    patterns.mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'site/scouting/patterns.html', patterns / 'index.html')
    print(f'Connected {len(rows)} completed scouting recordings')
