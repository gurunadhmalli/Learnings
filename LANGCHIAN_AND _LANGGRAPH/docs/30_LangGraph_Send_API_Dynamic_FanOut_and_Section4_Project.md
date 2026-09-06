# LangGraph Send API — Dynamic Fan-Out & the Section 4 Project

> From course slides ("LangGraph Send API: Static vs Dynamic Fan-Out", "Multi-Agent Research Workflow", "State Design", "Patterns Combined", "Section Project"). This doc covers the mechanism [27_Multi_Agent_Architecture_Patterns.md](27_Multi_Agent_Architecture_Patterns.md) §3.1 left static — `parrallel_agent.py`'s fan-out is a fixed set of edges wired at graph-build time — and walks through `multi_agent_research_system.py`, the Section 4 capstone project that combines **every** pattern from docs 24–29 into one working pipeline. Assumes 21 (reducers), 26 (Supervisor), 27 (taxonomy), and 28 (Blackboard) as background.

## Table of Contents
1. [Static vs Dynamic Fan-Out — Why `Send` Exists](#1-static-vs-dynamic-fan-out--why-send-exists)
2. [The Automatic Barrier — Fan-In](#2-the-automatic-barrier--fan-in)
3. [The Multi-Agent Research Workflow](#3-the-multi-agent-research-workflow)
4. [State Design — `ResearchState`](#4-state-design--researchstate)
5. [Walkthrough: `multi_agent_research_system.py`](#5-walkthrough-multi_agent_research_systempy)
6. [Patterns Combined — How This Maps to Docs 24–29](#6-patterns-combined--how-this-maps-to-docs-2429)
7. [Gaps Between the Slides and the Code](#7-gaps-between-the-slides-and-the-code)
8. [Common Mistakes](#8-common-mistakes)
9. [Interview Questions](#9-interview-questions)
10. [Quick Revision](#10-quick-revision)

---

## 1. Static vs Dynamic Fan-Out — Why `Send` Exists

`parrallel_agent.py` (documented in 27 §3.1) fans out with plain edges: `START` connects to `research_agent`, `creative_agent`, and `technical_agent` because `graph.add_edge()` was called three times, once per agent, when the graph was built. That count is baked into the code — three branches, always three, decided by whoever wrote the graph.

The slide's comparison:

| | Static (`add_edge`) | Dynamic (`Send`) |
|---|---|---|
| Destinations | Hardcoded at `graph.add_edge()` | Decided at runtime |
| Who decides the count | The developer, when writing the graph | A node, while the graph is running |
| Example | `START` → `research_agent` / `creative_agent` / `technical_agent`, always exactly 3 | `Supervisor` → `dispatch_searches()` → however many `Send` objects it returns |

Dynamic fan-out solves a real problem: the *number* of parallel branches isn't always known until you've seen the input. A supervisor might decide a simple topic only needs 2 searches, a broad one needs 5 — that shape can't be expressed with a fixed set of `add_edge()` calls, because the graph topology would have to change per-request.

The mechanism is `langgraph.types.Send`. Instead of a normal conditional-edge router returning a node name (`Literal["a", "b"]`, as in 20), a **dispatch function** returns a `list[Send]`:

```python
from langgraph.types import Send

def dispatch_searches(state: ResearchState) -> list[Send]:
    return [
        Send("search_agent", {"search_query": query, "findings": []})
        for query in state["search_queries"]
    ]
```

Each `Send(node_name, payload)` spins up one independent invocation of `node_name`, seeded with `payload` as that instance's *own* state — not the parent graph's full state. This is why `search_agent` in the project has a narrower state type (`SearchTaskState`, just `search_query` + `findings`) than the graph's overall `ResearchState`: each dispatched instance only ever sees what `Send` handed it, the same way `map()` applies one function to many independent inputs.

Wiring it into the graph looks like a conditional edge, but the router is the `Send`-returning function and the list of destinations is given explicitly for graph-visualization purposes:

```python
graph.add_conditional_edges("supervisor", dispatch_searches, ["search_agent"])
```

---

## 2. The Automatic Barrier — Fan-In

The slide's diagram labels the merge point "Automatic barrier — waits for ALL". Every `Send("search_agent", …)` instance eventually reaches the plain edge `search_agent → analyst`. LangGraph doesn't run `analyst` after the *first* `search_agent` finishes — it waits until **every** dynamically spawned `search_agent` instance for that superstep has completed, then runs `analyst` once. This is the same fan-in guarantee that ordinary multi-edge convergence gives you (as in `parrallel_agent.py`'s `synthesize` step, 27 §3.1) — `Send` doesn't change the fan-in rule, only how the fan-out branch count is decided.

This barrier is also *why* `findings` needs a reducer. Three (or `N`) concurrent `search_agent` instances each return `{"findings": [...]}`; without a reducer the last write would silently clobber the others (21's default-overwrite behavior). The state schema uses `operator.add`:

```python
findings: Annotated[list[dict], operator.add]
```

so every instance's returned list is concatenated onto the shared `findings` list rather than overwriting it — this is the **Shared State** communication pattern from 28, not Blackboard yet (that comes next, at the `analyst` step).

---

## 3. The Multi-Agent Research Workflow

Putting fan-out, the barrier, and the rest of the pipeline together, the slide's full diagram is:

```
START
  │
  ▼
┌─────────────────────┐
│      Supervisor       │  Plans the research (Supervisor pattern, 26)
│      (3 queries)      │
└──────────┬────────────┘
           │  dispatch_searches() → list[Send]   (dynamic fan-out, §1)
   ┌───────┼───────┐
   ▼       ▼       ▼
┌──────┐┌──────┐┌──────┐
│search││search││search│   search_agent(n1..n3) — parallel execution (27 §3.1)
│_agent││_agent││_agent│
└───┬──┘└───┬──┘└───┬──┘
    └───────┼───────┘
            ▼            Automatic barrier — waits for ALL (§2)
    ┌───────────────┐
    │    Analyst      │  Reads shared findings — Blackboard pattern (28)
    │   (synthesize)  │
    └───────┬─────────┘
            ▼
    ┌───────────────┐
    │  Report Writer  │◄────────────┐
    └───────┬─────────┘             │  Score < 0.7 AND iter < 2
            ▼                       │  (loop back — 22's loop-with-exit-condition)
    ┌───────────────┐               │
    │ Quality Checker │──────────────┘
    │ (score + verdict)│
    └───────┬─────────┘
            │  Score >= 0.7 OR iter >= 2
            ▼
           END
```

The `Report Writer ⇄ Quality Checker` loop is explicitly called out on the slide as the **iterative refinement / Blackboard loop**: `Quality Checker` doesn't just gate pass/fail, it writes `quality_feedback` onto shared state, and `Report Writer` reads that feedback back off shared state on its next pass — two agents communicating through the state object rather than by passing a message directly to one another, which is exactly the Blackboard definition from 28 (not a new pattern, the same one the Analyst step uses, just applied to a cycle instead of a one-shot fan-in).

---

## 4. State Design — `ResearchState`

The slide pairs each field with who reads/writes it — that ownership map is the useful part, more than the field list itself:

```python
class ResearchState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    topic: str
    search_queries: list[str]
    findings: Annotated[list[dict], operator.add]
    analysis: str
    report: str
    quality_score: float
    quality_feedback: str
    iteration: int
```

| Field | Meaning | Owner |
|---|---|---|
| `messages` | Agent conversation / activity log | All nodes append (`add_messages` reducer, 21) |
| `topic` | What to research | Set once, by the caller |
| `search_queries` | Planned queries | Written by `supervisor` |
| `findings` | Collected results | Written by every `search_agent` instance (`operator.add` reducer — §2) |
| `analysis` | Synthesis | Written by `analyst` |
| `report` | Draft/final report | Written (and rewritten) by `report_writer` |
| `quality_score` / `quality_feedback` | Review outcome | Written by `quality_checker` |
| `iteration` | Revision-cycle counter | Incremented by `quality_checker`, read by both the loop guard and `report_writer` (to know if this is a revision) |

Every field this state needs already appeared individually in earlier docs (21's reducers, 26/28's blackboard state) — what's new here is one schema carrying fields owned by five different node roles at once, which is the practical shape a real multi-agent pipeline's state ends up taking.

---

## 5. Walkthrough: `multi_agent_research_system.py`

The file's own docstring names exactly which earlier patterns it's assembling:

```python
"""
Section 4 Project: Multi-Agent Research System
Combines all patterns from Section 4 into a working research pipeline.

Patterns used:
- Supervisor architecture (4.3)
- Parallel execution (4.5) via Send API
- Shared state / blackboard (4.6)
- Iterative refinement loop
"""
```

**`supervisor(state)`** — asks the LLM for exactly 3 search queries as a JSON array, with a hardcoded fallback (`f"{topic} overview"`, etc.) if the model doesn't return valid JSON. Returns `search_queries` plus a logged `AIMessage`.

**`dispatch_searches(state)`** — the `Send`-returning router from §1, one `Send("search_agent", {...})` per planned query.

**`search_agent(state: SearchTaskState)`** — runs once per dispatched query, asks the LLM for 2–3 findings as JSON (`{"title", "detail"}`), tags each with `source_query`, and returns just `{"findings": results}`. It never sees `topic`, `analysis`, or any other `ResearchState` field — only what `Send` handed it, reinforcing §1's point about narrowed per-instance state.

**`analyst(state)`** — the fan-in target. Reads the *entire* accumulated `findings` list (everything every `search_agent` instance wrote, merged by the `operator.add` reducer) and asks the LLM to synthesize themes, contradictions, and insights into `analysis`.

**`report_writer(state)`** — drafts the report from `analysis` + a sample of raw `findings`. On revision passes (`iteration > 0`), it prepends the prior `quality_feedback` into the system prompt — the Blackboard read that closes the refinement loop from §3.

**`quality_checker(state)`** — uses `llm.with_structured_output(QualityReview)` (a Pydantic model: `score`, `feedback`, `approved`) to score the report, then force-approves once `iteration >= 2` regardless of score, so the loop can't run forever even if the model keeps rejecting its own revisions. It always increments `iteration`.

**`quality_gate(state)`** — the `Literal["report_writer", "end"]` router (20's pattern) implementing the diamond from §3's diagram: `score >= 0.7 or iteration >= 2` → `"end"`, else `"report_writer"`. This is a **second**, independent safety net alongside `quality_checker`'s own force-approve — either one alone would stop the loop; the two agree by construction since both compare against the same `iteration >= 2` threshold.

**`create_research_system()`** — wires it all together:

```python
graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", dispatch_searches, ["search_agent"])   # dynamic fan-out
graph.add_edge("search_agent", "analyst")                                        # barrier + fan-in
graph.add_edge("analyst", "report_writer")
graph.add_edge("report_writer", "quality_checker")
graph.add_conditional_edges(                                                      # the loop
    "quality_checker", quality_gate, {"report_writer": "report_writer", "end": END}
)
```

Three demo entry points exercise it differently: `demo_individual_search()` calls `search_agent` directly (bypassing `Send` entirely, useful for isolating a single node — same testability argument 29 made for subgraphs), `demo_research_with_streaming()` runs the full graph with `stream_mode="updates"` to print each node's output as it lands, and `demo_full_research()` (the one wired to `if __name__ == "__main__"`) runs it end-to-end and prints the full activity log, final stats, and report.

---

## 6. Patterns Combined — How This Maps to Docs 24–29

The slide's own summary table, with the doc that actually covers each row:

| Concept | Where it's used in the project | Documented in |
|---|---|---|
| Tool-calling agents | Search agents (intended: use web search tools) | [24](24_LangGraph_Tool_Calling_and_Agents.md) — see gap in §7 below |
| Supervisor architecture | Supervisor plans and delegates queries | [26](26_LangGraph_MultiAgent_Handoff_Pattern.md), [27](27_Multi_Agent_Architecture_Patterns.md) |
| Agent handoffs | Context (topic → queries → findings → analysis → report) flows phase to phase | [26](26_LangGraph_MultiAgent_Handoff_Pattern.md) |
| Parallel execution | Search agents run simultaneously via `Send` | §1–§2 above (new) |
| Shared state / blackboard | All findings + revision feedback on shared state | [28](28_Multi_Agent_Communication_Patterns_and_Reducers.md) |
| Hierarchical structure | *(not actually present — see §7)* | [29](29_LangGraph_Hierarchical_Multi_Agent_Architecture.md) |

Every row was already individually documented except **Parallel execution via `Send`** — 27 §3.1 only had the static fan-out (`parrallel_agent.py`). This doc, together with `multi_agent_research_system.py`, is what finally closes the gap README.md flagged: *"Collaborative and Parallel multi-agent patterns still have no dedicated working-code doc."* Parallel now does.

---

## 7. Gaps Between the Slides and the Code

Worth flagging explicitly, the way 29 §5 flagged its own design wrinkle — these are real differences between what the slide illustrates and what `multi_agent_research_system.py` actually does:

- **"2, 3, or 5 searches?" vs. always 3.** The slide's dynamic fan-out example shows the supervisor choosing a variable count at runtime. The actual `supervisor()` prompt hardcodes "generate exactly 3 specific search queries" and the return value is sliced with `queries[:3]`. The `Send`-based *mechanism* genuinely supports a variable-length list — nothing in `dispatch_searches` assumes 3 — but the current prompt doesn't exercise that flexibility. Loosening the prompt (and dropping the `[:3]` slice) would be the natural way to make the count actually dynamic.
- **No real tool calls.** The "Patterns Combined" slide labels search agents as using "web search tools" (Tool-calling agents, 4.2/doc 24). `search_agent()` doesn't call `bind_tools` or a `@tool`-decorated function anywhere — it just prompts the LLM to *fabricate* 2–3 findings from its own knowledge. This is the same gap 24's README entry already tracks repo-wide: no file in this codebase calls `bind_tools` yet. A real implementation would swap the fabricated-findings call for an actual search tool (Tavily, DuckDuckGo, etc.) bound to `search_agent`'s LLM.
- **Hierarchical structure (4.7)** is listed in the "Patterns Combined" table but the project has no department-level sub-supervisors or subgraphs — it's a flat pipeline (Supervisor → parallel workers → Analyst → Report Writer → Quality Checker), matching 27's **Supervisor** + **Parallel** patterns, not **Hierarchical** (29). Likely the slide row names a concept from earlier in the same course section (4.7) without claiming this specific project implements it — the two-department tree that *does* implement it lives in `hierarchical_agents.py` (29), a separate file.

None of these are bugs — the code runs and demonstrates the mechanism correctly — they're places where the shipped project is a simplified version of what the slide's diagram depicts.

---

## 8. Common Mistakes

- **Forgetting the reducer on the fan-out target field.** If `findings` were plain `list[dict]` instead of `Annotated[list[dict], operator.add]`, only the last `search_agent` instance to finish its superstep would "win" — the others' results would be silently discarded (21's default-overwrite trap), not merged.
- **Assuming `Send` payload can read parent state.** `SearchTaskState` only has `search_query` and `findings` — it does *not* include `topic`, `analysis`, or anything else from `ResearchState`. Each `Send` instance sees exactly the dict passed as its second argument, nothing more. If a search agent needs `topic` for context, it has to be included explicitly in the `Send(...)` payload.
- **Treating the quality loop's two exit checks as redundant/removable.** `quality_checker`'s own `approved = review.approved or state["iteration"] >= 2` and `quality_gate`'s `score >= 0.7 or iteration >= 2` look duplicated, but they answer different questions: the checker decides what to *tell the user* (`approved` flag, used nowhere else in this file but meaningful if extended), the gate decides whether to *keep looping*. Removing the gate's own `iteration >= 2` check and relying solely on `score >= 0.7` would risk an infinite loop if the LLM never scores high enough — the gate needs its own independent cap, it can't just trust the checker's `approved` field (which isn't even returned to state at all here, only `score`/`feedback`/`iteration` are).
- **Confusing this Blackboard *loop* with the Blackboard *fan-in* at `analyst`.** Both are the same communication pattern (28) — read shared state instead of receiving a direct message — but one reads it once (Analyst reading `findings` after a barrier) and the other reads it repeatedly across a cycle (Report Writer reading `quality_feedback` on each revision). Same pattern, different shape (fan-in vs. loop).

---

## 9. Interview Questions

**Q: When would you reach for `Send` instead of a normal conditional edge with a fixed set of destination nodes?**
A: When the *number* of parallel branches depends on runtime data the graph can't know about until a node has executed — e.g., "however many search queries the supervisor decided to plan" rather than a fixed roster of named agents. A normal conditional edge picks among a fixed set of named destinations; `Send` creates N independent instances of the *same* node, each with its own scoped payload.

**Q: Why does `search_agent` use a different `TypedDict` (`SearchTaskState`) than the rest of the graph (`ResearchState`)?**
A: Because each `Send("search_agent", payload)` call seeds that instance's state from `payload` alone — it never gets the parent graph's full `ResearchState`. Scoping it to just what the node actually needs (`search_query`, `findings`) both documents the real contract and prevents accidentally depending on fields that were never passed in.

**Q: What guarantees does LangGraph give about node execution order after a `Send` fan-out, and what would break without them?**
A: It waits for every dynamically spawned instance to finish (the "automatic barrier") before running the node(s) downstream of them — same superstep-barrier guarantee as static fan-in. Without it, `analyst` could start synthesizing before all the search results existed, and without the `operator.add` reducer on `findings`, whichever instance finished last would overwrite the others instead of all results being merged.

**Q: This project has two places that check whether to stop the report-revision loop — `quality_checker`'s internal `approved` computation and `quality_gate`'s routing condition. Why not just one?**
A: They serve different roles: `quality_checker` decides what the *review result* should say (could be surfaced to a caller as an `approved` flag), while `quality_gate` decides whether the *graph itself* keeps cycling. The gate needs its own hard iteration cap independent of the checker's judgment — otherwise a model that never scores `>= 0.7` would loop indefinitely, since nothing else in the graph would force a stop.

---

## 10. Quick Revision

- **`Send(node_name, payload)`** returned from a router function (in place of a node-name string) gives **dynamic fan-out**: the number of parallel branches is decided at runtime by a node's own logic, not fixed at graph-build time like `add_edge`.
- Each `Send` instance runs with **only** the `payload` dict as its state — narrower than the parent graph's full state, hence the separate `SearchTaskState` type.
- LangGraph applies an **automatic barrier**: everything downstream of a fan-out (`search_agent → analyst`) waits until *all* dynamically spawned instances finish, exactly like static fan-in.
- The barrier is why the fanned-out field (`findings`) needs an `operator.add` reducer (21) — concurrent writers, one shared list, no reducer means silent overwrite.
- `multi_agent_research_system.py` (the Section 4 capstone) chains: **Supervisor** (plans, 26) → **dynamic `Send` fan-out** (parallel search, this doc) → **Blackboard fan-in** (Analyst reads shared `findings`, 28) → **Report Writer ⇄ Quality Checker Blackboard loop** (iterative refinement via shared `quality_feedback`, capped at `iteration >= 2` to guarantee termination, 22).
- Real gaps vs. the slide: query count is hardcoded to 3 (not actually dynamic yet), search agents fabricate findings rather than calling a real search tool (24's tool-calling gap still open), and there's no hierarchical sub-supervisor layer in this particular file (that's `hierarchical_agents.py` / 29, separately).
