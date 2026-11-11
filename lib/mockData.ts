import type { UserProfile, ChatResponse, HealthResponse, ScenariosResponse } from "./api"

// Mock User Profiles
export const mockUserProfiles: UserProfile[] = [
  {
    id: "demo-user",
    name: "John Doe",
    age: 40,
    current_cash: 30000,
    investment_assets: 250000,
    yearly_savings_rate: 0.15,
    salary: 96000,
    portfolio: { stocks: 0.7, bonds: 0.3 },
    risk_appetite: "medium",
    target_retire_age: 65,
    target_monthly_income: 4000,
    description: "Balanced approach with moderate risk tolerance",
  },
  {
    id: "young-professional",
    name: "Sarah Chen",
    age: 28,
    current_cash: 15000,
    investment_assets: 45000,
    yearly_savings_rate: 0.2,
    salary: 75000,
    portfolio: { stocks: 0.85, bonds: 0.15 },
    risk_appetite: "high",
    target_retire_age: 60,
    target_monthly_income: 5000,
    description: "Young professional with aggressive growth strategy",
  },
  {
    id: "mid-career",
    name: "Michael Rodriguez",
    age: 45,
    current_cash: 50000,
    investment_assets: 400000,
    yearly_savings_rate: 0.18,
    salary: 120000,
    portfolio: { stocks: 0.65, bonds: 0.25, real_estate: 0.1 },
    risk_appetite: "medium",
    target_retire_age: 62,
    target_monthly_income: 6000,
    description: "Mid-career professional with diversified portfolio",
  },
  {
    id: "conservative-saver",
    name: "Linda Thompson",
    age: 55,
    current_cash: 80000,
    investment_assets: 600000,
    yearly_savings_rate: 0.12,
    salary: 85000,
    portfolio: { stocks: 0.4, bonds: 0.5, cash: 0.1 },
    risk_appetite: "low",
    target_retire_age: 67,
    target_monthly_income: 4500,
    description: "Conservative approach nearing retirement",
  },
  {
    id: "high-earner",
    name: "David Kim",
    age: 38,
    current_cash: 100000,
    investment_assets: 800000,
    yearly_savings_rate: 0.25,
    salary: 180000,
    portfolio: { stocks: 0.7, bonds: 0.2, alternatives: 0.1 },
    risk_appetite: "high",
    target_retire_age: 55,
    target_monthly_income: 8000,
    description: "High earner targeting early retirement",
  },
]

// Mock Quick Scenarios
export const mockQuickScenarios: string[] = [
  "What if I retire 2 years earlier?",
  "How would a market crash affect my plan?",
  "Should I increase my savings rate by 5%?",
  "What if I need $100k for healthcare costs?",
  "How does inflation impact my retirement income?",
  "What if I work part-time in retirement?",
  "Should I pay off my mortgage before retiring?",
  "What if I inherit $200k from my parents?",
  "How would changing jobs affect my retirement?",
  "What if I want to retire abroad?",
]

// Mock Follow-up Questions
export const mockFollowUpQuestions: string[] = [
  "What's the minimum increase that makes a difference?",
  "How does this compare to working longer?",
  "Can I automate these additional contributions?",
  "What if I can only do this for 3 years?",
  "How can I make my plan more crash-resistant?",
  "Should I increase my bond allocation?",
  "What are the biggest risks to consider?",
  "How much should I save in an HSA?",
]

// Mock Analysis Data Templates
export const mockAnalysisTemplates = {
  savingsRateIncrease: {
    title: "Increased Savings Rate (+5%)",
    riskLevel: "Low Risk" as const,
    successRate: 92,
    successRateChange: 7,
    additionalSavings: { amount: 450, change: "5% increase" },
    retirementIncome: { amount: 3650, change: "+$450" },
    extraYears: { years: 6, description: "income duration" },
    products: [
      {
        name: "Target Date 2030",
        allocation: 60,
        return: "7.8% return",
        description: "Age-appropriate growth",
        icon: "🎯",
      },
      {
        name: "International Index",
        allocation: 20,
        return: "7.2% return",
        description: "Diversification",
        icon: "📈",
      },
      {
        name: "Bond Aggregate",
        allocation: 20,
        return: "4% return",
        description: "Risk reduction",
        icon: "🛡️",
      },
    ],
    cashflows: [
      { year: 1, amount: 58000 },
      { year: 2, amount: 60000 },
      { year: 3, amount: 62000 },
      { year: 4, amount: 65000 },
      { year: 5, amount: 68000 },
    ],
  },

  earlyRetirement: {
    title: "Early Retirement (Age 63)",
    riskLevel: "Medium Risk" as const,
    successRate: 78,
    successRateChange: -7,
    retirementIncome: { amount: 2850, change: "-$350" },
    extraYears: { years: -2, description: "reduced accumulation" },
    products: [
      {
        name: "Growth Portfolio",
        allocation: 70,
        return: "8.5% return",
        description: "Higher growth for shorter timeline",
        icon: "📈",
      },
      {
        name: "International Growth",
        allocation: 20,
        return: "9% return",
        description: "Global diversification",
        icon: "🌍",
      },
      {
        name: "Bond Index",
        allocation: 10,
        return: "4% return",
        description: "Stability component",
        icon: "🛡️",
      },
    ],
    cashflows: [
      { year: 1, amount: 40000 },
      { year: 2, amount: 42000 },
      { year: 3, amount: 44000 },
      { year: 4, amount: 46000 },
      { year: 5, amount: 48000 },
    ],
  },

  marketCrash: {
    title: "Market Crash Resilience",
    riskLevel: "Medium Risk" as const,
    successRate: 82,
    successRateChange: -3,
    retirementIncome: { amount: 3050, change: "-$150" },
    extraYears: { years: -1, description: "recovery period" },
    products: [
      {
        name: "Defensive Balanced Portfolio",
        allocation: 40,
        return: "6.5% return",
        description: "Crash-resistant allocation",
        icon: "🛡️",
      },
      {
        name: "Bond Aggregate",
        allocation: 40,
        return: "4% return",
        description: "Stability during volatility",
        icon: "📊",
      },
      {
        name: "Value Stocks",
        allocation: 20,
        return: "7.5% return",
        description: "Recovery potential",
        icon: "💎",
      },
    ],
    cashflows: [
      { year: 1, amount: 38000 },
      { year: 2, amount: 41000 },
      { year: 3, amount: 44000 },
      { year: 4, amount: 47000 },
      { year: 5, amount: 50000 },
    ],
  },

  healthcareCosts: {
    title: "Healthcare Cost Impact",
    riskLevel: "Medium Risk" as const,
    successRate: 79,
    successRateChange: -6,
    additionalSavings: { amount: 288, change: "healthcare buffer" },
    retirementIncome: { amount: 2367, change: "-$833" },
    products: [
      {
        name: "Healthcare-Focused Portfolio",
        allocation: 40,
        return: "7% return",
        description: "Healthcare sector exposure",
        icon: "🏥",
      },
      {
        name: "Stable Value Fund",
        allocation: 30,
        return: "4.5% return",
        description: "Predictable returns",
        icon: "📈",
      },
      {
        name: "Healthcare Sector ETF",
        allocation: 30,
        return: "8% return",
        description: "Sector-specific growth",
        icon: "💊",
      },
    ],
    cashflows: [
      { year: 1, amount: 35000 },
      { year: 2, amount: 37000 },
      { year: 3, amount: 39000 },
      { year: 4, amount: 41000 },
      { year: 5, amount: 43000 },
    ],
  },

  default: {
    title: "Current Scenario Analysis",
    riskLevel: "Medium Risk" as const,
    successRate: 85,
    retirementIncome: { amount: 3200, change: "baseline" },
    products: [
      {
        name: "Balanced Portfolio",
        allocation: 50,
        return: "7% return",
        description: "Balanced growth approach",
        icon: "⚖️",
      },
      {
        name: "Bond Index",
        allocation: 30,
        return: "4.2% return",
        description: "Income generation",
        icon: "📊",
      },
      {
        name: "International Index",
        allocation: 20,
        return: "7.2% return",
        description: "Global diversification",
        icon: "🌍",
      },
    ],
    cashflows: [
      { year: 1, amount: 42000 },
      { year: 2, amount: 44500 },
      { year: 3, amount: 47000 },
      { year: 4, amount: 49500 },
      { year: 5, amount: 52000 },
    ],
  },
}

// Mock streaming simulation
async function* simulateMockStreaming(message: string, profile: UserProfile) {
  const statusUpdates = [
    { status: "Starting analysis..." },
    { status: "Thinking..." },
    { status: "Fetching investment products..." },
    { status: "Running calculations..." },
    { status: "Generating recommendations..." },
    { status: "Finalizing analysis..." },
  ]

  // Emit status updates
  for (const update of statusUpdates) {
    await new Promise((resolve) => setTimeout(resolve, 800))
    yield {
      type: "status" as const,
      data: update,
      timestamp: Date.now(),
    }
  }

  // Generate final response
  const finalResponse = generateMockChatResponse(message, profile)

  // Stream content in chunks
  const words = finalResponse.response.split(" ")
  let accumulatedContent = ""

  for (let i = 0; i < words.length; i += 3) {
    const chunk = words.slice(i, i + 3).join(" ") + " "
    accumulatedContent += chunk

    await new Promise((resolve) => setTimeout(resolve, 100))
    yield {
      type: "content" as const,
      data: { content: chunk },
      timestamp: Date.now(),
    }
  }

  // Send final complete response
  yield {
    type: "complete" as const,
    data: {
      response: finalResponse.response,
      analysis: finalResponse.analysis,
      status: "completed",
    },
    timestamp: Date.now(),
  }
}

// Mock Chat Response Generator
export const generateMockChatResponse = (message: string, profile: UserProfile): ChatResponse => {
  let analysisTemplate = mockAnalysisTemplates.default
  let responseText = ""

  // Determine response based on message content
  if (message.toLowerCase().includes("savings rate")) {
    analysisTemplate = mockAnalysisTemplates.savingsRateIncrease
    responseText = `Great question, ${profile.name}! I've analyzed the impact of increasing your savings rate by 5%. Based on your current profile (age ${profile.age}, ${profile.risk_appetite} risk tolerance), this is one of the most powerful levers you have for improving your retirement outcome.`
  } else if (message.toLowerCase().includes("retire") && message.toLowerCase().includes("earlier")) {
    analysisTemplate = mockAnalysisTemplates.earlyRetirement
    responseText = `I've analyzed retiring 2 years earlier for your profile, ${profile.name}. Given your current age of ${profile.age} and target retirement age of ${profile.target_retire_age}, early retirement is appealing but comes with important trade-offs to consider.`
  } else if (message.toLowerCase().includes("market crash") || message.toLowerCase().includes("crash")) {
    analysisTemplate = mockAnalysisTemplates.marketCrash
    responseText = `Excellent question about market resilience, ${profile.name}! I've analyzed how a significant market crash would affect your retirement plan. Based on your ${profile.risk_appetite} risk tolerance and current portfolio allocation, here's what you should know.`
  } else if (message.toLowerCase().includes("healthcare")) {
    analysisTemplate = mockAnalysisTemplates.healthcareCosts
    responseText = `Healthcare costs are a crucial consideration, ${profile.name}. I've analyzed the impact of needing an additional $100k for healthcare expenses during retirement, considering your current financial situation.`
  } else {
    responseText = `I've analyzed your scenario, ${profile.name}. Based on your profile (${profile.risk_appetite} risk tolerance, $${profile.salary.toLocaleString()} salary), I've created a customized projection that considers your current financial situation.`
  }

  return {
    response: responseText,
    analysis: {
      scenario: profile,
      recommended_changes: {
        diversification: "Optimize portfolio allocation",
        savings: "Consider increasing contributions",
        risk_management: "Review risk tolerance annually",
      },
      predictions: {
        metrics: {
          monthly_income: analysisTemplate.retirementIncome?.amount || 3200,
          success_rate_pct: analysisTemplate.successRate,
          risk_level: analysisTemplate.riskLevel.toLowerCase().replace(" risk", "") as "low" | "medium" | "high",
          flexibility: "High",
          time_horizon_years: profile.target_retire_age - profile.age,
        },
        deltas: analysisTemplate.additionalSavings
          ? {
              additional_savings_monthly: analysisTemplate.additionalSavings.amount,
              retirement_income_monthly: analysisTemplate.retirementIncome?.amount || 3200,
              retirement_income_delta: analysisTemplate.retirementIncome?.amount
                ? analysisTemplate.retirementIncome.amount - 3200
                : 0,
              success_rate_delta_pct: analysisTemplate.successRateChange || 0,
              extra_years_income_duration: analysisTemplate.extraYears?.years || 0,
            }
          : undefined,
        products: analysisTemplate.products.map((p) => ({
          name: p.name,
          allocation: p.allocation / 100,
          exp_return: Number.parseFloat(p.return.replace(/[^\d.]/g, "")) / 100,
          risk_rating: analysisTemplate.riskLevel.toLowerCase().replace(" risk", ""),
          asset_class: p.name.toLowerCase().replace(/\s+/g, "_"),
        })),
        cashflows: analysisTemplate.cashflows.map((c) => ({
          year: c.year,
          end_assets: c.amount,
        })),
      },
      follow_ups: mockFollowUpQuestions.slice(0, 4),
      alternatives: [
        "Conservative approach with lower risk",
        "Aggressive growth strategy",
        "Balanced portfolio optimization",
        "Alternative investment consideration",
      ],
      considerations: `This analysis is tailored for ${profile.name} based on your ${profile.risk_appetite} risk tolerance and ${profile.target_retire_age - profile.age}-year time horizon. The recommendations consider your current financial situation and retirement goals.`,
    },
    status: "completed",
  }
}

// Export the streaming function
export { simulateMockStreaming }

// ─── Mock Scenario Projection ───────────────────────────────────────────────

import type { ScenarioProjectionRequest, ScenarioProjectionResponse } from "./api"
import type {
  PortfolioInsightRequest,
  PortfolioInsightResponse,
  PortfolioMetrics,
  FundProfile,
  MacroSnapshot,
  InsightFactorFor,
  InsightFactorAgainst,
  InsightGrade,
  InsightSuitability,
  InsightRecommendation,
} from "./api"

export function generateMockProjection(
  request: ScenarioProjectionRequest
): ScenarioProjectionResponse {
  const { scenario_description, timeframe_months, current_portfolio } = request
  const scenario = scenario_description.toLowerCase()

  // Time multiplier for projections
  const timeMultiplier = timeframe_months / 12

  // Base market return assumptions
  let marketReturn = 0.07 * timeMultiplier
  let contributionBoost = 0

  // Parse scenario for keywords to adjust projections
  if (scenario.includes("increase") && scenario.includes("contribution")) {
    contributionBoost = 0.03 * timeMultiplier
  }
  if (scenario.includes("max") || scenario.includes("maximize")) {
    contributionBoost = 0.05 * timeMultiplier
  }
  if (scenario.includes("15%") || scenario.includes("20%")) {
    contributionBoost = 0.04 * timeMultiplier
  }
  if (scenario.includes("market crash") || scenario.includes("downturn") || scenario.includes("drop")) {
    marketReturn = -0.15 * timeMultiplier
  }
  if (scenario.includes("recession")) {
    marketReturn = -0.10 * timeMultiplier
  }
  if (scenario.includes("bull") || scenario.includes("growth")) {
    marketReturn = 0.12 * timeMultiplier
  }
  if (scenario.includes("stop") && scenario.includes("contribution")) {
    contributionBoost = -0.03 * timeMultiplier
  }
  if (scenario.includes("roth") || scenario.includes("ira")) {
    contributionBoost += 0.01 * timeMultiplier
  }
  if (scenario.includes("401k") || scenario.includes("401(k)")) {
    contributionBoost += 0.015 * timeMultiplier
  }

  const totalChangePercent = (marketReturn + contributionBoost) * 100
  const totalChange = Math.round(current_portfolio.total_value * (marketReturn + contributionBoost))
  const projectedTotal = current_portfolio.total_value + totalChange

  // Project accounts
  const projectedAccounts = current_portfolio.accounts.map((acc) => {
    // 401k and Roth get extra boost from contribution scenarios
    let accountBoost = marketReturn + contributionBoost
    if (acc.name.includes("401") && scenario.includes("401")) {
      accountBoost += 0.02 * timeMultiplier
    }
    if (acc.name.includes("Roth") && scenario.includes("roth")) {
      accountBoost += 0.015 * timeMultiplier
    }

    const change = Math.round(acc.balance * accountBoost)
    return {
      id: acc.id,
      name: acc.name,
      current_value: acc.balance,
      projected_value: acc.balance + change,
      change,
      change_percent: +(accountBoost * 100).toFixed(2),
    }
  })

  // Project holdings
  const projectedHoldings = current_portfolio.holdings.map((h) => {
    // Stocks more volatile in crash scenarios
    let holdingReturn = marketReturn + contributionBoost
    if (scenario.includes("crash") || scenario.includes("drop")) {
      if (h.symbol === "VTI" || h.symbol === "VXUS" || h.symbol === "VGT") {
        holdingReturn = marketReturn * 1.3 // More volatile
      } else if (h.symbol === "BND") {
        holdingReturn = 0.02 * timeMultiplier // Bonds stable
      }
    }

    const change = Math.round(h.value * holdingReturn)
    const projectedValue = h.value + change
    const projectedAllocation = +(
      (projectedValue / projectedTotal) *
      100
    ).toFixed(1)

    return {
      symbol: h.symbol,
      name: h.name,
      current_value: h.value,
      projected_value: projectedValue,
      current_allocation: h.allocation,
      projected_allocation: projectedAllocation,
      change,
      change_percent: +(holdingReturn * 100).toFixed(2),
    }
  })

  // Generate summary based on scenario
  let summary = ""
  let headline = ""
  if (scenario.includes("increase") && scenario.includes("contribution")) {
    headline = "Increased contributions accelerate growth"
    summary = `By increasing your contribution rate, your portfolio would grow an additional ${formatCurrency(Math.abs(totalChange))} over ${timeframe_months} months. This assumes ${(marketReturn / timeMultiplier * 100).toFixed(0)}% annual market returns and accounts for the 2026 contribution limits.`
  } else if (scenario.includes("max")) {
    headline = "Maximized contributions boost retirement"
    summary = `Maximizing your retirement contributions would boost your portfolio by ${formatCurrency(Math.abs(totalChange))} over ${timeframe_months} months. The tax-advantaged growth compounds significantly over your remaining working years.`
  } else if (scenario.includes("crash") || scenario.includes("drop")) {
    headline = "Market downturn impacts portfolio value"
    summary = `In a market downturn scenario, your portfolio could decline by ${formatCurrency(Math.abs(totalChange))} (${Math.abs(totalChangePercent).toFixed(1)}%) over ${timeframe_months} months. However, continued contributions would buy shares at lower prices, benefiting long-term returns.`
  } else if (scenario.includes("stop") && scenario.includes("contribution")) {
    headline = "Paused contributions slow growth"
    summary = `Pausing contributions would slow your portfolio growth. You would have ${formatCurrency(Math.abs(totalChange))} less over ${timeframe_months} months compared to maintaining your current savings rate.`
  } else {
    headline = `Portfolio ${totalChange >= 0 ? "growth" : "decline"} projected`
    summary = `Based on your scenario, your portfolio would ${totalChange >= 0 ? "grow by" : "decline by"} ${formatCurrency(Math.abs(totalChange))} (${Math.abs(totalChangePercent).toFixed(1)}%) over ${timeframe_months} months. This projection accounts for market returns and any changes to your contribution strategy.`
  }

  // Generate structured risks and opportunities based on scenario
  const risks: { title: string; detail: string; severity: "high" | "medium" | "low" }[] = []
  const opportunities: { title: string; detail: string; impact: "high" | "medium" | "low" }[] = []
  const action_items: { action: string; priority: "high" | "medium" | "low"; category: "contribution" | "allocation" | "tax" | "planning" }[] = []
  let key_factors: string[] = []

  if (scenario.includes("increase") || scenario.includes("max")) {
    risks.push(
      { title: "Reduced Take-Home Pay", detail: "Increased contributions will lower your monthly disposable income. Ensure you maintain an adequate emergency fund.", severity: "medium" },
      { title: "Market Volatility", detail: "Market fluctuations could temporarily reduce account values, though long-term trends favor staying invested.", severity: "low" },
    )
    opportunities.push(
      { title: "Tax-Advantaged Compounding", detail: "Pre-tax contributions grow tax-deferred, significantly accelerating wealth accumulation over time.", impact: "high" },
      { title: "Stronger Retirement Foundation", detail: "Higher contributions now build a larger base for compound growth in later years.", impact: "high" },
    )
    action_items.push(
      { action: "Review your monthly budget to ensure increased contributions are sustainable", priority: "high", category: "planning" },
      { action: "Verify you're capturing the full employer match before increasing further", priority: "high", category: "contribution" },
      { action: "Consider splitting increases between pre-tax and Roth for tax diversification", priority: "medium", category: "tax" },
    )
    key_factors = ["Higher contribution rate", "Tax-advantaged growth", "Compound interest over time"]
  } else if (scenario.includes("crash") || scenario.includes("drop")) {
    risks.push(
      { title: "Significant Value Decline", detail: "Portfolio could drop 15-30% in a severe downturn, with recovery typically taking 2-4 years historically.", severity: "high" },
      { title: "Sequence-of-Returns Risk", detail: "If near retirement, a crash could permanently impact your retirement timeline and income.", severity: "high" },
      { title: "Emotional Decision-Making", detail: "Market drops often trigger panic selling, which locks in losses and misses the recovery.", severity: "medium" },
    )
    opportunities.push(
      { title: "Dollar-Cost Averaging Benefit", detail: "Continued contributions during a downturn buy more shares at lower prices, enhancing long-term returns.", impact: "high" },
      { title: "Tax-Loss Harvesting", detail: "Losses in taxable accounts can offset gains and reduce your tax bill by up to $3,000/year.", impact: "medium" },
      { title: "Rebalancing Opportunity", detail: "A crash creates a natural rebalancing moment to buy undervalued asset classes.", impact: "medium" },
    )
    action_items.push(
      { action: "Maintain regular contributions — do not pause during downturns", priority: "high", category: "contribution" },
      { action: "Review asset allocation to ensure it matches your risk tolerance", priority: "high", category: "allocation" },
      { action: "Consider tax-loss harvesting in taxable brokerage accounts", priority: "medium", category: "tax" },
    )
    key_factors = ["Market decline magnitude", "Recovery timeline", "Continued contributions"]
  } else if (scenario.includes("stop")) {
    risks.push(
      { title: "Lost Employer Match", detail: "Stopping contributions means forfeiting free money from employer matching — typically 3-6% of salary.", severity: "high" },
      { title: "Irreplaceable Compounding Time", detail: "Each year without contributions permanently reduces your retirement nest egg. Time in market cannot be recovered.", severity: "high" },
    )
    opportunities.push(
      { title: "Build Emergency Reserves", detail: "Redirecting funds to build a 3-6 month emergency fund can provide financial stability.", impact: "medium" },
      { title: "Resume When Ready", detail: "Contributions can be restarted at any time, and catch-up contributions are available after age 50.", impact: "medium" },
    )
    action_items.push(
      { action: "If possible, contribute at least enough to capture full employer match", priority: "high", category: "contribution" },
      { action: "Set a specific date to resume full contributions", priority: "high", category: "planning" },
      { action: "Explore whether a Roth conversion during lower-income years makes sense", priority: "low", category: "tax" },
    )
    key_factors = ["Lost employer match", "Reduced compounding", "Lower future balance"]
  } else {
    risks.push(
      { title: "Projection Uncertainty", detail: "Actual market returns may differ significantly from the assumed 7% annual average used in this projection.", severity: "medium" },
      { title: "Inflation Erosion", detail: "Even with positive returns, inflation at 2.5%+ annually reduces the real purchasing power of your savings.", severity: "low" },
    )
    opportunities.push(
      { title: "Dollar-Cost Averaging", detail: "Consistent investing through regular contributions smooths out market volatility over time.", impact: "medium" },
      { title: "Time in Market Advantage", detail: "Historically, staying invested outperforms trying to time market entries and exits.", impact: "high" },
    )
    action_items.push(
      { action: "Review your portfolio allocation annually to stay on track", priority: "medium", category: "allocation" },
      { action: "Consider increasing contributions by 1% each year", priority: "medium", category: "contribution" },
    )
    key_factors = ["Market return assumptions", "Contribution consistency", "Time horizon"]
  }

  return {
    projection: {
      total_value: projectedTotal,
      total_change: totalChange,
      total_change_percent: +totalChangePercent.toFixed(2),
      accounts: projectedAccounts,
      holdings: projectedHoldings,
    },
    assumptions: {
      market_return_annual: 0.07,
      inflation_rate: 0.025,
      contribution_limit_401k: 23000,
      contribution_limit_ira: 7000,
    },
    headline,
    summary,
    key_factors,
    risks,
    opportunities,
    action_items,
  }
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

// ─── AI Portfolio Insight (mock) ────────────────────────────────────────────
// Mirrors backend/data/market_reference.json so mock-mode metrics/prose stay
// consistent with the real synthetic-provider output.
const MOCK_FUND_PROFILES: Record<string, FundProfile> = {
  VTI: { symbol: "VTI", name: "Vanguard Total Stock Market ETF", asset_class: "equity_us", category: "Large Blend", expense_ratio: 0.0003, yield_pct: 1.3, avg_return_5y_pct: 14.2, net_assets_usd: 1650000000000, top_sector: "Technology", top_sector_pct: 32.1, description: "Broad exposure to the entire U.S. stock market, from large-cap to small-cap.", source: "Sage Synthetic Reference Bundle", as_of: "2025-06-30" },
  BND: { symbol: "BND", name: "Vanguard Total Bond Market ETF", asset_class: "bond", category: "Intermediate Core Bond", expense_ratio: 0.0003, yield_pct: 3.9, avg_return_5y_pct: 0.4, net_assets_usd: 340000000000, top_sector: "U.S. Treasury", top_sector_pct: 45.0, description: "Broad exposure to U.S. investment-grade bonds, including Treasuries, corporates, and mortgage-backed securities.", source: "Sage Synthetic Reference Bundle", as_of: "2025-06-30" },
  VXUS: { symbol: "VXUS", name: "Vanguard Total International Stock ETF", asset_class: "equity_intl", category: "Foreign Large Blend", expense_ratio: 0.0005, yield_pct: 2.9, avg_return_5y_pct: 7.8, net_assets_usd: 480000000000, top_sector: "Financials", top_sector_pct: 19.4, description: "Broad exposure to developed and emerging international equity markets outside the U.S.", source: "Sage Synthetic Reference Bundle", as_of: "2025-06-30" },
  VGT: { symbol: "VGT", name: "Vanguard Information Technology ETF", asset_class: "equity_us", category: "Technology", expense_ratio: 0.0009, yield_pct: 0.6, avg_return_5y_pct: 21.5, net_assets_usd: 90000000000, top_sector: "Technology", top_sector_pct: 98.5, description: "Concentrated exposure to U.S. technology companies including software, hardware, and semiconductor firms.", source: "Sage Synthetic Reference Bundle", as_of: "2025-06-30" },
  VWO: { symbol: "VWO", name: "Vanguard FTSE Emerging Markets ETF", asset_class: "equity_intl", category: "Diversified Emerging Markets", expense_ratio: 0.0007, yield_pct: 2.7, avg_return_5y_pct: 5.1, net_assets_usd: 85000000000, top_sector: "Financials", top_sector_pct: 24.6, description: "Exposure to large- and mid-cap stocks in emerging market countries.", source: "Sage Synthetic Reference Bundle", as_of: "2025-06-30" },
  VTIP: { symbol: "VTIP", name: "Vanguard Short-Term Inflation-Protected Securities ETF", asset_class: "bond", category: "Inflation-Protected Bond", expense_ratio: 0.0004, yield_pct: 2.0, avg_return_5y_pct: 2.6, net_assets_usd: 19000000000, top_sector: "U.S. Treasury (TIPS)", top_sector_pct: 100.0, description: "Short-duration U.S. Treasury Inflation-Protected Securities for real-return protection.", source: "Sage Synthetic Reference Bundle", as_of: "2025-06-30" },
  VGSLX: { symbol: "VGSLX", name: "Vanguard Real Estate Index Fund Admiral Shares", asset_class: "real_estate", category: "Real Estate", expense_ratio: 0.0013, yield_pct: 3.5, avg_return_5y_pct: 5.9, net_assets_usd: 68000000000, top_sector: "Specialized REITs", top_sector_pct: 38.2, description: "Diversified exposure to U.S. real estate investment trusts (REITs).", source: "Sage Synthetic Reference Bundle", as_of: "2025-06-30" },
  VMFXX: { symbol: "VMFXX", name: "Vanguard Federal Money Market Fund", asset_class: "cash", category: "Money Market", expense_ratio: 0.0011, yield_pct: 4.25, avg_return_5y_pct: 2.1, net_assets_usd: 300000000000, top_sector: "U.S. Government Repurchase Agreements", top_sector_pct: 60.0, description: "Cash-equivalent holdings of short-term U.S. government securities and repurchase agreements.", source: "Sage Synthetic Reference Bundle", as_of: "2025-06-30" },
}

const MOCK_MACRO_SNAPSHOT: MacroSnapshot = {
  treasury_10y_yield_pct: 4.2,
  treasury_2y_yield_pct: 4.0,
  fed_funds_rate_pct: 4.5,
  cpi_yoy_pct: 2.7,
  sp500_ytd_return_pct: 6.2,
  source: "Sage Synthetic Reference Bundle",
  as_of: "2025-06-30",
}

function mockAssetClassFor(symbol: string, sector: string): string {
  const known = MOCK_FUND_PROFILES[symbol]
  if (known) return known.asset_class
  const s = sector.toLowerCase()
  if (s.includes("bond") || s.includes("fixed income") || s.includes("inflation")) return "bond"
  if (s.includes("cash") || s.includes("money market")) return "cash"
  if (s.includes("real estate") || s.includes("reit")) return "real_estate"
  if (s.includes("international") || s.includes("emerging")) return "equity_intl"
  return "equity_us"
}

export function generateMockPortfolioInsight(
  request: PortfolioInsightRequest
): PortfolioInsightResponse {
  const { profile_id, current_portfolio } = request
  const profile = mockUserProfiles.find((p) => p.id === profile_id) ?? mockUserProfiles[0]
  const { holdings, total_value } = current_portfolio

  let weightedExpenseRatio = 0
  let weightedYield = 0
  let equityPct = 0
  let bondPct = 0
  let cashPct = 0
  let intlPct = 0
  let realEstatePct = 0
  let topSector = ""
  let topSectorPct = 0

  for (const h of holdings) {
    const weight = total_value > 0 ? h.allocation / 100 : 0
    const fund = MOCK_FUND_PROFILES[h.symbol]
    weightedExpenseRatio += (fund?.expense_ratio ?? 0.0008) * weight
    weightedYield += (fund?.yield_pct ?? 1.5) * weight

    const assetClass = mockAssetClassFor(h.symbol, h.sector)
    if (assetClass === "bond") bondPct += h.allocation
    else if (assetClass === "cash") cashPct += h.allocation
    else if (assetClass === "real_estate") realEstatePct += h.allocation
    else {
      equityPct += h.allocation
      if (assetClass === "equity_intl") intlPct += h.allocation
    }

    if (h.allocation > topSectorPct) {
      topSectorPct = h.allocation
      topSector = h.sector
    }
  }

  const yearsToRetirement = Math.max(0, profile.target_retire_age - profile.age)
  const glidepathEquityTarget = Math.max(0, Math.min(100, 110 - profile.age))
  const equityVsGlidepathDelta = +(equityPct - glidepathEquityTarget).toFixed(1)
  const targetNestEgg = (profile.target_monthly_income * 12) / 0.04
  const targetFundGap = Math.max(0, targetNestEgg - total_value)

  const metrics: PortfolioMetrics = {
    total_value,
    holdings_count: holdings.length,
    weighted_expense_ratio: +weightedExpenseRatio.toFixed(5),
    weighted_yield: +weightedYield.toFixed(2),
    equity_pct: +equityPct.toFixed(1),
    bond_pct: +bondPct.toFixed(1),
    cash_pct: +cashPct.toFixed(1),
    intl_pct: +intlPct.toFixed(1),
    real_estate_pct: +realEstatePct.toFixed(1),
    top_sector: topSector,
    top_sector_pct: +topSectorPct.toFixed(1),
    equity_vs_glidepath_delta: equityVsGlidepathDelta,
    years_to_retirement: yearsToRetirement,
    target_fund_gap: +targetFundGap.toFixed(0),
  }

  const funds: Record<string, FundProfile> = {}
  for (const h of holdings) {
    funds[h.symbol] = MOCK_FUND_PROFILES[h.symbol] ?? {
      symbol: h.symbol,
      name: h.name,
      asset_class: mockAssetClassFor(h.symbol, h.sector),
      category: h.sector,
      expense_ratio: 0.0008,
      yield_pct: 1.5,
      avg_return_5y_pct: 8.0,
      net_assets_usd: 0,
      top_sector: h.sector,
      top_sector_pct: 100,
      description: "Synthetic placeholder profile (symbol not in the curated reference bundle).",
      source: "Sage Synthetic Reference Bundle (fallback)",
      as_of: "2025-06-30",
    }
  }

  const isConservative = profile.risk_appetite === "low"
  const isAggressive = profile.risk_appetite === "high"
  const equityGapAbs = Math.abs(equityVsGlidepathDelta)
  const equityTooLow = equityVsGlidepathDelta < -5
  const equityTooHigh = equityVsGlidepathDelta > 5

  const score = Math.round(
    Math.max(
      45,
      Math.min(
        96,
        88 -
          equityGapAbs * 0.6 -
          (metrics.weighted_expense_ratio > 0.002 ? 8 : 0) -
          (targetFundGap > total_value ? 6 : 0) -
          (topSectorPct > 45 ? 5 : 0)
      )
    )
  )
  const letter: InsightGrade["letter"] = score >= 90 ? "A" : score >= 78 ? "B" : score >= 65 ? "C" : score >= 50 ? "D" : "F"

  const headline = equityTooLow
    ? "Low-cost, diversified, but leaning conservative for the horizon"
    : equityTooHigh
    ? "Growth-oriented and low-cost, but volatility could run ahead of risk tolerance"
    : "Well-balanced, low-cost portfolio broadly on track"

  const review = [
    `This is a ${holdings.length}-holding portfolio worth ${formatCurrency(total_value)} for a ${profile.age}-year-old with ${profile.risk_appetite} risk tolerance. The mix is ${metrics.equity_pct}% equity (${metrics.intl_pct}% international), ${metrics.bond_pct}% bonds, ${metrics.cash_pct}% cash, and ${metrics.real_estate_pct}% real estate, giving it several distinct return and defense engines rather than a single bet.`,
    `Costs are ${metrics.weighted_expense_ratio < 0.001 ? "excellent" : metrics.weighted_expense_ratio < 0.003 ? "reasonable" : "on the higher side"}: the weighted expense ratio is ${(metrics.weighted_expense_ratio * 100).toFixed(3)}%. The largest single sector is ${metrics.top_sector} at ${metrics.top_sector_pct}% of assets${topSectorPct > 40 ? ", which is a meaningful concentration to be aware of" : ", which is a reasonable single-position weight"}.`,
    `Versus the age-based 110-minus-age glidepath, equity exposure is ${equityVsGlidepathDelta >= 0 ? `${equityVsGlidepathDelta} points above` : `${Math.abs(equityVsGlidepathDelta)} points below`} the heuristic target, over a ${yearsToRetirement}-year horizon to the stated retirement age. ${targetFundGap > 0 ? `There is still a ${formatCurrency(targetFundGap)} gap to the 4%-rule nest-egg target implied by the $${profile.target_monthly_income}/month goal.` : "The portfolio has already reached the 4%-rule nest-egg target implied by the stated monthly income goal."}`,
  ]

  const factorsFor: InsightFactorFor[] = [
    {
      title: "Low fund costs",
      detail: `The weighted expense ratio is only ${(metrics.weighted_expense_ratio * 100).toFixed(3)}%, which preserves more of the portfolio's return over time.`,
      weight: metrics.weighted_expense_ratio < 0.001 ? "high" : "medium",
    },
    {
      title: "Diversified asset mix",
      detail: `The portfolio spans equity, bonds, cash, and real estate (${metrics.equity_pct}/${metrics.bond_pct}/${metrics.cash_pct}/${metrics.real_estate_pct}%), reducing reliance on any single asset class.`,
      weight: "medium",
    },
  ]
  if (metrics.intl_pct > 10) {
    factorsFor.push({
      title: "International diversification",
      detail: `${metrics.intl_pct}% of the portfolio is allocated internationally, reducing dependence on U.S.-only equity outcomes.`,
      weight: "medium",
    })
  }

  const factorsAgainst: InsightFactorAgainst[] = []
  if (targetFundGap > 0) {
    factorsAgainst.push({
      title: "Retirement income gap remains",
      detail: `The portfolio is ${formatCurrency(targetFundGap)} short of the 4%-rule target nest egg needed to support the stated monthly income goal.`,
      severity: targetFundGap > total_value ? "high" : "medium",
    })
  }
  if (equityTooLow) {
    factorsAgainst.push({
      title: "Conservative equity posture",
      detail: `Equity allocation is ${equityGapAbs} percentage points below the age-based glidepath, which may limit long-term growth over the ${yearsToRetirement}-year horizon.`,
      severity: "medium",
    })
  }
  if (equityTooHigh && !isAggressive) {
    factorsAgainst.push({
      title: "Equity exposure above risk tolerance",
      detail: `Equity allocation is ${equityGapAbs} percentage points above the glidepath while the stated risk tolerance is ${profile.risk_appetite}, which may expose the portfolio to more volatility than intended.`,
      severity: "medium",
    })
  }
  if (topSectorPct > 45) {
    factorsAgainst.push({
      title: "Sector concentration",
      detail: `${topSector} makes up ${topSectorPct}% of the portfolio, which is a meaningful single-sector concentration.`,
      severity: "medium",
    })
  }
  if (factorsAgainst.length === 0) {
    factorsAgainst.push({
      title: "Minor diversification refinement possible",
      detail: "No material red flags were found; the portfolio could still benefit from routine rebalancing as markets drift.",
      severity: "low",
    })
  }

  const verdict: InsightSuitability["verdict"] =
    equityGapAbs <= 5 && targetFundGap <= total_value * 0.5
      ? "well_suited"
      : equityGapAbs <= 12
      ? "mostly_suited"
      : "needs_adjustment"

  const recommendations: InsightRecommendation[] = []
  if (equityTooLow) {
    recommendations.push({
      action: "Consider increasing equity exposure gradually toward the age-based glidepath",
      priority: "high",
      category: "risk",
      rationale: `Equity is currently ${equityGapAbs} points below the 110-minus-age benchmark, which may limit growth needed to close the retirement gap.`,
    })
  }
  if (equityTooHigh && !isAggressive) {
    recommendations.push({
      action: "Consider trimming equity exposure toward the age-based glidepath",
      priority: "medium",
      category: "risk",
      rationale: `Equity is currently ${equityGapAbs} points above the glidepath relative to a ${profile.risk_appetite} risk tolerance.`,
    })
  }
  if (targetFundGap > 0) {
    recommendations.push({
      action: `Raise annual savings if possible to narrow the ${formatCurrency(targetFundGap)} nest-egg gap`,
      priority: "high",
      category: "income",
      rationale: "The current portfolio still falls short of the 4%-rule target needed to support the stated monthly income goal.",
    })
  }
  recommendations.push({
    action: "Keep using low-cost index funds and monitor for fee creep",
    priority: "low",
    category: "cost",
    rationale: `The ${(metrics.weighted_expense_ratio * 100).toFixed(3)}% weighted expense ratio is a meaningful long-term advantage worth preserving.`,
  })

  return {
    headline,
    review,
    grade: {
      letter,
      score,
      rationale: `The grade reflects ${(metrics.weighted_expense_ratio * 100).toFixed(3)}% costs, a ${equityGapAbs}-point equity-vs-glidepath gap, and ${targetFundGap > 0 ? `a remaining ${formatCurrency(targetFundGap)} nest-egg shortfall` : "an on-track nest-egg trajectory"}.`,
    },
    factors_for: factorsFor,
    factors_against: factorsAgainst,
    suitability: {
      verdict,
      detail: `The portfolio is ${verdict === "well_suited" ? "well aligned" : verdict === "mostly_suited" ? "mostly aligned" : "in need of some adjustment"} for a ${profile.age}-year-old with ${profile.risk_appetite} risk tolerance and a ${yearsToRetirement}-year horizon.`,
      risk_alignment: `${isConservative ? "Conservative" : isAggressive ? "Aggressive" : "Medium"} risk tolerance vs. ${metrics.equity_pct}% equity / ${metrics.cash_pct}% cash allocation.`,
      horizon_alignment: `${equityGapAbs <= 5 ? "Close to" : equityVsGlidepathDelta < 0 ? "Below" : "Above"} the age-based equity glidepath by ${equityGapAbs} percentage points.`,
      income_alignment: targetFundGap > 0 ? `Not yet on track for the stated $${profile.target_monthly_income}/month target; ${formatCurrency(targetFundGap)} gap remains.` : `On track for the stated $${profile.target_monthly_income}/month target under the 4% rule.`,
    },
    recommendations,
    metrics,
    market_context: {
      provider: "synthetic",
      funds,
      macro: MOCK_MACRO_SNAPSHOT,
    },
    data_sources: ["Sage Synthetic Reference Bundle"],
    generated_at: new Date().toISOString(),
    degraded: false,
    disclaimer:
      "This AI-generated insight is for educational purposes only and is not personalized financial, investment, or tax advice. Fund and market data are synthetic/illustrative unless otherwise noted. Consult a licensed financial advisor before making investment decisions.",
  }
}

// Mock API responses
export const mockApiResponses = {
  health: {
    status: "healthy",
    agent_id: "mock-agent-12345",
  } as HealthResponse,

  scenarios: {
    scenarios: mockQuickScenarios,
  } as ScenariosResponse,

  profiles: mockUserProfiles,
}
