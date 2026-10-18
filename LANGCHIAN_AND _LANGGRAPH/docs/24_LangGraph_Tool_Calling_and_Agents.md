# LangGraph Tool Calling & Agents — Deep Dive

> Builds on [05_messages.md](05_messages.md) (`ToolMessage`, message history) and [22_LangGraph_Cycles_and_Loops_Deep_Dive.md](22_LangGraph_Cycles_and_Loops_Deep_Dive.md) §6 (the agentic/ReAct loop, covered there conceptually). **No local code demonstrates this yet** — none of `agent_handsoff.py`, `research_assistant.py`, `langgraph_core.py`, or `langgraph_full.py` actually call `bind_tools`, define a `@tool`, or use `ToolNode`/`create_react_agent`, despite being the files you'd expect it in. This is the biggest real gap in the repo: "agents" in the LangChain/LangGraph sense specifically means an LLM that can call tools in a loop, and that mechanism isn't exercised anywhere yet.

## Table of Contents
1. [The Big Idea](#1-the-big-idea)
2. [Defining a Tool](#2-defining-a-tool)
3. [`bind_tools` — Giving the LLM a Menu](#3-bind_tools--giving-the-llm-a-menu)
4. [Reading a Tool Call Off the Response](#4-reading-a-tool-call-off-the-response)
5. [Executing the Tool and Feeding the Result Back](#5-executing-the-tool-and-feeding-the-result-back)
6. [`ToolNode` — LangGraph's Built-in Executor](#6-toolnode--langgraphs-built-in-executor)
7. [Wiring the Full ReAct Loop by Hand](#7-wiring-the-full-react-loop-by-hand)
8. [`create_react_agent` — The Shortcut](#8-create_react_agent--the-shortcut)
9. [Common Mistakes](#9-common-mistakes)
10. [Interview Questions](#10-interview-questions)
11. [Quick Revision](#11-quick-revision)

---

## 1. The Big Idea

Every graph built so far in this repo (`agent_handsoff.py`, `langgraph_core.py`, `human_in_loop.py`, `checkpoint.py`) has the LLM only ever doing one thing: reading messages and writing text back. It never *acts* on the outside world — it can't look up today's weather, run a calculation, query a database, or call an API. **Tool calling** is the mechanism that lets an LLM say "I need to run `get_weather(city='Paris')` before I can answer" instead of guessing or refusing.

```
Without tools:  Human ──▶ LLM ──▶ "I don't have real-time data" (guesses or refuses)

With tools:     Human ──▶ LLM ──▶ [wants to call get_weather("Paris")]
                                       │
                                  tool executes
                                       │
                          Human ◀── LLM ◀── "It's 18°C and cloudy"
```

The LLM itself never executes code. It only ever outputs *structured intent* — "call this function with these arguments" — as part of its normal response. Your code is responsible for noticing that intent, actually running the function, and handing the result back to the LLM as a new message. That request → detect → execute → feed-back → final-answer cycle **is** what "agent" means in this ecosystem; it's the same loop shape as [22 §6](22_LangGraph_Cycles_and_Loops_Deep_Dive.md#6-type-4--agentic-tool-calling-loop-react) described conceptually, just made concrete here.

---

## 2. Defining a Tool

A tool is a plain Python function decorated with `@tool` from `langchain_core.tools`. The docstring is not documentation for humans — it's the description the **LLM reads to decide whether and how to call it**. Type hints become the tool's argument schema.

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    # pretend this hits a real weather API
    return f"It's 18°C and cloudy in {city}."

@tool
def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b
```

| Piece | What it becomes |
|---|---|
| Function name (`get_weather`) | The tool's name, exactly as the LLM will reference it |
| Docstring | The tool's *description* — the LLM's only signal for when to use it |
| Type-hinted parameters | JSON schema the LLM must fill in to call the tool |
| Return value | Whatever gets stringified and sent back to the LLM as the tool's result |

A vague docstring ("Get weather") gives the LLM less to work with than a specific one ("Get the current weather for a given city. Use this whenever the user asks about temperature, rain, or forecast."). Tool descriptions are effectively prompt engineering — the LLM never sees your function body, only the name, docstring, and schema.

---

## 3. `bind_tools` — Giving the LLM a Menu

An LLM doesn't know a tool exists until you tell it, per-call, via `bind_tools`. This returns a new runnable — the original LLM is unchanged.

```python
from langchain.chat_models import init_chat_model

llm = init_chat_model(model="command-a-03-2025", model_provider="cohere")
llm_with_tools = llm.bind_tools([get_weather, add])

response = llm_with_tools.invoke("What's the weather in Paris?")
```

`bind_tools` doesn't make the LLM *call* anything — it just attaches the tool schemas to every request so the model can *choose* to emit a tool call instead of (or alongside) plain text. Compare to [08_langchain_output_parsers.md](08_langchain_output_parsers.md)'s `with_structured_output()`: both attach a schema to steer the response shape, but `with_structured_output()` forces exactly one Pydantic object back, while `bind_tools` lets the model choose freely between plain text, one tool call, or several tool calls in the same response.

---

## 4. Reading a Tool Call Off the Response

The response is still an `AIMessage` (see [05_messages.md](05_messages.md)), but when the model decides to call a tool, `response.tool_calls` is populated instead of (or alongside) `response.content`.

```python
response = llm_with_tools.invoke("What's the weather in Paris?")

print(response.content)     # often empty or a short lead-in
print(response.tool_calls)
# [{'name': 'get_weather', 'args': {'city': 'Paris'}, 'id': 'call_abc123'}]
```

Each entry in `tool_calls` has three fields that matter:

| Field | Purpose |
|---|---|
| `name` | Which tool the model wants — must match a `@tool` function's name exactly |
| `args` | Dict of arguments the model filled in, matching that tool's schema |
| `id` | Correlates this call to the `ToolMessage` reply (a response can request several tools at once) |

The model can also request **zero** tool calls (plain answer) or **multiple** tool calls in one response (e.g., checking weather in three cities at once) — `tool_calls` is always a list, and it's empty when the model just answers directly.

---

## 5. Executing the Tool and Feeding the Result Back

The LLM produced *intent*, not a result — your code runs the actual function and reports back with a `ToolMessage`, whose `tool_call_id` must match the `id` from the request so the model knows which call this result answers.

```python
from langchain_core.messages import ToolMessage

tool_call = response.tool_calls[0]
result = get_weather.invoke(tool_call["args"])   # actually run the function

tool_message = ToolMessage(content=result, tool_call_id=tool_call["id"])

# Now send the whole exchange back so the LLM can produce a final answer
final = llm_with_tools.invoke([
    HumanMessage(content="What's the weather in Paris?"),
    response,        # the AIMessage that requested the tool call
    tool_message,    # the tool's result
])
print(final.content)   # "It's 18°C and cloudy in Paris."
```

Note that `@tool`-decorated functions are runnables themselves — `get_weather.invoke(tool_call["args"])` runs it directly, no manual `**kwargs` unpacking needed since `args` is already the right shape.

This request → tool call → `ToolMessage` → final answer sequence is exactly four messages in the conversation history, and it's the same message-accumulation pattern from [21_LangGraph_Accumulated_State_Explanation.md](21_LangGraph_Accumulated_State_Explanation.md) (`Annotated[list[BaseMessage], add_messages]`) — every tool round-trip just appends more messages to the same growing list.

---

## 6. `ToolNode` — LangGraph's Built-in Executor

Doing step 5 by hand (finding the tool by name, calling `.invoke()`, wrapping the result in a `ToolMessage`) is exactly the kind of boilerplate LangGraph ships a pre-built node for: `ToolNode`. It takes a list of tools and, when placed in a graph, automatically reads the *last message's* `tool_calls` and executes all of them (including several in parallel if the model requested multiple).

```python
from langgraph.prebuilt import ToolNode

tools = [get_weather, add]
tool_node = ToolNode(tools)

# Given a state whose last message is an AIMessage with tool_calls,
# ToolNode returns {"messages": [ToolMessage(...), ToolMessage(...), ...]}
```

`ToolNode` expects the same `MessagesState`-shaped state used everywhere else in this repo (`messages: Annotated[list[BaseMessage], add_messages]`) — it reads `state["messages"][-1].tool_calls` and needs nothing else.

---

## 7. Wiring the Full ReAct Loop by Hand

This is the concrete version of the loop [22 §6](22_LangGraph_Cycles_and_Loops_Deep_Dive.md#6-type-4--agentic-tool-calling-loop-react) described in the abstract — "ReAct" (**Rea**son + **Act**) because the LLM alternates between reasoning in text and acting via tool calls until it has enough information to stop.

```python
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

llm_with_tools = llm.bind_tools([get_weather, add])

def call_model(state: AgentState) -> dict:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    # The AIMessage requested a tool -> go execute it. Otherwise we're done.
    return "tools" if last.tool_calls else "end"

graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", ToolNode([get_weather, add]))

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")   # loop back so the LLM can use the tool result

app = graph.compile()
```

Mapping this onto [22 §2](22_LangGraph_Cycles_and_Loops_Deep_Dive.md#2-the-anatomy-of-every-loop)'s four-piece loop anatomy:

| Anatomy piece | This loop |
|---|---|
| Loop body node | `agent` (reasons, maybe requests a tool) |
| Progress field | The growing `messages` list itself — each pass adds a tool call or a final answer |
| Router | `should_continue` — checks `tool_calls` on the last message |
| Exit path | `"end"` → `END`, reached the moment the model replies with no `tool_calls` |

The loop can run several times in a row — request tool A, get its result, decide it now needs tool B, get that result, *then* answer — with no code change required; `should_continue` just keeps routing back to `tools` until the model stops asking for them.

---

## 8. `create_react_agent` — The Shortcut

Section 7's graph is such a common shape that LangGraph ships it pre-built as `create_react_agent`, from `langgraph.prebuilt`. It builds the exact `agent ⇄ tools` loop above internally.

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(llm, tools=[get_weather, add])

result = agent.invoke({"messages": [HumanMessage(content="What's the weather in Paris, and what's 12 + 30?")]})
for m in result["messages"]:
    print(type(m).__name__, "-", m.content or m.tool_calls)
```

Use §7's manual version when you need custom routing (e.g., a confirmation step before certain tools run — combine with [23_LangGraph_Human_in_the_Loop_Deep_Dive.md](23_LangGraph_Human_in_the_Loop_Deep_Dive.md)'s `interrupt()`), and reach for `create_react_agent` when you just need a standard tool-using agent with no extra branching.

---

## 9. Common Mistakes

- **Forgetting `bind_tools`.** An LLM with tools defined but not bound will never emit `tool_calls` — it has no idea the tools exist.
- **Not matching `tool_call_id`.** If the `ToolMessage.tool_call_id` doesn't exactly match the `id` from the request, the model can't correlate the result to its request and the API call may error.
- **Forgetting the loop-back edge.** `graph.add_edge("tools", "agent")` is what lets the LLM actually see and use the tool's result — without it, the tool runs but nothing reads its output.
- **Trusting tool call args blindly.** The model can hallucinate arguments or call a tool with malformed input — validate before hitting a real API or database, same as any external input.
- **Confusing `bind_tools` with `with_structured_output()`.** `bind_tools` lets the model freely choose text vs. one-or-more tool calls; `with_structured_output()` (see [08](08_langchain_output_parsers.md)) forces exactly one typed object every time. Use `bind_tools` for "the model decides whether to act," and `with_structured_output()` for "I need this response in a fixed shape."
- **Unbounded ReAct loops.** A model that keeps calling tools without ever converging on a final answer needs the same safety net as any other loop — `recursion_limit` (see [22 §9](22_LangGraph_Cycles_and_Loops_Deep_Dive.md#9-loop-safety-recursion_limit-and-graphrecursionerror)).

---

## 10. Interview Questions

**Q: What does `bind_tools` actually change about the LLM?**
A: Nothing about the model itself — it returns a new runnable that includes the tools' JSON schemas in every request, so the model *may* respond with a `tool_calls` list instead of (or alongside) plain text. The model still isn't executing anything; it's only emitting structured intent.

**Q: Who actually runs the tool's code — the LLM or your program?**
A: Your program (or `ToolNode` on your behalf). The LLM only ever produces `{name, args}` describing what it wants called; a tool call is inert until something reads `response.tool_calls` and invokes the matching function.

**Q: What is `ToolMessage.tool_call_id` for?**
A: It links a tool's result back to the specific `tool_calls` entry that requested it, which matters once a single `AIMessage` can request multiple tools at once — the model needs to know which result answers which call.

**Q: How does the ReAct loop know when to stop?**
A: The router checks whether the latest `AIMessage.tool_calls` is empty. An empty list means the model chose to answer in plain text instead of requesting another tool, which routes to `END` instead of back to the tool-executing node.

**Q: When would you write the `agent ⇄ tools` graph by hand instead of using `create_react_agent`?**
A: When you need custom control flow around tool execution — e.g., a human-approval gate before a specific tool runs, custom retry/error handling per tool, or additional nodes interleaved in the loop. `create_react_agent` is the fixed, no-frills shape; hand-wiring exposes every edge for customization.

---

## 11. Quick Revision

- **Tool** = a `@tool`-decorated function; its docstring and type hints ARE the schema the LLM reads — write them for the model, not for humans.
- **`bind_tools([...])`** attaches tool schemas to an LLM's requests without forcing a call — the model can still just answer in plain text.
- **`response.tool_calls`** is a list of `{name, args, id}` dicts on the `AIMessage` — empty when the model didn't want a tool, possibly multiple entries when it wants several at once.
- **`ToolMessage(content=result, tool_call_id=...)`** reports a tool's result back to the model; the `tool_call_id` must match the request it's answering.
- **`ToolNode(tools)`** is LangGraph's built-in executor — reads `tool_calls` off the last message, runs every requested tool, returns the `ToolMessage`s.
- **The ReAct loop** = `agent` node (LLM decides) ⇄ `tools` node (execute), routed by "did the last message request a tool?", exiting to `END` the moment it doesn't.
- **`create_react_agent(llm, tools=[...])`** is the same loop, prebuilt — reach for it when you don't need custom routing around tool execution.
- This is currently a **documentation-only** topic in this repo — no file uses `bind_tools`/`ToolNode`/`create_react_agent` yet. Building a small demo (e.g. a calculator or weather-lookup agent) would be the natural next hands-on exercise.
