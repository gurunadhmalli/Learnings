# LangGraph Advanced Checkpointer Patterns — Deep Dive

> Builds on [23_LangGraph_Human_in_the_Loop_Deep_Dive.md](23_LangGraph_Human_in_the_Loop_Deep_Dive.md) (which covers `MemorySaver`, `thread_id`, and the `interrupt()`/`Command(resume=...)` pause mechanism conceptually, with no local code at the time it was written). Since then, [checkpoint.py](../checkpoint.py) and [human_in_loop.py](../human_in_loop.py) were added to the repo — this file documents what they actually do, which goes beyond what 23 covers: durable **SQLite** persistence, **time-travel** through checkpoint history, **branching** conversations, checkpoint internals, and an *older* pause style (`interrupt_before` + `update_state`) that predates the `interrupt()` function.

## Table of Contents
1. [Two Ways to Pause a Graph](#1-two-ways-to-pause-a-graph)
2. [`interrupt_before` + `update_state()` — the Static Pause](#2-interrupt_before--update_state--the-static-pause)
3. [`SqliteSaver` — Durable Persistence Across Restarts](#3-sqlitesaver--durable-persistence-across-restarts)
4. [`get_state_history()` — Time Travel Through Checkpoints](#4-get_state_history--time-travel-through-checkpoints)
5. [Anatomy of a Checkpoint Snapshot](#5-anatomy-of-a-checkpoint-snapshot)
6. [Branching Conversations from a Checkpoint](#6-branching-conversations-from-a-checkpoint)
7. [Rewinding to a Specific Checkpoint](#7-rewinding-to-a-specific-checkpoint)
8. [Common Mistakes](#8-common-mistakes)
9. [Interview Questions](#9-interview-questions)
10. [Quick Revision](#10-quick-revision)

---

## 1. Two Ways to Pause a Graph

[Doc 23 §6](23_LangGraph_Human_in_the_Loop_Deep_Dive.md#6-the-pause-mechanism-interrupt-and-commandresume) teaches the modern, *dynamic* pause: calling `interrupt()` from **inside** a node, at exactly the point the code decides it needs a human. `human_in_loop.py` instead uses the older, *static* pause: declaring, at `compile()` time, which named nodes the graph should always stop **before** running.

| | `interrupt()` (doc 23) | `interrupt_before=[...]` (`human_in_loop.py`) |
|---|---|---|
| Where the pause point is decided | Inside the node's own code, conditionally | At `compile()` time, as a fixed list of node names |
| How the graph pauses | Mid-node, via a function call | Before the named node even starts |
| How a human's decision gets in | `Command(resume=value)` — value returned directly from `interrupt()` | `app.update_state(config, {...})` — writes fields into state before resuming |
| How you resume | `app.invoke(Command(resume=value), config)` | `app.invoke(None, config)` — `None` means "no new input, just continue" |
| Flexibility | Can pause conditionally, anywhere in a node's logic | Always pauses before that node, every single time it's reached |

Both require the same two prerequisites from [doc 23 §3–5](23_LangGraph_Human_in_the_Loop_Deep_Dive.md#3-prerequisite-1--memorysaver-checkpointer): a checkpointer compiled in, and a `thread_id` in every call's config. `interrupt_before` is simpler to reach for when a node should *always* pause (e.g., "always review before sending"); `interrupt()` is more flexible when the decision to pause is conditional (e.g., "only pause if the amount exceeds $500").

---

## 2. `interrupt_before` + `update_state()` — the Static Pause

From `human_in_loop.py`'s `demo_interrupt_for_approval`:

```python
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["approval"],   # always pause right before this node runs
)

config = {"configurable": {"thread_id": "demo-1"}}

# Run 1: executes draft, then stops BEFORE approval runs
result = app.invoke({"request": "...", "draft": "", "approved": False, ...}, config)

# Human reviews result["draft"] out-of-band, decides to reject with feedback...
app.update_state(config, {"approved": False, "feedback": "Make it more concise"})

# Resume: None = "no new input, just continue from the checkpoint"
final_result = app.invoke(None, config)
```

`update_state()` writes directly into the checkpointed state dict — as if the `approval` node itself had returned `{"approved": False, "feedback": "..."}` — **without running any node's code**. This is the key difference from `interrupt()`'s return value: `interrupt()` hands a value back to code running *inside* the node, while `update_state()` mutates the state *from the outside*, before the paused node even starts.

`human_in_loop.py`'s `demo_iterative_review` composes this with a loop (same shape as [22](22_LangGraph_Cycles_and_Loops_Deep_Dive.md)'s retry loops): `interrupt_before=["submit"]` means the graph pauses **every time** it loops back to `submit`, so a human reviews each revision round before the next one starts — `apply → submit(⏸) → apply → submit(⏸) → ... → done`.

---

## 3. `SqliteSaver` — Durable Persistence Across Restarts

Doc 23 §3 names `SqliteSaver`/`PostgresSaver` as the production alternative to `MemorySaver` but doesn't show one. `checkpoint.py`'s `demo_sqlite_persistence` does:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string(db_path) as saver:
    app = graph.compile(checkpointer=saver)
    config = {"configurable": {"thread_id": "persistent-user"}}
    app.invoke({"messages": [HumanMessage(content="Remember: the secret code is ALPHA-7")]}, config)
# `with` block exits here — simulates the process ending

# Later — a brand new `with` block, a brand new SqliteSaver object,
# but the SAME db_path and the SAME thread_id:
with SqliteSaver.from_conn_string(db_path) as saver:
    app = graph.compile(checkpointer=saver)
    config = {"configurable": {"thread_id": "persistent-user"}}
    result = app.invoke({"messages": [HumanMessage(content="What was the secret code?")]}, config)
    # The LLM answers correctly -- it still has Turn 1 in its checkpointed history
```

The whole point of this demo: nothing about the **graph definition** changes between `MemorySaver` and `SqliteSaver` — same `compile(checkpointer=...)` call, same `thread_id`-keyed config. What changes is *where the bytes live*. `MemorySaver` keeps them in the Python process's RAM, so a second `with` block using a fresh `SqliteSaver` object pointed at the same file still finds Turn 1's message — proving the state survived past the first `saver` object's lifetime, standing in for a real process restart.

---

## 4. `get_state_history()` — Time Travel Through Checkpoints

Doc 23 says a checkpointer "persists state after every super-step" but doesn't show how to look at that history. `app.get_state_history(config)` returns every checkpoint ever saved for a thread, **most recent first**, as an iterator of state snapshots:

```python
for i, snapshot in enumerate(app.get_state_history(config)):
    print(f"Checkpoint {i}: {len(snapshot.values['messages'])} messages")
    if i >= 3:
        break
```

For a 2-node graph (`analyze → summarize`) run once, `checkpoint.py`'s `demo_checkpoint_internals` shows LangGraph actually saves **three** checkpoints for that single `invoke()` call, not one:

```
[checkpoint 0] initial input state           (BEFORE analyze runs)
[checkpoint 1] after analyze completes
[checkpoint 2] after summarize completes     (the "current" state you'd get from get_state())
```

This is the concrete mechanism behind the claim in [doc 23 §7](23_LangGraph_Human_in_the_Loop_Deep_Dive.md#7-the-paused-state--the-three-phases): checkpoints exist at every super-step boundary, not just at the final result — which is exactly what lets you pause or rewind to *any* of those intermediate points, not only the very end.

---

## 5. Anatomy of a Checkpoint Snapshot

Every object yielded by `get_state()` or `get_state_history()` is a `StateSnapshot` with six meaningful fields:

| Field | Meaning |
|---|---|
| `state.values` | Your actual `TypedDict` data at this point — the only field you'd normally touch in application code |
| `state.next` | Tuple of node names that will run next; `()` means the graph finished (or is fully resolved) at this checkpoint |
| `state.config` | The `{"configurable": {"thread_id": ..., "checkpoint_id": ...}}` dict that uniquely addresses *this specific* checkpoint |
| `state.parent_config` | Same shape, but pointing at the checkpoint that came immediately before this one — `None` only for the very first checkpoint |
| `state.metadata` | Provenance: `source` (why this checkpoint was written), `step` (super-step number), `writes` (which node just wrote, and what) |
| `state.created_at` | Timestamp the checkpoint was saved |

`state.parent_config` is what makes checkpoint history a **linked list**, not just a flat log:

```
[initial] ──parent──▶ [after analyze] ──parent──▶ [after summarize]
                                                          ▲
                                                    state.config (current)
```

Each snapshot only knows the checkpoint immediately behind it; walking `parent_config` repeatedly is how you'd reconstruct the full chain back to the start without calling `get_state_history()` at all.

---

## 6. Branching Conversations from a Checkpoint

Because a checkpoint's `values` is just a plain dict, you can copy it into a **different** `thread_id` and continue two independent conversations from the same starting point — `checkpoint.py`'s `demo_branching_conversations`:

```python
main_config = {"configurable": {"thread_id": "main"}}
app.invoke({"messages": [HumanMessage(content="What's the weather like?")]}, main_config)
main_state = app.get_state(main_config)

# Branch A: copy main's state into a NEW thread, then continue differently
branch_a_config = {"configurable": {"thread_id": "branch-beach"}}
app.update_state(branch_a_config, main_state.values)
result_a = app.invoke({"messages": [HumanMessage(content="What about a beach vacation?")]}, branch_a_config)

# Branch B: same starting point, different continuation
branch_b_config = {"configurable": {"thread_id": "branch-mountain"}}
app.update_state(branch_b_config, main_state.values)
result_b = app.invoke({"messages": [HumanMessage(content="What about mountain hiking?")]}, branch_b_config)
```

`main`, `branch-beach`, and `branch-mountain` are three independent save slots ([doc 23 §4](23_LangGraph_Human_in_the_Loop_Deep_Dive.md#4-prerequisite-2--thread_id-conversation-id)) that all share the same conversation *prefix* but diverge from that point on — exactly like branching a Git commit into two branches that share history up to the fork point.

---

## 7. Rewinding to a Specific Checkpoint

Every checkpoint has its own `checkpoint_id`, addressable independently of the "latest" one. Passing a specific `checkpoint_id` in the config lets you load — and resume from — a point *earlier* than the thread's current state, effectively undoing everything after it:

```python
# Find the checkpoint saved right after "analyze" ran
target_snapshot = next(
    s for s in app.get_state_history(config)
    if "analyze" in s.metadata.get("writes", {})
)
target_id = target_snapshot.config["configurable"]["checkpoint_id"]

rewind_config = {"configurable": {"thread_id": "internals-demo", "checkpoint_id": target_id}}
rewound_state = app.get_state(rewind_config)
print(rewound_state.next)   # ('summarize',) — we're back to BEFORE summarize ran

# Calling app.invoke(None, rewind_config) here would RE-RUN summarize
# with a fresh LLM call, discarding whatever the original run produced after this point.
```

This is the same "resume from a checkpoint" mechanism used for human-in-the-loop pauses in [doc 23](23_LangGraph_Human_in_the_Loop_Deep_Dive.md) — the only difference is *which* checkpoint you resume from. Resuming from the latest one continues forward normally; resuming from an older one **replays** everything after it, which is useful for "redo this step with different input" workflows (e.g., regenerate a summary without re-running the expensive analysis step).

---

## 8. Common Mistakes

- **Confusing `update_state()` with `interrupt()`'s resume value.** `update_state()` mutates state from outside, before a node runs; it does not make any node's code execute. `Command(resume=value)` (doc 23) hands `value` to code *waiting inside* a node's `interrupt()` call. Mixing up which pattern a given piece of code uses leads to state that's silently wrong rather than an error.
- **Assuming `SqliteSaver` needs different graph code than `MemorySaver`.** It doesn't — the entire point of the checkpointer interface is that `compile(checkpointer=X)` is the only line that changes. If you find yourself restructuring nodes to "support" SQLite, something's off.
- **Forgetting `get_state_history()` returns newest-first.** Iterating it directly gives you the most recent checkpoint at index 0, not the oldest — reverse it (or use `parent_config` walking) if you need chronological order.
- **Rewinding and then invoking without realizing it replays a node.** Resuming from a `checkpoint_id` that isn't the latest one will **re-execute** the pending node (an LLM call included) — this costs a fresh API call and can produce a different result than the original run, not the same one replayed.
- **Branching by mutating the original thread instead of copying to a new one.** `app.update_state(main_config, ...)` changes `main` itself. To branch, you must target a **different** `thread_id` in the config while reusing the source state's `values`.

---

## 9. Interview Questions

**Q: How many checkpoints does a single `.invoke()` call on a 2-node graph produce, and why?**
A: Three — one for the initial input state (before any node runs), and one after each of the two nodes completes. LangGraph checkpoints at every super-step boundary, not just once at the end.

**Q: What's the practical difference between `interrupt_before=["node"]` and calling `interrupt()` inside `"node"`?**
A: `interrupt_before` is a static, compile-time decision — that node *always* pauses before it runs, every time it's reached. `interrupt()` is a runtime decision made by the node's own code, so the same node can sometimes pause and sometimes not, based on its own logic (e.g., only pause if a dollar amount exceeds a threshold).

**Q: How would you implement "redo this step with a different prompt" using checkpoints?**
A: Find the checkpoint saved right before the step you want to redo (via `get_state_history()`, matching on `metadata["writes"]`), build a config with that checkpoint's `checkpoint_id`, optionally call `update_state()` to change relevant fields, then `invoke(None, that_config)` — this replays forward from that exact point.

**Q: What does `state.parent_config` let you do that `get_state_history()` doesn't already give you directly?**
A: It lets you walk the checkpoint chain one hop at a time from any single snapshot you already have in hand, without a second call to the checkpointer — useful when you only have one `StateSnapshot` object and want its immediate predecessor, not the whole history.

**Q: Why does switching from `MemorySaver` to `SqliteSaver` require no changes to node functions or graph structure?**
A: Because checkpointers all implement the same interface behind `compile(checkpointer=...)` — nodes and edges only ever read/write the `TypedDict` state; they have no awareness of how or where checkpoints are persisted. Persistence is a cross-cutting concern injected at compile time, not something node code participates in.

---

## 10. Quick Revision

- **Two pause styles:** `interrupt_before=[...]` (static, decided at compile time, resume with `invoke(None, config)`) vs. `interrupt()` (dynamic, decided inside the node, resume with `invoke(Command(resume=value), config)`) — [doc 23](23_LangGraph_Human_in_the_Loop_Deep_Dive.md) covers only the latter.
- **`update_state(config, {...})`** writes fields into checkpointed state from the outside, without running any node — different from `interrupt()`'s resume value, which is handed to code waiting *inside* a node.
- **`SqliteSaver.from_conn_string(path)`** is a drop-in replacement for `MemorySaver` — same `compile(checkpointer=...)` call, but checkpoints persist to disk and survive process restarts.
- **`get_state_history(config)`** returns every checkpoint for a thread, newest first — a graph checkpoints before the first node, and after every node completes.
- **`StateSnapshot` fields:** `values` (your data), `next` (pending nodes), `config`/`parent_config` (this checkpoint's and the previous checkpoint's addresses — a linked list), `metadata` (source/step/writes), `created_at`.
- **Branching** = copy a checkpoint's `values` into a *new* `thread_id` via `update_state()`, then continue independently — two threads sharing a common history prefix, like a Git branch point.
- **Rewinding** = resume from a `checkpoint_id` earlier than the current one; this re-executes every node from that point forward (fresh LLM calls included), it does not replay the original outputs verbatim.
