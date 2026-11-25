#!/usr/bin/env python3
"""Create a one-file, offline HTML edition from the existing GitHub Pages site."""
from pathlib import Path
import base64
import json
import mimetypes
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda name: (ROOT / name).read_text(encoding="utf-8")
html = read("index.html")
css = "\n".join(read(name) for name in ("style.css", "v10.css", "v11.css"))
js = read("app.js")
lab_html = read("maabedet_malbanim_interactive.html")

assets = {}
for path in sorted((ROOT / "assets").glob("*")):
    if not path.is_file():
        continue
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    assets[f"assets/{path.name}"] = f"data:{mime};base64,{encoded}"

css = css.replace("url('assets/approved_map.png')", "var(--kingdomOriginalBg)")
css = css.replace('url("assets/approved_map.png")', "var(--kingdomOriginalBg)")
css = css.replace("url('assets/approved_map_crisp.webp')", "var(--kingdomCrispBg)")
css = css.replace('url("assets/approved_map_crisp.webp")', "var(--kingdomCrispBg)")
for name in ("style.css", "v10.css", "v11.css"):
    html = html.replace(f'<link rel="stylesheet" href="{name}">', "")
html = html.replace("</head>", f"<style>\n{css}\n</style></head>", 1)

js = js.replace(
    "assets/portal_hd_${i+1}.webp",
    "${window.__KINGDOM_ASSETS['assets/portal_hd_'+(i+1)+'.webp']}"
)
js = js.replace(
    "assets/room_${r}.webp",
    "${window.__KINGDOM_ASSETS['assets/room_'+r+'.webp']}"
)
js = js.replace(
    'src="maabedet_malbanim_interactive.html"',
    "src=\"'+window.__rectLabURL+'\""
)
js = re.sub(r"</script", r"<\\/script", js, flags=re.I)
lab_literal = json.dumps(lab_html, ensure_ascii=False).replace("<", r"\u003c")
loader = (
    "window.__KINGDOM_ASSETS=" + json.dumps(assets, ensure_ascii=False) + ";\n"
    "const ASSETS=window.__KINGDOM_ASSETS;\n"
    "document.documentElement.style.setProperty('--kingdomOriginalBg',"
    "'url(\"'+ASSETS['assets/approved_map_hd.webp']+'\")');\n"
    "document.documentElement.style.setProperty('--kingdomCrispBg',"
    "'url(\"'+ASSETS['assets/approved_map_crisp.webp']+'\")');\n"
    "for(const img of document.querySelectorAll('img[src^=\"assets/\"]')){"
    "let key=img.getAttribute('src');if(ASSETS[key])img.src=ASSETS[key];}\n"
    "window.__rectLabURL=URL.createObjectURL(new Blob([" + lab_literal +
    "],{type:'text/html;charset=utf-8'}));\n"
)
html = html.replace(
    '<script src="app.js"></script>',
    '<script>\n' + loader + "\n" + js + "\n</script>",1
)
assert '<script src="app.js">' not in html
assert '<link rel="stylesheet"' not in html
assert 'assets/portal_hd_${i+1}.webp' not in html
assert 'assets/room_${r}.webp' not in html
assert 'src="maabedet_malbanim_interactive.html"' not in html
assert 'window.__rectLabURL' in html
assert 'data:image/webp;base64,' in html
out = ROOT / "mamlechet_hatnua_standalone.html"
out.write_text(html, encoding="utf-8")
print(f"Created {out.name}: {out.stat().st_size:,} bytes; {len(assets)} embedded assets")
