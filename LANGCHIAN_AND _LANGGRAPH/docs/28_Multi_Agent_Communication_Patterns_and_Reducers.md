# Multi-Agent Communication — Message Passing, Shared State & Reducers

> From course slides ("How Do Agents Talk?", "Three Communication Patterns", "Reducers - The Secret Sauce"). [27_Multi_Agent_Architecture_Patterns.md](27_Multi_Agent_Architecture_Patterns.md) answers *who talks to whom* (Supervisor, Hierarchical, Collaborative, Sequential, Parallel). This doc answers a different question that sits underneath all five of those: once you've decided which agents exist, **how does data actually move between them**, and **what happens when two agents try to write at the same time**. [21_LangGraph_Accumulated_State_Explanation.md](21_LangGraph_Accumulated_State_Explanation.md) already covers the `operator.add` reducer in isolation; this doc places it inside the full reducer taxonomy (§3) and connects it back to real code already in this repo (`supervisor_agent.py`, `parrallel_agent.py`).

## Table of Contents
1. [How Do Agents Talk? Two Fundamental Approaches](#1-how-do-agents-talk-two-fundamental-approaches)
2. [The Three Communication Patterns](#2-the-three-communication-patterns)
3. [Reducers — The Secret Sauce](#3-reducers--the-secret-sauce)
4. [Grounding This in the Repo's Code](#4-grounding-this-in-the-repos-code)
5. [Writing a Custom Reducer](#5-writing-a-custom-reducer)
6. [How This Is Used in Production](#6-how-this-is-used-in-production)
7. [Choosing a Communication Pattern — Decision Guide](#7-choosing-a-communication-pattern--decision-guide)
8. [Common Mistakes](#8-common-mistakes)
9. [Interview Questions](#9-interview-questions)
10. [Quick Revision](#10-quick-revision)

---

## 1. How Do Agents Talk? Two Fundamental Approaches

Every multi-agent framework has to answer one plumbing question: when Agent A finishes, how does its output get in front of Agent B? There are exactly two fundamental answers, and every named pattern in §2 is a variation on one of them.

### 1.1 Direct Message Passing

```
┌─────────┐   msg   ┌─────────┐
│ Agent A │ ──────▶ │ Agent B │
└─────────┘         └─────────┘
```

Agent A calls Agent B directly (a function call, an API call, a queued message addressed *to* B) and hands it a payload. This is the intuitive, naive approach — it's how you'd wire two independent scripts together with no framework at all.

| Problem | Why it happens |
|---|---|
| **Tightly coupled** | A has to know B exists, know its interface, and know to call it. Swapping B for a different agent, or inserting a new agent C between them, means editing A's code. |
| **Hard to scale** | Add a fourth agent and you're now managing N² potential point-to-point wires instead of N agents talking to one shared place. Nobody outside the A→B call can observe what was sent without instrumenting that call specifically. |

### 1.2 Shared State (the Blackboard)

```
┌─────────┐  write   ┌───────────────────────┐   read   ┌─────────┐
│ Agent A │ ───────▶ │      SHARED STATE      │ ◀─────── │ Agent B │
└─────────┘          │      (The Blackboard)  │          └─────────┘
                      │  research:  "..."      │
                      │  analysis:  "..."      │
                      │  decisions: [...]       │
                      └───────────────────────┘
```

Agent A doesn't call Agent B at all — it writes its result into a shared structure (the **blackboard**), and Agent B independently reads whatever it needs from that same structure. Neither agent needs to know the other exists; they only need to agree on the shape of the shared state.

| Benefit | Why it follows from the design |
|---|---|
| **Decoupled** | A only knows about the blackboard's schema, never about B. Add, remove, or reorder readers/writers without touching A's code. |
| **Observable** | The entire history of the task lives in one place — inspect the blackboard at any point and see exactly what every agent has contributed so far. This is what makes a framework like LangGraph traceable in LangSmith: every node's write is a diff against one object, not a scattered set of point-to-point calls. |
| **Scalable** | Adding a tenth agent means adding a tenth reader/writer of the same structure, not nine new point-to-point wires. |

The slide's own analogy: **think of an office** — people don't each individually phone every colleague whose work might matter to theirs; they write into shared documents, dashboards, and trackers that anyone in the relevant department can read. LangGraph's `StateGraph` *is* the blackboard: the `TypedDict` you pass to `StateGraph(...)` is the shared structure, and every node is a person walking up to write on it or read from it, exactly like [26](26_LangGraph_MultiAgent_Handoff_Pattern.md)'s and [27](27_Multi_Agent_Architecture_Patterns.md)'s worker agents already do — this doc is naming the mechanism those docs were already using.

**The one-sentence takeaway that matters for everything below:** in LangGraph specifically, you are *always* using Shared State — there is no direct-message-passing mode. What §2 calls "Message Passing" is not a different transport mechanism; it's the special case of Shared State where the shared field happens to be called `messages`.

---

## 2. The Three Communication Patterns

| Pattern | How It Works | When to Use |
|---|---|---|
| **Message Passing** | Agents append to a shared `messages` list | Conversational workflows, chat agents |
| **Shared State** | Agents read/write typed state fields | Structured pipelines, data processing |
| **Blackboard** | Combination: shared workspace + messages | Complex multi-agent collaboration |

### 2.1 Message Passing

Every agent's contribution is appended to one growing list of messages — the same list an LLM's chat history is built from. In LangGraph this is a `TypedDict` field typed as `Annotated[list[BaseMessage], add_messages]` (§3.3 covers the reducer in depth). Each agent reads the *entire conversation so far* and appends its own turn, exactly like a group chat where everyone can scroll back through everything that's been said.

```python
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def agent_b(state: ChatState) -> dict:
    reply = llm.invoke(state["messages"])   # sees full history
    return {"messages": [reply]}             # appended, not replacing history
```

Best fit: **conversational workflows** — support bots, multi-turn chat agents, anything where "what was said, in what order" *is* the state, and every participant benefits from seeing the raw transcript rather than a structured summary of it.

### 2.2 Shared State

Instead of one undifferentiated list, each agent reads and writes specific **typed fields** — `research_result: str`, `sentiment_score: float`, `line_items: list[dict]`. There's no transcript; there's a structured record, closer to a form each agent fills in one field of.

```python
class PipelineState(TypedDict):
    raw_text: str
    extracted_entities: list[str]
    sentiment: str
    summary: str

def extractor(state: PipelineState) -> dict:
    return {"extracted_entities": run_ner(state["raw_text"])}

def sentiment_agent(state: PipelineState) -> dict:
    return {"sentiment": classify(state["raw_text"])}
```

Best fit: **structured pipelines and data processing** — each stage produces a well-defined, machine-readable artifact rather than a chat turn, and there's rarely a need to replay "the conversation" because there wasn't one; there's a document being progressively filled in.

### 2.3 Blackboard

The combination: a shared **conversational** `messages` list for the parts of the task that are genuinely dialogue-shaped, *plus* shared **typed** fields for the parts that are structured data — coexisting in the same `TypedDict`. This is the pattern most real multi-agent systems converge on once they outgrow a pure chat transcript, because most real tasks aren't *all* conversation or *all* structured data — they're both at once.

```python
class BlackboardState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]   # the conversation
    research: str                                            # structured field
    analysis: str                                            # structured field
    decisions: Annotated[list[str], operator.add]            # accumulating log
```

Best fit: **complex multi-agent collaboration** — a Supervisor-orchestrated system ([27 §2](27_Multi_Agent_Architecture_Patterns.md#2-the-supervisor-pattern)) is very often a Blackboard in practice: the `messages` list carries the running dialogue (what each worker said, what the supervisor decided), while dedicated fields (`next_agent`, `task_complete`, `final_response`) carry the structured control-flow data the supervisor's routing logic depends on. §4 shows this is exactly what `supervisor_agent.py` already does.

---

## 3. Reducers — The Secret Sauce

> "Reducers control **how** state gets updated when multiple agents write."

### 3.1 The problem reducers solve

A `StateGraph`'s default behavior for any key is **overwrite**: whatever the most recent node returned for that key becomes the new value, and the old value is discarded. That's the right behavior sometimes (a `status` field should reflect the *latest* status, full stop) — but it's actively wrong the moment two agents are meant to be *contributing to* the same key rather than *replacing* it.

Concretely: if `findings: list[str]` uses the default overwrite behavior, and Agent A returns `{"findings": ["fact 1"]}` followed by Agent B returning `{"findings": ["fact 2"]}`, the final state has only `["fact 2"]` — Agent A's contribution is silently gone. Nothing crashes; nothing warns you. This is the single most common state-management bug in a LangGraph multi-agent system, and it's exactly why reducers exist: a **reducer is the merge function LangGraph runs instead of overwrite**, every time a node returns a value for that key.

### 3.2 The four reducer types

| Reducer | Behavior | Example |
|---|---|---|
| **Default (overwrite)** | Last write wins | `status: str` |
| **`operator.add`** | Appends to list (or adds numbers) | `findings: Annotated[list, operator.add]` |
| **`add_messages`** | Smart message merge | `messages: Annotated[list, add_messages]` |
| **Custom function** | Any merge logic you define | `votes: Annotated[dict, merge_votes]` |

**Default (overwrite).** No `Annotated` wrapper at all — just `status: str`. Correct whenever a field represents "the current value of X," where X genuinely has only one true value at a time (a task's current phase, the last agent to act, a running total you intentionally want *replaced* rather than accumulated).

**`operator.add`.** `Annotated[list[str], operator.add]` merges by concatenation (`old + new`); on `int`/`float` fields it merges by addition. This is [21](21_LangGraph_Accumulated_State_Explanation.md)'s full topic — read that doc for the mechanics and a worked step-by-step trace. Right for logs, running counters, and any "keep appending, never lose a prior entry" field where **order and dedup don't matter** — which is exactly where it falls short for chat history (see next row).

**`add_messages`.** LangGraph's purpose-built reducer for the `messages` field, imported from `langgraph.graph.message`. It looks like `operator.add` (both append) but does meaningfully more:

- **Appends by default**, same as `operator.add`, for any message that's new.
- **Updates in place** rather than duplicating, if an incoming message shares an `id` with one already in the list — this is what lets a node *edit* an earlier message (e.g. attach a tool result to the AI message that requested it) instead of always appending a fresh entry.
- **Understands `RemoveMessage`** — a sentinel value that deletes a message by `id` from the accumulated list, which is how LangGraph implements message trimming/pruning without you hand-rolling list surgery.

This is *why* `messages` almost never uses plain `operator.add` in real code: chat history needs id-aware merge/update/delete semantics that concatenation alone can't express. `supervisor_agent.py` (§4) uses `add_messages` for exactly this reason.

**Custom function.** Anything `operator.add` and `add_messages` can't express — the signature is always `(current_value, new_value) -> merged_value`, and LangGraph calls it with the accumulated state so far and whatever the latest node returned. `merge_votes` from the slide's example is the classic case: several agents each cast a vote, and combining them isn't concatenation (you'd get duplicate voter keys) or addition (votes are a dict, not a number) — it's domain-specific merge logic only you can define. See §5 for a full worked example.

---

## 4. Grounding This in the Repo's Code

The slides' three patterns and four reducers aren't abstract — this repo already has two working examples that land on opposite corners of the taxonomy.

| File | Pattern (§2) | Reducer(s) used | Why |
|---|---|---|---|
| `supervisor_agent.py` | **Blackboard** | `messages: Annotated[list[BaseMessage], add_messages]` (conversational) + plain `next_agent: str`, `task_complete: bool`, `final_response: str` (overwrite) | The running dialogue between supervisor and workers needs id-aware merge (`add_messages`); the routing/control fields each have exactly one true current value, so overwrite is correct for them. This is a textbook Blackboard: conversation + structured control data, same `TypedDict`. Documented in full in [27 §2.3](27_Multi_Agent_Architecture_Patterns.md#23-a-second-working-example--supervisor_agentpy). |
| `parrallel_agent.py`'s `ParallelState` | **Shared State** | All fields (`research_result`, `creative_result`, `technical_result`, `final_synthesis`) use **default overwrite** | No reducer needed here — and that's the interesting part. Because the three parallel agents each write to a *different, dedicated field* rather than a shared field, there's no concurrent-write conflict for a reducer to resolve in the first place. Overwrite is correct because each field only ever receives one write. |

That second row is worth sitting with: **the need for a non-default reducer isn't about parallelism, it's about key collision.** `parrallel_agent.py`'s three agents *do* run concurrently (§3.1 of [27](27_Multi_Agent_Architecture_Patterns.md#31-map-reduce--a-concrete-parallel-pattern-parrallel_agentpy)), but because each one owns its own field, plain overwrite is fine. A reducer only becomes necessary the moment **two or more writers target the same key** — which is exactly the situation [27 §3.1](27_Multi_Agent_Architecture_Patterns.md#31-map-reduce--a-concrete-parallel-pattern-parrallel_agentpy) flags as a real gap in that file's `map_summarize()`: a `Send`-based fan-out over documents would need `summaries: Annotated[list[str], operator.add]`, because *then* every dynamically-dispatched branch really would be writing to the same `summaries` key.

---

## 5. Writing a Custom Reducer

A reducer is just a plain Python function with the signature `(current, new) -> merged`. You wire it into state the same way as any built-in reducer — `Annotated[Type, your_function]` — and LangGraph calls it automatically every time a node returns a value for that key.

```python
from typing_extensions import TypedDict, Annotated

def merge_votes(current: dict[str, int], new: dict[str, int]) -> dict[str, int]:
    """Combine per-agent vote tallies instead of overwriting or concatenating."""
    merged = dict(current)
    for option, count in new.items():
        merged[option] = merged.get(option, 0) + count
    return merged

class VotingState(TypedDict):
    votes: Annotated[dict[str, int], merge_votes]

def agent_a(state: VotingState) -> dict:
    return {"votes": {"approve": 1}}

def agent_b(state: VotingState) -> dict:
    return {"votes": {"approve": 1, "reject": 1}}

# After both run (in either order): {"approve": 2, "reject": 1}
# Plain overwrite would leave only whichever agent ran last.
# operator.add on a dict isn't even defined — dicts don't support `+`.
```

Two things worth internalizing from this example:

- **Order matters conceptually, not just mechanically.** `merged = dict(current)` then folding `new` into it means "new" always has the chance to add to an existing tally rather than clobber it — get this backwards (`merged = dict(new)` folding `current` in) in a reducer with asymmetric merge logic and you'd silently invert which write "wins" ties, a much subtler bug than the overwrite problem §3.1 describes because it only shows up when both sides disagree.
- **A custom reducer is the general escape hatch**, not a last resort to be avoided. `operator.add` and `add_messages` are just two pre-built custom reducers LangGraph ships because they're needed so often (lists/counters, chat history) — reach for a hand-written one the moment your merge logic is domain-specific (deduping by a business key, taking a max/min, weighted averaging, resolving conflicting agent recommendations by confidence score).

---

## 6. How This Is Used in Production

The slide framing ("decoupled / observable / scalable" for Blackboard) is not marketing — each of those three properties maps to a concrete production concern.

| Production concern | How Shared State / Blackboard addresses it |
|---|---|
| **Debuggability & tracing** | Because every agent's output lands in one inspectable structure, a tool like LangSmith can show the *entire* state diff at every node — not just "agent B was called," but exactly which keys changed and what the values were before/after. Direct message passing has no equivalent single place to look; you'd need to instrument every point-to-point call individually. |
| **Persistence & resumability** | LangGraph's checkpointer ([25](25_LangGraph_Advanced_Checkpointer_Patterns.md)) saves the *shared state*, not a call stack. That's what makes `interrupt()`/`Command(resume=...)` ([23](23_LangGraph_Human_in_the_Loop_Deep_Dive.md)) and `get_state_history()` time-travel possible at all — there's one object to snapshot. A direct-message-passing system has no natural "pause here and resume tomorrow" story, because the in-flight state is scattered across call stacks and closures, not one durable structure. |
| **Fault isolation & retries** | If a worker agent crashes mid-task, the blackboard already holds every other agent's completed contribution — you can retry just the failed agent's write, not the whole pipeline. This is the same fault-isolation argument [27 §3.1](27_Multi_Agent_Architecture_Patterns.md#31-map-reduce--a-concrete-parallel-pattern-parrallel_agentpy) makes for Map-Reduce, one level more general. |
| **Team scalability** | Different engineers/teams can own different agents that all read/write the same documented state schema without ever coordinating on point-to-point interfaces — the `TypedDict` schema *is* the contract between teams, the same role an API schema plays between services. |
| **Correctness under concurrency** | The moment a production system fans work out to run concurrently (parallel research agents, a `Send`-based map step over thousands of records), reducers stop being a nice-to-have and become the only thing standing between "10,000 concurrent writes merge correctly" and "9,999 of them silently vanish." This is precisely the gap flagged in `parrallel_agent.py`'s `map_summarize()` (§4) — real production fan-out needs `operator.add` or a custom reducer on every field more than one branch writes to. |
| **Schema evolution** | A structured Blackboard schema (§2.3) can be versioned and validated (e.g. via Pydantic models instead of a bare `TypedDict`) the way any production data contract is — a raw `messages` transcript can't be validated the same way, which is exactly why serious production systems keep conversational and structured data in *separate* fields of the same Blackboard rather than trying to parse structure back out of chat text. |
| **Cost/latency control** | An unbounded `messages` list under `add_messages` grows every turn — production systems combine it with `RemoveMessage`-based trimming or summarization-on-write (a custom reducer that compresses old turns instead of just appending) to keep the prompt sent to the LLM bounded, the same context-window concern [22](22_LangGraph_Cycles_and_Loops_Deep_Dive.md) and [27 §3.1](27_Multi_Agent_Architecture_Patterns.md#31-map-reduce--a-concrete-parallel-pattern-parrallel_agentpy) raise elsewhere. |

The pattern across all seven rows: **production multi-agent systems don't pick Shared State because it's theoretically elegant — they pick it because it's the only design that gives you observability and persistence for free**, as a side effect of there being exactly one structure to snapshot, diff, and inspect. Frameworks outside LangGraph converge on the same idea under different names — AutoGen's `GroupChatManager` shared conversation, CrewAI's shared task context, even classic AI blackboard systems from the 1980s (the term predates modern agents entirely) — because the underlying problem (decoupled contributors, one inspectable source of truth) is the same regardless of framework.

---

## 7. Choosing a Communication Pattern — Decision Guide

1. **Is the task fundamentally a dialogue — turn-taking where each participant needs the full prior conversation to respond sensibly?** → **Message Passing** (`messages` + `add_messages`).
2. **Is the task fundamentally a document being filled in — each agent contributes one well-defined, machine-readable piece with no need to "converse"?** → **Shared State** (typed fields, mostly default overwrite, `operator.add` only where a field is genuinely accumulated by more than one writer).
3. **Does the task have both — a real conversation *and* structured data the routing/control logic depends on?** → **Blackboard** (both `messages` and dedicated typed fields in the same state, as `supervisor_agent.py` already does).
4. **Once the shape is chosen, for every individual field ask: can more than one node write to this key?** If no → default overwrite is correct and adding a reducer is unnecessary complexity. If yes → pick `operator.add` (simple accumulation), `add_messages` (chat history specifically), or a custom function (anything else) per §3.2.

---

## 8. Common Mistakes

- **Using default overwrite on a field two agents both write to.** The single most common bug this doc exists to prevent (§3.1) — silent data loss with no error, no warning, just a missing contribution that's easy to misattribute to "the agent didn't produce output" when it actually did and got clobbered.
- **Using `operator.add` on `messages` instead of `add_messages`.** Works for simple append-only demos, but breaks the moment you need to update an existing message (e.g. attach a tool result) or trim history — `operator.add` can only ever append, never edit or delete by id.
- **Reaching for Message Passing when the task is really Shared State.** Cramming structured pipeline data (extracted entities, scores, structured records) into free-text chat turns means every downstream agent has to *re-parse* the last message to extract what it needs — brittle, and loses the type safety a dedicated field gives you for free. If it's not genuinely conversational, give it its own field.
- **Building a custom reducer that isn't commutative when the underlying writes can arrive in either order.** LangGraph doesn't guarantee your nodes' returns are merged in a specific order under concurrent fan-out; a custom reducer whose result depends on *which side is `current` vs. `new`* is a latent, hard-to-reproduce bug (§5's order-matters callout).
- **Letting an `add_messages`-reducer field grow unbounded in production.** Every appended turn is more tokens sent to the LLM on every subsequent call — the "smart merge" reducer solves *correctness* of the merge, not the separate cost/context-window problem of an ever-growing history (§6's last row).
- **Treating "Shared State" and "no coordination needed" as the same thing.** Shared State removes the need for agents to know about *each other*, but someone still has to design and document the schema every agent reads/writes — skipping that design step just moves the coupling from code (direct calls) into an undocumented, implicit contract about what each key means.

---

## 9. Interview Questions

**Q: What two fundamental approaches exist for agents to exchange data, and why does one dominate in practice?**
A: Direct message passing (A calls B with a payload) and shared state / the blackboard (A writes, B independently reads from a common structure). Shared state dominates because it decouples writers from readers, makes the entire task state observable in one place, and scales to N agents without N² point-to-point wires — direct message passing requires every sender to know its receiver's interface.

**Q: LangGraph's `StateGraph` is described as always using "shared state." How does that square with it also supporting "message passing"?**
A: They're not two different transport mechanisms — message passing in LangGraph *is* shared state, specialized to one field: a `messages` key using the `add_messages` reducer. Every LangGraph pattern, including pure chat agents, is built on the same underlying `TypedDict` + reducer machinery; "message passing" vs. "shared state" vs. "blackboard" (§2) describes what shape you give that shared structure, not a different plumbing layer underneath it.

**Q: What problem do reducers solve, concretely?**
A: LangGraph's default behavior for any state key is overwrite — the most recent node's return value replaces whatever was there. That's correct for "current value" fields but silently discards prior contributions the moment two agents are meant to be *adding to* the same key rather than replacing it (e.g. a shared `findings` list). A reducer replaces overwrite with an explicit merge function LangGraph calls on every write to that key.

**Q: Why does `messages` typically use `add_messages` instead of `operator.add`, even though both append?**
A: `operator.add` can only concatenate — it has no concept of message identity. `add_messages` is id-aware: if an incoming message shares an `id` with one already in the list, it updates that message in place instead of duplicating it, and it understands `RemoveMessage` sentinels for deleting a message by id. That's needed for things `operator.add` can't express, like attaching a tool result to an earlier AI message or trimming old turns from history.

**Q: When would you write a custom reducer instead of using `operator.add` or `add_messages`?**
A: Whenever the merge logic is domain-specific and isn't simple concatenation or chat-history semantics — deduping by a business key, taking a max/min across writers, weighted-averaging a score, or combining structured data like per-option vote counts (the `merge_votes: dict → dict` example) where neither addition nor concatenation is even defined for the type involved.

**Q: `parrallel_agent.py`'s three research agents write to `research_result`, `creative_result`, and `technical_result` respectively, and all three fields use default overwrite with no reducer. Is that a bug?**
A: No — the need for a non-default reducer comes from *key collision* (more than one writer targeting the same field), not from concurrency itself. These three agents run in parallel but each owns a distinct field, so there's no write to reconcile; overwrite (in effect, "the one and only write wins") is correct. A reducer would only become necessary if a future change had two of those agents both writing to one shared field.

---

## 10. Quick Revision

- **Two fundamental approaches**: Direct Message Passing (tightly coupled, hard to scale) vs. Shared State / Blackboard (decoupled, observable, scalable) — §1. LangGraph only implements the second; "message passing" inside LangGraph is just Shared State specialized to a `messages` field.
- **Three named patterns** (§2): Message Passing (`messages` + `add_messages`, for conversational workflows), Shared State (typed fields, for structured pipelines), Blackboard (both together, for complex multi-agent collaboration) — `supervisor_agent.py` is a working Blackboard example (§4).
- **Reducers solve the "who's write wins" problem** (§3): Default (overwrite, last write wins), `operator.add` (concatenate lists / add numbers, full mechanics in [21](21_LangGraph_Accumulated_State_Explanation.md)), `add_messages` (id-aware smart merge for chat history — update in place + `RemoveMessage` support, not just append), Custom function (`(current, new) -> merged`, for anything domain-specific like `merge_votes`).
- **A reducer is only needed when more than one writer targets the same key** — concurrency alone doesn't require one (`parrallel_agent.py`'s distinct per-agent fields, §4); key collision does.
- **This repo's two grounding examples**: `supervisor_agent.py` (Blackboard: `add_messages` for the conversation + overwrite for control fields) and `parrallel_agent.py` (Shared State: all overwrite, because no field is shared between writers).
- **Production value is observability + persistence, essentially for free** (§6): one inspectable structure means LangSmith can trace every state diff, and the checkpointer ([25](25_LangGraph_Advanced_Checkpointer_Patterns.md)) can snapshot/resume/time-travel the whole task, neither of which direct message passing offers without extra instrumentation.
- **Design order**: decide the communication *shape* first (§7, conversation vs. structured data vs. both), then decide per-field whether a reducer is needed at all, and only then pick which reducer — don't reach for a custom function before checking whether `operator.add` or `add_messages` already covers it.

---

**Related code in this repo:** [supervisor_agent.py](../supervisor_agent.py) (Blackboard + `add_messages`), [parrallel_agent.py](../parrallel_agent.py) (Shared State, fan-out/fan-in), [agent_handsoff.py](../agent_handsoff.py) (single-hop Supervisor, documented in [26](26_LangGraph_MultiAgent_Handoff_Pattern.md)).
