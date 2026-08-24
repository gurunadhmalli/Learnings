# Phase 6 — Agentic AI

**Weeks 38–41 · ~170 hours**

An agent is an LLM in a loop with tools and a stopping condition. That's it — the difficulty is entirely in **reliability**. Demos are easy; agents that work on the 200th run are hard.

---

## 6.1 Foundations of agency (Week 38, ~40h)

### The core loop
```
observe → think → act → observe → ... → stop
```
Everything else is engineering around this.

- **Tool use / function calling** — schema design, argument validation, execution, result formatting. Tool descriptions are prompts; write them as carefully.
- **ReAct** — interleaved reasoning and acting; the foundational pattern
- Plan-and-execute vs interleaved; when upfront planning helps and when it locks in mistakes
- Reflexion / self-critique loops; verifier models
- **Stopping conditions** — max steps, budget caps, no-progress detection, explicit termination tool. *An unbounded agent is a bug.*
- Error handling: tool failure, malformed arguments, retries with feedback, graceful degradation
- Cost and latency ceilings enforced in code, not in the prompt

### Agent architectures
- Single agent with tools (start here — it's usually enough)
- Router / dispatcher patterns
- **Multi-agent:** supervisor-worker, hierarchical, debate, swarm. Understand that multi-agent multiplies failure modes; use it when tasks genuinely decompose, not because it sounds sophisticated.
- Human-in-the-loop: approval gates on consequential actions, interrupt-and-resume
- Workflow vs agent — a **deterministic workflow with LLM steps is more reliable than an agent** for most tasks. Choose agency deliberately, only when the path can't be known in advance.

### Memory
- Short-term: conversation buffer, windowing, summarization, and context compaction
- Long-term: vector memory, episodic vs semantic, entity/fact stores, memory write policies (what's worth remembering?)
- Scratchpads and external state files
- **Context engineering** — the discipline that replaced prompt engineering: what goes in the window, in what order, at what cost, with what compaction strategy

### Tools & environments
- **MCP (Model Context Protocol)** — the emerging standard for exposing tools/resources to models; learn to build an MCP server
- Code execution as the universal tool — sandboxing (Docker, gVisor, Firecracker, E2B), resource limits, network policy
- Browser automation (Playwright), computer use
- API integration, auth handling, least-privilege credentials
- Retrieval as a tool rather than a fixed pipeline step

---

## 6.2 Frameworks (Week 39, ~40h)

Learn the patterns, then pick one. Frameworks churn; the patterns don't.

- **LangGraph** — explicit graph/state machine, checkpointing, human-in-the-loop, time travel. Best fit for production control flow.
- **LangChain** — large ecosystem, LCEL; useful for integrations, heavy for core logic
- **LlamaIndex** — strongest for RAG-centric agents and data connectors
- **CrewAI**, **AutoGen / AG2**, **OpenAI Agents SDK**, **Claude Agent SDK**, **Pydantic AI**, **Smolagents** (code-as-action)
- **DSPy** — programmatic optimization of prompts/pipelines instead of hand-tuning
- **Temporal / durable execution** — for long-running agents that must survive restarts

**Do this once:** build the same agent twice — once with a framework, once with plain API calls and a `while` loop (~200 lines). You'll understand what the framework is actually doing and when it's earning its complexity.

---

## 6.3 Reliability engineering for agents (Week 40, ~45h)

This is the part nobody teaches and every company needs.

### Evaluation
- **Trajectory evaluation** — was the sequence of actions correct, not just the final answer?
- Final-outcome evaluation with programmatic checks wherever possible
- Tool-call accuracy: right tool, right arguments, right order
- Step-level attribution: which step introduced the error?
- Benchmarks to know: SWE-bench, GAIA, WebArena, τ-bench, AgentBench
- Building your own eval set from real traces — golden trajectories
- Regression testing: replay recorded scenarios in CI

### Observability
- Distributed tracing across LLM calls, tool calls, and retries (OpenTelemetry semantics for GenAI)
- Token, latency, and cost attribution per step and per session
- Langfuse / LangSmith / Phoenix / Braintrust
- Session replay for debugging

### Failure modes and their fixes
| Failure | Cause | Fix |
|---|---|---|
| Infinite loop | No progress detection | Step cap + repeated-state detection + explicit finish tool |
| Tool thrash | Ambiguous tool descriptions | Rewrite descriptions; reduce tool count; add examples |
| Context overflow | No compaction | Summarize, offload to files, prune old turns |
| Compounding error | Long horizons; 95% per step ≈ 36% over 20 steps | Shorten horizons, add verification steps, checkpoint |
| Silent wrong answer | No verification | Programmatic checks, second-model verification |
| Cost explosion | Unbounded retries | Hard budget enforcement in the loop |
| Prompt injection via tool output | Trusting retrieved content | Treat all tool output as untrusted data, never as instructions |

- **The reliability math:** independent per-step success $p$ over $n$ steps gives $p^n$. Reducing step count is usually more effective than improving per-step accuracy.

### Security for agents
- Least-privilege tool access; scoped credentials per session
- The "lethal trifecta": private data + untrusted content + external communication — avoid having all three in one agent
- Approval gates for irreversible actions (payments, deletions, emails)
- Sandboxed execution, egress filtering
- Audit logging of every action taken on a user's behalf

---

## 6.4 Advanced patterns (Week 41, ~45h)

- Reasoning models (o-series, R1-style) — when extended thinking helps vs wastes tokens; test-time compute scaling
- Self-improving loops: agents that write and run their own evals
- Code agents: repo understanding, retrieval over codebases, patch generation, test-driven agent loops
- Computer-use / GUI agents and their reliability ceiling
- Multi-agent orchestration: shared state, message passing, conflict resolution, termination
- Simulation and synthetic user testing for agent QA
- Caching and memoization of deterministic tool calls
- Streaming partial results and progressive disclosure in agent UX
- Fallback ladders: agent → workflow → human

---

## Phase 6 deliverables

1. **Agent from scratch** — no framework, ~200 lines: tool registry, JSON schema validation, the loop, step/budget caps, error recovery, tracing. Your reference implementation forever.
2. **Production agent** — pick a genuinely useful task (research assistant over your own document corpus, a data-analysis agent that writes and executes SQL/Python, a codebase Q&A + patch agent). Requirements: LangGraph or equivalent, human approval gate on writes, full tracing, cost caps, and a **trajectory eval suite of ≥30 scenarios running in CI**.
3. **An MCP server** exposing a real tool set, usable from a compatible client.
4. **Reliability writeup** — run your agent 100 times on the same eval set, report success rate, categorize every failure, then implement three fixes and re-report. The before/after table is the deliverable.

---

## Phase 6 exit checklist

- [ ] Implement the agent loop from scratch without reference
- [ ] Explain why a deterministic workflow often beats an agent
- [ ] Compute expected success over 15 steps at 96% per-step accuracy
- [ ] Explain the "lethal trifecta" and how you'd break it in a design
- [ ] Design a trajectory eval for a multi-step task
- [ ] Explain what MCP standardizes and why it matters
- [ ] Name five agent failure modes and their fixes, from memory
- [ ] Explain context compaction strategies and their tradeoffs
