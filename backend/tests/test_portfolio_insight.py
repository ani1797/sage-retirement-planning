"""
Tests for backend/portfolio_insight.py and backend/market_data.py -- the AI
Insight feature's deterministic metrics, prompt construction, disk cache, and
market data provider fallback chain.

Run with: uv run pytest tests/test_portfolio_insight.py -v
"""

import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import market_data
import portfolio_insight


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_PORTFOLIO_SYMBOLS = ["VTI", "BND", "VXUS", "VGT", "VWO", "VTIP", "VGSLX", "VMFXX"]


def make_profile(**overrides):
    defaults = dict(
        age=40,
        salary=96000,
        risk_appetite="medium",
        target_retire_age=65,
        target_monthly_income=4000,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_portfolio(holdings):
    total_value = sum(h["value"] for h in holdings)
    return {"total_value": total_value, "holdings": holdings}


CONSERVATIVE_HOLDINGS = [
    {"symbol": "BND", "name": "Vanguard Total Bond Market", "value": 400000, "allocation": 40, "sector": "Fixed Income"},
    {"symbol": "VTIP", "name": "Vanguard Short-Term TIPS", "value": 150000, "allocation": 15, "sector": "Inflation Protected"},
    {"symbol": "VMFXX", "name": "Vanguard Money Market", "value": 150000, "allocation": 15, "sector": "Cash"},
    {"symbol": "VTI", "name": "Vanguard Total Stock Market", "value": 300000, "allocation": 30, "sector": "US Equity"},
]

MODERATE_HOLDINGS = [
    {"symbol": "VTI", "name": "Vanguard Total Stock Market", "value": 293348, "allocation": 40, "sector": "US Equity"},
    {"symbol": "VXUS", "name": "Vanguard Intl Stock", "value": 146674, "allocation": 20, "sector": "International"},
    {"symbol": "BND", "name": "Vanguard Total Bond Market", "value": 132007, "allocation": 18, "sector": "Fixed Income"},
    {"symbol": "VGSLX", "name": "Vanguard Real Estate Index", "value": 88005, "allocation": 12, "sector": "Real Estate"},
    {"symbol": "VMFXX", "name": "Vanguard Money Market", "value": 73337, "allocation": 10, "sector": "Cash"},
]

AGGRESSIVE_HOLDINGS = [
    {"symbol": "VGT", "name": "Vanguard Information Technology", "value": 400000, "allocation": 40, "sector": "Technology"},
    {"symbol": "VTI", "name": "Vanguard Total Stock Market", "value": 300000, "allocation": 30, "sector": "US Equity"},
    {"symbol": "VWO", "name": "Vanguard Emerging Markets", "value": 200000, "allocation": 20, "sector": "Emerging Markets"},
    {"symbol": "VMFXX", "name": "Vanguard Money Market", "value": 100000, "allocation": 10, "sector": "Cash"},
]


@pytest.fixture(autouse=True)
def isolate_caches(tmp_path, monkeypatch):
    """Redirect both the market-data and insight caches to a temp dir so
    tests never touch (or are polluted by) the real backend/data/cache."""
    market_cache_dir = tmp_path / "market"
    insight_cache_dir = tmp_path / "insights"
    monkeypatch.setattr(market_data, "_cache", market_data.CachedMarketData(cache_dir=market_cache_dir))
    monkeypatch.setattr(portfolio_insight, "INSIGHT_CACHE_DIR", insight_cache_dir)
    monkeypatch.delenv("MARKET_DATA_PROVIDER", raising=False)
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("PORTFOLIO_INSIGHT_CACHE_TTL_HOURS", raising=False)
    yield


# ---------------------------------------------------------------------------
# 1. Synthetic reference bundle covers every mockPortfolio symbol
# ---------------------------------------------------------------------------

def test_reference_bundle_covers_all_mock_portfolio_symbols():
    covered = set(market_data.reference_bundle_symbols())
    missing = set(MOCK_PORTFOLIO_SYMBOLS) - covered
    assert not missing, f"market_reference.json is missing symbols used by lib/mockPortfolio.ts: {missing}"


# ---------------------------------------------------------------------------
# 2. compute_metrics: math correctness across risk profiles
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "holdings,expected_total_alloc_pct",
    [
        (CONSERVATIVE_HOLDINGS, 100.0),
        (MODERATE_HOLDINGS, 100.0),
        (AGGRESSIVE_HOLDINGS, 100.0),
    ],
)
def test_compute_metrics_allocation_buckets_sum_to_total(holdings, expected_total_alloc_pct):
    profile = make_profile()
    portfolio = make_portfolio(holdings)
    context = market_data.get_market_context([h["symbol"] for h in holdings])
    metrics = portfolio_insight.compute_metrics(profile, portfolio, context)

    bucket_sum = metrics.equity_pct + metrics.bond_pct + metrics.cash_pct + metrics.real_estate_pct
    assert bucket_sum == pytest.approx(expected_total_alloc_pct, abs=0.2)
    assert metrics.intl_pct <= metrics.equity_pct  # intl is a subset of equity
    assert metrics.total_value == pytest.approx(portfolio["total_value"])
    assert metrics.holdings_count == len(holdings)


def test_compute_metrics_moderate_profile_matches_expected_splits():
    profile = make_profile(age=42, target_retire_age=65, target_monthly_income=4000)
    portfolio = make_portfolio(MODERATE_HOLDINGS)
    context = market_data.get_market_context([h["symbol"] for h in MODERATE_HOLDINGS])
    metrics = portfolio_insight.compute_metrics(profile, portfolio, context)

    assert metrics.equity_pct == pytest.approx(60.0)  # VTI 40 + VXUS 20
    assert metrics.bond_pct == pytest.approx(18.0)
    assert metrics.cash_pct == pytest.approx(10.0)
    assert metrics.real_estate_pct == pytest.approx(12.0)
    assert metrics.intl_pct == pytest.approx(20.0)
    assert metrics.years_to_retirement == 23
    # 110 - 42 = 68 glidepath target; actual equity 60 -> delta -8
    assert metrics.equity_vs_glidepath_delta == pytest.approx(-8.0)
    # 4%-rule nest egg = (4000*12)/0.04 = 1,200,000; portfolio total = 733,370
    assert metrics.target_fund_gap == pytest.approx(1_200_000 - portfolio["total_value"], abs=1)


def test_compute_metrics_conservative_holdings_show_high_bond_cash():
    profile = make_profile(risk_appetite="low")
    portfolio = make_portfolio(CONSERVATIVE_HOLDINGS)
    context = market_data.get_market_context([h["symbol"] for h in CONSERVATIVE_HOLDINGS])
    metrics = portfolio_insight.compute_metrics(profile, portfolio, context)

    assert metrics.bond_pct + metrics.cash_pct >= 50.0
    assert metrics.weighted_expense_ratio is not None


def test_compute_metrics_aggressive_holdings_show_high_equity():
    profile = make_profile(risk_appetite="high", age=28, target_retire_age=60)
    portfolio = make_portfolio(AGGRESSIVE_HOLDINGS)
    context = market_data.get_market_context([h["symbol"] for h in AGGRESSIVE_HOLDINGS])
    metrics = portfolio_insight.compute_metrics(profile, portfolio, context)

    assert metrics.equity_pct >= 85.0  # VGT + VTI + VWO
    assert metrics.top_sector in {"Technology", "US Equity", "Emerging Markets"}


def test_infer_asset_class_sector_fallback_heuristics():
    context = market_data.get_market_context([])  # empty -> no fund data at all
    assert portfolio_insight._infer_asset_class({"symbol": "ZZZ", "sector": "Fixed Income"}, context) == "bond"
    assert portfolio_insight._infer_asset_class({"symbol": "ZZZ", "sector": "Inflation Protected"}, context) == "bond"
    assert portfolio_insight._infer_asset_class({"symbol": "ZZZ", "sector": "Cash"}, context) == "cash"
    assert portfolio_insight._infer_asset_class({"symbol": "ZZZ", "sector": "Real Estate"}, context) == "real_estate"
    assert portfolio_insight._infer_asset_class({"symbol": "ZZZ", "sector": "International"}, context) == "equity_intl"
    assert portfolio_insight._infer_asset_class({"symbol": "ZZZ", "sector": "Emerging Markets"}, context) == "equity_intl"
    # No hint substring matches -> defaults to equity_us
    assert portfolio_insight._infer_asset_class({"symbol": "ZZZ", "sector": "US Equity"}, context) == "equity_us"
    assert portfolio_insight._infer_asset_class({"symbol": "ZZZ", "sector": "Technology"}, context) == "equity_us"


def test_infer_asset_class_prefers_market_context_over_sector_heuristic():
    context = market_data.get_market_context(["VGSLX"])
    # VGSLX's synthetic profile says real_estate, even if sector text said something else.
    result = portfolio_insight._infer_asset_class({"symbol": "VGSLX", "sector": "Diversified"}, context)
    assert result == "real_estate"


def test_compute_metrics_handles_empty_holdings():
    profile = make_profile()
    portfolio = {"total_value": 0, "holdings": []}
    context = market_data.get_market_context([])
    metrics = portfolio_insight.compute_metrics(profile, portfolio, context)
    assert metrics.holdings_count == 0
    assert metrics.equity_pct == 0.0
    assert metrics.top_sector is None


# ---------------------------------------------------------------------------
# 3. Prompt construction
# ---------------------------------------------------------------------------

def test_build_insight_prompt_contains_key_figures_and_schema_override():
    profile = make_profile()
    portfolio = make_portfolio(MODERATE_HOLDINGS)
    context = market_data.get_market_context([h["symbol"] for h in MODERATE_HOLDINGS])
    metrics = portfolio_insight.compute_metrics(profile, portfolio, context)
    prompt = portfolio_insight.build_insight_prompt(profile, portfolio, metrics, context)

    assert "Do not use the AnalysisOutput schema" in prompt
    assert "VTI" in prompt
    assert f"{metrics.equity_pct}% equity" in prompt
    assert "factors_for" in prompt and "factors_against" in prompt


def test_build_insight_prompt_handles_no_market_data_gracefully():
    profile = make_profile()
    portfolio = make_portfolio([{"symbol": "ZZZZ", "name": "Unknown Fund", "value": 1000, "allocation": 100, "sector": "Unclassified"}])
    context = market_data.get_market_context(["ZZZZ"])
    metrics = portfolio_insight.compute_metrics(profile, portfolio, context)
    prompt = portfolio_insight.build_insight_prompt(profile, portfolio, metrics, context)
    assert "No market data available for held symbols" in prompt


# ---------------------------------------------------------------------------
# 4. Insight cache: hit / miss / expiry / force_refresh
# ---------------------------------------------------------------------------

def test_insight_cache_miss_then_hit():
    portfolio = make_portfolio(MODERATE_HOLDINGS)
    digest = portfolio_insight.portfolio_hash(portfolio)

    assert portfolio_insight.get_cached_insight("demo-user", digest) is None

    payload = {"headline": "Test", "review": ["a"]}
    portfolio_insight.set_cached_insight("demo-user", digest, payload)

    cached = portfolio_insight.get_cached_insight("demo-user", digest)
    assert cached == payload


def test_insight_cache_expires_after_ttl(monkeypatch):
    portfolio = make_portfolio(MODERATE_HOLDINGS)
    digest = portfolio_insight.portfolio_hash(portfolio)
    monkeypatch.setenv("PORTFOLIO_INSIGHT_CACHE_TTL_HOURS", "0.0000001")  # ~0.36ms

    portfolio_insight.set_cached_insight("demo-user", digest, {"headline": "Stale"})
    time.sleep(0.05)

    assert portfolio_insight.get_cached_insight("demo-user", digest) is None


def test_portfolio_hash_changes_when_holdings_change():
    base = make_portfolio(MODERATE_HOLDINGS)
    digest1 = portfolio_insight.portfolio_hash(base)

    changed_holdings = [dict(h) for h in MODERATE_HOLDINGS]
    changed_holdings[0]["value"] += 1000
    changed = make_portfolio(changed_holdings)
    digest2 = portfolio_insight.portfolio_hash(changed)

    assert digest1 != digest2


def test_portfolio_hash_stable_regardless_of_holdings_order():
    base = make_portfolio(MODERATE_HOLDINGS)
    reordered = make_portfolio(list(reversed(MODERATE_HOLDINGS)))
    assert portfolio_insight.portfolio_hash(base) == portfolio_insight.portfolio_hash(reordered)


def test_insight_cache_handles_corrupt_file_gracefully(tmp_path, monkeypatch):
    cache_dir = tmp_path / "corrupt_insights"
    monkeypatch.setattr(portfolio_insight, "INSIGHT_CACHE_DIR", cache_dir)
    portfolio = make_portfolio(MODERATE_HOLDINGS)
    digest = portfolio_insight.portfolio_hash(portfolio)

    path = portfolio_insight._insight_cache_path("demo-user", digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")

    assert portfolio_insight.get_cached_insight("demo-user", digest) is None


# ---------------------------------------------------------------------------
# 5. Market data provider fallback chain
# ---------------------------------------------------------------------------

def test_get_market_context_synthetic_provider_not_degraded():
    context = market_data.get_market_context(["VTI", "BND"])
    assert context.provider == "synthetic"
    assert context.degraded is False
    assert set(context.funds.keys()) == {"VTI", "BND"}
    assert context.macro.source == "Sage Synthetic Reference Bundle"


def test_get_market_context_alphavantage_without_key_degrades_to_synthetic(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "alphavantage")
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    context = market_data.get_market_context(["VTI"])
    assert context.provider == "alphavantage"
    assert context.degraded is True
    assert context.funds["VTI"].source == "Sage Synthetic Reference Bundle"


def test_get_market_context_treasury_fund_profiles_always_degrade_to_synthetic(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "treasury")

    context = market_data.get_market_context(["VTI"])
    assert context.provider == "treasury"
    # Treasury has no fund-level data, so fund profiles always fall back.
    assert context.funds["VTI"].source == "Sage Synthetic Reference Bundle"
    assert context.degraded is True


def test_get_market_context_unknown_symbol_omitted_not_crashed():
    context = market_data.get_market_context(["NOT_A_REAL_SYMBOL"])
    assert "NOT_A_REAL_SYMBOL" not in context.funds
    assert context.macro is not None  # macro snapshot still resolves


def test_get_market_context_uses_cache_on_second_call(monkeypatch):
    """A provider that raises after the first successful call should still
    let the second get_market_context() call succeed from cache."""
    call_count = {"n": 0}

    class FlakyProvider(market_data.MarketDataProvider):
        name = "flaky"

        def get_fund_profile(self, symbol):
            call_count["n"] += 1
            if call_count["n"] > 1:
                raise RuntimeError("simulated outage")
            return market_data.FundProfile(
                symbol=symbol.upper(), name="Flaky Fund", asset_class="equity_us",
                expense_ratio=0.001, yield_pct=1.0, source="Flaky Provider", as_of="2025-01-01",
            )

        def get_macro_snapshot(self):
            return market_data._synthetic_macro_snapshot()

    monkeypatch.setattr(market_data, "_provider_for_name", lambda name: FlakyProvider())
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "flaky")

    first = market_data.get_market_context(["FAKE"])
    assert first.funds["FAKE"].source == "Flaky Provider"
    assert first.degraded is False

    second = market_data.get_market_context(["FAKE"])
    assert second.funds["FAKE"].source == "Flaky Provider"
    assert second.degraded is False  # served from fresh (non-stale) cache, not a fallback


# ---------------------------------------------------------------------------
# 6. Malformed-LLM-JSON handling (mirrors the endpoint's parsing logic)
# ---------------------------------------------------------------------------

def _extract_json_like_main_py(response_text: str):
    """Mirrors the brace-scan parsing done in main.py's
    /api/portfolio-insight handler, so we can unit test that logic without
    booting the full FastAPI app."""
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    if json_start == -1 or json_end <= json_start:
        return None
    return json.loads(response_text[json_start:json_end])


def test_extract_json_handles_agent_prose_wrapping():
    wrapped = 'Sure, here you go:\n\n{"headline": "Solid portfolio"}\n\nLet me know if you need more.'
    result = _extract_json_like_main_py(wrapped)
    assert result == {"headline": "Solid portfolio"}


def test_extract_json_returns_none_for_no_json():
    assert _extract_json_like_main_py("I cannot help with that.") is None


def test_extract_json_raises_for_truncated_json():
    truncated = '{"headline": "Solid portfolio", "review": [}'
    with pytest.raises(json.JSONDecodeError):
        _extract_json_like_main_py(truncated)


def test_portfolio_insight_response_model_validates_full_shape():
    """Confirms the response model accepts a realistic LLM-shaped payload,
    merged with the Python-computed metrics/market_context/etc. as the
    endpoint does."""
    profile = make_profile()
    portfolio = make_portfolio(MODERATE_HOLDINGS)
    context = market_data.get_market_context([h["symbol"] for h in MODERATE_HOLDINGS])
    metrics = portfolio_insight.compute_metrics(profile, portfolio, context)

    llm_payload = {
        "headline": "Balanced but under-funded",
        "review": ["Para 1", "Para 2", "Para 3"],
        "grade": {"letter": "B", "score": 79, "rationale": "Low costs, modest gap."},
        "factors_for": [{"title": "Low cost", "detail": "Cheap funds.", "weight": "high"}],
        "factors_against": [{"title": "Income gap", "detail": "Short of target.", "severity": "high"}],
        "suitability": {
            "verdict": "mostly_suited",
            "detail": "Reasonably aligned.",
            "risk_alignment": "ok",
            "horizon_alignment": "ok",
            "income_alignment": "behind",
        },
        "recommendations": [
            {"action": "Save more", "priority": "high", "category": "income", "rationale": "Close the gap."}
        ],
    }
    llm_payload["metrics"] = metrics.model_dump()
    llm_payload["market_context"] = {
        "provider": context.provider,
        "funds": {k: v.model_dump() for k, v in context.funds.items()},
        "macro": context.macro.model_dump(),
    }
    llm_payload["data_sources"] = context.data_sources
    llm_payload["generated_at"] = portfolio_insight.now_iso()
    llm_payload["degraded"] = context.degraded
    llm_payload.setdefault("disclaimer", portfolio_insight.DISCLAIMER)

    response = portfolio_insight.PortfolioInsightResponse(**llm_payload)
    assert response.grade.letter == "B"
    assert response.metrics.equity_pct == pytest.approx(60.0)
    assert response.disclaimer == portfolio_insight.DISCLAIMER
