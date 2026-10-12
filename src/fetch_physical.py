"""Collect height, weight and (optionally) EA FC physical ratings for players.

Sources, in order of preference
1. Wikidata (CC0). Queried live from this script. Gives height and sometimes weight,
   date of birth, citizenship and the Transfermarkt id.
2. Transfermarkt dataset by dcaribou (CC0). Download players.csv from
   https://www.kaggle.com/datasets/davidcariboo/player-scores and put it at
   data/external/transfermarkt_players.csv. Gives height_in_cm and date of birth.
3. EA FC / FIFA ratings (optional). These are video game ratings scraped from
   SoFIFA, used only as rough proxies for strength, jumping and speed. Put any
   players_XX.csv files (stefanoleone992 format) in data/external/ea/. They are
   game designers' judgments, not physical tests, and should not be republished.

Output
    data/external/wikidata_players.csv
"""
import csv
import io
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "external"
ENDPOINT = "https://query.wikidata.org/sparql"
UA = "header-quality-portfolio/0.1 (student project; contact via GitHub)"

QUERY = """
SELECT ?p ?name ?dob ?height ?mass ?country ?tm
       (GROUP_CONCAT(DISTINCT ?alias; separator="|") AS ?aliases) WHERE {{
  ?p wdt:P106 wd:Q937857 ;
     p:P2048/psn:P2048/wikibase:quantityAmount ?height ;
     wdt:P569 ?dob .
  FILTER(YEAR(?dob) >= {a} && YEAR(?dob) < {b})
  ?p rdfs:label ?name . FILTER(LANG(?name) = "en")
  OPTIONAL {{ ?p p:P2067/psn:P2067/wikibase:quantityAmount ?mass }}
  OPTIONAL {{ ?p wdt:P27/rdfs:label ?country . FILTER(LANG(?country) = "en") }}
  OPTIONAL {{ ?p wdt:P2446 ?tm }}
  OPTIONAL {{ ?p skos:altLabel ?alias . FILTER(LANG(?alias) IN ("en","es","pt","fr","de","it")) }}
}}
GROUP BY ?p ?name ?dob ?height ?mass ?country ?tm
"""


def run(query):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))
        except Exception as err:  # Wikidata times out now and then
            print("  retry", attempt + 1, err)
            time.sleep(10 * (attempt + 1))
    return []


def main():
    EXT.mkdir(parents=True, exist_ok=True)
    rows = []
    # players in the StatsBomb data were born roughly 1930 to 2008
    for a in range(1930, 2010, 2):
        part = run(QUERY.format(a=a, b=a + 2))
        print(f"born {a}-{a + 1}: {len(part)} rows")
        rows += part
        time.sleep(2)  # be polite to the public endpoint
    out = EXT / "wikidata_players.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["p", "name", "dob", "height", "mass", "country", "tm", "aliases"])
        w.writeheader()
        w.writerows(rows)
    print("saved", len(rows), "rows to", out)


if __name__ == "__main__":
    main()
