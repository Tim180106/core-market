"""
test_data_sources.py — v0.2
Section 2 AMENDMENT — C.O.R.E

v0.1 relied on yfinance for everything and got 0/14 on a live Colab run (Yahoo rate-limiting the
whole session). This version tests the amended strategy instead:
  - NSE Bhavcopy (official, direct) for stocks
  - yfinance as a low-cost opportunistic secondary path (kept, just not trusted as primary)
  - Stooq direct CSV as fallback for commodities/currency

Run in Colab after `pip install -r requirements.txt`:
    python scripts/test_data_sources.py
"""

import io
import time
import zipfile
from datetime import date, timedelta

import requests
import yaml

try:
    import yfinance as yf
except ImportError:
    yf = None  # yfinance is now optional/secondary — don't hard-fail if it's missing


def load_config(path: str = "config/settings.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def most_recent_weekday(d: date) -> date:
    """NSE doesn't publish on weekends — step back to the most recent Mon-Fri."""
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d -= timedelta(days=1)
    return d


def test_nse_bhavcopy(cfg: dict) -> bool:
    """Warm up cookies against nseindia.com, then pull the most recent Bhavcopy zip."""
    nse_cfg = cfg["fetch"]["nse_bhavcopy"]
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    session = requests.Session()
    session.headers.update(headers)

    try:
        session.get(nse_cfg["warmup_url"], timeout=15)
    except Exception as e:
        print(f"  [WARN] NSE cookie warm-up failed: {e}")

    target_date = most_recent_weekday(date.today() - timedelta(days=1))
    for attempt in range(5):  # try up to 5 prior weekdays in case of a market holiday
        d = target_date - timedelta(days=attempt)
        d = most_recent_weekday(d)
        url = nse_cfg["url_template"].format(yyyymmdd=d.strftime("%Y%m%d"))
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 200 and resp.content[:2] == b"PK":  # PK = zip file signature
                with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                    names = z.namelist()
                    print(f"  [OK]   NSE Bhavcopy ({d}) — {names[0]}, {len(resp.content)} bytes")
                return True
            print(f"  [WARN] NSE Bhavcopy ({d}) — HTTP {resp.status_code}, trying earlier date...")
        except Exception as e:
            print(f"  [WARN] NSE Bhavcopy ({d}) — {e}")
        time.sleep(1)
    print("  [FAIL] NSE Bhavcopy — no valid file found in last 5 weekdays")
    return False


def test_stooq_csv(label: str, symbol: str) -> bool:
    if not symbol:
        print(f"  [SKIP] {label:<12} — no stooq symbol set yet, verify manually")
        return False
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and b"Date,Open" in resp.content[:50]:
            lines = resp.content.decode().strip().splitlines()
            print(f"  [OK]   {label:<12} (stooq:{symbol}) — {len(lines)-1} rows")
            return True
        print(f"  [FAIL] {label:<12} (stooq:{symbol}) — unexpected response: {resp.content[:80]}")
        return False
    except Exception as e:
        print(f"  [FAIL] {label:<12} (stooq:{symbol}) — {e}")
        return False


def test_yfinance_optional(label: str, symbol: str) -> bool:
    if yf is None:
        return False
    try:
        df = yf.Ticker(symbol).history(period="5d")
        if df is not None and not df.empty:
            print(f"  [OK]   {label:<12} ({symbol}) via yfinance — {len(df)} rows")
            return True
    except Exception as e:
        print(f"  [INFO] {label:<12} ({symbol}) yfinance still unavailable: {e}")
    return False


def main():
    cfg = load_config()
    universe = cfg["universe"]

    print("\n=== NSE Bhavcopy (stocks — new primary source) ===")
    bhavcopy_ok = test_nse_bhavcopy(cfg)

    print("\n=== Commodities & currency (yfinance first, Stooq fallback) ===")
    results = {}
    for name, spec in {**universe["commodities"], "usd_inr": universe["currency"]["usd_inr"]}.items():
        ok = test_yfinance_optional(name, spec["symbol"])
        if not ok:
            ok = test_stooq_csv(name, spec.get("stooq_symbol"))
        results[name] = ok

    print("\n=== Indices (endpoint TBD — yfinance opportunistic attempt only) ===")
    for name, spec in universe["indices"].items():
        results[f"index:{name}"] = test_yfinance_optional(name, spec["symbol"])

    print("\n=== Macro (manual source — no live check) ===")
    print(f"  [SKIP] {universe['macro']['source']} — verify manually per docs/data_sources.md")

    print("\n=== Summary ===")
    ok_count = sum(1 for v in results.values() if v) + (1 if bhavcopy_ok else 0)
    total = len(results) + 1
    print(f"{ok_count}/{total} sources reachable right now (NSE Bhavcopy counted once, covers whole stock universe).")
    if not bhavcopy_ok:
        print("NSE Bhavcopy failed — check the [WARN] lines above; likely a User-Agent/cookie issue")
        print("or NSE changed the URL pattern again. Paste the output into the next Claude chat.")


if __name__ == "__main__":
    main()
