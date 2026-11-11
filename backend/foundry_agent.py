"""
Foundry Agent Service integration.

This module owns every interaction with Azure AI Foundry: it registers a real
prompt agent (via the current Agent Service API — Agents (classic) is
deprecated and retires 2026-03-31), and exposes a small run/stream surface
that main.py's existing thread-shaped helpers delegate to. One agent, one
Foundry project, backs built-in chat, the portfolio insight feature, and
(via backend/voice/realtime_client.py) Voice Live.

Endpoint format: https://<resource>.services.ai.azure.com/api/projects/<project>
Runs expire 10 minutes after creation, so every tool-call loop here is bounded.
"""

import json
import os
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from azure.identity import DefaultAzureCredential

try:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import FunctionTool, PromptAgentDefinition

    FOUNDRY_SDK_AVAILABLE = True
except ImportError:
    FOUNDRY_SDK_AVAILABLE = False

MAX_TOOL_ITERATIONS = 6

# ─── System instructions (single source of truth for chat, insight, and voice) ──
SYSTEM_INSTRUCTIONS = """
You are Sage, a retirement planning assistant. For every scenario request you must:
1. Analyze the user's financial situation and retirement goals
2. Calculate realistic projections using the provided data, using the code interpreter tool to calculate financial metrics.
3. Return structured JSON that matches the AnalysisOutput schema EXACTLY. The schema is provided below.
4. Provide actionable recommendations and product allocations, using the get_product_catalogue function to fetch investment products.
5. Include follow-up questions and alternative scenarios

ALWAYS use the code interpreter and product catalogue tools for data analysis and product recommendations.

Use the get_product_catalogue function for investment product data.
Always provide specific numbers and percentages in your analysis based on the output from the code interpreter tool.


CRITICAL: Your response must be a single, well-formed JSON object with a schema that matches the sample AnalysisOutput below. Make sure retirement income is calculated accurately and is not zero.

IMPORTANT: The "cashflows" array must contain objects with EXACTLY these two fields:
- "year": integer (ONLY these six values in this order: 0, 5, 10, 15, 20, 25)
- "end_assets": float (total assets at end of that year)

CONSISTENCY REQUIREMENT:
The cashflow array and metrics (especially metrics.time_horizon_years) must be calculated using the same logic and assumptions, based on the projected retirement income for the scenario. Asset depletion in the cashflow array must match the time horizon in the metrics. If other income sources (e.g., Social Security, pensions) are included in the retirement income, they must be reflected in both metrics and cashflow calculations.

CRITICAL CASHFLOW HORIZON RULES (STRICT):
1. Always produce a 25-year projection horizon represented by EXACTLY 6 cashflow points at 5-year intervals: years 0, 5, 10, 15, 20, 25.
2. Do NOT include any years beyond 25 or intermediate years (e.g., no year 30, 1, 3, 7, etc.).
3. Do NOT omit any required year; if assets are depleted earlier, continue listing the remaining required years with end_assets reflecting projected residual assets (can be 0 once depleted, never negative).
4. Never output more or fewer than 6 cashflow objects. Never reorder the sequence.
5. If you internally model annually, aggregate/record the end-of-period asset value for the specified 5-year checkpoints only.

If the plan horizon is naturally shorter than 25 years (e.g., assets exhaust in year 18), you MUST still output points for 20 and 25 with end_assets equal to the projected value (0 if depleted). This consistency enables downstream visualization and comparison.

Field semantics & sign conventions:
Unless noted, deltas use: scenario - baseline (positive = improvement toward goal). EXCEPTION: retirement_income_delta = metrics.monthly_income - target_monthly_income (progress vs goal, not vs baseline). Target goal = scenario.target_monthly_income.

metrics.monthly_income: Scenario projected sustainable monthly retirement income (whole dollars).
metrics.success_rate_pct: Scenario probability (0-100) of meeting or exceeding target_monthly_income for the planned retirement horizon.
metrics.risk_level: Qualitative risk classification for the scenario (e.g., low / medium / high).
metrics.flexibility (optional): Short descriptor of withdrawal or adjustment flexibility.
metrics.time_horizon_years: Scenario expected sustainable income duration (years until asset depletion or planned horizon).

deltas.additional_savings_monthly: Extra monthly savings required for the scenario vs current plan (never negative; 0 if no increase needed).
deltas.retirement_income_monthly: Baseline projected sustainable monthly retirement income BEFORE applying changes (absolute, non-negative; NOT a delta or shortfall figure).
deltas.retirement_income_delta: Scenario progress vs target = metrics.monthly_income - target_monthly_income (positive = above target, negative = shortfall, 0 if within ±0.5). (This is the only delta not using scenario - baseline.)
deltas.success_rate_delta_pct: Scenario success_rate_pct - baseline success rate (may be negative).
deltas.extra_years_income_duration: metrics.time_horizon_years - baseline income duration (positive = longer, negative = shorter).

Consistency rules (must hold after rounding; allow ±1 tolerance for percentage/year values due to rounding):
retirement_income_delta = metrics.monthly_income - target_monthly_income
success_rate_delta_pct = metrics.success_rate_pct - baseline_success_rate_pct
extra_years_income_duration = metrics.time_horizon_years - baseline_income_duration_years
additional_savings_monthly = max(0, scenario_monthly_savings - baseline_monthly_savings)

Rounding:
Currency to nearest whole dollar; percentages to nearest whole percent; years to nearest whole year. Clamp success_rate_pct to [0,100].

Do not:
- Invert signs.
- Leave required numeric fields blank.
- Use narrative text in numeric fields.

Provide concise considerations explaining major negative deltas or trade-offs.

Example JSON structure:
{
  "scenario": {
    "id": "scenario_id",
    "name": "User Name", 
    "age": 40,
    "current_cash": 50000,
    "investment_assets": 230000,
    "yearly_savings_rate": 0.15,
    "salary": 96000,
    "portfolio": {"stocks": 0.7, "bonds": 0.3},
    "risk_appetite": "medium",
    "target_retire_age": 65,
    "target_monthly_income": 4000,
    "description": "..."
  },
  "recommended_changes": {
    "savings_rate": 0.20,
    "portfolio_rebalancing": {"stocks": 0.65, "bonds": 0.35},
    "additional_products": ["product1", "product2"]
  },
  "predictions": {
        "metrics": {
            "monthly_income": 4200,
            "success_rate_pct": 85,
            "risk_level": "medium",
            "flexibility": "moderate",
            "time_horizon_years": 25
        },
        "deltas": {
            "additional_savings_monthly": 400,
            "retirement_income_monthly": 4000,
            "retirement_income_delta": 200,
            "success_rate_delta_pct": 15,
            "extra_years_income_duration": 3
        },
    "products": [
      {
        "name": "Balanced Portfolio",
        "allocation": 0.6,
        "exp_return": 0.07,
        "risk_rating": "medium",
        "asset_class": "mixed"
      }
    ],
    "cashflows": [
      {"year": 0, "end_assets": 280000},
      {"year": 5, "end_assets": 450000},
      {"year": 10, "end_assets": 620000},
      {"year": 15, "end_assets": 780000},
      {"year": 20, "end_assets": 920000},
      {"year": 25, "end_assets": 1050000}
    ]
  },
  "follow_ups": [
    "What if I retired 2 years earlier?",
    "How would a market crash affect my plan?"
  ],
  "alternatives": [
    "Increasing savings rate to 20%",
    "Considering more conservative portfolio"
  ],
  "considerations": "Your plan shows good fundamentals but consider increasing your emergency fund."
}

Do not include any explanatory text before or after the JSON. The JSON must be complete and valid.
Each cashflow object must have ONLY "year" and "end_assets" fields - no other fields like "inflation" or "monthly_income".
"""


def get_product_catalogue(risk: str = "medium") -> str:
    """Query investment product catalogue by risk level."""
    # Imported lazily to avoid a circular import with main.py at module load time.
    from main import INVESTMENT_PRODUCTS

    catalogue = INVESTMENT_PRODUCTS.get("products_by_risk", {}).get(
        risk, INVESTMENT_PRODUCTS.get("products_by_risk", {}).get("medium", [])
    )
    return json.dumps({"products": catalogue})


# ─── Tool registry: name -> (python callable, FunctionTool schema) ──────────
TOOL_REGISTRY: Dict[str, Callable[..., str]] = {
    "get_product_catalogue": get_product_catalogue,
}


def _function_tools() -> List["FunctionTool"]:
    return [
        FunctionTool(
            name="get_product_catalogue",
            description="Query investment product catalogue by risk level.",
            parameters={
                "type": "object",
                "properties": {
                    "risk": {
                        "type": "string",
                        "description": "Risk level: low, medium, or high",
                        "enum": ["low", "medium", "high"],
                    }
                },
                "required": ["risk"],
                "additionalProperties": False,
            },
            strict=True,
        )
    ]


def _dispatch_tool(name: str, arguments_json: str) -> str:
    """Execute a registered tool by name and return its JSON string result."""
    func = TOOL_REGISTRY.get(name)
    if func is None:
        return "{}"
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError:
        args = {}
    try:
        return func(**args)
    except TypeError:
        # Tolerate tools that take a single positional-ish kwarg with a default,
        # matching the previous Chat Completions call sites' leniency.
        return func(args.get("risk", "medium")) if "risk" in args else func()


# ─── Client + agent registration ────────────────────────────────────────────
_project_client: Optional["AIProjectClient"] = None
_project_client_initialized = False
_registered_agent = None  # AgentVersionDetails once register_agent() succeeds


def get_project_client() -> Optional["AIProjectClient"]:
    """Return a memoized AIProjectClient, or None if unconfigured/unavailable.
    Mirrors the existing graceful-degradation behaviour: an unset endpoint
    means the app starts in limited mode rather than failing to boot."""
    global _project_client, _project_client_initialized
    if _project_client_initialized:
        return _project_client

    _project_client_initialized = True
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
    if not endpoint or not FOUNDRY_SDK_AVAILABLE:
        return None
    try:
        _project_client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    except Exception as e:
        print(f"Failed to create Foundry project client: {e}")
        _project_client = None
    return _project_client


def register_agent():
    """Idempotently register (or update) the Sage prompt agent on Foundry
    Agent Service. Safe to call multiple times — each call creates a new
    immutable version under the same agent name. Returns the AgentVersionDetails
    object (with .name/.version), or None if Foundry is unconfigured."""
    global _registered_agent
    project = get_project_client()
    if project is None:
        return None

    agent_name = os.environ.get("FOUNDRY_AGENT_NAME", "sage-retirement-agent")
    model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4")

    try:
        version = project.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=model,
                instructions=SYSTEM_INSTRUCTIONS,
                tools=_function_tools(),
            ),
        )
        _registered_agent = version
        print(f"Foundry agent registered: {version.name} v{version.version}")
        return version
    except Exception as e:
        print(f"FATAL: Could not register Foundry agent: {e}")
        print("Backend will start in limited mode - voice endpoints available, chat disabled")
        return None


def get_registered_agent():
    """Return the last successfully registered agent version, if any."""
    return _registered_agent


def create_conversation() -> Optional[str]:
    """Create a new server-side Foundry conversation and return its id."""
    project = get_project_client()
    if project is None:
        return None
    openai_client = project.get_openai_client()
    conversation = openai_client.conversations.create()
    return conversation.id


def _agent_reference() -> Dict[str, str]:
    agent_name = os.environ.get("FOUNDRY_AGENT_NAME", "sage-retirement-agent")
    return {"name": agent_name, "type": "agent_reference"}


def run_agent(conversation_id: str, user_input: str) -> str:
    """Run a single turn against the registered agent, with a bounded
    function-call loop, and return the final text. Equivalent to the old
    Chat-Completions-based `_run_assistant_sync`, but backed by a real
    Foundry prompt agent and server-side conversation state."""
    project = get_project_client()
    if project is None:
        raise RuntimeError("Foundry project client is not configured")
    openai_client = project.get_openai_client()

    next_input: Any = user_input
    final_text = ""
    for _ in range(MAX_TOOL_ITERATIONS):
        response = openai_client.responses.create(
            input=next_input,
            conversation=conversation_id,
            extra_body={"agent_reference": _agent_reference()},
        )
        function_calls = [item for item in response.output if item.type == "function_call"]
        if not function_calls:
            final_text = response.output_text or ""
            break

        tool_outputs = []
        for call in function_calls:
            result = _dispatch_tool(call.name, call.arguments)
            tool_outputs.append(
                {"type": "function_call_output", "call_id": call.call_id, "output": result}
            )
        next_input = tool_outputs

    return final_text


def stream_agent(conversation_id: str, user_input: str) -> Iterator[Tuple[str, str]]:
    """Generator: run a streaming turn against the registered agent, with a
    bounded function-call loop. Yields ("content", text_delta) and
    ("status", status_message) tuples — the exact contract
    `_stream_chat_with_tools` already promises to the frontend SSE layer."""
    project = get_project_client()
    if project is None:
        raise RuntimeError("Foundry project client is not configured")
    openai_client = project.get_openai_client()

    next_input: Any = user_input
    for _ in range(MAX_TOOL_ITERATIONS):
        stream = openai_client.responses.create(
            input=next_input,
            conversation=conversation_id,
            extra_body={"agent_reference": _agent_reference()},
            stream=True,
        )
        final_response = None
        for event in stream:
            if event.type == "response.output_text.delta":
                yield ("content", event.delta)
            elif event.type == "response.completed":
                final_response = event.response

        if final_response is None:
            break

        function_calls = [item for item in final_response.output if item.type == "function_call"]
        if not function_calls:
            break

        yield ("status", "Fetching investment data...")
        tool_outputs = []
        for call in function_calls:
            result = _dispatch_tool(call.name, call.arguments)
            tool_outputs.append(
                {"type": "function_call_output", "call_id": call.call_id, "output": result}
            )
        next_input = tool_outputs
        yield ("status", "Calculating retirement projections...")
