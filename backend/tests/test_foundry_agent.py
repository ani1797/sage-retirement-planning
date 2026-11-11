"""
Tests for backend/foundry_agent.py -- the Foundry Agent Service integration
module that backs chat, the portfolio insight feature, and Voice Live.

Run with: uv run pytest tests/test_foundry_agent.py -v
"""

import json
from unittest.mock import MagicMock

import pytest

import foundry_agent


@pytest.fixture(autouse=True)
def reset_foundry_agent_globals(monkeypatch):
    """Every test gets a clean slate: no memoized client/agent, and no
    Foundry env vars leaking in from the developer's local .env."""
    monkeypatch.setattr(foundry_agent, "_project_client", None)
    monkeypatch.setattr(foundry_agent, "_project_client_initialized", False)
    monkeypatch.setattr(foundry_agent, "_registered_agent", None)
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_AGENT_NAME", raising=False)
    monkeypatch.delenv("MODEL_DEPLOYMENT_NAME", raising=False)
    yield


# ---------------------------------------------------------------------------
# 1. Tool schema + dispatch
# ---------------------------------------------------------------------------

def test_function_tools_schema_has_additionalProperties_false():
    """Strict function tools require additionalProperties: false, or the
    Responses API rejects the call with HTTP 400 (discovered live)."""
    tools = foundry_agent._function_tools()
    assert len(tools) == 1
    tool = tools[0]
    assert tool.strict is True
    assert tool.parameters["additionalProperties"] is False


def test_dispatch_tool_get_product_catalogue():
    result = foundry_agent._dispatch_tool("get_product_catalogue", json.dumps({"risk": "high"}))
    parsed = json.loads(result)
    assert "products" in parsed
    assert isinstance(parsed["products"], list)


def test_dispatch_tool_unknown_name_returns_empty_object():
    assert foundry_agent._dispatch_tool("not_a_real_tool", "{}") == "{}"


def test_dispatch_tool_malformed_arguments_falls_back_gracefully():
    # Malformed JSON should not raise -- args become {} and the tool still runs.
    result = foundry_agent._dispatch_tool("get_product_catalogue", "{not valid json")
    parsed = json.loads(result)
    assert "products" in parsed


# ---------------------------------------------------------------------------
# 2. Graceful degradation when Foundry is unconfigured
# ---------------------------------------------------------------------------

def test_get_project_client_returns_none_when_unconfigured():
    assert foundry_agent.get_project_client() is None


def test_get_project_client_is_memoized(monkeypatch):
    calls = {"count": 0}

    def fake_client(*args, **kwargs):
        calls["count"] += 1
        return MagicMock()

    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example.services.ai.azure.com/api/projects/test")
    monkeypatch.setattr(foundry_agent, "AIProjectClient", fake_client)
    monkeypatch.setattr(foundry_agent, "FOUNDRY_SDK_AVAILABLE", True)

    first = foundry_agent.get_project_client()
    second = foundry_agent.get_project_client()
    assert first is second
    assert calls["count"] == 1


def test_register_agent_returns_none_when_unconfigured():
    assert foundry_agent.register_agent() is None


def test_create_conversation_returns_none_when_unconfigured():
    assert foundry_agent.create_conversation() is None


def test_run_agent_raises_when_unconfigured():
    with pytest.raises(RuntimeError):
        foundry_agent.run_agent("conv-1", "hello")


def test_stream_agent_raises_when_unconfigured():
    with pytest.raises(RuntimeError):
        list(foundry_agent.stream_agent("conv-1", "hello"))


# ---------------------------------------------------------------------------
# 3. Registration idempotency (mocked AIProjectClient)
# ---------------------------------------------------------------------------

def _make_mock_project(create_version_return=None):
    project = MagicMock()
    version = create_version_return or MagicMock(name="version", version="1")
    project.agents.create_version.return_value = version
    return project, version


def test_register_agent_idempotent_calls_create_version_each_time(monkeypatch):
    project, version = _make_mock_project()
    monkeypatch.setattr(foundry_agent, "get_project_client", lambda: project)

    first = foundry_agent.register_agent()
    second = foundry_agent.register_agent()

    assert first is version
    assert second is version
    assert project.agents.create_version.call_count == 2
    assert foundry_agent.get_registered_agent() is version


def test_register_agent_returns_none_on_exception(monkeypatch):
    project = MagicMock()
    project.agents.create_version.side_effect = RuntimeError("boom")
    monkeypatch.setattr(foundry_agent, "get_project_client", lambda: project)

    assert foundry_agent.register_agent() is None


# ---------------------------------------------------------------------------
# 4. run_agent tool-call loop (mocked Responses API)
# ---------------------------------------------------------------------------

def _mock_response(output, output_text=""):
    resp = MagicMock()
    resp.output = output
    resp.output_text = output_text
    return resp


def _function_call_item(name="get_product_catalogue", arguments='{"risk": "medium"}', call_id="call_1"):
    item = MagicMock()
    item.type = "function_call"
    item.name = name
    item.arguments = arguments
    item.call_id = call_id
    return item


def test_run_agent_returns_text_with_no_tool_calls(monkeypatch):
    project = MagicMock()
    openai_client = MagicMock()
    project.get_openai_client.return_value = openai_client
    openai_client.responses.create.return_value = _mock_response(output=[], output_text="Hello!")
    monkeypatch.setattr(foundry_agent, "get_project_client", lambda: project)

    result = foundry_agent.run_agent("conv-1", "hi")
    assert result == "Hello!"
    assert openai_client.responses.create.call_count == 1


def test_run_agent_executes_tool_call_then_returns_final_text(monkeypatch):
    project = MagicMock()
    openai_client = MagicMock()
    project.get_openai_client.return_value = openai_client
    openai_client.responses.create.side_effect = [
        _mock_response(output=[_function_call_item()], output_text=""),
        _mock_response(output=[], output_text="Here is your plan."),
    ]
    monkeypatch.setattr(foundry_agent, "get_project_client", lambda: project)

    result = foundry_agent.run_agent("conv-1", "give me a plan")
    assert result == "Here is your plan."
    assert openai_client.responses.create.call_count == 2
    # Second call should have been fed the tool output, not the raw user input.
    second_call_kwargs = openai_client.responses.create.call_args_list[1].kwargs
    assert second_call_kwargs["input"][0]["type"] == "function_call_output"
    assert second_call_kwargs["input"][0]["call_id"] == "call_1"


def test_run_agent_bounded_tool_loop_terminates(monkeypatch):
    """If the agent keeps calling tools forever, run_agent must still return
    (bounded by MAX_TOOL_ITERATIONS) instead of looping indefinitely."""
    project = MagicMock()
    openai_client = MagicMock()
    project.get_openai_client.return_value = openai_client
    openai_client.responses.create.return_value = _mock_response(
        output=[_function_call_item()], output_text=""
    )
    monkeypatch.setattr(foundry_agent, "get_project_client", lambda: project)

    result = foundry_agent.run_agent("conv-1", "loop forever")
    assert result == ""  # never got a final text
    assert openai_client.responses.create.call_count == foundry_agent.MAX_TOOL_ITERATIONS


# ---------------------------------------------------------------------------
# 5. stream_agent event translation (mocked streaming Responses API)
# ---------------------------------------------------------------------------

def _stream_event(event_type, **attrs):
    ev = MagicMock()
    ev.type = event_type
    for key, value in attrs.items():
        setattr(ev, key, value)
    return ev


def test_stream_agent_yields_content_deltas_then_stops(monkeypatch):
    project = MagicMock()
    openai_client = MagicMock()
    project.get_openai_client.return_value = openai_client

    final_response = _mock_response(output=[], output_text="Hi there")
    events = [
        _stream_event("response.output_text.delta", delta="Hi"),
        _stream_event("response.output_text.delta", delta=" there"),
        _stream_event("response.completed", response=final_response),
    ]
    openai_client.responses.create.return_value = iter(events)
    monkeypatch.setattr(foundry_agent, "get_project_client", lambda: project)

    chunks = list(foundry_agent.stream_agent("conv-1", "hi"))
    assert chunks == [("content", "Hi"), ("content", " there")]


def test_stream_agent_executes_tool_call_and_continues(monkeypatch):
    project = MagicMock()
    openai_client = MagicMock()
    project.get_openai_client.return_value = openai_client

    tool_call_response = _mock_response(output=[_function_call_item()], output_text="")
    final_response = _mock_response(output=[], output_text="Done")
    openai_client.responses.create.side_effect = [
        iter([_stream_event("response.completed", response=tool_call_response)]),
        iter([
            _stream_event("response.output_text.delta", delta="Done"),
            _stream_event("response.completed", response=final_response),
        ]),
    ]
    monkeypatch.setattr(foundry_agent, "get_project_client", lambda: project)

    chunks = list(foundry_agent.stream_agent("conv-1", "give me a plan"))
    kinds = [k for k, _ in chunks]
    assert "status" in kinds
    assert ("content", "Done") in chunks
    assert openai_client.responses.create.call_count == 2
