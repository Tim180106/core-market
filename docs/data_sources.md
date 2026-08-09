# Data Source Map — C.O.R.E
Version: v0.1
Section: 2 — Data Source Mapping
Last verified: 2026-08-10 (web-verified where noted; re-check before long-running use, these things drift)

This file is the single reference for **every external data source** C.O.R.E pulls from.
Every future section that fetches data must point back here instead of re-deciding sources ad hoc.

---

## 1. Guiding rule for this section

Nothing here costs money and nothing needs an API key. Where a "clean API" doesn't exist for free,
we use a documented workaround (scraping a public page, downloading a public CSV, or a manual
periodic snapshot) and we say so explicitly, so nobody mistakes it for a guaranteed live feed later.

---

## 2. Equity & Index data — `yfinance`

**Library:** `yfinance` (unofficial, scrapes Yahoo Finance's public endpoints — no key).

**Known limitation we must design around (verified via current reporting, not just assumption):**
Yahoo has tightened anti-scraping defenses. `yfinance` users are commonly hitting `YFRateLimitError`
(HTTP 429) with bursty or frequent requests, and Yahoo occasionally reshapes its endpoints, which can
break the library without warning. This is a real, current risk for this project, not a hypothetical.

**Design decisions this forces (build into Section 3, flagging now):**
- Always download in small batches with delays between calls, never one call per ticker in a tight loop.
- Cache every raw pull to disk (`data/raw/`) so re-runs don't re-hit the network.
- Wrap every call in retry-with-backoff.
- Keep a fallback path to **Stooq** (`pandas_datareader` or direct CSV, also free/no-key) for core
  indices/large-caps if `yfinance` is rate-limited mid-session. Stooq's Indian single-stock coverage is
  thinner than Yahoo's, so it's a fallback for indices/majors, not a full replacement.

### Indices (confirmed symbols)
| Name | yfinance symbol | Notes |
|---|---|---|
| Nifty 50 | `^NSEI` | NSE broad benchmark |
| Sensex 30 | `^BSESN` | BSE benchmark |
| Nifty Bank | `^NSEBANK` | Banking sector index |
| Nifty Next 50 | `^NSEMDCP50` | Verify on pull — this symbol has been unreliable historically |

### Individual stocks
- **NSE-listed stocks:** ticker + `.NS` suffix, e.g. `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`.
- **BSE-listed stocks:** ticker + `.BO` suffix, e.g. `500325.BO`.
- We standardize on **`.NS` (NSE) as primary** for the stock universe since NSE has deeper liquidity;
  `.BO` is kept only as a cross-check / fallback per symbol.

### Initial stock universe (Nifty 50 large-caps — liquid, low missing-data risk)
Placeholder set for Section 3 to actually pull; final list goes in `settings.yaml`:
`RELIANCE.NS, TCS.NS, HDFCBANK.NS, ICICIBANK.NS, INFY.NS, HINDUNILVR.NS, ITC.NS, SBIN.NS,
BHARTIARTL.NS, KOTAKBANK.NS, LT.NS, AXISBANK.NS, BAJFINANCE.NS, MARUTI.NS, SUNPHARMA.NS`

---

## 3. Commodity data — `yfinance` (futures proxies)

No free clean commodity-spot API exists without a key, so we use CME/COMEX futures continuous
contracts as liquid, free proxies — standard practice for retail-grade correlation work.

| Commodity | yfinance symbol | Notes |
|---|---|---|
| Gold | `GC=F` | COMEX gold futures |
| Silver | `SI=F` | COMEX silver futures |
| Crude oil (WTI) | `CL=F` | NYMEX |
| Crude oil (Brent) | `BZ=F` | ICE — India's imports are Brent-priced, so prefer this over WTI |
| Copper | `HG=F` | COMEX — industrial demand proxy |
| Natural gas | `NG=F` | NYMEX |

Caveat: these are USD-denominated global futures, not INR spot prices. Any correlation feature built
on them should also account for USD-INR movement (Section 5), or the "commodity effect" and "currency
effect" will get tangled together.

---

## 4. Currency — `yfinance`

| Pair | yfinance symbol |
|---|---|
| USD/INR | `USDINR=X` |

---

## 5. Macro / rates / inflation data — RBI DBIE (manual/periodic, no clean API)

**Source:** RBI's public Database on Indian Economy — `dbie.rbihub.in` — publishes policy repo rate,
CPI inflation, WPI, CRR, SLR, USD/INR reference rate, FX reserves, etc. It's free and official, but it
does **not** expose a clean JSON/CSV API for automated pulls — it's a browsable data portal.

**Design decision:** rather than build a fragile scraper against a government site's HTML (which is
exactly the kind of thing that silently breaks and quietly corrupts a model), macro series are:
1. Downloaded manually as CSV from DBIE on a periodic basis (monthly is plenty — these series update
   monthly/bi-monthly anyway, e.g. RBI's Monetary Policy Committee meets ~6x/year),
2. Committed to `data/macro/` in the repo as versioned snapshots,
3. Loaded by the pipeline like any other CSV, with a "last updated" date stamped in the filename.

This trades live-ness (which these series don't have anyway — CPI is a monthly print, repo rate changes
~6x/year) for reliability, which is the right trade for a beginner-run system.

**Series we will track this way (populated into `data/macro/` starting Section 5):**
- Policy repo rate
- CPI inflation (y/y)
- WPI inflation (y/y)
- Cash Reserve Ratio (CRR) / Statutory Liquidity Ratio (SLR)
- USD/INR RBI reference rate (cross-check vs `USDINR=X`)

**Secondary/backup source:** `data.gov.in` (India's open data portal) publishes some overlapping series
with actual CSV/API download links — worth checking per-series in Section 5 if DBIE's manual export is
awkward for a given field.

---

## 6. Calendar effects — computed, not fetched

Day-of-week, month, F&O monthly-expiry date (last Thursday of the month, standard NSE convention —
must be verified against the actual NSE holiday calendar since holidays shift it), and Indian festival
dates (Diwali/Muhurat trading, etc.) are **computed from calendar logic + a static festival-date table**
we maintain in `config/`, not pulled from any live source. No data source risk here — just needs to be
kept up to date once a year.

---

## 7. Lunar phase — computed, not fetched

Per the project brief, lunar phase is derived from a pure astronomical formula (no API, no dependency
risk). Full implementation is Section 4's job; noted here only so the "data source map" is complete —
this is the one input with zero external dependency at all.

---

## 8. Summary table — what depends on what

| Data type | Source | Key required? | Live/refreshable? | Fragility |
|---|---|---|---|---|
| Indices (Nifty/Sensex/BankNifty) | yfinance | No | Yes | Medium (rate limits) |
| Individual stocks | yfinance | No | Yes | Medium (rate limits) |
| Commodities (futures proxies) | yfinance | No | Yes | Medium |
| USD/INR | yfinance | No | Yes | Medium |
| Macro (repo rate, CPI, WPI, CRR/SLR) | RBI DBIE (manual CSV) | No | Monthly, manual | Low (but manual) |
| Calendar/festival effects | Static table + logic | No | Yes (self-computed) | Low |
| Lunar phase | Pure formula | No | Yes (self-computed) | None |

---

## 9. Open items for Section 3 (Data Ingestion Pipeline) to actually implement

- Batching + retry/backoff wrapper around every `yfinance` call.
- Local raw-data cache so a rate-limit mid-run doesn't lose earlier progress.
- Stooq fallback path for the index-level series specifically.
- A `data_freshness.json` or similar manifest so the pipeline (and the personas, later) know how stale
  each series is, especially the manually-updated macro CSVs.
