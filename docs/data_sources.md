# Data Source Map — C.O.R.E
Version: v0.2 (AMENDED after live Colab test — see Section 2 Amendment below)
Section: 2 — Data Source Mapping
Last verified: 2026-08-10

---

## SECTION 2 AMENDMENT (read this first)

v0.1 of this doc treated `yfinance` as the primary source for everything: indices, stocks,
commodities, and currency. A live connectivity test run in Colab returned **0/14 sources reachable**
— every single yfinance call failed with `YFRateLimitError`, including global futures tickers that
have nothing to do with India. That rules out "our specific tickers are the problem" — this is Yahoo
blocking the request pattern/IP wholesale, which is a widely-documented, current issue with
`yfinance` on shared-IP environments like Colab (Yahoo tightened anti-scraping defenses through
2025–2026; the underlying `yfinance` GitHub repo has dozens of open reports of exactly this).

**Decision:** Split the sourcing strategy by asset class instead of leaning on one library for
everything:

| Asset class | Old plan (v0.1) | New plan (v0.2) |
|---|---|---|
| NSE indices & stocks | yfinance | **NSE Bhavcopy (official, direct)** — primary. yfinance kept as opportunistic secondary only. |
| Commodities & USD/INR | yfinance | yfinance retry-first, **Stooq direct CSV** fallback (not `pandas_datareader.stooq`, which is broken for commodities — see below) |
| Macro (repo rate, CPI, etc.) | Manual RBI DBIE CSV | Unchanged |
| Calendar / lunar | Computed | Unchanged |

This is a better design anyway, not just a workaround: NSE publishing its own data directly is more
authoritative than an unofficial scrape of a third party's unofficial scrape of NSE's data.

---

## 1. Equity & Index data — NSE Bhavcopy (NEW primary source)

**What it is:** NSE publishes an official end-of-day "Bhavcopy" file every trading day, directly from
their own servers. Since July 2024 this is in the new **UDiFF (Unified Distilled File Format)** —
the old `archives.nseindia.com/.../cmDDMMMYYYYbhav.csv.zip` links are discontinued; anything built
before mid-2024 (including many tutorials still floating around) is using a dead URL pattern.

**Confirmed current URL pattern (equities, Capital Market segment):**
```
https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{YYYYMMDD}_F_0000.csv.zip
```
e.g. for 10 Aug 2026: `.../BhavCopy_NSE_CM_0_0_0_20260810_F_0000.csv.zip`

**Known gotcha (build this into Section 3, flagging now):** NSE's servers commonly reject requests
that look like bare scripts — a plain `requests.get()` with no browser-like `User-Agent` header often
gets a 403, and some setups need a "warm-up" GET to `https://www.nseindia.com` first to pick up
session cookies before the archive URL will respond. This is a known quirk of the NSE site, not
something specific to our code.

**What it covers:** Every NSE-listed equity's OHLCV for that day, in one file — covers our whole
stock universe in a single daily download instead of one call per ticker. This is also inherently
more Colab-friendly: one file per day instead of 15+ separate rate-limitable calls.

**What it does NOT cover:** Index-level closing values (Nifty 50, Sensex, Nifty Bank) come from a
separate NSE report, not the equity Bhavcopy. The exact current endpoint for this needs to be
pinned down and live-tested in Section 3 rather than guessed here — NSE has changed this a few times
too, and shipping an unverified URL would just move the problem instead of fixing it.

**Historical depth:** Bhavcopy archives go back to the 1990s, so backtesting depth is not a concern.

---

## 2. Commodity & currency data — yfinance (retry) → Stooq CSV (fallback)

Gold/silver/crude/copper/USD-INR aren't NSE instruments, so Bhavcopy doesn't help here. Plan:

1. **Try yfinance first**, since the block may be temporary/session-specific — worth a low-cost retry
   at ingestion time in Section 3, not worth relying on.
2. **Fallback: Stooq's direct CSV download endpoint**, not the `pandas_datareader.stooq` wrapper —
   that wrapper has been broken for commodity symbols specifically since late 2021 (confirmed via
   current bug reports), even though it still works for equities/indices. The raw endpoint
   (`https://stooq.com/q/d/l/?s=SYMBOL&...`) still works directly. Stooq has a low daily request quota,
   so this is a fallback for a handful of commodity/currency series, not a high-volume source.

| Instrument | Stooq symbol (to verify exact form in Section 3) |
|---|---|
| Gold | `xauusd` |
| Crude oil (WTI) | `cl.f` |
| USD/INR | `usdinr` |

These are noted as "to verify" deliberately — Stooq's symbol conventions are inconsistently
documented and the previous section's mistake (shipping an untested assumption) is exactly what
we're correcting now. Section 3 verifies live before this is trusted.

---

## 3. Macro / rates / inflation — unchanged from v0.1

RBI DBIE manual CSV snapshots, as documented previously. No change — this was never dependent on
yfinance or NSE Bhavcopy in the first place.

---

## 4. Calendar effects & lunar phase — unchanged from v0.1

Computed, zero external dependency. No change.

---

## 5. Revised summary table

| Data type | Primary source | Fallback | Key required? | Fragility |
|---|---|---|---|---|
| NSE indices | NSE index report (endpoint TBD, Section 3) | yfinance retry | No | Medium — needs endpoint verification |
| NSE/BSE stocks | NSE Bhavcopy (UDiFF) | yfinance retry | No | Low–Medium (User-Agent/cookie handling needed) |
| Commodities | yfinance retry | Stooq direct CSV | No | Medium |
| USD/INR | yfinance retry | Stooq direct CSV | No | Medium |
| Macro (repo/CPI/WPI/CRR/SLR) | RBI DBIE (manual) | data.gov.in | No | Low (manual) |
| Calendar/festival effects | Static table + logic | — | No | Low |
| Lunar phase | Pure formula | — | No | None |

---

## 6. Open items for Section 3 (now updated)

- Implement NSE Bhavcopy downloader with proper headers/cookie warm-up, batching by date (one file/day
  covers the whole stock universe — no per-ticker looping needed).
- Pin down and live-test the exact current NSE index-report endpoint.
- Implement Stooq direct-CSV fallback for commodities/currency, verify exact symbol strings live.
- Keep yfinance as an opportunistic secondary path everywhere (cheap to try, just not trustworthy
  as primary right now) — wrap every call in the retry/backoff already declared in settings.yaml.
- Local raw-data cache so a rate-limit or 403 mid-run doesn't lose earlier progress.
- `data_freshness.json` manifest, as previously planned.
