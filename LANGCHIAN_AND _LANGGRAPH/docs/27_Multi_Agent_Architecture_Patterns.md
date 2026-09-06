# Multi-Agent Architecture Patterns — Deep Dive

> From course slides ("Why Multi-Agent?", "Multi-Agent Patterns", "When to Use Multi-Agent", "The ReAct Pattern", "Binding Tools to LLMs"). This doc owns the **taxonomy** — the five named multi-agent patterns and when each earns its complexity. It deliberately doesn't re-explain ReAct or `bind_tools` mechanics in full; those are already covered in depth by [24_LangGraph_Tool_Calling_and_Agents.md](24_LangGraph_Tool_Calling_and_Agents.md), and this doc's §5–6 only recap them far enough to place them inside the bigger picture, with pointers back to 24 for the real detail. [26_LangGraph_MultiAgent_Handoff_Pattern.md](26_LangGraph_MultiAgent_Handoff_Pattern.md) is this repo's one *working* example of a pattern from the taxonomy below (Supervisor) — §2 maps it explicitly onto the slide's terms.

## Table of Contents
1. [Why Multi-Agent? Single Agent vs. Multi-Agent](#1-why-multi-agent-single-agent-vs-multi-agent)
2. [The Supervisor Pattern](#2-the-supervisor-pattern)
3. [The Full Pattern Taxonomy](#3-the-full-pattern-taxonomy)
4. [When to Use Multi-Agent](#4-when-to-use-multi-agent)
5. [Where ReAct Fits In](#5-where-react-fits-in)
6. [Where Tool Binding Fits In](#6-where-tool-binding-fits-in)
7. [Choosing a Pattern — Decision Guide](#7-choosing-a-pattern--decision-guide)
8. [Common Mistakes](#8-common-mistakes)
9. [Interview Questions](#9-interview-questions)
10. [Quick Revision](#10-quick-revision)

---

## 1. Why Multi-Agent? Single Agent vs. Multi-Agent

A **single agent** is one LLM, one system prompt, handling every part of a task — reasoning, research, writing, checking its own work. That works fine until the task has genuinely distinct phases or requires distinct expertise, at which point one prompt trying to do everything runs into three concrete failure modes:

| Single-agent failure | What it looks like in practice |
|---|---|
| **Confused by complexity** | A prompt covering research + writing + fact-checking gives weaker instructions for each than three prompts covering one job each — the model's attention and instruction-following budget is split across unrelated jobs |
| **No specialization** | The same tone/temperature/system prompt has to work for "search accurately" and "write persuasively," which pull in different directions |
| **Hard to debug** | When the final output is wrong, there's no way to tell whether the *research* was bad or the *writing* was bad — it's one opaque call |

A **multi-agent system** splits the work into specialized roles — e.g. Research, Writer, Reviewer — each with its own narrow prompt, coordinated by a **Supervisor**:

```
                    ┌──────────┐   ┌────────┐   ┌──────────┐
                    │ Research │   │ Writer │   │ Reviewer │
                    └────┬─────┘   └───┬────┘   └────┬─────┘
                         └──────────────┼─────────────┘
                                        ▼
                                 ┌────────────┐
                                 │ Supervisor │
                                 └────────────┘
```

This buys three things directly opposite the single-agent failure modes: **specialized** (each agent's prompt only needs to be good at one job), **modular** (add/remove/replace an agent without touching the others), and **debuggable** (a bad final answer can be traced to *which* agent produced the bad intermediate step, the same traceability argument [26 §2](26_LangGraph_MultiAgent_Handoff_Pattern.md#2-why-not-just-one-big-prompt) makes for the triage/specialist split).

The trade a multi-agent system makes for this: more LLM calls (cost + latency), more moving parts to orchestrate, and a new failure mode of its own — a bad *handoff* between agents can lose or corrupt context even when every individual agent behaves correctly.

---

## 2. The Supervisor Pattern

The slides' "Why Multi-Agent?" diagram names three worker agents (Research, Writer, Reviewer) reporting to one **Supervisor**. This is the same shape as `agent_handsoff.py`'s triage-agent system documented in full in [26](26_LangGraph_MultiAgent_Handoff_Pattern.md) — just with different role names:

| Slide's terms | `agent_handsoff.py`'s terms |
|---|---|
| Supervisor | `traige_agent` |
| Research / Writer / Reviewer (worker agents) | `sales_agent` / `support_agent` / `billing_agent` (specialists) |
| Supervisor decides *which worker acts next* | `with_structured_output()` + `Literal` decides *which specialist to route to* |

The general shape: the supervisor is a single node whose only job is to look at the current state (task, or conversation so far) and decide **who acts next** — it doesn't do the domain work itself. Each worker does one narrow job and reports back. The router pattern from [20_langgraph_conditional_edges_and_routing.md](20_langgraph_conditional_edges_and_routing.md) (`add_conditional_edges` + a `Literal`-typed decision) is the standard way to implement the supervisor's dispatch decision in LangGraph — see [26 §3](26_LangGraph_MultiAgent_Handoff_Pattern.md#3-the-handoff-decision--structured-output-as-a-router) for the exact Pydantic model and routing code.

One structural difference worth flagging: `agent_handsoff.py` routes triage → specialist → `END` (single hop, no return trip). A Research/Writer/Reviewer pipeline more naturally loops back through the supervisor after each worker finishes (research done → supervisor → writer → supervisor → reviewer → supervisor → done), which is the cyclic-graph extension [26 §6](26_LangGraph_MultiAgent_Handoff_Pattern.md#6-wiring-it-together) flags as future work — edge each worker back to the supervisor node instead of straight to `END`, using the same loop-anatomy pieces (loop body, progress field, router, exit condition) from [22_LangGraph_Cycles_and_Loops_Deep_Dive.md](22_LangGraph_Cycles_and_Loops_Deep_Dive.md). This looped shape is exactly what `supervisor_agent.py` (§2.3 below) implements for real.

### 2.1 The Diagram, Generalized

The slide states the same shape in its most generic form — `Agent A/B/C` instead of named roles, because the pattern doesn't care what the workers *are*:

```
                  User Query
                      │
                      ▼
              ┌──────────────┐
              │  Supervisor  │  ◄── decides which agent to call
              └──────┬───────┘
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Agent A │ │ Agent B │ │ Agent C │
    └─────────┘ └─────────┘ └─────────┘
```

Read literally, this is a star topology (§3's term) with exactly one decision point — the Supervisor box is the *only* place in the diagram where a choice gets made; every other arrow is a fixed dispatch or return. The slide's own gloss for that one decision point: **"Supervisor, the head of the department of the company, and each department [is one of the agents]"** — i.e. the Supervisor doesn't do the department's work, it just knows which department a given request belongs to.

### 2.2 Supervisor Responsibilities

The companion slide breaks the Supervisor's one box in §2.1's diagram into five concrete responsibilities — this is the job description behind "decides which agent to call":

| # | Responsibility | Slide's subtext |
|---|---|---|
| 1 | **Understand the task** | Parse user intent and requirements |
| 2 | **Break it into subtasks** | Decompose complex work into steps |
| 3 | **Route to appropriate agent** | Select the right specialist |
| 4 | **Collect and synthesize results** | Combine agent outputs |
| 5 | **Decide when task is complete** | Know when to stop and respond |

None of these are abstract — every one of them is a specific piece of code in `supervisor_agent.py` (§2.3):

| # | Responsibility | Where it lives in `supervisor_agent.py` |
|---|---|---|
| 1 | Understand the task | The `supervisor()` node's `system_prompt` (lines 46–55) — it's handed the running `state["messages"]` and told what each specialist is for, so the LLM call that follows is reasoning about *this* conversation's intent, not a generic one |
| 2 | Break it into subtasks | Implicit in the loop shape, not an explicit decomposition step: the supervisor is re-invoked after *every* worker (`researcher → supervisor`, `writer → supervisor`, `critic → supervisor`, lines 178–180), so "the plan" emerges one hop at a time rather than being planned upfront |
| 3 | Route to appropriate agent | The `RouteDecision` Pydantic model + `Literal["researcher","writer","critic","FINISH"]` (lines 34–38), enforced via `llm.with_structured_output(RouteDecision)` (line 40) — same router-as-structured-output mechanism as [26 §3](26_LangGraph_MultiAgent_Handoff_Pattern.md#3-the-handoff-decision--structured-output-as-a-router) |
| 4 | Collect and synthesize results | The `finalize()` node (lines 140–147) — walks `state["messages"]` in reverse looking for the last `[Writer]`-tagged message and returns it as `final_response` |
| 5 | Decide when task is complete | `decision.next == "FINISH"` inside `supervisor()` (line 65) sets `task_complete: True`; `route_to_agent()` (lines 151–154) checks that flag *before* checking which agent was named, so `task_complete` always wins and routes to `finalize` |

### 2.3 A Second Working Example — `supervisor_agent.py`

Unlike `agent_handsoff.py` (single hop, triage → specialist → `END`), `supervisor_agent.py` is the looped version §2 predicted: `researcher`/`writer`/`critic` all edge back to `supervisor`, and the supervisor keeps getting re-invoked — with the *entire* accumulated `messages` list as context — until it emits `FINISH`. Structurally:

```
START → supervisor ⇄ {researcher, writer, critic} → supervisor → ... → finalize → END
```

Two things worth noting when reading this file as a reference implementation:

- **The `next_agnet` typo (line 66).** On the `FINISH` branch, the return dict sets `"next_agnet"` (misspelled) instead of `"next_agent"`, so `state["next_agent"]` is never actually updated to `"FINISH"`. It's harmless here only because `route_to_agent()` checks `state.get("task_complete")` *first* and returns `"finalize"` before ever reading `next_agent` — but it's a reminder that `TypedDict` gives no compile-time protection against key typos in the returned partial-state dict, the same class of bug [21](21_LangGraph_Accumulated_State_Explanation.md) flags for reducer-merged state in general.
- **Worker prompts are re-derived from a message-list slice, not passed explicitly.** `researcher()` pulls the *first* `HumanMessage` (line 94–96, the original task), while `writer()` and `critic()` join the *last 5* / *last 3* messages respectively (lines 115, 133) as their `context`. This is an implicit, hand-rolled version of "give each worker only the context it needs" — it works for this demo's short conversations, but nothing bounds it as the conversation grows, unlike a designed context-window strategy.

---

## 3. The Full Pattern Taxonomy

The Supervisor pattern is one of five named multi-agent architectures. This course (per the slide's footer) focuses on Supervisor specifically, but knowing where it sits among the others is exactly the kind of thing interviewers probe for.

| Pattern | Description | Typical use case | Control flow shape |
|---|---|---|---|
| **Supervisor** | One agent coordinates others — decides who acts next, workers don't talk to each other directly | Complex workflows with a clear coordinator role | Star: supervisor ⇄ each worker |
| **Hierarchical** | Multiple *levels* of supervisors — a top supervisor delegates to sub-supervisors, each coordinating their own team of workers | Large organizations / large systems where one supervisor would itself become a bottleneck | Tree: supervisor → sub-supervisors → workers |
| **Collaborative** | Agents communicate peer-to-peer, no single coordinator — each can see and respond to what others produce | Creative tasks where ideas benefit from cross-pollination (e.g. brainstorming, iterative critique) | Mesh: agent ⇄ agent, no fixed center |
| **Sequential** | Agents process strictly in order, each one's output is the next one's input, like a pipeline | Pipelines with a fixed, linear order of operations (e.g. extract → transform → summarize) | Chain: A → B → C |
| **Parallel** | Agents work simultaneously on independent sub-tasks, results merged afterward | Speed optimization when sub-tasks don't depend on each other | Fan-out / fan-in: dispatch → [A, B, C] concurrently → merge |

Expanding on how each maps to LangGraph primitives already used elsewhere in this repo:

- **Supervisor** — `add_conditional_edges` off a router node, as in §2 above and [26](26_LangGraph_MultiAgent_Handoff_Pattern.md) in full.
- **Hierarchical** — nested supervisors, i.e. a supervisor node whose "worker" is itself a compiled sub-graph containing its *own* supervisor + workers. LangGraph supports compiling a graph and using it as a node in a parent graph, which is exactly what this pattern needs — the top-level supervisor doesn't need to know the sub-supervisor's internal structure, only that it accepts a task and returns a result.
- **Collaborative** — no single router; typically modeled as a shared-state loop where every agent reads the same accumulating `messages` list ([21_LangGraph_Accumulated_State_Explanation.md](21_LangGraph_Accumulated_State_Explanation.md)) and each turn some policy (round-robin, or an LLM "who should speak next" call) picks the next speaker. Structurally this is a loop like [22](22_LangGraph_Cycles_and_Loops_Deep_Dive.md)'s loop types, just with the router choosing among *peers* instead of choosing "continue vs. stop."
- **Sequential** — the simplest case: plain `add_edge(A, B)` chains, no conditional routing needed at all — this is exactly LCEL's `|` composition ([03_pipe_operator.md](03_pipe_operator.md)) generalized to whole agents instead of chain steps.
- **Parallel** — LangGraph supports fan-out by adding edges from one node to multiple downstream nodes (they run concurrently) and fan-in by having a downstream node depend on all of them; this is the graph-native version of `RunnableParallel` from [07_Chains.md](07_Chains.md), scaled up to full agents instead of individual LCEL steps.

### 3.1 Map-Reduce — A Concrete Parallel Pattern (`parrallel_agent.py`)

The Parallel row above has two working examples in this repo, both in `parrallel_agent.py`:

| Function | Shape | What's parallel |
|---|---|---|
| `create_parallel_research()` (lines 28–107) | fan-out → 3 *different* jobs → fan-in (`synthesize`) | Research/Creative/Technical agents, matching §2.1's star diagram but with no supervisor — there's no routing decision, every branch always runs |
| `create_map_reduce_summarizer()` (lines 143–183) | `map` → `reduce` | The *same* job (summarize) applied to N independent documents |

The second is the classic **Map-Reduce** pattern: apply one operation across many independent inputs (map), then combine the per-input results into one output (reduce). Worth a deep dive because the obvious assumption — "it exists to save tokens" — is wrong, or at best incomplete.

**What problem it actually solves.** Not primarily token cost. Its real job is scale: getting past context-window limits, running independent work in parallel for latency, isolating failures to a single unit of work, and letting cheap/expensive models handle different stages. Token savings are a side effect that shows up *sometimes*, not the mechanism itself.

| Problem | How Map-Reduce helps |
|---|---|
| **Context-window limits** | 10,000 documents can't fit in one prompt. Map-Reduce turns it into 10,000 small calls (or a hierarchical tree of map → reduce-batches → final-reduce) instead of one impossible call. |
| **Latency (parallelism)** | Three 5-second document calls run sequentially take ~15s; run concurrently they take ~5s. This only pays off if the map step is *actually* dispatched concurrently — see the code note below. |
| **Specialization** | `create_parallel_research()`'s three agents each get a narrow prompt (facts / ideas / implementation) instead of one prompt trying to do all three jobs — the same argument §1 makes for multi-agent generally. |
| **Reliability** | One giant request either fully succeeds or fully fails. N independent map calls let you retry just the one that failed instead of redoing everything. |
| **Fault isolation** | Same idea at data-record scale — if customer 357 of 1,000 fails, retry 357, not the batch. |
| **Model tiering (real cost lever)** | Run map with a cheap/fast model (per-document summarization is low-stakes) and reduce with a stronger model (final synthesis is where quality matters most). This — not token count — is the more reliable way Map-Reduce actually saves money. |
| **Rate limits** | Capping map concurrency (e.g. 10 workers) lets you stay under an API's requests/minute ceiling instead of firing 10,000 requests at once. |

**The token-cost nuance.** Map-Reduce *can* shrink the final prompt: 100 docs × 2,000 tokens can't be sent in one call, but summarizing each to ~200 tokens first means the reduce step only sees 100 × 200 = 20,000 tokens. But the map stage still pays the original 200,000 input tokens (plus its own output tokens) — Map-Reduce compresses what reaches the *final reasoning step*, it doesn't make the underlying processing free. Done carelessly it can even cost *more*: 100 map calls + 1 reduce call = 101 LLM calls, versus maybe 10 calls if you'd batched documents into larger chunks instead. So the right mental model isn't "Map-Reduce = cheaper" — it's:

```
LARGE PROBLEM → independent pieces → process in parallel → compress results → combine results
```

i.e. **Map-Reduce is a scalability/decomposition technique**; cost has to be optimized separately (batching, model tiering, concurrency limits), same as reliability and latency are optimized independently in any distributed system.

**A real bug in `map_summarize()` (lines 146–157).** It's named and shaped like a map step but isn't actually parallel — it's a plain `for` loop calling `llm.invoke()` once per document, so all N calls run sequentially. True parallelism here needs either `asyncio.gather()` over `llm.ainvoke()` calls, LCEL's `RunnableParallel`, or — for the production-grade version — LangGraph's `Send` API, which dynamically fans out one node per document at runtime. `Send`-based fan-out is also where the [reducer](21_LangGraph_Accumulated_State_Explanation.md) concept stops being optional: each dynamically-dispatched `Send` writes to the *same* `summaries` key concurrently, so `MapReduceState` would need `summaries: Annotated[list[str], operator.add]` instead of a plain `list[str]` — without a reducer, LangGraph can't merge N concurrent writes to one key (see the `add_messages` discussion this doc's reducer questions came from).

---

## 4. When to Use Multi-Agent

| Good fit | Overkill for |
|---|---|
| Complex tasks with distinct phases | Simple Q&A |
| Need for specialized expertise per phase | Single-domain tasks |
| Parallel processing opportunities | Low-latency requirements |
| Human-like team dynamics (a task naturally maps to "roles") | |

The underlying trade is always **cost/latency vs. control/quality**. Every extra agent hop is at minimum one more LLM call — more money, more time, one more place for the conversation to lose context between hops. That's a bad trade for a single-turn factual question (just answer it), and it's an actively harmful trade when a user is waiting on a fast response (a chat widget that needs to reply in under a second has no room for a 4-hop supervisor chain). It's a good trade exactly when the task has enough internal structure — distinct phases, distinct expertise needed per phase, or independent sub-tasks that can run in parallel — that splitting it up buys more in quality/debuggability than it costs in the extra round-trips.

This is the same cost/benefit judgment [24 §9](24_LangGraph_Tool_Calling_and_Agents.md#9-common-mistakes) makes about unbounded ReAct loops, one level up: every additional hop (tool call *or* agent handoff) is latency and cost that has to be justified by what it buys you.

---

## 5. Where ReAct Fits In

**ReAct** (**Rea**soning + **Act**ing) is the loop *inside* a single agent, not a multi-agent pattern itself — it's how one agent (e.g. the "Research" worker in §1's diagram) decides when it has done enough to stop:

```
Question → Thought → Action → Observation → Thought → ... → Answer
             │          │           │
         reasoning   call tool   tool result
```

The agent reasons about what it needs, takes an action (calls a tool), observes the result, and reasons again — repeating until it has enough information to answer. This is documented in full, with working LangGraph code (`call_model` / `should_continue` / `ToolNode` / the `agent ⇄ tools` graph), in [24 §7](24_LangGraph_Tool_Calling_and_Agents.md#7-wiring-the-full-react-loop-by-hand); [22 §6](22_LangGraph_Cycles_and_Loops_Deep_Dive.md#6-type-4--agentic-tool-calling-loop-react) covers the same loop conceptually as one of the five loop archetypes.

The relationship between this doc's taxonomy and ReAct: **ReAct is what happens *inside a node*; the patterns in §3 are about how *multiple nodes* (agents) relate to each other.** A Supervisor-pattern worker agent is very often itself a ReAct agent internally — e.g. the "Research" worker doesn't just answer from memory, it runs its own Thought → Action(search) → Observation loop before reporting back to the supervisor. Nothing prevents nesting: a Sequential pipeline's second stage, a Collaborative pattern's each peer, or a Hierarchical pattern's each sub-supervisor's workers can all independently be ReAct loops.

---

## 6. Where Tool Binding Fits In

Tool binding is the mechanism that makes the "Action" step of ReAct possible: `@tool` turns a Python function into something an LLM can request, and `bind_tools()` attaches that tool's schema to the LLM so it *can* request it.

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"

llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools([search])
```

| Step | What it does |
|---|---|
| `@tool` decorator | Wraps the function; its **docstring becomes the tool's description** — the only thing the LLM reads to decide when to use it |
| `bind_tools([...])` | Attaches the tool's JSON schema to every request this LLM instance makes, so the model *can* choose to call it |
| Result | The LLM can now decide, per-request, whether to answer directly or emit a `tool_calls` entry requesting `search` |

This is a condensed recap — the full mechanics (reading `response.tool_calls`, matching `tool_call_id`, `ToolNode`, the difference from `with_structured_output()`) live in [24 §2–5](24_LangGraph_Tool_Calling_and_Agents.md#2-defining-a-tool); this doc's point is narrower: tool binding is what a **worker agent** uses internally to *act*, same as §5's ReAct loop — it's a building block one level below the multi-agent taxonomy in §3, not an alternative to it. A Supervisor's dispatch decision (§2) and a worker's tool call (this section) look superficially similar — both are "the LLM chooses one option from a set" — but they solve different problems, exactly as [26 §7](26_LangGraph_MultiAgent_Handoff_Pattern.md#7-how-this-differs-from-the-react-tool-calling-loop) contrasts handoff-routing against tool-calling.

---

## 7. Choosing a Pattern — Decision Guide

A quick decision path from task shape to pattern, using §3's taxonomy:

1. **Do sub-tasks have a fixed, linear order where each needs the previous one's output?** → **Sequential**.
2. **Are sub-tasks independent of each other and only need merging at the end?** → **Parallel**.
3. **Is there one natural "coordinator" role that decides who does what next, and is the team small enough for one coordinator to manage directly?** → **Supervisor**.
4. **Would that one coordinator itself become a bottleneck — too many workers, or workers that themselves need their own sub-teams?** → **Hierarchical** (supervisor of supervisors).
5. **Is there no natural single coordinator, and does the task benefit from agents reacting to each other's output freely (brainstorming, critique, iteration)?** → **Collaborative**.

And underneath whichever pattern is chosen, §4's table still gates the decision one level up: if the task is simple Q&A, single-domain, or latency-sensitive, the answer to all five questions above is "don't — use one agent."

---

## 8. Common Mistakes

- **Reaching for multi-agent before confirming the task actually has distinct phases.** If one well-written prompt already handles the task, a Supervisor + workers setup is pure overhead — more cost, more latency, more places to debug, for no quality gain. Check §4 before designing anything.
- **Picking Supervisor by default without checking if it's the right shape.** A strictly linear task (extract → transform → summarize) doesn't need a coordinator making a decision at each step — it needs Sequential, which is cheaper and simpler (no routing LLM call at all, just fixed edges).
- **Building Collaborative when Supervisor would do.** Peer-to-peer mesh communication is harder to reason about and debug than a star topology with one coordinator — reserve it for tasks that genuinely benefit from agents seeing and reacting to each other's output, not as a default "more advanced" choice.
- **Flattening a Hierarchical problem into one Supervisor.** A single supervisor directly managing a dozen workers has the same "confused by complexity" problem §1 describes for single agents — if a supervisor's own dispatch logic is getting complicated, that's the signal to introduce a layer of sub-supervisors instead of one bigger routing prompt.
- **Confusing ReAct (§5) and tool binding (§6) with the multi-agent patterns in §3.** ReAct is a loop inside one agent; tool binding is what makes that loop's "Action" step possible. Neither is itself a multi-agent pattern — a single-agent ReAct system and a five-agent Supervisor system can each independently use (or not use) tool calling.
- **Ignoring latency budget.** Every pattern except a trivial single-hop Sequential adds LLM round-trips; a Hierarchical system in particular can chain many hops (top supervisor → sub-supervisor → worker → back up) before answering. Not the right choice under a hard low-latency requirement, per §4's "Overkill For" column.

---

## 9. Interview Questions

**Q: What concrete problems does splitting a single agent into a multi-agent system solve?**
A: Three, per §1: a single prompt covering multiple unrelated jobs gets confused by the combined complexity, can't specialize its tone/instructions per job, and produces failures that are hard to attribute to a specific cause. Splitting into specialized agents each with a narrow prompt fixes all three — at the cost of more LLM calls and an orchestration layer.

**Q: Name the five multi-agent patterns and one distinguishing trait of each.**
A: Supervisor (one coordinator dispatches to workers), Hierarchical (multiple levels of supervisors, for when one coordinator becomes a bottleneck), Collaborative (peer-to-peer, no fixed coordinator), Sequential (strict pipeline order, each agent's output feeds the next), Parallel (independent sub-tasks run concurrently, merged after).

**Q: When would you choose Hierarchical over a single Supervisor?**
A: When the team is large enough, or workers specialized enough, that one supervisor's dispatch logic itself becomes complex to reason about — the same "confused by complexity" problem that motivated moving away from a single agent in the first place, just one layer up. Splitting into sub-supervisors, each managing a smaller team, keeps each coordinator's job narrow.

**Q: How does ReAct relate to the Supervisor pattern — are they the same thing?**
A: No. ReAct is the reasoning/acting loop *inside* one agent (deciding when to call a tool and when it has enough to answer). Supervisor is about *which agent* handles the next step of a multi-agent workflow. They compose: a Supervisor's individual worker agents are very often themselves ReAct agents internally.

**Q: Give a concrete example of a task that's "overkill" for multi-agent, and explain why.**
A: A single-turn factual question in a low-latency chat widget. It's simple Q&A (no distinct phases to split across agents), single-domain (no need for per-phase specialization), and latency-sensitive (every extra agent hop is a full LLM round-trip the user is waiting on) — all three of §4's "Overkill For" conditions apply at once.

**Q: In LangGraph terms, what's the structural difference between implementing Sequential vs. Supervisor?**
A: Sequential is just fixed `add_edge(A, B)` chains — no routing decision, no conditional logic, the order is baked into the graph shape. Supervisor needs a router node using `add_conditional_edges` (per [20](20_langgraph_conditional_edges_and_routing.md)) whose destination is decided at runtime by an LLM call (typically via `with_structured_output()` + `Literal`, per [26 §3](26_LangGraph_MultiAgent_Handoff_Pattern.md#3-the-handoff-decision--structured-output-as-a-router)) — the path through the graph isn't fixed at compile time.

---

## 10. Quick Revision

- **Single agent fails at complexity, specialization, and debuggability** once a task has genuinely distinct phases — that's the motivating problem multi-agent systems solve.
- **Five named patterns**: Supervisor (star, one coordinator), Hierarchical (tree, supervisors of supervisors), Collaborative (mesh, peer-to-peer), Sequential (chain, fixed pipeline order), Parallel (fan-out/fan-in, independent sub-tasks merged).
- **This repo has two working Supervisor examples**: `agent_handsoff.py` (single-hop triage → specialist → `END`, documented fully in [26](26_LangGraph_MultiAgent_Handoff_Pattern.md)) and `supervisor_agent.py` (§2.3 — looped, worker → supervisor → worker... until `FINISH`). The slide's five **Supervisor Responsibilities** (understand → decompose → route → synthesize → decide-when-done, §2.2) map onto `supervisor_agent.py`'s `supervisor()`, worker-loop shape, `RouteDecision`, `finalize()`, and `task_complete` flag respectively.
- **The Parallel pattern's working example is `parrallel_agent.py`** (§3.1): fan-out/fan-in with specialized agents (`create_parallel_research`), and Map-Reduce over homogeneous inputs (`create_map_reduce_summarizer`). Map-Reduce's purpose is scale (context-window limits, latency via concurrency, fault isolation, model tiering) — **not** primarily token savings, and its `map_summarize()` is a bug example of a map step that looks parallel but runs sequentially.
- **When to use multi-agent**: distinct phases, need for specialized expertise, parallelizable sub-tasks, human-like team roles. **When it's overkill**: simple Q&A, single-domain tasks, low-latency requirements — always weigh against the extra LLM calls and orchestration cost.
- **ReAct is orthogonal to the taxonomy** — it's the Thought→Action→Observation loop *inside* one agent (full detail in [24](24_LangGraph_Tool_Calling_and_Agents.md)), not a way agents relate to each other. Any worker in any of the five patterns can independently be a ReAct agent.
- **Tool binding (`@tool` + `bind_tools()`) is the building block under ReAct** — it's what lets a single agent's "Action" step actually be a callable function, one level below the multi-agent patterns entirely.
- **Decision order**: check §4 first (does this even need multiple agents?), then use §7's questions to pick which of the five patterns fits the task's actual shape — don't default to Supervisor just because it's the most commonly taught pattern.
