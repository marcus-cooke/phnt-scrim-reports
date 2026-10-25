"""Check original brand asset bytes and portable font/style application."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];source=ROOT/'site/brand';public=ROOT/'docs/brand'
manifest=json.loads((source/'manifest.json').read_text())
for item in manifest['files']:
    for root in [source,public]:
        assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256'],f'Brand asset differs: {root/item["path"]}'
css=(public/'brand.css').read_text()
for target in re.findall(r'url\([\'"]?([^\)\'\"]+)',css):assert (public/target).is_file(),f'Missing font: {target}'
assert '--brand-accent:#d52b27' in css
assert '--font-body:\'Instrument Sans\'' in css
assert '--font-phantom:Oxanium' in css
for p in [ROOT/'docs/index.html',*list((ROOT/'docs/matches').glob('*/index.html'))]:
    html=p.read_text(encoding='utf-8');assert html.count('rel="stylesheet"')==1,f'Duplicate/missing shared styles on {p}'
    assert 'brand/brand.css' in html
    assert '<title>Phantom Regiment' in html
outer=(ROOT/'docs/index.html').read_text(encoding='utf-8')
assert 'brand/phantom-logomark.svg' in outer and 'brand/phantom-wordmark.svg' in outer
print('PASS: original logo/font fingerprints, self-hosted font URLs, shared branding on shell and both match reports')
