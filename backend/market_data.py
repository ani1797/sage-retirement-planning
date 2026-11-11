"""
Market data provider layer for the AI Insight feature.

Design goals (see docs/ai-insight.md for the full rationale):
- Free/synthetic sources only. No paid vendor (Morningstar, Moody's) is wired
  up -- there is no self-serve tier for either that would give the retail
  fund analytics this feature wants, at any budget.
- `MARKET_DATA_PROVIDER` env var selects the provider (default: synthetic).
- Every provider funnels through the same fallback chain: live -> stale cache
  -> bundled synthetic reference data, so an outage degrades data quality
  (flagged via `MarketContext.degraded`), never breaks the request.
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel

DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = DATA_DIR / "cache" / "market"
REFERENCE_BUNDLE_PATH = DATA_DIR / "market_reference.json"

DEFAULT_CACHE_TTL_HOURS = 24


# ─── Models ──────────────────────────────────────────────────────────────────

class FundProfile(BaseModel):
    symbol: str
    name: str
    asset_class: str  # equity_us | equity_intl | bond | real_estate | cash
    category: Optional[str] = None
    expense_ratio: Optional[float] = None
    yield_pct: Optional[float] = None
    avg_return_5y_pct: Optional[float] = None
    net_assets_usd: Optional[float] = None
    top_sector: Optional[str] = None
    top_sector_pct: Optional[float] = None
    description: Optional[str] = None
    source: str
    as_of: str


class MacroSnapshot(BaseModel):
    treasury_10y_yield_pct: Optional[float] = None
    treasury_2y_yield_pct: Optional[float] = None
    fed_funds_rate_pct: Optional[float] = None
    cpi_yoy_pct: Optional[float] = None
    sp500_ytd_return_pct: Optional[float] = None
    source: str
    as_of: str


class MarketContext(BaseModel):
    funds: Dict[str, FundProfile]
    macro: MacroSnapshot
    provider: str
    degraded: bool = False
    degraded_reason: Optional[str] = None
    data_sources: List[str] = []


# ─── Reference bundle (default provider + universal fallback) ──────────────

_reference_bundle_cache: Optional[dict] = None


def _load_reference_bundle() -> dict:
    global _reference_bundle_cache
    if _reference_bundle_cache is None:
        with open(REFERENCE_BUNDLE_PATH) as f:
            _reference_bundle_cache = json.load(f)
    return _reference_bundle_cache


def reference_bundle_symbols() -> List[str]:
    """All symbols covered by the bundled synthetic reference data."""
    return list(_load_reference_bundle().get("funds", {}).keys())


def _synthetic_fund_profile(symbol: str) -> Optional[FundProfile]:
    bundle = _load_reference_bundle()
    record = bundle.get("funds", {}).get(symbol.upper())
    if record is None:
        return None
    return FundProfile(**record)


def _synthetic_macro_snapshot() -> MacroSnapshot:
    bundle = _load_reference_bundle()
    return MacroSnapshot(**bundle["macro"])


# ─── Disk TTL cache ──────────────────────────────────────────────────────────

class CachedMarketData:
    """A tiny JSON-file TTL cache. Each key maps to one cache file; stale
    entries are still readable (not deleted) so the fallback chain can use
    them if a live provider is down."""

    def __init__(self, cache_dir: Path = CACHE_DIR, ttl_hours: Optional[float] = None):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = (ttl_hours if ttl_hours is not None else float(
            os.environ.get("MARKET_DATA_CACHE_TTL_HOURS", DEFAULT_CACHE_TTL_HOURS)
        )) * 3600

    def _path(self, key: str) -> Path:
        safe_key = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str, allow_stale: bool = False) -> Optional[dict]:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            with open(path) as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
        age = time.time() - payload.get("_cached_at", 0)
        if age > self.ttl_seconds and not allow_stale:
            return None
        return payload.get("data")

    def set(self, key: str, data: dict) -> None:
        path = self._path(key)
        with open(path, "w") as f:
            json.dump({"_cached_at": time.time(), "data": data}, f)


# ─── Provider abstraction ───────────────────────────────────────────────────

class MarketDataProvider(ABC):
    name: str = "unknown"

    @abstractmethod
    def get_fund_profile(self, symbol: str) -> Optional[FundProfile]:
        ...

    @abstractmethod
    def get_macro_snapshot(self) -> MacroSnapshot:
        ...


class SyntheticProvider(MarketDataProvider):
    """Default provider. $0, no network, no license exposure -- and the
    universal fallback target when a live provider fails or is unconfigured."""

    name = "synthetic"

    def get_fund_profile(self, symbol: str) -> Optional[FundProfile]:
        return _synthetic_fund_profile(symbol)

    def get_macro_snapshot(self) -> MacroSnapshot:
        return _synthetic_macro_snapshot()


class AlphaVantageProvider(MarketDataProvider):
    """Free-tier Alpha Vantage ETF_PROFILE endpoint (25 req/day, 5/min).
    Requires ALPHAVANTAGE_API_KEY. Falls back to the synthetic bundle for
    macro data since Alpha Vantage's free tier has no equivalent snapshot."""

    name = "alphavantage"
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 10.0):
        self.api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY", "")
        self.timeout = timeout

    def get_fund_profile(self, symbol: str) -> Optional[FundProfile]:
        if not self.api_key:
            return None
        try:
            resp = httpx.get(
                self.BASE_URL,
                params={"function": "ETF_PROFILE", "symbol": symbol, "apikey": self.api_key},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return None

        if not data or "Information" in data or "Note" in data or "Error Message" in data:
            # Rate-limited, invalid key, or unknown symbol -- treat as a miss.
            return None

        sectors = data.get("sectors") or []
        top_sector = None
        top_sector_pct = None
        if sectors:
            top = max(sectors, key=lambda s: float(s.get("weight", 0) or 0))
            top_sector = top.get("sector")
            top_sector_pct = float(top.get("weight", 0) or 0) * 100

        as_of = time.strftime("%Y-%m-%d")
        try:
            return FundProfile(
                symbol=symbol.upper(),
                name=data.get("net_assets", symbol.upper()) and symbol.upper(),
                asset_class="equity_us",  # Alpha Vantage ETF_PROFILE doesn't classify; caller may override.
                expense_ratio=float(data["net_expense_ratio"]) if data.get("net_expense_ratio") else None,
                yield_pct=float(data["dividend_yield"]) * 100 if data.get("dividend_yield") else None,
                net_assets_usd=float(data["net_assets"]) if data.get("net_assets") else None,
                top_sector=top_sector,
                top_sector_pct=top_sector_pct,
                source="Alpha Vantage (ETF_PROFILE)",
                as_of=as_of,
            )
        except (KeyError, ValueError, TypeError):
            return None

    def get_macro_snapshot(self) -> MacroSnapshot:
        # No free macro endpoint bundled here yet -- synthetic covers this.
        return _synthetic_macro_snapshot()


class TreasuryYieldProvider(MarketDataProvider):
    """US Treasury Fiscal Data API -- public domain, no auth, no restrictive
    ToS (unlike FRED, whose 2024 terms prohibit AI/LLM training use). Supplies
    macro yield data only; fund profiles always fall through to synthetic."""

    name = "treasury"
    BASE_URL = (
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
        "v2/accounting/od/avg_interest_rates"
    )

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def get_fund_profile(self, symbol: str) -> Optional[FundProfile]:
        return None  # Treasury Fiscal Data has no fund-level data.

    def get_macro_snapshot(self) -> MacroSnapshot:
        try:
            resp = httpx.get(
                self.BASE_URL,
                params={"sort": "-record_date", "page[size]": "1"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
            record = (payload.get("data") or [None])[0]
        except (httpx.HTTPError, ValueError, IndexError):
            record = None

        if not record:
            return _synthetic_macro_snapshot()

        synthetic = _synthetic_macro_snapshot()
        try:
            rate = float(record.get("avg_interest_rate_amt", 0))
        except (TypeError, ValueError):
            rate = None

        return MacroSnapshot(
            treasury_10y_yield_pct=rate if rate else synthetic.treasury_10y_yield_pct,
            treasury_2y_yield_pct=synthetic.treasury_2y_yield_pct,
            fed_funds_rate_pct=synthetic.fed_funds_rate_pct,
            cpi_yoy_pct=synthetic.cpi_yoy_pct,
            sp500_ytd_return_pct=synthetic.sp500_ytd_return_pct,
            source="US Treasury Fiscal Data API",
            as_of=record.get("record_date", synthetic.as_of),
        )


# ─── Fallback-chained context builder ───────────────────────────────────────

_cache = CachedMarketData()


def _provider_for_name(name: str) -> MarketDataProvider:
    if name == "alphavantage":
        return AlphaVantageProvider()
    if name == "treasury":
        return TreasuryYieldProvider()
    return SyntheticProvider()


def get_market_context(symbols: List[str], force_refresh: bool = False) -> MarketContext:
    """Resolve a MarketContext for the given symbols using the configured
    provider, with a live -> stale cache -> synthetic bundle fallback chain.
    `MarketContext.degraded` is set whenever anything short of a fully live
    lookup was used for any symbol or the macro snapshot."""
    provider_name = os.environ.get("MARKET_DATA_PROVIDER", "synthetic")
    provider = _provider_for_name(provider_name)

    degraded = False
    degraded_reasons: List[str] = []
    data_sources: set = set()
    funds: Dict[str, FundProfile] = {}

    for symbol in symbols:
        cache_key = f"fund_{provider_name}_{symbol.upper()}"
        profile: Optional[FundProfile] = None

        if not force_refresh:
            cached = _cache.get(cache_key)
            if cached:
                profile = FundProfile(**cached)

        if profile is None:
            try:
                profile = provider.get_fund_profile(symbol)
            except Exception:
                profile = None
            if profile is not None:
                _cache.set(cache_key, profile.model_dump())

        if profile is None:
            # Live lookup failed/unconfigured -- try a stale cache entry.
            stale = _cache.get(cache_key, allow_stale=True)
            if stale:
                profile = FundProfile(**stale)
                degraded = True
                degraded_reasons.append(f"{symbol}: using stale cached data")

        if profile is None:
            # Final fallback: bundled synthetic reference data.
            profile = _synthetic_fund_profile(symbol)
            if profile is not None and provider_name != "synthetic":
                degraded = True
                degraded_reasons.append(f"{symbol}: {provider_name} unavailable, used synthetic reference data")

        if profile is not None:
            funds[symbol.upper()] = profile
            data_sources.add(profile.source)

    macro_cache_key = f"macro_{provider_name}"
    macro: Optional[MacroSnapshot] = None
    if not force_refresh:
        cached_macro = _cache.get(macro_cache_key)
        if cached_macro:
            macro = MacroSnapshot(**cached_macro)

    if macro is None:
        try:
            macro = provider.get_macro_snapshot()
            _cache.set(macro_cache_key, macro.model_dump())
        except Exception:
            stale_macro = _cache.get(macro_cache_key, allow_stale=True)
            if stale_macro:
                macro = MacroSnapshot(**stale_macro)
                degraded = True
                degraded_reasons.append("macro: using stale cached data")
            else:
                macro = _synthetic_macro_snapshot()
                if provider_name != "synthetic":
                    degraded = True
                    degraded_reasons.append(f"macro: {provider_name} unavailable, used synthetic reference data")

    data_sources.add(macro.source)

    return MarketContext(
        funds=funds,
        macro=macro,
        provider=provider_name,
        degraded=degraded,
        degraded_reason="; ".join(degraded_reasons) if degraded_reasons else None,
        data_sources=sorted(data_sources),
    )
