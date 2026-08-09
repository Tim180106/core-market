========================================
HANDOFF BLOCK — SECTION 2: Data Source Mapping — COMPLETE
========================================
STATE SO FAR:
- Repo skeleton, config-driven approach, and Colab setup notebook from Section 1 unchanged.
- Full data source map documented: indices/stocks/commodities/currency via yfinance (.NS primary,
  .BO fallback), macro via manual RBI DBIE CSV snapshots (no clean free API exists), calendar effects
  and lunar phase computed with zero external dependency.
- Explicit design decision: yfinance is rate-limit-prone in 2026 — batching, retry/backoff, and a
  Stooq fallback for indices are declared in settings.yaml now so Section 3 builds them in from the start
  instead of retrofitting after hitting 429s.
- Initial stock universe populated: 15 liquid Nifty 50 large-caps across financials/IT/energy/fmcg/
  auto/pharma/telecom/industrials sectors.
- NEURAL-STARK-01 UI assets (Section 1 finding) still slated for reuse in Section 16.

FILES/ARTIFACTS PRODUCED THIS SECTION:
- docs/data_sources.md — v0.1 — full source map, symbols, reliability caveats, design rationale — docs/
- config/settings.yaml — v0.2 — populated universe (indices, stocks, commodities, currency, macro,
  calendar, lunar) + fetch-behavior config (batch size, retries, backoff, fallback) — config/
- scripts/test_data_sources.py — v0.1 — Colab connectivity-check script for every declared source — scripts/

TABLE OF CONTENTS STATUS:
Phase A — Foundation
  [x] 1. Environment & GitHub Repo Setup — COMPLETE
  [x] 2. Data Source Mapping — COMPLETE
  [ ] 3. Data Ingestion Pipeline (OHLCV for NSE/BSE stocks & indices) — NEXT
  [ ] 4. Lunar Phase Engine (pure astronomical calculation, no API)
  [ ] 5. Macro & Commodity Data Integration (copper, crude, gold, USD-INR, etc.)
Phase B — Feature Engineering
  [ ] 6a. Correlation Discovery Framework — Candidate Generation
  [ ] 6b. Correlation Discovery Framework — Search & Ranking
  [ ] 7. Feature Engineering Pipeline
  [ ] 8. Statistical Validation & Spurious-Correlation Filter
Phase C — Modeling
  [ ] 9. Model Architecture Design
  [ ] 10. Training Pipeline
  [ ] 11. Backtesting Framework
  [ ] 12. Prediction & Probability Calibration
Phase D — Persona Debate System
  [ ] 13. Persona Definitions & Reasoning Templates
  [ ] 14. Debate Protocol Engine
  [ ] 15. C.O.R.E Synthesis Layer
  [ ] 16. Debate Transcript & Visualization (reuse existing NEURAL-STARK-01 UI assets)
Phase E — Integration & Delivery
  [ ] 17. End-to-End Pipeline Integration
  [ ] 18. Testing, Validation & Known Limitations Log
  [ ] 19. User Guide & Maintenance Instructions

INSTRUCTIONS FOR NEXT CLAUDE CHAT:
- Paste this entire handoff block as the first message in a new chat.
- Also paste/attach: your actual config/settings.yaml if you tweaked the stock universe, and the
  output of running scripts/test_data_sources.py in Colab (tells the next chat which sources are
  currently live vs. rate-limited, so it can plan around it).
- Next section to build: Section 3 — Data Ingestion Pipeline — build the actual OHLCV download/cache
  pipeline for the stock & index universe (with the batching/retry/backoff/Stooq-fallback behavior
  declared in settings.yaml now finally implemented), saving cached raw data to data/raw/.
========================================
