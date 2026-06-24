"""
FIFA Rankings Scraper — scrapes live data, falls back to embedded 2026 WC rankings.
"""
import time, random, logging
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

FIFA_RANKING_URL = "https://inside.fifa.com/fifa-world-ranking/men"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

FALLBACK_RANKINGS = [
    {"rank":1,"team":"France","confederation":"UEFA","points":1840.69},
    {"rank":2,"team":"Spain","confederation":"UEFA","points":1836.44},
    {"rank":3,"team":"Argentina","confederation":"CONMEBOL","points":1832.45},
    {"rank":4,"team":"England","confederation":"UEFA","points":1808.44},
    {"rank":5,"team":"Portugal","confederation":"UEFA","points":1791.06},
    {"rank":6,"team":"Brazil","confederation":"CONMEBOL","points":1782.44},
    {"rank":7,"team":"Netherlands","confederation":"UEFA","points":1752.26},
    {"rank":8,"team":"Morocco","confederation":"CAF","points":1722.21},
    {"rank":9,"team":"Belgium","confederation":"UEFA","points":1719.47},
    {"rank":10,"team":"Germany","confederation":"UEFA","points":1696.47},
    {"rank":11,"team":"Croatia","confederation":"UEFA","points":1657.51},
    {"rank":13,"team":"Colombia","confederation":"CONMEBOL","points":1648.43},
    {"rank":14,"team":"Senegal","confederation":"CAF","points":1644.52},
    {"rank":15,"team":"Mexico","confederation":"CONCACAF","points":1636.47},
    {"rank":16,"team":"United States","confederation":"CONCACAF","points":1633.42},
    {"rank":17,"team":"Uruguay","confederation":"CONMEBOL","points":1631.37},
    {"rank":18,"team":"Japan","confederation":"AFC","points":1629.37},
    {"rank":19,"team":"Switzerland","confederation":"UEFA","points":1621.38},
    {"rank":21,"team":"Iran","confederation":"AFC","points":1605.46},
    {"rank":22,"team":"Turkey","confederation":"UEFA","points":1598.45},
    {"rank":23,"team":"Ecuador","confederation":"CONMEBOL","points":1592.36},
    {"rank":24,"team":"Austria","confederation":"UEFA","points":1586.37},
    {"rank":25,"team":"South Korea","confederation":"AFC","points":1580.38},
    {"rank":27,"team":"Australia","confederation":"AFC","points":1563.39},
    {"rank":28,"team":"Algeria","confederation":"CAF","points":1556.42},
    {"rank":29,"team":"Egypt","confederation":"CAF","points":1551.37},
    {"rank":30,"team":"Canada","confederation":"CONCACAF","points":1547.41},
    {"rank":31,"team":"Norway","confederation":"UEFA","points":1541.42},
    {"rank":33,"team":"Panama","confederation":"CONCACAF","points":1525.39},
    {"rank":34,"team":"Ivory Coast","confederation":"CAF","points":1519.41},
    {"rank":38,"team":"Sweden","confederation":"UEFA","points":1498.38},
    {"rank":40,"team":"Paraguay","confederation":"CONMEBOL","points":1489.35},
    {"rank":41,"team":"Czech Republic","confederation":"UEFA","points":1485.37},
    {"rank":43,"team":"Scotland","confederation":"UEFA","points":1479.38},
    {"rank":44,"team":"Tunisia","confederation":"CAF","points":1473.35},
    {"rank":46,"team":"DR Congo","confederation":"CAF","points":1459.36},
    {"rank":50,"team":"Uzbekistan","confederation":"AFC","points":1441.38},
    {"rank":55,"team":"Qatar","confederation":"AFC","points":1419.39},
    {"rank":57,"team":"Iraq","confederation":"AFC","points":1411.36},
    {"rank":60,"team":"South Africa","confederation":"CAF","points":1399.35},
    {"rank":61,"team":"Saudi Arabia","confederation":"AFC","points":1396.35},
    {"rank":63,"team":"Jordan","confederation":"AFC","points":1389.36},
    {"rank":65,"team":"Bosnia and Herzegovina","confederation":"UEFA","points":1381.37},
    {"rank":69,"team":"Cape Verde","confederation":"CAF","points":1359.36},
    {"rank":74,"team":"Ghana","confederation":"CAF","points":1341.35},
    {"rank":82,"team":"Curaçao","confederation":"CONCACAF","points":1309.36},
    {"rank":83,"team":"Haiti","confederation":"CONCACAF","points":1305.37},
    {"rank":85,"team":"New Zealand","confederation":"OFC","points":1299.38},
]

def scrape_fifa_rankings() -> pd.DataFrame:
    logger.info("Scraping FIFA rankings from %s", FIFA_RANKING_URL)
    try:
        time.sleep(random.uniform(1.0, 2.5))
        resp = requests.get(FIFA_RANKING_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []
        table = soup.find("table")
        if table:
            for tr in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
                if len(cells) >= 3:
                    try:
                        rows.append({"rank": int(cells[0]), "team": cells[1], "points": float(cells[-1].replace(",","."))})
                    except: continue
        if rows:
            df = pd.DataFrame(rows)
            df["scraped_at"] = datetime.now().isoformat()
            df["source"] = "live"
            logger.info("Scraped %d teams live", len(df))
            return df
        logger.warning("Could not parse FIFA table — using fallback")
    except Exception as e:
        logger.warning("Scraping failed: %s — using fallback", e)
    return _fallback()

def _fallback() -> pd.DataFrame:
    df = pd.DataFrame(FALLBACK_RANKINGS)
    df["scraped_at"] = datetime.now().isoformat()
    df["source"] = "fallback_2026"
    return df

def load_or_scrape_rankings(force_refresh=False) -> pd.DataFrame:
    cache = RAW_DIR / "fifa_rankings_live.csv"
    if not force_refresh and cache.exists():
        age_h = (time.time() - cache.stat().st_mtime) / 3600
        if age_h < 24:
            logger.info("Loaded cached rankings (%.1fh old)", age_h)
            return pd.read_csv(cache)
    df = scrape_fifa_rankings()
    df.to_csv(cache, index=False)
    return df

if __name__ == "__main__":
    df = load_or_scrape_rankings(force_refresh=True)
    print(df.to_string(index=False))
