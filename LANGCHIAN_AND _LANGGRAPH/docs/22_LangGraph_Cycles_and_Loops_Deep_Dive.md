# LangGraph Cycles & Loops — Deep Dive

> Builds on [19_langgraph-complete-beginner-guide.md](19_langgraph-complete-beginner-guide.md) (why graphs can loop and chains can't) and [20_langgraph_conditional_edges_and_routing.md](20_langgraph_conditional_edges_and_routing.md) (the `add_conditional_edges` mechanics that make loops possible). This file goes deep on *loops specifically*: the anatomy every loop shares, the different loop shapes you'll actually build, and the safety mechanics that stop them running forever. Code walkthroughs reference [condtional_edges.py](../condtional_edges.py) and [cyclic_loop.py](../cyclic_loop.py) in the repo root.

## Table of Contents
1. [What a Cycle Actually Is](#1-what-a-cycle-actually-is)
2. [The Anatomy of Every Loop](#2-the-anatomy-of-every-loop)
3. [Type 1 — Retry-Until-Valid Loop](#3-type-1--retry-until-valid-loop)
4. [Type 2 — Iterative-Deepening Loop](#4-type-2--iterative-deepening-loop)
5. [Type 3 — Counted For-N Loop](#5-type-3--counted-for-n-loop)
6. [Type 4 — Agentic Tool-Calling Loop (ReAct)](#6-type-4--agentic-tool-calling-loop-react)
7. [Type 5 — Human-in-the-Loop (Pause / Resume)](#7-type-5--human-in-the-loop-pause--resume)
8. [Exit Conditions: Combining "Good Enough" OR "Out of Budget"](#8-exit-conditions-combining-good-enough-or-out-of-budget)
9. [Loop Safety: `recursion_limit` and `GraphRecursionError`](#9-loop-safety-recursion_limit-and-graphrecursionerror)
10. [Common Mistakes](#10-common-mistakes)
11. [Full Worked Example](#11-full-worked-example)
12. [Interview Questions](#12-interview-questions)
13. [Quick Revision](#13-quick-revision)

---

## 1. What a Cycle Actually Is

In graph theory, a **cycle** is a path that starts at a node and, by following edges, can return to that same node. A **DAG** (Directed Acyclic Graph) forbids this — every LCEL chain is a DAG, which is exactly why chains can't loop (see [19](19_langgraph-complete-beginner-guide.md) §"Can't loop back"). **LangGraph explicitly allows cycles.** That's the one-sentence reason the library exists.

```
DAG (chain):        A ──→ B ──→ C ──→ END          (no way back, ever)

Cyclic graph:        ┌────────────────┐
                      ▼                │
                A ──→ B ──→ check ──→──┘  (loops back to B)
                              │
                              └─if-good──→ END
```

A **loop** in LangGraph is nothing exotic under the hood — it's just a [conditional edge](20_langgraph_conditional_edges_and_routing.md) whose mapping dict points a label back to a node that has *already run in this invocation*. There is no special `add_loop()` API. Every loop you will ever build is `add_conditional_edges(node, router, {"retry": "some_earlier_node", "done": END})`.

What makes it a *loop* and not just a *branch* is purely topological: the destination is a node upstream of (or equal to) the current one, so control flow can revisit it.

---

## 2. The Anatomy of Every Loop

Every loop in LangGraph — regardless of what it's used for — is built from the same four pieces. Learn to spot these four in any loop and you can read (or design) any of them.

| Piece | Role | Example (from `cyclic_loop.py`) |
|---|---|---|
| **1. Loop body node(s)** | Does the actual work each pass — generate, research, improve | `generate_code`, `research` |
| **2. Progress/state field** | Something in state that *changes* each pass, so the loop isn't identical work forever | `iteration`, `code`, `findings` |
| **3. Router (condition check)** | A conditional edge that decides: loop again, or exit | `should_continue` |
| **4. Exit path** | A label in the router's mapping that leads to `END` (or a finalize node → `END`), reachable *without* looping forever | `"end"` → `finalize` → `END` |

If any one of these is missing, the loop is broken:

- No progress field → the loop can run forever doing the exact same thing (e.g., forgetting `"iteration": state["iteration"] + 1`).
- No router → it's not a loop, it's just a repeated direct edge (which LangGraph would treat as an infinite unconditional cycle — see [§9](#9-loop-safety-recursion_limit-and-graphrecursionerror)).
- No reachable exit path → guaranteed infinite loop until the recursion limit kills it.

**State shape rule of thumb:** a loop's state needs at minimum a **counter** (`iteration: int`, plain replace-on-write is fine — the loop body always writes the freshly incremented value) and, if you want to keep history from every pass rather than just the latest, an **accumulator** (`Annotated[list, operator.add]` — see [21_LangGraph_Accumulated_State_Explanation.md](21_LangGraph_Accumulated_State_Explanation.md)). `cyclic_loop.py`'s `ResearchState.findings` and `errors` are accumulators; `iteration` is a plain replace field.

---

## 3. Type 1 — Retry-Until-Valid Loop

**Shape:** generate → validate → (bad? go back to generate : proceed). The most common loop in agentic systems — "keep trying until the output passes a check, or give up after N attempts."

Two working examples of this exact shape exist in the repo already:

### `condtional_edges.py::demo_conditional_loop` (simplest form)

```python
def shoud_continue(state: QualityState) -> Literal["improve", "finalize"]:
    if state["quality_score"] >= 7:
        return "finalize"
    elif state["iteration"] >= 3:
        return "finalize"
    else:
        return "improve"

graph.add_edge(START, "evalute")
graph.add_conditional_edges("evalute", shoud_continue, {"improve": "improve", "finalize": "finalize"})
graph.add_edge("improve", "evalute")   # ← the loop-back edge
graph.add_edge("finalize", END)
```

Flow: `evalute` scores the content → router checks the score → `"improve"` sends control back to `improve`, which rewrites the content and *unconditionally* flows back to `evalute` (`add_edge("improve", "evalute")`) → the cycle repeats. Note the loop-back here is a **direct edge** (`improve → evalute` always happens), while the *decision to enter the loop again* is the conditional edge on `evalute`'s output. This is a common pattern: only one node in the cycle needs to be conditional; the rest of the ring can be plain edges.

### `cyclic_loop.py::demo_self_correcting_code` (same shape, richer state)

```python
def should_continue(state: CodeGenState) -> Literal["generate", "end"]:
    if state["success"]:
        return "end"
    elif state["iteration"] >= state["max_iterations"]:
        return "end"
    else:
        return "generate"

graph.add_edge(START, "generate")
graph.add_edge("generate", "validate")
graph.add_conditional_edges("validate", should_continue, {"generate": "generate", "end": "finalize"})
graph.add_edge("finalize", END)
```

Here the loop-back edge (`"generate": "generate"`) is itself inside the conditional mapping, rather than a separate direct edge — functionally identical, just wired differently. `validate` returns `{"errors": [...], "success": False}` on failure; `generate` reads `state["errors"][-1]` on the *next* pass to build a "fix this" prompt instead of a "write this" prompt — that's the progress field doing real work, not just counting.

**When to use this shape:** LLM output validation, code generation with test feedback, structured-output repair, any "critic checks, generator fixes" pattern.

---

## 4. Type 2 — Iterative-Deepening Loop

**Shape:** unlike a retry loop (which repeats the *same* step until it succeeds), a deepening loop does *different, escalating* work each pass — go one level deeper each time, up to a depth budget.

`cyclic_loop.py::demo_iterative_research`:

```python
def should_continue(state: ResearchState) -> Literal["research", "synthesize"]:
    if state["iteration"] >= state["max_depth"]:
        return "synthesize"
    return "research"

graph.add_edge(START, "research")
graph.add_edge("research", "generate_questions")
graph.add_conditional_edges("generate_questions", should_continue, {"research": "research", "synthesize": "synthesize"})
graph.add_edge("synthesize", END)
```

Flow: `research` (gather facts) → `generate_questions` (decide what to dig into *next*, and bump `iteration`) → router checks depth budget → loop back to `research` with a *different* query (`state["questions"][-1]`) each time, or exit to `synthesize` once `max_depth` is hit.

**Key difference from Type 1:** the exit condition here is a **pure budget check** (`iteration >= max_depth`) with no quality/success signal — there's no "good enough" early exit, it always runs exactly `max_depth` passes. Contrast with Type 1's `should_continue`, which exits *early* the moment `success`/`quality_score` clears the bar, and only falls back to the iteration cap as a safety net. That distinction — "loop until good OR out of budget" vs. "loop exactly N times by design" — is the real difference between these two shapes, not the node names.

**When to use this shape:** recursive research/exploration, multi-hop retrieval (RAG that re-queries based on what it just found), progressive summarization, tree-of-thought expansion.

---

## 5. Type 3 — Counted For-N Loop

Not separately demoed in the repo, but worth naming because it's the degenerate/simplest case of Type 2 — no quality check at all, just "do this exactly N times":

```python
class BatchState(TypedDict):
    items: list[str]
    processed: Annotated[list[str], operator.add]
    index: int

def process_one(state: BatchState) -> dict:
    item = state["items"][state["index"]]
    result = llm.invoke(f"Summarize: {item}")
    return {"processed": [result.content], "index": state["index"] + 1}

def has_more(state: BatchState) -> Literal["continue", "done"]:
    return "continue" if state["index"] < len(state["items"]) else "done"

graph.add_conditional_edges("process_one", has_more, {"continue": "process_one", "done": END})
```

This is a graph-native replacement for a Python `for` loop when each iteration needs to be a durable, resumable, independently-retriable step (e.g., you want a checkpoint after every item — see [§7](#7-type-5--human-in-the-loop-pause--resume)). If you don't need that durability, a plain Python loop calling `app.invoke()` per item, or LangGraph's `Send` API for parallel fan-out, is simpler — don't reach for a cyclic graph node just to replace a for-loop with no other requirement.

---

## 6. Type 4 — Agentic Tool-Calling Loop (ReAct)

**Not present anywhere in the current codebase** — `agent_handsoff.py`, `research_assistant.py`, `langgraph_core.py`, and `langgraph_full.py` were checked; none use `bind_tools` + a graph cycle together (bindings exist in LangChain per [05_messages.md](05_messages.md), but no file wires a tool-calling loop as a LangGraph cycle). This is the most common loop shape in production agents, so it's documented here conceptually even though there's no local example yet.

**Shape:** LLM decides whether to call a tool → if yes, run the tool and feed the result back to the LLM → repeat until the LLM responds with plain text instead of a tool call.

```python
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

llm_with_tools = llm.bind_tools([search_tool, calculator_tool])

def call_model(state: AgentState) -> dict:
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", ToolNode([search_tool, calculator_tool]))

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")   # ← the loop-back: tool result goes back to the LLM

app = graph.compile()
```

`tools_condition` is a prebuilt router (from `langgraph.prebuilt`) that inspects the last message: if it's an `AIMessage` with `tool_calls`, route to `"tools"`; otherwise route to `END`. This is structurally identical to Type 1 (retry-until-valid) — the "validity check" is just "did the model decide it's done talking" instead of a quality score — but it's specific enough (this exact pattern is called **ReAct**: Reason → Act → Observe → repeat) that it's worth naming separately, since it's the backbone of almost every tool-using agent.

**When to use this shape:** any agent that can call external tools/APIs an unknown number of times before answering — search agents, code-execution agents, multi-tool assistants.

---

## 7. Type 5 — Human-in-the-Loop (Pause / Resume)

**Also not present in the codebase yet.** Mentioned in passing in [19](19_langgraph-complete-beginner-guide.md) ("Execution must pause, wait for a human to review/approve, then resume exactly where it stopped") but no file demonstrates it. Documented here because it's the loop type that most depends on a feature not used anywhere locally: **checkpointers**.

**Shape:** the graph runs up to a review node, *stops* (not errors — a deliberate pause), waits — potentially minutes or days — for a human decision injected from outside, then resumes and either loops back for another pass or proceeds.

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

def review_node(state: State) -> dict:
    decision = interrupt({"question": "Approve this draft?", "draft": state["draft"]})
    return {"approved": decision == "approve"}

def route_after_review(state: State) -> Literal["revise", "publish"]:
    return "publish" if state["approved"] else "revise"

graph.add_conditional_edges("review", route_after_review, {"revise": "generate", "publish": END})

app = graph.compile(checkpointer=MemorySaver())   # required — state must survive the pause

config = {"configurable": {"thread_id": "draft-1"}}
app.invoke({"draft": "..."}, config)                       # runs until interrupt(), then stops
app.invoke(Command(resume="approve"), config)               # resumes exactly where it paused
```

Without a `checkpointer`, `interrupt()` has nothing to persist state *into* while execution is suspended, so this pattern structurally requires compiling with one (`graph.compile(checkpointer=...)`) — every other loop type in this doc works fine on a plain `graph.compile()`. This is also the only loop type where "the next iteration" can be triggered by something outside the process entirely (a person clicking "approve" in a UI, arbitrarily later) rather than by the graph's own router immediately continuing.

**When to use this shape:** approval workflows, content moderation gates, any step where an LLM shouldn't have unsupervised authority to proceed (send an email, execute a trade, delete data).

---

## 8. Exit Conditions: Combining "Good Enough" OR "Out of Budget"

Both working loops in the codebase (`demo_conditional_loop`, `demo_self_correcting_code`) use the same two-clause exit pattern, and it's worth naming explicitly because it's the correct default for almost every retry loop:

```python
def should_continue(state) -> Literal["retry", "done"]:
    if <quality signal says we're good>:      # early exit: happy path
        return "done"
    elif state["iteration"] >= state["max_iterations"]:  # safety exit: give up
        return "done"
    else:
        return "retry"
```

Both clauses route to the **same** exit label. This matters: a loop that only checks the quality signal can spin forever on a task the LLM never solves; a loop that only checks the iteration cap ignores an early success and burns budget doing unnecessary extra passes. You want both — exit as soon as either condition fires. This is the loop-level equivalent of a `while (not done) and (attempts < max):` in plain Python.

---

## 9. Loop Safety: `recursion_limit` and `GraphRecursionError`

The state-level iteration cap (`max_iterations`, `max_depth` in the examples above) is an **application-level** safety net you have to remember to write yourself and wire correctly. LangGraph also has a **framework-level** backstop that applies regardless of whether your state-level cap is correct: every `invoke()`/`stream()` call has a `recursion_limit` (default **25** super-steps) — if the graph is still running after that many steps, LangGraph raises `GraphRecursionError` instead of looping forever.

```python
from langgraph.errors import GraphRecursionError

try:
    result = app.invoke(initial_state, {"recursion_limit": 50})
except GraphRecursionError:
    print("Graph exceeded max steps — likely a broken exit condition")
```

**None of the loops currently in the codebase set `recursion_limit` explicitly.** They don't strictly need to, because each already has its own state-level cap (`max_iterations=3`, `max_depth=2`) well under the default 25-step ceiling — but that's relying on the state-level logic being correct. If `should_continue` in `condtional_edges.py` had a typo (e.g., comparing `state["iteration"] >= 3` where `iteration` is never actually incremented — an easy mistake, see [§10](#10-common-mistakes) item 1), the default `recursion_limit=25` is the only thing standing between that bug and a truly infinite loop. Treat the two caps as layered defenses, not alternatives: the state-level cap gives you a controlled, informative exit (`finalize` runs, you get a real result with `feedback: "gave up after 3 tries"`); the `recursion_limit` is the emergency brake that fires when the state-level cap itself is broken.

---

## 10. Common Mistakes

1. **Forgetting to increment the progress field.** If `improve_content` didn't return `"iteration": state["iteration"] + 1`, the iteration-cap clause of `should_continue` would never fire, and only the quality-score clause (or the framework `recursion_limit`) would ever stop the loop. Always double check every loop-body node that's supposed to advance progress actually returns the incremented value.

2. **Using a plain-replace field where an accumulator was intended, or vice versa.** `errors: Annotated[list[str], operator.add]` in `CodeGenState` accumulates every error across all attempts — useful for a post-mortem, but means `state["errors"][-1]` (not `state["errors"][0]`) is needed to get the *latest* error. If you actually only ever want the latest error, a plain `errors: str` field is simpler and avoids the list ever growing unboundedly across a very long-running loop.

3. **No reachable exit path from every entry into the loop.** Every branch that can enter the loop body must have *some* route, direct or eventual, to an exit label. It's easy to add a third router branch (e.g., a `"escalate"` path) and forget to also give *that* path a way out.

4. **Relying only on the LLM's judgment for the exit condition with no iteration cap.** `should_continue` that checks only `state["quality_score"] >= 7` with no `elif iteration >= max` fallback is one bad LLM response away from looping until `GraphRecursionError` kills it uninformatively, instead of gracefully finalizing with "best effort after N tries."

5. **Conflating a direct-edge ring with a conditional loop.** `graph.add_edge("improve", "evalute")` in `demo_conditional_loop` is *not itself* the loop-back decision — it's just "always go here next." The actual loop control is entirely in the conditional edge on `evalute`. If you're debugging why a loop won't exit, check the *conditional* edge's router and mapping first, not the plain edges connecting the ring.

6. **Not setting `recursion_limit` on graphs used with untrusted/unbounded state-level caps** (e.g., `max_iterations` read from user input). If a caller can pass `max_iterations=10000`, your state-level cap no longer protects you — the framework `recursion_limit` becomes the real ceiling, so make sure it's set to something you actually mean, not left at the default by accident, when caps come from outside your code.

---

## 11. Full Worked Example

Combines Type 1 (retry-until-valid) with both safety layers from [§9](#9-loop-safety-recursion_limit-and-graphrecursionerror):

```python
from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError

class DraftState(TypedDict):
    draft: str
    score: int
    iteration: int
    max_iterations: int

def write_draft(state: DraftState) -> dict:
    # imagine this calls an LLM to (re)write state["draft"]
    return {"draft": f"draft v{state['iteration'] + 1}", "iteration": state["iteration"] + 1}

def score_draft(state: DraftState) -> dict:
    # imagine this calls an LLM/critic to score the draft 1-10
    return {"score": 8 if state["iteration"] >= 2 else 3}

def should_continue(state: DraftState) -> Literal["retry", "done"]:
    if state["score"] >= 7:
        return "done"
    if state["iteration"] >= state["max_iterations"]:
        return "done"
    return "retry"

graph = StateGraph(DraftState)
graph.add_node("write", write_draft)
graph.add_node("score", score_draft)

graph.add_edge(START, "write")
graph.add_edge("write", "score")
graph.add_conditional_edges("score", should_continue, {"retry": "write", "done": END})

app = graph.compile()

try:
    result = app.invoke(
        {"draft": "", "score": 0, "iteration": 0, "max_iterations": 5},
        {"recursion_limit": 20},   # framework-level backstop above the state-level cap
    )
    print(f"Finished after {result['iteration']} iterations, score {result['score']}")
except GraphRecursionError:
    print("Loop exceeded recursion_limit — should_continue is likely broken")
```

Walk-through: `write` produces a draft and advances `iteration` → `score` rates it → `should_continue` checks *both* exit clauses (score good enough, or budget exhausted) and either loops back to `write` or ends. The `recursion_limit=20` is a deliberate ceiling above the state-level `max_iterations=5`, so if `should_continue`'s logic were ever wrong, `GraphRecursionError` fires at 20 steps instead of running away silently.

---

## 12. Interview Questions

**Q: What structurally makes a loop possible in LangGraph but not in an LCEL chain?**
A: LangGraph allows cycles in the graph (a conditional edge's mapping can point back to an already-executed node); LCEL chains are DAGs by construction and cannot express "go back."

**Q: What four components does every LangGraph loop need?**
A: A loop-body node (does the work), a progress/state field that changes each pass, a router (conditional edge that checks whether to continue), and a reachable exit path to `END`.

**Q: What's the difference between a retry-until-valid loop and an iterative-deepening loop?**
A: A retry loop repeats essentially the *same* step until a quality/success check passes (early-exit on success, fallback exit on budget). A deepening loop does *progressively different* work each pass (e.g., going one level deeper) and typically runs for a fixed budget by design, with no early "good enough" exit.

**Q: Why should a loop's exit router usually check two conditions (success OR max iterations) instead of just one?**
A: Checking only the success/quality condition risks an infinite loop if the condition never becomes true. Checking only the iteration cap ignores an early success and wastes unnecessary passes. Checking both, routing either to the same exit label, gives you an early exit on success and a guaranteed bound otherwise.

**Q: What's the difference between the state-level iteration cap and `recursion_limit`?**
A: The state-level cap (e.g., `max_iterations` in your `TypedDict`) is application logic you write and control yourself, and its failure mode when broken is a true infinite loop. `recursion_limit` is a framework-level backstop (default 25 super-steps) that raises `GraphRecursionError` regardless of whether your own logic is correct — a safety net *under* your safety net.

**Q: How would you implement an agent that keeps calling tools until it has a final answer?**
A: A ReAct-style loop: an `agent` node calls the LLM (with tools bound), a `tools` node (commonly `ToolNode`) executes any requested tool calls, and a conditional edge (commonly `tools_condition`) routes back to `agent` if the last message has tool calls, or to `END` if it's a plain text answer — `graph.add_edge("tools", "agent")` closes the loop.

**Q: Why does a human-in-the-loop pause require a checkpointer, when other loop types don't?**
A: `interrupt()` suspends the graph mid-run and must persist the paused state somewhere it can be reloaded from when execution resumes later (potentially in a different process, after real time has passed). A checkpointer is what makes that state durable across the pause; other loop types resume immediately within the same `invoke()` call and don't need durability.

---

## 13. Quick Revision

- A **cycle** = a conditional edge whose mapping points back to an earlier node. No special API — it's the same `add_conditional_edges` from [20](20_langgraph_conditional_edges_and_routing.md), just wired to loop.
- Every loop = **loop body** + **progress field** + **router** + **reachable exit**. Missing any one breaks the loop.
- **Type 1 — Retry-until-valid**: generate → validate → retry or exit (`demo_conditional_loop`, `demo_self_correcting_code`). Exit = success OR budget.
- **Type 2 — Iterative-deepening**: escalating work each pass, fixed depth budget, no early exit (`demo_iterative_research`).
- **Type 3 — Counted for-N**: no quality check, just "N times" — the durable/resumable alternative to a Python `for` loop.
- **Type 4 — Agentic/ReAct**: `agent ⇄ tools` via `tools_condition`, loops until the LLM stops calling tools. Not yet in this codebase.
- **Type 5 — Human-in-the-loop**: `interrupt()` + `Command(resume=...)`, requires `compile(checkpointer=...)`. Not yet in this codebase.
- Prefer **two-clause exits**: quality/success check OR iteration cap, both routing to the same exit label.
- **`recursion_limit`** (default 25) is the framework-level backstop under your own state-level cap — set it explicitly when the state-level cap isn't fully trusted (e.g., derived from external input).
- Debugging a loop that won't exit: check the **conditional** edge's router/mapping first — plain edges in the ring just carry control, they don't decide anything.
