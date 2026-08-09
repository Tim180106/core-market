"""
test_data_sources.py — v0.1
Section 2 deliverable — C.O.R.E

Run this in Colab (NOT in a restricted/offline sandbox) after `pip install -r requirements.txt`.
It does a small, polite, one-shot pull from every free source in config/settings.yaml and reports
which ones are currently reachable — nothing here is a full ingestion pipeline, that's Section 3.

Usage (from repo root, inside Colab after mounting/cloning the repo):
    python scripts/test_data_sources.py
"""

import time
import sys
from pathlib import Path

import yaml

try:
    import yfinance as yf
except ImportError:
    sys.exit("yfinance not installed — run: pip install yfinance")


def load_config(path: str = "config/settings.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def try_pull(label: str, symbol: str, period: str = "5d", retries: int = 3, backoff: int = 5) -> bool:
    """Attempt a small yfinance pull with retry/backoff. Returns True on success."""
    for attempt in range(1, retries + 1):
        try:
            df = yf.Ticker(symbol).history(period=period)
            if df is not None and not df.empty:
                print(f"  [OK]   {label:<20} ({symbol}) — {len(df)} rows, last close: {df['Close'].iloc[-1]:.2f}")
                return True
            print(f"  [EMPTY]{label:<20} ({symbol}) — no rows returned")
            return False
        except Exception as e:
            wait = backoff * attempt
            print(f"  [WARN] {label:<20} ({symbol}) — attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                print(f"         retrying in {wait}s...")
                time.sleep(wait)
    print(f"  [FAIL] {label:<20} ({symbol}) — giving up after {retries} attempts")
    return False


def main():
    cfg = load_config()
    universe = cfg["universe"]
    results = {}

    print("\n=== Indices ===")
    for name, spec in universe["indices"].items():
        results[f"index:{name}"] = try_pull(name, spec["symbol"])
        time.sleep(cfg["fetch"]["delay_between_batches_sec"])

    print("\n=== Sample stocks (first 3 of universe, to stay polite to Yahoo) ===")
    for stock in universe["stocks"][:3]:
        results[f"stock:{stock['ticker']}"] = try_pull(stock["ticker"], stock["ticker"])
        time.sleep(cfg["fetch"]["delay_between_batches_sec"])

    print("\n=== Commodities ===")
    for name, spec in universe["commodities"].items():
        results[f"commodity:{name}"] = try_pull(name, spec["symbol"])
        time.sleep(cfg["fetch"]["delay_between_batches_sec"])

    print("\n=== Currency ===")
    fx = universe["currency"]["usd_inr"]
    results["currency:usd_inr"] = try_pull("usd_inr", fx["symbol"])

    print("\n=== Macro (manual source — no live check) ===")
    print(f"  [SKIP] macro series come from {universe['macro']['source']} — verify manually, see docs/data_sources.md")

    print("\n=== Summary ===")
    ok = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"{ok}/{total} sources reachable right now.")
    if ok < total:
        print("Some sources failed — this is EXPECTED occasionally with yfinance (rate limits).")
        print("Re-run later, or check docs/data_sources.md for the Stooq fallback plan (Section 3).")


if __name__ == "__main__":
    main()
