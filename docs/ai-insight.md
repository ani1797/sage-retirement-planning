# AI Portfolio Insight

The **AI Portfolio Insight** section gives a written, grounded review of a client's portfolio — factors in favor
of and against it, a suitability verdict, a "Sage AI Grade," and concrete recommendations — displayed above the
Holdings table in the client Portfolio view, and in a compact form in the advisor Client Detail overview tab.

## Design principle: the LLM never does arithmetic

Every number in the response (allocation percentages, weighted expense ratio, glidepath delta, retirement
income gap, etc.) is **computed in Python** from the holdings and resolved market data, before the agent ever
sees a prompt. The agent's only job is judgment and language over a factual brief it's handed — it's explicitly
told "every number has already been computed... treat all figures as ground truth" and instructed never to
invent figures. This makes the numeric parts of the feature fully unit-testable without any LLM call (see
`backend/tests/test_portfolio_insight.py`), and eliminates a whole class of hallucinated-statistics bugs.

## Data sources

Only **free, no-license-risk** market data sources are wired up. No paid vendor (Morningstar, Moody's) is used —
this is a deliberate, permanent choice, not a temporary budget constraint:

| Provider | What it's for | Notes |
|---|---|---|
| **`synthetic`** (default) | Fund facts (expense ratio, yield, category, 5y return, top sector) + a macro snapshot (Treasury yields, Fed funds rate, CPI, S&P 500 YTD) | Curated, hand-maintained figures in `backend/data/market_reference.json`, approximating each fund's public fact sheet. $0 cost, no network call, no ToS exposure. Also the **universal fallback** when a live provider is unavailable. |
| **`alphavantage`** | Live fund profile via the free-tier `ETF_PROFILE` endpoint | Requires `ALPHAVANTAGE_API_KEY` (free signup, 25 req/day). Falls back to `synthetic` for macro data (no free equivalent) and for fund data when unconfigured, rate-limited, or the symbol is unknown. |
| **`treasury`** | Live macro Treasury yield data via the public US Treasury Fiscal Data API | No auth required. Supplies macro data only — always falls back to `synthetic` for fund-level data, since Treasury has no fund data at all. |

### Deliberately excluded (and why)

- **Morningstar / Moody's** — no self-serve tier exists for retail fund ratings/analytics at *any* budget; this
  isn't a pricing problem, it's a lack of a public API at all for individual developers.
- **FRED (Federal Reserve Economic Data)** — excluded because FRED's 2024 terms of service prohibit using FRED
  data to train or fine-tune AI/LLM models, which is too close to this feature's use case to risk.
- **yfinance** — an unofficial scraper of Yahoo Finance's undocumented endpoints, not a licensed API; carries
  meaningful Terms of Service risk for anything beyond personal/hobby use.

## Fallback chain

Every provider funnels through the same chain in `backend/market_data.py`'s `get_market_context()`:

```
live provider call → stale disk cache (same key, past its TTL) → bundled synthetic reference data
```

An outage or missing API key degrades data *quality* (flagged via `MarketContext.degraded` /
`degraded_reason`, surfaced in the UI as a small amber notice), but never breaks the request — there's always a
synthetic fallback.

## Metrics computed

`backend/portfolio_insight.py`'s `compute_metrics()` (pure function, holdings + market context → numbers):

- `weighted_expense_ratio`, `weighted_yield` — value-weighted across holdings with known fund data.
- `equity_pct` / `bond_pct` / `cash_pct` / `intl_pct` (subset of equity) / `real_estate_pct` — asset-class
  buckets, classified via each fund's market-context `asset_class` first, falling back to sector-name string
  matching (e.g. "Fixed Income" → bond, "Real Estate" → real_estate) for symbols the reference bundle doesn't
  cover.
- `top_sector` / `top_sector_pct` — largest single-sector concentration.
- `equity_vs_glidepath_delta` — actual equity % minus a `110 - age` age-based glidepath heuristic.
- `years_to_retirement` — `target_retire_age - age`.
- `target_fund_gap` — 4%-rule nest egg (`target_monthly_income * 12 / 0.04`) minus current total value.

## Endpoints

- **`POST /api/portfolio-insight`** — `{ profile_id, current_portfolio, force_refresh }` → full
  `PortfolioInsightResponse` (headline, review paragraphs, grade, factors for/against, suitability,
  recommendations, metrics, market context, disclaimer). Checks a 24h disk cache
  (`backend/data/cache/insights/{profile_id}-{portfolio_hash}.json`) first, unless `force_refresh` is set;
  hashing the holdings means any portfolio change auto-invalidates the cache.
- **`GET /api/market-context?symbols=VTI,BND`** — diagnostic endpoint returning the resolved `MarketContext` for
  a symbol list, so provider wiring can be verified with a single `curl` and without burning an agent run.

## Frontend

- `lib/api.ts` — insight types + `getPortfolioInsight()`.
- `lib/mockData.ts` — `generateMockPortfolioInsight()`, a fully self-contained mock-mode implementation that
  mirrors `market_reference.json` and the backend's metric math, so mock mode demos the feature with zero
  backend/Azure dependency and distinct output per risk appetite.
- `components/frontend/AIInsightSection.tsx` — the UI: header with a "Foundry IQ" badge + Refresh, Sage AI Grade
  badge, written review, two-column Factors in Favor / Factors Against, suitability strip, recommendations,
  collapsible "Market data used" panel, skeleton loading, error + retry, disclaimer footer. Supports
  `variant="full"` (client Portfolio view) and `variant="compact"` (advisor Client Detail overview tab).
- Integrated into `PortfolioView.tsx` (above the Holdings table, below Asset Allocation) and
  `ClientDetailView.tsx` (advisor overview tab, alongside the existing AI Summary card).

## Configuration

```bash
# backend/.env
MARKET_DATA_PROVIDER=synthetic          # synthetic | alphavantage | treasury
# ALPHAVANTAGE_API_KEY=your-key         # only if MARKET_DATA_PROVIDER=alphavantage
MARKET_DATA_CACHE_TTL_HOURS=24
PORTFOLIO_INSIGHT_CACHE_TTL_HOURS=24
```

See **[docs/environment-configuration.md](./environment-configuration.md)** for the full reference.

## Tests

`backend/tests/test_portfolio_insight.py` covers: metric math across conservative/moderate/aggressive mock
portfolios, asset-class inference (market-context-preferred and sector-heuristic-fallback paths), prompt
construction (including the schema-override instruction), insight cache hit/miss/expiry/force_refresh,
`portfolio_hash()` stability and invalidation, the provider fallback chain (synthetic / alphavantage without a
key / treasury), and malformed-LLM-JSON handling. It also asserts the synthetic reference bundle covers every
symbol used by `lib/mockPortfolio.ts`.

## Disclaimer

Every response includes a fixed disclaimer (`portfolio_insight.DISCLAIMER`): this is an AI-generated
educational assessment, not financial advice, and the "Sage AI Grade" is Sage's own synthesized assessment —
explicitly not a Morningstar, Moody's, or other third-party rating.
