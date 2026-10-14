"""Check that the English and Portuguese pages of the website quote the same numbers.

Each page in site_src/ is compared with its copy in site_src/pt/. Every number in
the visible text and in image descriptions is read, with English formatting
(10,327 and 0.67) on one side and Portuguese formatting (10.327 and 0,67) on the
other, and the two lists must match exactly. Run it after editing any page.

    python src/check_site_sync.py
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site_src"

EN_NUM = re.compile(r"(?<![\w.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\d])|(?<![\w.,])\d+(?:\.\d+)?(?![\d])")
PT_NUM = re.compile(r"(?<![\w.,])\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![\d])|(?<![\w.,])\d+(?:,\d+)?(?![\d])")


def text_of(html):
    """Visible text plus alt text, without tags, links or inline SVG drawing code."""
    html = re.sub(r"<svg.*?</svg>", " ", html, flags=re.S)
    alts = " ".join(re.findall(r'alt="([^"]*)"', html))
    body = re.sub(r"<[^>]+>", " ", html)
    return body + " " + alts


def numbers(html, lang):
    t = text_of(html)
    if lang == "en":
        return Counter(float(m.replace(",", "")) for m in EN_NUM.findall(t))
    return Counter(float(m.replace(".", "").replace(",", ".")) for m in PT_NUM.findall(t))


def compare():
    problems = []
    for en in sorted(SRC.glob("*.html")):
        pt = SRC / "pt" / en.name
        if not pt.exists():
            problems.append(f"{en.name}: no Portuguese copy")
            continue
        a, b = numbers(en.read_text(encoding="utf-8"), "en"), numbers(pt.read_text(encoding="utf-8"), "pt")
        only_en, only_pt = a - b, b - a
        if only_en or only_pt:
            problems.append(f"{en.name}: only in English {dict(only_en)}, only in Portuguese {dict(only_pt)}")
    return problems


if __name__ == "__main__":
    out = compare()
    print("\n".join(out) if out else "English and Portuguese pages quote the same numbers")
    sys.exit(1 if out else 0)
