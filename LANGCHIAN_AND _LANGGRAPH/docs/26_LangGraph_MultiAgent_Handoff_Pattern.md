# LangGraph Multi-Agent Handoff Pattern — Deep Dive

> Builds on [08_langchain_output_parsers.md](08_langchain_output_parsers.md) (`with_structured_output()`) and [20_langgraph_conditional_edges_and_routing.md](20_langgraph_conditional_edges_and_routing.md) (`add_conditional_edges`, `Literal`-typed routers). Walks through [agent_handsoff.py](../agent_handsoff.py), which builds a customer-service system with a triage agent that hands off to one of several specialists — a named pattern ("supervisor/router" multi-agent orchestration) that wasn't previously documented despite having working code.

## Table of Contents
1. [The Big Idea](#1-the-big-idea)
2. [Why Not Just One Big Prompt?](#2-why-not-just-one-big-prompt)
3. [The Handoff Decision — Structured Output as a Router](#3-the-handoff-decision--structured-output-as-a-router)
4. [Shared State Across Agents](#4-shared-state-across-agents)
5. [Specialist Agents Read the Same Context](#5-specialist-agents-read-the-same-context)
6. [Wiring It Together](#6-wiring-it-together)
7. [How This Differs from the ReAct Tool-Calling Loop](#7-how-this-differs-from-the-react-tool-calling-loop)
8. [Common Mistakes](#8-common-mistakes)
9. [Interview Questions](#9-interview-questions)
10. [Quick Revision](#10-quick-revision)

---

## 1. The Big Idea

A single LLM with one giant system prompt covering sales, billing, and technical support has to be good at all three simultaneously — its instructions balloon, and it has no clean way to specialize its tone or knowledge per domain. The **handoff pattern** splits this into a **triage agent** that only does one job — classify and route — plus several **specialist agents**, each with a narrow, focused system prompt for its own domain.

```
                         ┌──────────────┐
        customer ──────▶ │ triage_agent │
                         └──────┬───────┘
                                │ (structured decision: where to route)
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        ┌───────────┐    ┌────────────┐    ┌────────────┐
        │sales_agent│    │support_agent│   │billing_agent│
        └───────────┘    └────────────┘    └────────────┘
              │                 │                 │
              └─────────────────┴─────────────────┘
                                ▼
                               END
```

This is `agent_handsoff.py`'s `create_customer_service_system()`. The triage node never answers domain questions itself (except trivial ones it can resolve directly) — its only job is deciding **who should**.

---

## 2. Why Not Just One Big Prompt?

| | Single mega-prompt | Triage + specialists |
|---|---|---|
| Prompt focus | Must cover sales + billing + support simultaneously | Each agent's prompt only covers its own domain |
| Tone | One tone has to fit every situation | Sales can be persuasive, support patient, billing precise |
| Maintainability | Adding a new domain means editing one sprawling prompt | Add a new node + one routing branch |
| Debuggability | Hard to tell *why* a bad answer happened | Easy to tell which agent produced which message (`[Sales]`, `[Support]`, `[Billing]` prefixes in `agent_handsoff.py`) |

This is the same "smaller pieces, greater control" argument as decomposing a chain into steps ([07_Chains.md](07_Chains.md)) or a RAG pipeline into stages ([16_rag.md](16_rag.md)) — the underlying model doesn't get "better," but the system around it becomes easier to reason about and extend.

---

## 3. The Handoff Decision — Structured Output as a Router

The triage node needs a *machine-readable* decision, not prose, so the graph's router can act on it deterministically. `agent_handsoff.py` uses `with_structured_output()` (see [08](08_langchain_output_parsers.md)) with a `Literal`-constrained Pydantic model:

```python
from pydantic import BaseModel, Field
from typing_extensions import Literal

class HandoffDecision(BaseModel):
    handoff_to: Literal["sales", "billing", "support", "stay", "end"] = Field(
        description="which agent to hand off to"
    )
    context: str = Field(description="key context to pass to next agent")
    reason: str = Field(description="reason to give the next agent")

handoff_llm = llm.with_structured_output(HandoffDecision)
decision = handoff_llm.invoke(messages)
```

The `Literal` constrains the model to exactly one of five valid labels — the same technique [doc 20](20_langgraph_conditional_edges_and_routing.md) uses for router return types, just applied to a *field on a Pydantic model* instead of a plain function's return annotation. This guarantees `decision.handoff_to` is always one of the five strings the router downstream knows how to handle — no risk of the model inventing an unroutable label like `"tech_support"` when the graph only wired up `"support"`.

`context` and `reason` are the payload that makes the handoff useful rather than just a label: they carry *why* this customer is being routed and *what the specialist needs to know*, so the specialist doesn't have to re-derive it from scratch.

---

## 4. Shared State Across Agents

All agents in the graph read and write the same `TypedDict` state — the handoff's "context" isn't passed as a function argument, it's written into shared state by triage and read back out by whichever specialist runs next:

```python
class HandsoffState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_agent: str
    handoff_reason: str
    context_summary: str
```

Triage's return value populates `context_summary` and `current_agent`:

```python
return {
    "current_agent": decision.handoff_to,
    "handoff_reason": decision.reason,
    "context_summary": decision.context,
    "messages": [AIMessage(content=f"[Triage] transferring to {decision.handoff_to}")],
}
```

This is the same accumulation mechanism from [21_LangGraph_Accumulated_State_Explanation.md](21_LangGraph_Accumulated_State_Explanation.md) — `messages` accumulates via `add_messages` (every node's message gets appended, so the full triage → specialist conversation is visible in the final result), while `current_agent`/`context_summary`/`handoff_reason` are plain replace-on-write fields since only the *latest* handoff decision matters, not a history of them.

---

## 5. Specialist Agents Read the Same Context

Each specialist's system prompt is built dynamically from `context_summary`, so it starts already knowing what triage learned — no re-asking the customer to repeat themselves:

```python
def sales_agent(state: HandsoffState) -> dict:
    system = f"""You are a sales specialist. Context from triage: {state.get('context_summary', 'None')}

    Help the customer with product questions and purchases.
    Be helpful and informative, not pushy."""

    response = llm.invoke([SystemMessage(content=system), *state["messages"], HumanMessage(content="Please assist me with this.")])
    return {
        "messages": [AIMessage(content=f"[Sales] {response.content}")],
        "current_agent": "sales_complete",
    }
```

`support_agent` and `billing_agent` follow the identical shape — different system prompt text, same signature: read `context_summary`, read the accumulated `messages`, respond with a domain-specific answer, tag it with a `[label]` prefix so it's traceable in a transcript, and mark `current_agent` as `"<domain>_complete"`.

---

## 6. Wiring It Together

The router is a plain function (see [doc 20](20_langgraph_conditional_edges_and_routing.md)) that reads `current_agent` and maps it onto one of the branches registered in `add_conditional_edges`:

```python
def route_from_traige(state: HandsoffState) -> str:
    agent = state["current_agent"]
    if agent in ["sales", "support", "billing"]:
        return agent
    return "end"

graph = StateGraph(HandsoffState)
graph.add_node("traige_agent", traige_agent)
graph.add_node("sales_agent", sales_agent)
graph.add_node("support_agent", support_agent)
graph.add_node("billing_agent", billing_agent)

graph.add_edge(START, "traige_agent")
graph.add_conditional_edges(
    "traige_agent", route_from_traige,
    {"sales": "sales_agent", "support": "support_agent", "billing": "billing_agent", "end": END},
)
graph.add_edge("sales_agent", END)
graph.add_edge("support_agent", END)
graph.add_edge("billing_agent", END)
```

Every specialist edges straight to `END` — this graph is a single-hop handoff (triage routes once, the specialist answers once, done). It does **not** loop back to triage for a second opinion; extending it to multi-turn handoffs (a specialist deciding "actually, this needs billing too") would mean routing specialists back through triage instead of to `END`, turning this into a cyclic graph in the sense of [22_LangGraph_Cycles_and_Loops_Deep_Dive.md](22_LangGraph_Cycles_and_Loops_Deep_Dive.md).

---

## 7. How This Differs from the ReAct Tool-Calling Loop

Both patterns route based on an LLM's decision, but they solve different problems — worth contrasting against [24_LangGraph_Tool_Calling_and_Agents.md](24_LangGraph_Tool_Calling_and_Agents.md):

| | ReAct tool-calling loop (doc 24) | Multi-agent handoff (this doc) |
|---|---|---|
| What's being chosen | *Which function to call* to gather information or take an action | *Which specialized LLM persona* should handle the rest of the conversation |
| Decision mechanism | `bind_tools()` + reading `response.tool_calls` | `with_structured_output()` + reading a `Literal` field |
| Typical shape | Cyclic — loops back to the same agent node after each tool result | Typically single-hop — one routing decision, then a terminal specialist node |
| Who "acts" | The tool (a Python function, API call, etc.) | Another LLM call, with a different system prompt |
| State carried forward | Tool results appended as `ToolMessage`s | A `context_summary` string, deliberately extracted/summarized by the router itself |

The two compose naturally: a specialist agent in a handoff system could itself be a ReAct tool-calling agent (e.g., `billing_agent` might need to call a `look_up_invoice(customer_id)` tool before answering) — nothing here prevents nesting one pattern inside a node of the other.

---

## 8. Common Mistakes

- **Letting the triage prompt answer domain questions itself.** Its only job is classification + context extraction; if it starts trying to also answer sales questions, you lose the entire benefit of specialization.
- **Not constraining the handoff label with `Literal`.** Without it, the model could return `"technical_support"` when the graph's `add_conditional_edges` mapping only knows `"support"` — an unroutable label that either errors or silently falls through to a wrong branch depending on how the router function is written.
- **Forgetting to pass `context_summary` into each specialist's prompt.** Without it, specialists re-ask the customer for information triage already extracted, defeating the purpose of routing with context.
- **Assuming this is a loop.** As wired in `agent_handsoff.py`, this graph runs triage exactly once per `invoke()` — every specialist branch dead-ends at `END`. A specialist can't currently say "actually, route this to billing too" without the graph being restructured to route back through triage.
- **Confusing structured-output routing with tool calling.** `with_structured_output()` here is being used to pick a *destination node*, not to describe a function call — don't reach for `bind_tools`/`ToolNode` (doc 24) when what you actually want is a fixed-set routing decision; `Literal` + `with_structured_output()` is simpler and sufficient.

---

## 9. Interview Questions

**Q: Why use `with_structured_output()` with a `Literal` field for the handoff decision instead of just asking the LLM to reply with a plain-text agent name?**
A: A `Literal`-constrained field guarantees the value is exactly one of the pre-registered options the router understands; free-text output could contain typos, synonyms, or extra prose that a router function would need brittle string-matching to handle correctly.

**Q: What's the role of `context_summary` in this pattern, and where does it come from?**
A: It's a short summary the triage agent extracts from the customer's message, written into shared state so the specialist that gets routed to doesn't have to re-derive it — it comes from the `context` field on the `HandoffDecision` the triage LLM returns.

**Q: How would you extend this pattern to let a specialist route to a different specialist, not just end the conversation?**
A: Route the specialist's output back through the triage node (or a lighter-weight dedicated router) instead of straight to `END`, giving the specialist a way to signal "this actually needs a different domain" — this turns the graph cyclic, following the loop patterns in [doc 22](22_LangGraph_Cycles_and_Loops_Deep_Dive.md).

**Q: What's the key difference between this handoff pattern and the ReAct tool-calling loop?**
A: The handoff pattern chooses between different LLM *personas* (each with its own system prompt) to answer a conversation, typically as a single routing hop; the ReAct loop chooses between callable *functions* to gather information or take action, typically looping back to the same LLM repeatedly until it has enough to answer.

**Q: Why does every specialist agent prefix its response with a label like `[Sales]`?**
A: It's a debugging/traceability aid — since all agents write into the same shared `messages` list, the prefix makes it possible to tell which specialist produced which message when inspecting the final transcript, without needing to track `current_agent` alongside every message.

---

## 10. Quick Revision

- **Handoff pattern** = one triage/router agent that classifies and extracts context, then routes to one of several narrow specialist agents — contrast with one mega-prompt trying to cover every domain.
- **`with_structured_output()` + `Literal`** turns the routing decision into a guaranteed-valid label the graph's `add_conditional_edges` mapping can dispatch on — no free-text parsing needed.
- **Shared `TypedDict` state** (not function arguments) is how context passes from triage to specialist — `context_summary` is written once by triage, read by whichever specialist gets routed to.
- **`messages` accumulates via `add_messages`**; `current_agent`/`context_summary`/`handoff_reason` are plain replace-on-write fields, since only the latest routing decision matters.
- **As built in `agent_handsoff.py`, this is single-hop**, not a loop — every specialist edges straight to `END`. Multi-round handoffs require routing specialists back through triage instead.
- **Distinct from the ReAct loop** ([doc 24](24_LangGraph_Tool_Calling_and_Agents.md)): this picks between LLM personas for a conversation; ReAct picks between callable functions for gathering information — the two compose (a specialist can itself be a tool-calling agent).
