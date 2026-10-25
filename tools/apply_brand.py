"""Apply Phantom's shared brand assets to the shell and both static reports."""
from pathlib import Path
import shutil,re

ROOT=Path(__file__).resolve().parents[1]
def branded_html(text,prefix,outer=False):
    text=re.sub(r'<link\s+rel="icon"[^>]*>','',text)
    text=re.sub(r'<link\s+rel="stylesheet"\s+href="[^"]*brand/brand\.css"[^>]*>','',text)
    links=f'<link rel="icon" href="{prefix}brand/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}brand/brand.css">'
    text=text.replace('</head>',links+'</head>')
    if outer:
        text=text.replace('<title>PHNT · Scrim reports</title>','<title>Phantom Regiment · Scrim reports</title>')
        text=text.replace('<body>','<body class="clan-shell">')
        old='<div><div class="brand">PHNT / WAR DOGS</div><h1>Scrim reports</h1></div>'
        new='<div class="identity"><a class="brand-lockup" href="https://phantomwardogs.com/" target="_blank" rel="noopener" aria-label="Phantom Regiment official website"><img class="brand-mark" src="brand/phantom-logomark.svg" alt=""><img class="brand-wordmark" src="brand/phantom-wordmark.svg" alt="Phantom"></a><div class="report-heading"><div class="brand">PHNT · MATCH INTELLIGENCE</div><h1>Scrim reports</h1></div></div>'
        text=text.replace(old,new)
        # Encode the report view as state, not as a matching section anchor,
        # so initial navigation keeps the report's tabs visible.
        text=text.replace("'/index.html#'+section","'/index.html#view='+section")
    else:text=text.replace('<title>PHNT · Scrim review</title>','<title>Phantom Regiment · Match report</title>')
    text=text.replace("const target=document.getElementById('tab-'+location.hash.slice(1));if(target)target.click();", "const requested=new URLSearchParams(location.hash.slice(1)).get('view')||location.hash.slice(1);const target=document.getElementById('tab-'+requested);if(target)target.click();window.addEventListener('load',()=>window.scrollTo(0,0),{once:true});")
    return text

def apply_brand():
    shutil.copytree(ROOT/'site/brand',ROOT/'docs/brand',dirs_exist_ok=True)
    p=ROOT/'site/index.html';p.write_text(branded_html(p.read_text(encoding='utf-8'),'',True),encoding='utf-8')
    p=ROOT/'docs/index.html'
    if p.exists():p.write_text(branded_html(p.read_text(encoding='utf-8'),'',True),encoding='utf-8')
    for p in (ROOT/'docs/matches').glob('*/index.html'):p.write_text(branded_html(p.read_text(encoding='utf-8'),'../../'),encoding='utf-8')
    print('Applied original Phantom SVG lockup, self-hosted Oxanium/Instrument Sans and shared signal-red/graphite styling')
if __name__=='__main__':apply_brand()
