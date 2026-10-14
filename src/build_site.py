"""Build the website in docs/ from the page sources in site_src/. English pages
come from site_src/*.html and Portuguese pages from site_src/pt/*.html, wrapped in
the same header and footer. Charts are copied from figures/ (English) and
figures/pt/ (Portuguese), and the rankings data both versions read is written to
docs/data/duels.js.

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

# order matters, it is the reading order and drives the previous / next links.
# Each language has its own page sources (site_src/ for English, site_src/pt/ for
# Portuguese), labels and output folder (docs/ and docs/pt/).
SLUGS = ["index", "data", "attack", "defense", "skill", "rankings", "method"]
LANG = {
    "en": {
        "html_lang": "en", "src": SRC, "out": SITE, "root": "", "img_src": ROOT / "figures",
        "brand": "Header quality in football",
        "desc": "Who wins in the air, and does it last? Expected models for headers and aerial duels "
                "from StatsBomb open data, by Filipe Aliseda.",
        "labels": ["Home", "The data", "Attacking headers", "Defensive headers", "Skill or luck",
                   "Rankings", "Method and limits"],
        "titles": ["Header quality in football", "What free data can measure", "Attacking headers",
                   "Defensive headers", "Skill or luck", "Player rankings", "Method and limits"],
        "nav": ["", "Data", "Attack", "Defense", "Skill or luck", "Rankings", "Method"],
        "prev": "Previous", "next": "Next", "chapters": "Chapters", "data_by": "Data provided by",
        "foot": "Built by Filipe Aliseda, statistics student at the University of Florida. Code, data pipeline "
                "and full results are on <a href=\"{repo}\">GitHub</a>. Heights from the Transfermarkt dataset by "
                "David Cariboo (CC0). Tracking data from Metrica Sports sample data.",
    },
    "pt": {
        "html_lang": "pt-BR", "src": SRC / "pt", "out": SITE / "pt", "root": "../",
        "img_src": ROOT / "figures" / "pt",
        "brand": "Qualidade no jogo aéreo",
        "desc": "Quem ganha pelo alto, e isso se repete? Modelos esperados para cabeceios e duelos aéreos "
                "com dados abertos da StatsBomb, por Filipe Aliseda.",
        "labels": ["Início", "Os dados", "Cabeceios no ataque", "Cabeceios na defesa", "Talento ou sorte",
                   "Rankings", "Método e limites"],
        "titles": ["Qualidade no jogo aéreo", "O que dados gratuitos conseguem medir", "Cabeceios no ataque",
                   "Cabeceios na defesa", "Talento ou sorte", "Ranking de jogadores", "Método e limites"],
        "nav": ["", "Dados", "Ataque", "Defesa", "Talento ou sorte", "Rankings", "Método"],
        "prev": "Anterior", "next": "Próximo", "chapters": "Capítulos", "data_by": "Dados fornecidos por",
        "foot": "Feito por Filipe Aliseda, estudante de estatística na Universidade da Flórida. Código, "
                "processamento dos dados e resultados completos estão no <a href=\"{repo}\">GitHub</a>. Alturas "
                "do conjunto de dados do Transfermarkt de David Cariboo (CC0). Dados de rastreamento das "
                "amostras da Metrica Sports.",
    },
}

HEAD = """<!doctype html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="alternate" hreflang="en" href="{en_href}">
<link rel="alternate" hreflang="pt-BR" href="{pt_href}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='13' fill='%23fcfcfb' stroke='%2318242f' stroke-width='3'/%3E%3C/svg%3E">
</head>
<body>
<header class="site-head"><div class="inner">
<div class="brand-row"><a class="brand" href="index.html">{brand}</a>
<span class="lang-switch">{switch}</span></div>
<nav aria-label="{chapters}"><ul class="chapters">
{nav}
</ul></nav>
</div></header>
<main>
"""

FOOT = """
{pager}
</main>
<footer class="site-foot"><div class="inner">
<p>{foot}</p>
<div class="credit"><span>{data_by}</span><img src="img/statsbomb_logo.png" alt="StatsBomb"></div>
</div></footer>
{scripts}
</body>
</html>
"""


def build_pages(lang):
    L = LANG[lang]
    L["out"].mkdir(parents=True, exist_ok=True)
    pages = list(zip(SLUGS, L["labels"], [None, 1, 2, 3, 4, 5, 6], L["titles"]))
    for i, (slug, label, num, title) in enumerate(pages):
        nav = []
        for (s2, _, n2, _), short in zip(pages[1:], L["nav"][1:]):
            cur = ' aria-current="page"' if s2 == slug else ""
            nav.append(f'<li><a href="{s2}.html"{cur}><span class="num">{n2}</span>{short}</a></li>')
        pager = ""
        if slug != "index":
            prev = pages[i - 1]
            nxt = pages[i + 1] if i + 1 < len(pages) else None
            left = (f'<a class="prev" href="{prev[0]}.html"><span class="dir">{L["prev"]}</span>'
                    f'<span class="t">{prev[1]}</span></a>')
            right = (f'<a class="next" href="{nxt[0]}.html"><span class="dir">{L["next"]}</span>'
                     f'<span class="t">{nxt[1]}</span></a>') if nxt else ""
            pager = f'<nav class="pager" aria-label="{L["chapters"]}">{left}{right}</nav>'
        body = (L["src"] / f"{slug}.html").read_text(encoding="utf-8")
        scripts = ""
        if slug == "rankings":
            scripts = (f'<script src="{L["root"]}data/duels.js"></script>\n'
                       f'<script src="{L["root"]}rankings.js"></script>')
        page_title = title if slug == "index" else f"{title}. {L['brand']}"
        en_href, pt_href = (f"{slug}.html", f"pt/{slug}.html") if lang == "en" else (f"../{slug}.html", f"{slug}.html")
        if lang == "en":
            switch = (f'<a href="{en_href}" aria-current="true" lang="en">EN</a>'
                      f'<a href="{pt_href}" lang="pt-BR" hreflang="pt-BR" title="Versão em português">PT</a>')
        else:
            switch = (f'<a href="{en_href}" lang="en" hreflang="en" title="English version">EN</a>'
                      f'<a href="{pt_href}" aria-current="true" lang="pt-BR">PT</a>')
        html = (HEAD.format(html_lang=L["html_lang"], title=page_title, desc=L["desc"], root=L["root"],
                            brand=L["brand"], switch=switch, chapters=L["chapters"], nav="\n".join(nav),
                            en_href=en_href, pt_href=pt_href) + body +
                FOOT.format(pager=pager, foot=L["foot"].format(repo=REPO), data_by=L["data_by"], scripts=scripts))
        (L["out"] / f"{slug}.html").write_text(html, encoding="utf-8")


POS = {"CB": "Centre back", "FB": "Full back", "DM": "Defensive mid", "CM": "Central mid",
       "AM": "Attacking mid", "WM": "Wide mid", "W": "Winger", "ST": "Striker", "GK": "Goalkeeper"}


def main():
    for lang in LANG:
        L = LANG[lang]
        (L["out"] / "img").mkdir(parents=True, exist_ok=True)
        for f in L["img_src"].glob("*.png"):
            shutil.copy(f, L["out"] / "img" / f.name)
        shutil.copy(ROOT / "assets" / "statsbomb_logo.png", L["out"] / "img" / "statsbomb_logo.png")
    (SITE / "data").mkdir(exist_ok=True)
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
    for lang in LANG:
        if (LANG[lang]["src"] / "index.html").exists():
            build_pages(lang)
    shutil.copy(SRC / "rankings.js", SITE / "rankings.js")
    print(f"site built, {len(SLUGS)} pages per language, {len(rows)} players in the duel table")


if __name__ == "__main__":
    main()
