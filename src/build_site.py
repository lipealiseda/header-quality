"""Copy charts into the website folder (docs/) and write the rankings data the
rankings page reads. The pages themselves are hand written HTML in docs/.

GitHub Pages serves the docs/ folder of the main branch.

Run after charts.py and rankings.py
    python src/build_site.py
"""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import RES, ROOT  # noqa: E402

SITE = ROOT / "docs"
SRC = ROOT / "site_src"
REPO = "https://github.com/lipealiseda/header-quality"

# order matters, it is the reading order and drives the previous / next links
PAGES = [
    ("index", "Home", None, "Header quality in football"),
    ("data", "The data", 1, "What free data can measure"),
    ("attack", "Attacking headers", 2, "Attacking headers"),
    ("defense", "Defensive headers", 3, "Defensive headers"),
    ("skill", "Skill or luck", 4, "Skill or luck"),
    ("rankings", "Rankings", 5, "Player rankings"),
    ("method", "Method and limits", 6, "Method and limits"),
]
NAV = {"data": "Data", "attack": "Attack", "defense": "Defense", "skill": "Skill or luck",
       "rankings": "Rankings", "method": "Method"}

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Who wins in the air, and does it last? Expected models for headers and aerial duels from StatsBomb open data, by Filipe Aliseda.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='13' fill='%23fcfcfb' stroke='%2318242f' stroke-width='3'/%3E%3C/svg%3E">
</head>
<body>
<header class="site-head"><div class="inner">
<a class="brand" href="index.html">Header quality in football</a>
<nav aria-label="Chapters"><ul class="chapters">
{nav}
</ul></nav>
</div></header>
<main>
"""

FOOT = """
{pager}
</main>
<footer class="site-foot"><div class="inner">
<p>Built by Filipe Aliseda, statistics student at the University of Florida. Code, data pipeline and full results are on <a href="{repo}">GitHub</a>. Heights from the Transfermarkt dataset by David Cariboo (CC0). Tracking data from Metrica Sports sample data.</p>
<div class="credit"><span>Data provided by</span><img src="img/statsbomb_logo.png" alt="StatsBomb"></div>
</div></footer>
{scripts}
</body>
</html>
"""


def build_pages():
    for i, (slug, label, num, title) in enumerate(PAGES):
        nav = []
        for s2, l2, n2, _ in PAGES[1:]:
            cur = ' aria-current="page"' if s2 == slug else ""
            nav.append(f'<li><a href="{s2}.html"{cur}><span class="num">{n2}</span>{NAV[s2]}</a></li>')
        pager = ""
        if slug != "index":
            prev = PAGES[i - 1]
            nxt = PAGES[i + 1] if i + 1 < len(PAGES) else None
            left = (f'<a class="prev" href="{prev[0]}.html"><span class="dir">Previous</span>'
                    f'<span class="t">{prev[1]}</span></a>')
            right = (f'<a class="next" href="{nxt[0]}.html"><span class="dir">Next</span>'
                     f'<span class="t">{nxt[1]}</span></a>') if nxt else ""
            pager = f'<nav class="pager" aria-label="Chapters">{left}{right}</nav>'
        body = (SRC / f"{slug}.html").read_text(encoding="utf-8")
        scripts = ""
        if slug == "rankings":
            scripts = '<script src="data/duels.js"></script>\n<script src="rankings.js"></script>'
        page_title = title if slug == "index" else f"{title}. Header quality in football"
        html = (HEAD.format(title=page_title, nav="\n".join(nav)) + body +
                FOOT.format(pager=pager, repo=REPO, scripts=scripts))
        (SITE / f"{slug}.html").write_text(html, encoding="utf-8")
    shutil.copy(SRC / "rankings.js", SITE / "rankings.js")
POS = {"CB": "Centre back", "FB": "Full back", "DM": "Defensive mid", "CM": "Central mid",
       "AM": "Attacking mid", "WM": "Wide mid", "W": "Winger", "ST": "Striker", "GK": "Goalkeeper"}


def main():
    (SITE / "img").mkdir(parents=True, exist_ok=True)
    (SITE / "data").mkdir(exist_ok=True)
    for f in (ROOT / "figures").glob("*.png"):
        shutil.copy(f, SITE / "img" / f.name)
    shutil.copy(ROOT / "assets" / "statsbomb_logo.png", SITE / "img" / "statsbomb_logo.png")
    (SITE / ".nojekyll").write_text("")

    r = pd.read_csv(RES / "rank_duels_vs_expected.csv")
    q = r[r["qualified"] & r["pos_group"].isin(POS) & (r["pos_group"] != "GK")].copy()
    rows = []
    for x in q.itertuples():
        rows.append({
            "name": x.name, "pos": POS[x.pos_group], "club": x.main_club if isinstance(x.main_club, str) else "",
            "h": int(x.height_cm), "n": int(x.n), "won": int(x.actual), "exp": round(float(x.expected), 1),
            "above": round(float(x.shrunk_rate) * 100, 1),       # shown, same rounding as the charts
            "mu": round(float(x.shrunk_rate) * 100, 3),          # unrounded, for the comparison box
            "sd": round(float(x.post_sd) * 100, 3),
            "lo": round(float(x.lo95) * 100, 1), "hi": round(float(x.hi95) * 100, 1),
            # 95% rank range within each position group the page can filter by
            "rr": {g: [int(getattr(x, f"rank_{g}_lo")), int(getattr(x, f"rank_{g}_hi"))]
                   for g in ("def", "fwd", "mid", "all") if getattr(x, f"rank_{g}_lo") == getattr(x, f"rank_{g}_lo")},
        })
    js = "// built by src/build_site.py from results/rank_duels_vs_expected.csv\nwindow.DUELS = " + \
         json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (SITE / "data" / "duels.js").write_text(js, encoding="utf-8")
    build_pages()
    print(f"site built, {len(PAGES)} pages, {len(rows)} players in the duel table")


if __name__ == "__main__":
    main()
