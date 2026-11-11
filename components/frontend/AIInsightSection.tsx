"use client"

import React, { useCallback, useEffect, useState } from "react"
import {
  Sparkles,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  Info,
} from "lucide-react"
import type { PortfolioInsightRequest, PortfolioInsightResponse } from "@/lib/api"
import { getPortfolioInsight } from "@/lib/api"
import { PoweredByLabel } from "./shared/PoweredByLabel"

// ─── Types ──────────────────────────────────────────────────────────────────

interface AIInsightSectionProps {
  profileId: string
  currentPortfolio: PortfolioInsightRequest["current_portfolio"]
  variant?: "full" | "compact"
  className?: string
}

// ─── Small helpers ──────────────────────────────────────────────────────────

const GRADE_COLORS: Record<string, string> = {
  A: "bg-emerald-50 text-emerald-700 border-emerald-200",
  B: "bg-blue-50 text-blue-700 border-blue-200",
  C: "bg-amber-50 text-amber-700 border-amber-200",
  D: "bg-orange-50 text-orange-700 border-orange-200",
  F: "bg-red-50 text-red-700 border-red-200",
}

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-red-50 text-red-600",
  medium: "bg-amber-50 text-amber-600",
  low: "bg-gray-100 text-gray-500",
}

const VERDICT_LABELS: Record<string, string> = {
  well_suited: "Well suited",
  mostly_suited: "Mostly suited",
  needs_adjustment: "Needs adjustment",
  misaligned: "Misaligned",
}

const VERDICT_COLORS: Record<string, string> = {
  well_suited: "bg-emerald-50 text-emerald-700",
  mostly_suited: "bg-blue-50 text-blue-700",
  needs_adjustment: "bg-amber-50 text-amber-700",
  misaligned: "bg-red-50 text-red-700",
}

function PriorityPill({ priority }: { priority: string }) {
  return (
    <span
      className={`text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded ${PRIORITY_COLORS[priority] ?? PRIORITY_COLORS.low}`}
    >
      {priority}
    </span>
  )
}

// ─── Skeleton ───────────────────────────────────────────────────────────────

function InsightSkeleton({ compact }: { compact: boolean }) {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-4 bg-gray-100 rounded w-1/3" />
      <div className="h-3 bg-gray-100 rounded w-full" />
      <div className="h-3 bg-gray-100 rounded w-5/6" />
      {!compact && (
        <>
          <div className="h-3 bg-gray-100 rounded w-4/6" />
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="h-16 bg-gray-100 rounded-xl" />
            <div className="h-16 bg-gray-100 rounded-xl" />
          </div>
        </>
      )}
    </div>
  )
}

// ─── Component ──────────────────────────────────────────────────────────────

export const AIInsightSection: React.FC<AIInsightSectionProps> = ({
  profileId,
  currentPortfolio,
  variant = "full",
  className = "",
}) => {
  const [insight, setInsight] = useState<PortfolioInsightResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showMarketData, setShowMarketData] = useState(false)

  const fetchInsight = useCallback(
    async (forceRefresh: boolean) => {
      setLoading(true)
      setError(null)
      try {
        const result = await getPortfolioInsight({
          profile_id: profileId,
          current_portfolio: currentPortfolio,
          force_refresh: forceRefresh,
        })
        setInsight(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load AI insight")
      } finally {
        setLoading(false)
      }
    },
    [profileId, currentPortfolio]
  )

  useEffect(() => {
    fetchInsight(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileId])

  const compact = variant === "compact"

  return (
    <div
      className={`bg-white rounded-2xl border border-gray-200/80 p-6 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-500" />
          <h2 className="font-semibold text-gray-900">AI Portfolio Insight</h2>
          <PoweredByLabel product="Foundry IQ" variant="light" />
        </div>
        <div className="flex items-center gap-3">
          {insight && (
            <span className="text-xs text-gray-400 hidden sm:inline">
              As of {new Date(insight.generated_at).toLocaleDateString()}
            </span>
          )}
          <button
            onClick={() => fetchInsight(true)}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-indigo-600 disabled:opacity-50 transition-colors"
            title="Regenerate insight"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {loading && !insight && <InsightSkeleton compact={compact} />}

      {error && !insight && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-100 rounded-xl p-4 text-sm text-red-700">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p>{error}</p>
            <button
              onClick={() => fetchInsight(false)}
              className="mt-2 text-xs font-semibold underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {insight && (
        <div className="space-y-5">
          {/* Degraded data notice */}
          {insight.degraded && (
            <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
              <Info className="w-3.5 h-3.5 flex-shrink-0" />
              Live market data was unavailable; this review uses the offline synthetic reference bundle.
            </div>
          )}

          {/* Headline + Grade */}
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <p className="font-medium text-gray-900">{insight.headline}</p>
            </div>
            <div
              className={`flex items-center gap-2 border rounded-xl px-3 py-2 ${GRADE_COLORS[insight.grade.letter] ?? GRADE_COLORS.C}`}
            >
              <span className="text-2xl font-bold leading-none">{insight.grade.letter}</span>
              <div className="text-xs leading-tight">
                <p className="font-semibold">Sage AI Grade</p>
                <p className="opacity-70">{insight.grade.score}/100</p>
              </div>
            </div>
          </div>

          {/* Written review */}
          <div className="space-y-2">
            {(compact ? insight.review.slice(0, 1) : insight.review).map((para, i) => (
              <p key={i} className="text-sm text-gray-600 leading-relaxed">
                {para}
              </p>
            ))}
          </div>

          {!compact && (
            <>
              {/* Factors for / against */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-emerald-50/50 rounded-xl p-4 border border-emerald-100">
                  <div className="flex items-center gap-1.5 mb-2 text-emerald-700 font-semibold text-sm">
                    <ThumbsUp className="w-4 h-4" />
                    Factors in Favor
                  </div>
                  <ul className="space-y-2">
                    {insight.factors_for.map((f, i) => (
                      <li key={i} className="text-sm">
                        <span className="font-medium text-gray-800">{f.title}</span>
                        <p className="text-xs text-gray-500 mt-0.5">{f.detail}</p>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-red-50/50 rounded-xl p-4 border border-red-100">
                  <div className="flex items-center gap-1.5 mb-2 text-red-700 font-semibold text-sm">
                    <ThumbsDown className="w-4 h-4" />
                    Factors Against
                  </div>
                  <ul className="space-y-2">
                    {insight.factors_against.map((f, i) => (
                      <li key={i} className="text-sm">
                        <span className="font-medium text-gray-800">{f.title}</span>
                        <p className="text-xs text-gray-500 mt-0.5">{f.detail}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Suitability strip */}
              <div className="bg-gray-50/80 rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full ${VERDICT_COLORS[insight.suitability.verdict] ?? VERDICT_COLORS.mostly_suited}`}
                  >
                    {VERDICT_LABELS[insight.suitability.verdict] ?? insight.suitability.verdict}
                  </span>
                  <p className="text-sm text-gray-700">{insight.suitability.detail}</p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-gray-500">
                  <p><span className="font-medium text-gray-700">Risk: </span>{insight.suitability.risk_alignment}</p>
                  <p><span className="font-medium text-gray-700">Horizon: </span>{insight.suitability.horizon_alignment}</p>
                  <p><span className="font-medium text-gray-700">Income: </span>{insight.suitability.income_alignment}</p>
                </div>
              </div>

              {/* Recommendations */}
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-2">Recommendations</h3>
                <ul className="space-y-2">
                  {insight.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <PriorityPill priority={rec.priority} />
                      <div>
                        <span className="text-gray-800">{rec.action}</span>
                        <p className="text-xs text-gray-500 mt-0.5">{rec.rationale}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Market data used (collapsible) */}
              <div className="border-t border-gray-100 pt-3">
                <button
                  onClick={() => setShowMarketData((v) => !v)}
                  className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-700"
                >
                  {showMarketData ? (
                    <ChevronUp className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5" />
                  )}
                  Market data used
                </button>
                {showMarketData && (
                  <div className="mt-3 space-y-3 text-xs text-gray-500">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {Object.values(insight.market_context.funds).map((f) => (
                        <div key={f.symbol} className="bg-gray-50 rounded-lg p-2.5">
                          <p className="font-semibold text-gray-700">
                            {f.symbol} · {f.name}
                          </p>
                          <p>
                            Expense ratio {(f.expense_ratio * 100).toFixed(2)}% · Yield {f.yield_pct}% · 5y avg return {f.avg_return_5y_pct}%
                          </p>
                          <p className="text-gray-400">{f.source} · as of {f.as_of}</p>
                        </div>
                      ))}
                    </div>
                    <div className="bg-gray-50 rounded-lg p-2.5">
                      <p className="font-semibold text-gray-700">Macro snapshot</p>
                      <p>
                        10y Treasury {insight.market_context.macro.treasury_10y_yield_pct}% · Fed funds {insight.market_context.macro.fed_funds_rate_pct}% · CPI YoY {insight.market_context.macro.cpi_yoy_pct}% · S&amp;P 500 YTD {insight.market_context.macro.sp500_ytd_return_pct}%
                      </p>
                      <p className="text-gray-400">{insight.market_context.macro.source} · as of {insight.market_context.macro.as_of}</p>
                    </div>
                    <p>Sources: {insight.data_sources.join(", ")}</p>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Disclaimer */}
          <p className="text-[11px] text-gray-400 leading-relaxed border-t border-gray-100 pt-3">
            {insight.disclaimer}
          </p>
        </div>
      )}
    </div>
  )
}

export default AIInsightSection
