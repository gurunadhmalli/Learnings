# LangSmith — Observability & Tracing for LangGraph Systems

> From course slides ("The Problem: Flying Blind", "Why LLM Debugging is Hard", "What IS Observability?", "Traces: The Full Story", "Why This Matters NOW", "Enter: LangSmith"). The slide's own trace example is `multi_agent_research_system.py` (30) — Supervisor → 3 parallel search agents → Analyst → Writer → Quality → Revised — so this doc treats 30's capstone project as the running example throughout. 28 §6 and 07 already named LangSmith as "the production answer to observability" in passing; this is the dedicated doc that was missing.

## Table of Contents
1. [The Problem: Flying Blind](#1-the-problem-flying-blind)
2. [Why LLM Debugging Is Hard](#2-why-llm-debugging-is-hard)
3. [What IS Observability? — Traces, Metrics, Evals](#3-what-is-observability--traces-metrics-evals)
4. [Traces: The Full Story](#4-traces-the-full-story)
5. [Why This Matters NOW](#5-why-this-matters-now)
6. [Enter: LangSmith](#6-enter-langsmith)
7. [Common Mistakes](#7-common-mistakes)
8. [Interview Questions](#8-interview-questions)
9. [Quick Revision](#9-quick-revision)

---

## 1. The Problem: Flying Blind

Traditional software has a straight line from symptom to fix:

```
Bug → Stack trace → Line 47 → Fix
```

An LLM application doesn't:

```
Bad answer → ??? → Which agent? → Which prompt? → ???
```

The slide's line for this: *"Without observability, you're debugging by reading the final output and guessing."* There's no exception, no stack trace, no line number — just a report that reads wrong, with no pointer into the graph that produced it.

This gets worse in proportion to the system's own complexity. `multi_agent_research_system.py` (30) — the project this whole doc traces — is not a toy: **5+ nodes** (`supervisor`, `search_agent`, `analyst`, `report_writer`, `quality_checker`), **3 parallel agents** (the `Send`-dispatched `search_agent` instances, 30 §1), a **quality loop** (`report_writer ⇄ quality_checker`, 30 §3), and **8+ LLM calls per run** (1 supervisor + 3 search + 1 analyst + 1–3 writer passes + 1–3 quality checks). If the final report is wrong, "which of those 8+ calls caused it?" is not a question `print()` statements answer well.

---

## 2. Why LLM Debugging Is Hard

| Property | What it means | Consequence |
|---|---|---|
| **Non-deterministic** | Same input can produce different outputs | The bug might not reproduce on your next run |
| **Cascading errors** | Bad search → bad analysis → bad report | The root cause is 4 steps back from where the symptom shows up |
| **Silent failures** | No crash — just a confident, wrong answer | No error, no exception, nothing to catch in a try/except |
| **Cost surprises** | 10 iterations instead of 2 | 5x your expected token budget, discovered on the bill, not in a log |

Each of these has a direct hook into 30's project:

- **Non-deterministic**: `supervisor()`'s LLM call can plan different `search_queries` on two runs with the same `topic`, which cascades into different `findings`, different `analysis`, different `report` — the whole pipeline downstream of one non-deterministic call inherits its variance.
- **Cascading errors**: this is exactly the `search_agent → analyst → report_writer` chain (30 §3). If one `search_agent` instance fabricates a bad finding (30 §7 already flags that findings are fabricated by the LLM, not fetched by a real tool), `analyst` synthesizes it in as if it were real, and `report_writer` drafts a report built on it — three steps removed from where the actual bad data originated.
- **Silent failures**: `quality_checker` (30 §5) force-approves once `iteration >= 2` *regardless of score* — a report that scored 0.4 on both passes ships with no error, no flag, nothing distinguishing it in the output from a report that scored 0.9 on the first pass. The `approved` field exists but (per 30 §8) isn't even wired to anything outside the function.
- **Cost surprises**: nothing in `multi_agent_research_system.py` counts tokens or cost per node. The `iteration` cap keeps it bounded at 2 revision passes, but for the loop types in 22 that *don't* have a state-level cap and don't use `recursion_limit` either (a gap 22 §9 and the docs README's Gaps section both already flag), "10 iterations instead of 2" is a real, currently-unmeasured risk.

---

## 3. What IS Observability? — Traces, Metrics, Evals

> Understanding what your system is doing — the entire journey, not just the final answer.

| **Traces** — *what happened* | **Metrics** — *how much it cost* | **Evals** — *was it good?* |
|---|---|---|
| Agent flow | Token count | Correctness |
| Inputs/outputs | Latency per node | Relevance |
| Tool calls | Cost per run | Human feedback |
| Decisions made | Error rates | Regression detection |

These three answer three different questions, and none substitutes for another:

- **Traces** tell you *what the system did* — which nodes ran, in what order, with what data. This is the thing §1's "no stack trace for bad answers" complaint is actually asking for.
- **Metrics** tell you *what it cost to do that* — tokens, latency, dollars, failure rate. This is what would have caught 30's untracked cost-surprise risk from §2.
- **Evals** tell you *whether the outcome was actually good* — not "did it run," but "was the report correct, relevant, and better than last week's." This is the layer `quality_checker`'s LLM-as-judge score (30 §5) is a manual, single-run version of; a real eval suite runs that judgment across many inputs over time and tracks drift.

---

## 4. Traces: The Full Story

> Every step, every input, every output, every millisecond.

The slide's trace timeline is the exact shape of 30's project graph, rendered as an execution record instead of a graph diagram:

```
Supervisor    Search 1     Search 2   Search 3    Analyst      Writer     Quality    Revised
(planned 3  → (3 findings) (2 findings)(3 findings)→ (synthesized) → (drafted) → (0.6) → (0.8 ✓)
 queries)
```

Compare this directly to 30 §3's graph diagram: `Supervisor → [search_agent × 3] → Analyst → Report Writer ⇄ Quality Checker → END`. A trace is that same topology, but every box now carries a *record* instead of just a *name* — this is what `demo_research_with_streaming()` (30 §5) partially gives you today by printing each node's output as it streams, and what LangSmith gives you automatically and persistently (§6) without hand-rolled print statements.

The `Quality (0.6) → Revised (0.8 ✓)` pair in the trace is 30's refinement loop (§3, §8) caught in the act: first pass scored below the `0.7` threshold in `quality_gate`, looped back to `report_writer` with `quality_feedback` on shared state (the Blackboard read, 28), and the second pass cleared the bar. Without a trace, all you'd see is the final `0.8` report — the fact that there *was* a rejected first draft, and why it was rejected, would be invisible.

**Example: Search Agent 1 trace** — the level of detail one single node call gets:

```
Input:   "climate change research papers 2024"
Tool:    web_search (latency: 1.2s)
Output:  3 results with abstracts
Tokens:  input=45, output=890
Cost:    $0.003
```

Map this onto the real `search_agent(state: SearchTaskState)` function (30 §5): `Input` is the `search_query` field `Send` seeded this instance with (30 §1's per-instance payload, *not* the parent `ResearchState`), `Output` is the `findings` list this instance returns, and `Tokens`/`Cost` are exactly the numbers 30's project currently has no way of reporting on its own. Note the slide's example shows a `web_search` tool call — this is the *intended* shape from the "Patterns Combined" slide, not what `search_agent()` actually does today; 30 §7 already flags that the current implementation fabricates findings from the LLM's own knowledge rather than calling a real tool. A trace would make that gap directly visible: the `Tool:` line would read `(none)` instead of `web_search`, immediately.

---

## 5. Why This Matters NOW

> Don't add observability AFTER something breaks. By then, you're firefighting — you're not actually doing engineering.

| Benefit | What it buys you |
|---|---|
| **Deploy with confidence** | You know what's happening inside, not just what came out the end |
| **Optimize with data** | Find which agents are slow — don't guess |
| **Catch regressions** | See behavior changes before users complain |
| **Prove ROI** | e.g. *"$0.12/report"* — a real number instead of an estimate |

Applied to 30's project specifically: "optimize with data" would tell you, with numbers, whether the 3 parallel `search_agent` instances (30 §1's dynamic fan-out) are actually the bottleneck or whether `report_writer`'s revision pass is — a question the code as written has no way to answer, because nothing in it times a node. "Prove ROI" is the natural next step after 30 §7's fabricated-findings gap gets closed with a real search tool: once real API calls are in the loop, cost per report stops being a guess and becomes something worth actually tracking per run.

---

## 6. Enter: LangSmith

Built by the LangChain/LangGraph team — the same team that owns every pattern this repo's docs 19–30 walk through. The pitch: **automatic tracing with 2 environment variables, no code changes required.**

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-key>
```

(Optionally `LANGSMITH_PROJECT=<name>` to route traces into a named project instead of the default.)

Set those, and **every graph already built in this repo is fully traced** — nothing in the graph-construction code changes:

| Pattern | Where it lives | Traced automatically |
|---|---|---|
| Supervisor pattern | `agent_handsoff.py` (26), `multi_agent_research_system.py`'s `supervisor` node (30) | ✓ |
| Handoff system | `agent_handsoff.py` (26) | ✓ |
| Parallel research | `parrallel_agent.py` (27 §3.1, static), `multi_agent_research_system.py`'s `Send` fan-out (30, dynamic) | ✓ |
| Quality loops | `multi_agent_research_system.py`'s `report_writer ⇄ quality_checker` cycle (30 §3) | ✓ |

This is the concrete payoff of the "Observable" property 28 §6 already named as one of Shared State's three production wins: *"the entire history of the task lives in one place — inspect the blackboard at any point... this is what makes a framework like LangGraph traceable in LangSmith: every node's write is a diff against one object, not a scattered set of point-to-point calls."* Because every node in a LangGraph app reads and writes one shared state object (21's reducer model), LangSmith doesn't need per-call instrumentation the way a hand-rolled multi-service pipeline would — it just watches the state diffs at each superstep, which is exactly the trace timeline in §4.

---

## 7. Common Mistakes

- **Treating a trace as an eval.** A trace tells you *what happened* (Supervisor planned 3 queries, Search 2 returned 2 findings); it does not tell you *whether the report was actually good*. That's §3's Evals column, a separate concern — LangSmith can host both, but they answer different questions and neither substitutes for the other.
- **Waiting until production breaks to turn tracing on.** §5's whole point: by the time a bad report reaches a user, you're reconstructing what happened after the fact instead of watching it happen. The 2 env vars are cheap enough that there's no reason not to have them on from the first `create_research_system()` run.
- **Assuming `quality_checker`'s score is the same thing as an eval suite.** It's a single LLM-as-judge call scoring one report on one run (30 §5) — useful as a gate, but it's not tracking whether that judgment is *consistent* across runs or drifting over time the way §3's "regression detection" column implies a real eval pipeline would.
- **Expecting tracing to fix non-determinism, not just explain it.** LangSmith makes a bad run *inspectable* — it doesn't make the underlying LLM call deterministic. §2's "bug might not reproduce" is still true with tracing on; the difference is that when it does happen, you have the trace instead of nothing.

---

## 8. Interview Questions

**Q: Why is "read the final output and guess" not a viable debugging strategy for a multi-agent LangGraph system, in a way it might almost work for a single LLM call?**
A: A single call has one input and one output — reading the output and reasoning backward to the prompt is feasible. A pipeline like 30's (`supervisor → 3× search_agent → analyst → report_writer ⇄ quality_checker`) has 8+ LLM calls and a cascading-error property (§2): a bad final report could originate in any of those calls, several steps upstream, and the failure produces no exception to point at it (§2's "silent failures"). Without a trace of each intermediate step, there's no way to localize which call actually went wrong.

**Q: What's the difference between traces, metrics, and evals, and why do you need all three?**
A: Traces show *what happened* (agent flow, inputs/outputs, tool calls, decisions — §3 col 1); metrics show *what it cost* (tokens, latency, cost, error rate — col 2); evals show *whether it was good* (correctness, relevance, human feedback, regression — col 3). A trace can show a run completed successfully and cheaply while still being wrong (needs evals); metrics can show a run was slow without telling you why (needs the trace to localize which node); none of the three alone answers "should I ship this."

**Q: Why does LangGraph's shared-state design make LangSmith tracing effectively free (2 env vars, no code changes), where a hand-rolled multi-agent pipeline with direct message passing would need custom instrumentation at every call site?**
A: Every node in a LangGraph app reads and writes the same state object via reducers (21, 28 §6) — a superstep's output is always a diff against that one object. LangSmith only has to watch state transitions at each superstep, one integration point, to reconstruct the full trace. Direct message passing (28 §1) has no single object to watch — A calling B directly is invisible to anything not specifically instrumented on that call, so N point-to-point wires would need N sets of manual instrumentation.

**Q: In `multi_agent_research_system.py`, `quality_checker` force-approves once `iteration >= 2` regardless of score (30 §5). Why is this specifically the kind of failure that tracing — not a try/except — is the right tool for?**
A: There's no exception to catch: the function runs to completion, returns a valid `QualityReview`, and the graph terminates cleanly (§2's "silent failure" — no crash, no error, just a confident wrong answer, or in this case a confidently *shipped* low-scoring one). Only a trace showing `Quality: 0.4 → (forced approve, iteration=2) → END` — rather than just the final report text — would surface that the report shipped despite failing its own quality bar.

---

## 9. Quick Revision

- Traditional software debugs via **Bug → Stack trace → Line 47 → Fix**; LLM apps have no equivalent — **Bad answer → ??? → Which agent? → Which prompt? → ???** (§1).
- Four properties make LLM debugging specifically hard: **non-deterministic** (won't always reproduce), **cascading errors** (root cause several steps upstream — 30's `search_agent → analyst → report_writer` chain), **silent failures** (no crash, just a wrong answer — 30's `quality_checker` force-approve), **cost surprises** (unbounded iteration = unbounded token spend) (§2).
- Observability has three distinct legs — **traces** (what happened), **metrics** (what it cost), **evals** (was it good) (§3) — and none of the three substitutes for the others.
- A **trace** is a full record of every node's input, output, tool calls, tokens, and latency across a run — the same graph topology as 30 §3's diagram, but as an execution record instead of a static diagram (§4).
- The case for turning tracing on *before* something breaks, not after: **deploy with confidence, optimize with data instead of guessing, catch regressions before users do, and prove ROI with a real per-run cost number** (§5).
- **LangSmith**, built by the LangChain/LangGraph team, traces every graph in this repo automatically via two environment variables (`LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=...`) — no code changes, because every LangGraph node already reads/writes one shared, diffable state object (21, 28 §6) (§6).
