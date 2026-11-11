"""
Portfolio Insight feature: deterministic metrics + Pydantic response models +
prompt construction + disk cache. The LLM never does arithmetic here -- every
number in the response is computed in Python from `current_portfolio` and the
resolved `MarketContext`; the agent's job is judgment and language over a
factual brief it's handed. See docs/ai-insight.md for the full design.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from market_data import MarketContext

DATA_DIR = Path(__file__).parent / "data"
INSIGHT_CACHE_DIR = DATA_DIR / "cache" / "insights"
DEFAULT_INSIGHT_CACHE_TTL_HOURS = 24

DISCLAIMER = (
    "This is an AI-generated educational assessment, not financial advice. "
    "The \"Sage AI Grade\" is Sage's own synthesized assessment and is not a "
    "Morningstar, Moody's, or any other third-party rating. Consult a licensed "
    "financial advisor before making investment decisions."
)


# ─── Response models ─────────────────────────────────────────────────────────

class InsightGrade(BaseModel):
    letter: str  # A+ .. F
    score: int = Field(ge=0, le=100)
    rationale: str


class InsightFactorFor(BaseModel):
    title: str
    detail: str
    weight: Literal["high", "medium", "low"] = "medium"


class InsightFactorAgainst(BaseModel):
    title: str
    detail: str
    severity: Literal["high", "medium", "low"] = "medium"


class InsightSuitability(BaseModel):
    verdict: Literal["well_suited", "mostly_suited", "needs_adjustment", "misaligned"]
    detail: str
    risk_alignment: str
    horizon_alignment: str
    income_alignment: str


class InsightRecommendation(BaseModel):
    action: str
    priority: Literal["high", "medium", "low"] = "medium"
    category: Literal["allocation", "cost", "diversification", "risk", "income", "tax"] = "allocation"
    rationale: str


class PortfolioMetrics(BaseModel):
    total_value: float
    holdings_count: int
    weighted_expense_ratio: Optional[float] = None
    weighted_yield: Optional[float] = None
    equity_pct: float = 0.0
    bond_pct: float = 0.0
    cash_pct: float = 0.0
    intl_pct: float = 0.0
    real_estate_pct: float = 0.0
    top_sector: Optional[str] = None
    top_sector_pct: Optional[float] = None
    equity_vs_glidepath_delta: Optional[float] = None
    years_to_retirement: Optional[int] = None
    target_fund_gap: Optional[float] = None


class PortfolioInsightResponse(BaseModel):
    headline: str
    review: List[str]
    grade: InsightGrade
    factors_for: List[InsightFactorFor]
    factors_against: List[InsightFactorAgainst]
    suitability: InsightSuitability
    recommendations: List[InsightRecommendation]
    metrics: PortfolioMetrics
    market_context: Dict[str, Any]
    data_sources: List[str]
    generated_at: str
    disclaimer: str = DISCLAIMER
    degraded: bool = False


# ─── Deterministic metrics ──────────────────────────────────────────────────

# Coarse sector -> asset_class fallback used when a holding's symbol isn't in
# the market reference bundle (e.g. a fund we don't carry synthetic data for).
_SECTOR_ASSET_CLASS_HINTS = {
    "fixed income": "bond",
    "inflation protected": "bond",
    "cash": "cash",
    "real estate": "real_estate",
    "international": "equity_intl",
    "emerging markets": "equity_intl",
}


def _infer_asset_class(holding: Dict[str, Any], market_context: MarketContext) -> str:
    symbol = str(holding.get("symbol", "")).upper()
    fund = market_context.funds.get(symbol)
    if fund is not None:
        return fund.asset_class
    sector = str(holding.get("sector", "")).lower()
    for hint, asset_class in _SECTOR_ASSET_CLASS_HINTS.items():
        if hint in sector:
            return asset_class
    return "equity_us"  # default assumption for an unclassified equity holding


def compute_metrics(
    profile: Any,
    current_portfolio: Dict[str, Any],
    market_context: MarketContext,
) -> PortfolioMetrics:
    """Compute every numeric figure the insight prompt and response need.
    Pure function of (profile, portfolio, market context) -- fully unit
    testable without any network access or LLM call."""
    holdings: List[Dict[str, Any]] = current_portfolio.get("holdings", []) or []
    total_value = float(current_portfolio.get("total_value", 0) or sum(h.get("value", 0) for h in holdings))

    weighted_expense_ratio = 0.0
    weighted_yield = 0.0
    have_expense_data = False
    have_yield_data = False
    equity_value = 0.0
    bond_value = 0.0
    cash_value = 0.0
    intl_value = 0.0
    real_estate_value = 0.0
    sector_totals: Dict[str, float] = {}

    for h in holdings:
        value = float(h.get("value", 0) or 0)
        if total_value <= 0:
            continue
        weight = value / total_value
        symbol = str(h.get("symbol", "")).upper()
        fund = market_context.funds.get(symbol)

        if fund is not None and fund.expense_ratio is not None:
            weighted_expense_ratio += weight * fund.expense_ratio
            have_expense_data = True
        if fund is not None and fund.yield_pct is not None:
            weighted_yield += weight * fund.yield_pct
            have_yield_data = True

        asset_class = _infer_asset_class(h, market_context)
        if asset_class == "bond":
            bond_value += value
        elif asset_class == "cash":
            cash_value += value
        elif asset_class == "real_estate":
            real_estate_value += value
        elif asset_class == "equity_intl":
            equity_value += value
            intl_value += value
        else:  # equity_us and anything unclassified
            equity_value += value

        sector = h.get("sector") or "Unclassified"
        sector_totals[sector] = sector_totals.get(sector, 0.0) + value

    top_sector = None
    top_sector_pct = None
    if sector_totals and total_value > 0:
        top_sector = max(sector_totals, key=sector_totals.get)
        top_sector_pct = round(100 * sector_totals[top_sector] / total_value, 1)

    def pct(v: float) -> float:
        return round(100 * v / total_value, 1) if total_value > 0 else 0.0

    age = getattr(profile, "age", None)
    target_retire_age = getattr(profile, "target_retire_age", None)
    target_monthly_income = getattr(profile, "target_monthly_income", None)

    equity_vs_glidepath_delta = None
    if age is not None:
        recommended_equity_pct = max(0, min(100, 110 - age))
        equity_vs_glidepath_delta = round(pct(equity_value) - recommended_equity_pct, 1)

    years_to_retirement = None
    if age is not None and target_retire_age is not None:
        years_to_retirement = max(target_retire_age - age, 0)

    target_fund_gap = None
    if target_monthly_income is not None:
        # 4% safe-withdrawal-rate rule: annual income / 0.04 = required nest egg.
        required_nest_egg = (target_monthly_income * 12) / 0.04
        target_fund_gap = round(required_nest_egg - total_value, 2)

    return PortfolioMetrics(
        total_value=round(total_value, 2),
        holdings_count=len(holdings),
        weighted_expense_ratio=round(weighted_expense_ratio, 5) if have_expense_data else None,
        weighted_yield=round(weighted_yield, 2) if have_yield_data else None,
        equity_pct=pct(equity_value),
        bond_pct=pct(bond_value),
        cash_pct=pct(cash_value),
        intl_pct=pct(intl_value),
        real_estate_pct=pct(real_estate_value),
        top_sector=top_sector,
        top_sector_pct=top_sector_pct,
        equity_vs_glidepath_delta=equity_vs_glidepath_delta,
        years_to_retirement=years_to_retirement,
        target_fund_gap=target_fund_gap,
    )


# ─── Prompt construction ────────────────────────────────────────────────────

PORTFOLIO_INSIGHT_PROMPT = """
You are a portfolio review analyst. You will be given a factual brief -- every number has already been computed in Python, so treat all figures as ground truth. Your job is judgment and language: write a grounded, honest review of this portfolio, weigh factors for and against it, and give a Sage AI Grade.

IMPORTANT: You must respond with ONLY a valid JSON object. No explanatory text before or after. Do not use the AnalysisOutput schema from your default instructions -- use the schema specified below instead.

User profile: {profile_summary}

Portfolio metrics (computed, not estimated):
{metrics_summary}

Holdings:
{holdings_summary}

Market context for held funds (source: {data_sources}):
{market_context_summary}

Macro snapshot:
{macro_summary}

Write a candid, specific review. Reference actual numbers from the brief above -- never invent figures. Consider cost (expense ratios), diversification (equity/bond/cash/international mix, sector concentration), risk alignment (age-based glidepath, stated risk appetite), and progress toward the retirement income goal (target fund gap).

CRITICAL: Your response must be a single JSON object with this exact structure:
{{
  "headline": "<Short 5-10 word headline summarizing the overall assessment>",
  "review": [
    "<Paragraph 1: overall assessment of the portfolio>",
    "<Paragraph 2: cost and diversification analysis>",
    "<Paragraph 3: risk alignment and progress toward retirement goal>"
  ],
  "grade": {{
    "letter": "<A+ through F>",
    "score": <integer 0-100>,
    "rationale": "<1-2 sentence explanation of the grade, referencing specific metrics>"
  }},
  "factors_for": [
    {{"title": "<3-6 word title>", "detail": "<1-2 sentences, cite a specific number>", "weight": "high" | "medium" | "low"}}
  ],
  "factors_against": [
    {{"title": "<3-6 word title>", "detail": "<1-2 sentences, cite a specific number>", "severity": "high" | "medium" | "low"}}
  ],
  "suitability": {{
    "verdict": "well_suited" | "mostly_suited" | "needs_adjustment" | "misaligned",
    "detail": "<1-2 sentence overall suitability assessment>",
    "risk_alignment": "<short assessment of risk appetite vs actual allocation>",
    "horizon_alignment": "<short assessment of age/years-to-retirement vs equity glidepath>",
    "income_alignment": "<short assessment of progress toward the target retirement income>"
  }},
  "recommendations": [
    {{"action": "<specific actionable step>", "priority": "high" | "medium" | "low", "category": "allocation" | "cost" | "diversification" | "risk" | "income" | "tax", "rationale": "<1 sentence, cite a number>"}}
  ]
}}

Provide exactly 3 review paragraphs, 2-4 factors_for, 2-4 factors_against, and 2-4 recommendations.
Do not include any explanatory text before or after the JSON. The JSON must be complete and valid.
"""


def build_insight_prompt(
    profile: Any,
    current_portfolio: Dict[str, Any],
    metrics: PortfolioMetrics,
    market_context: MarketContext,
) -> str:
    holdings: List[Dict[str, Any]] = current_portfolio.get("holdings", []) or []

    profile_summary = (
        f"Age {getattr(profile, 'age', '?')}, salary ${getattr(profile, 'salary', 0):,.0f}, "
        f"{getattr(profile, 'risk_appetite', 'unknown')} risk tolerance, targeting retirement at "
        f"{getattr(profile, 'target_retire_age', '?')} with a target monthly income of "
        f"${getattr(profile, 'target_monthly_income', 0):,.0f}."
    )

    metrics_summary = "\n".join([
        f"- Total portfolio value: ${metrics.total_value:,.0f}",
        f"- Holdings count: {metrics.holdings_count}",
        f"- Weighted expense ratio: {metrics.weighted_expense_ratio * 100:.3f}%" if metrics.weighted_expense_ratio is not None else "- Weighted expense ratio: unavailable",
        f"- Weighted yield: {metrics.weighted_yield:.2f}%" if metrics.weighted_yield is not None else "- Weighted yield: unavailable",
        f"- Allocation: {metrics.equity_pct}% equity ({metrics.intl_pct}% international), {metrics.bond_pct}% bonds, {metrics.cash_pct}% cash, {metrics.real_estate_pct}% real estate",
        f"- Top sector concentration: {metrics.top_sector} at {metrics.top_sector_pct}%" if metrics.top_sector else "- Top sector concentration: unavailable",
        f"- Equity allocation vs. age-based glidepath (110-minus-age heuristic): {metrics.equity_vs_glidepath_delta:+.1f} percentage points" if metrics.equity_vs_glidepath_delta is not None else "- Equity vs glidepath: unavailable",
        f"- Years to retirement: {metrics.years_to_retirement}" if metrics.years_to_retirement is not None else "- Years to retirement: unavailable",
        f"- Gap to 4%-rule target nest egg: ${metrics.target_fund_gap:,.0f}" if metrics.target_fund_gap is not None else "- Target fund gap: unavailable",
    ])

    holdings_summary = "\n".join([
        f"- {h.get('symbol', 'UNK')} ({h.get('name', 'Unknown')}): ${h.get('value', 0):,.0f} ({h.get('allocation', 0)}%), sector: {h.get('sector', 'unclassified')}"
        for h in holdings
    ]) or "No holdings provided"

    market_context_summary = "\n".join([
        f"- {symbol}: {fund.category or fund.asset_class}, expense ratio {fund.expense_ratio * 100:.2f}%, yield {fund.yield_pct}%, 5y avg return {fund.avg_return_5y_pct}%"
        for symbol, fund in market_context.funds.items()
        if fund.expense_ratio is not None
    ]) or "No market data available for held symbols"

    macro = market_context.macro
    macro_summary = (
        f"10Y Treasury yield: {macro.treasury_10y_yield_pct}%, Fed funds rate: {macro.fed_funds_rate_pct}%, "
        f"CPI YoY: {macro.cpi_yoy_pct}%, S&P 500 YTD: {macro.sp500_ytd_return_pct}% (as of {macro.as_of})"
    )

    return PORTFOLIO_INSIGHT_PROMPT.format(
        profile_summary=profile_summary,
        metrics_summary=metrics_summary,
        holdings_summary=holdings_summary,
        data_sources=", ".join(market_context.data_sources),
        market_context_summary=market_context_summary,
        macro_summary=macro_summary,
    )


# ─── Disk cache (24h TTL by default, bypassed by force_refresh) ────────────

def portfolio_hash(current_portfolio: Dict[str, Any]) -> str:
    """Stable hash of the holdings so a portfolio change auto-invalidates the
    cached insight."""
    holdings = current_portfolio.get("holdings", []) or []
    normalized = sorted(
        (h.get("symbol", ""), round(float(h.get("value", 0) or 0), 2), round(float(h.get("allocation", 0) or 0), 2))
        for h in holdings
    )
    digest = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()
    return digest[:16]


def _insight_cache_path(profile_id: str, portfolio_digest: str) -> Path:
    INSIGHT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe_profile_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in profile_id)
    return INSIGHT_CACHE_DIR / f"{safe_profile_id}-{portfolio_digest}.json"


def get_cached_insight(profile_id: str, portfolio_digest: str) -> Optional[dict]:
    path = _insight_cache_path(profile_id, portfolio_digest)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    ttl_hours = float(os.environ.get("PORTFOLIO_INSIGHT_CACHE_TTL_HOURS", DEFAULT_INSIGHT_CACHE_TTL_HOURS))
    age = time.time() - payload.get("_cached_at", 0)
    if age > ttl_hours * 3600:
        return None
    return payload.get("data")


def set_cached_insight(profile_id: str, portfolio_digest: str, data: dict) -> None:
    path = _insight_cache_path(profile_id, portfolio_digest)
    with open(path, "w") as f:
        json.dump({"_cached_at": time.time(), "data": data}, f)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
