# LangGraph Conditional Edges & Routing — Deep Dive

> Builds on [19_langgraph-complete-beginner-guide.md](19_langgraph-complete-beginner-guide.md) §11 (Edges). That file gives you the basic definition; this one goes deep on *how routing actually works*, multi-way branching, and writing routers that don't break at runtime.

## Table of Contents
1. [Direct Edge vs Conditional Edge](#1-direct-edge-vs-conditional-edge)
2. [Why Conditional Edges Exist](#2-why-conditional-edges-exist)
3. [`add_conditional_edges` Syntax, Fully Broken Down](#3-add_conditional_edges-syntax-fully-broken-down)
4. [Using `Literal` Types for Type-Safe Routing](#4-using-literal-types-for-type-safe-routing)
5. [Multi-Way Branching (3+ Destinations)](#5-multi-way-branching-3-destinations)
6. [Common Mistakes](#6-common-mistakes)
7. [Full Worked Example](#7-full-worked-example)
8. [Interview Questions](#8-interview-questions)
9. [Quick Revision](#9-quick-revision)

---

## 1. Direct Edge vs Conditional Edge

LangGraph has exactly two ways to connect nodes.

| | Direct Edge | Conditional Edge |
|---|---|---|
| **Behavior** | A always goes to B | A goes to B *or* C, decided at runtime |
| **API** | `graph.add_edge("A", "B")` | `graph.add_conditional_edges("A", routing_fn, {...})` |
| **Decision point** | None — fixed wiring | A Python function inspects `state` and decides |
| **Diagram** | `A ──→ B` | `A ──?──→ B`  `└──?──→ C` |

**Direct edge** — the graph-building equivalent of just calling the next function. Use it when step 2 must *always* follow step 1, no exceptions (e.g., "after fetching data, always clean it").

**Conditional edge** — the graph-building equivalent of an `if/elif/else`. Use it whenever the next step depends on something you only know after the current node has run (data in the state, a classification result, a retry count, a validation flag).

---

## 2. Why Conditional Edges Exist

**Without conditions**, a graph is just a fixed pipeline — `A → B → C`, same path every single run, regardless of what's in the state. That's not fundamentally different from a plain function call chain (LCEL already does this fine — see [07_Chains.md](07_Chains.md)). You don't need a *graph* for a straight line.

**With conditions**, the same three nodes become a decision tree:

```
        ┌─ if X ──→ B
A ──────┼─ if Y ──→ C
        └─ else ───→ D
```

This is the entire reason LangGraph exists instead of just chaining Runnables: **dynamic control flow based on state**. Three things become possible that a linear chain cannot do:

- **Branching** — route to different nodes depending on a classification, a flag, or any computed value (e.g., "billing question → billing node, else → general node").
- **Loops** — a conditional edge can point *backwards* to a node that already ran: `{"retry": "generate", "good": END}`. If a check fails, go back and regenerate. That's a self-correcting agent loop, and it's structurally impossible in a straight-line chain.
- **Termination** — map a label to the special `END` node to stop the graph exactly when a condition is satisfied, instead of always running every node.

If you don't need any of that — your flow really is always the same sequence — a conditional edge is overkill; use direct edges.

---

## 3. `add_conditional_edges` Syntax, Fully Broken Down

```python
graph.add_conditional_edges(
    "check",           # 1. Source — the node whose output triggers the decision
    routing_function,  # 2. Router — a function that returns a label (string)
    {                  # 3. Mapping — label → actual destination node name
        "review": "review_node",
        "publish": "publish_node",
    },
)
```

### 3.1 The routing function

```python
def routing_function(state):
    if state["needs_review"]:
        return "review"
    else:
        return "publish"
```

Contract: it takes the **current state** (same shape as every node function) and returns a **string label**. It does *not* return a node name directly — it returns a label that gets looked up in the mapping dict. This is a deliberate indirection (see below).

### 3.2 The mapping dict

`{"review": "review_node", "publish": "publish_node"}` translates whatever label the router returns into the actual node to run next.

- Router returns `"review"` → LangGraph runs `review_node`.
- Router returns `"publish"` → LangGraph runs `publish_node`.
- Router returns anything **not** in the dict → runtime `KeyError` when the graph executes that edge (not at compile/`add_conditional_edges` time — see [§6](#6-common-mistakes)).

### 3.3 Why the extra indirection (label → node name) instead of returning the node name directly?

It decouples **decision logic** from **graph wiring**:

- The router only needs to know abstract outcomes ("review" vs "publish"), not the literal node names.
- You can rename `review_node` to `human_review_node` later and only touch the mapping dict — the routing function's logic doesn't change.
- The same routing function can be reused across graphs that wire the labels to different concrete nodes.

### 3.4 Visual flow (from the slide)

```
check ──→ router() ──→ "review" ──→ review_node
                    └── "publish" ──→ publish_node
```

`check` is the source node. After `check` finishes and updates state (e.g., setting `needs_review`), `router()` reads that state and returns a label, and the mapping sends execution to the matching node.

---

## 4. Using `Literal` Types for Type-Safe Routing

A router that just returns `str` gives you no safety net — a typo like `"revew"` compiles fine and only blows up at runtime. Annotating the return type with `typing.Literal` fixes that at the type-checker/IDE level:

```python
from typing import Literal

def router(state: State) -> Literal["path_a", "path_b", END]:
    if state["done"]:
        return END
    elif state["condition"]:
        return "path_a"
    else:
        return "path_b"
```

What this buys you:

- **IDE autocomplete** — your editor knows the only valid return values are `"path_a"`, `"path_b"`, or `END`, and will flag anything else.
- **Self-documenting router** — you can read the function signature and immediately see every possible destination without reading the function body.
- **Type-checker enforcement** — tools like `mypy`/`pyright` will error if a branch returns a string not in the `Literal`, catching a mismatch between the router and the mapping dict *before* runtime.

Note `END` appears inside the `Literal[...]` alongside the string labels — `END` is a special LangGraph sentinel (not a plain string you write yourself), used to terminate the graph. Mapping a label to `END` (or returning it directly, depending on your LangGraph version) ends execution instead of routing to another node.

`Literal` doesn't change runtime behavior at all — the function still just returns a string. It's purely a static-analysis / documentation aid. The actual runtime safety still comes from making sure every value the router can return exists as a key in the mapping dict passed to `add_conditional_edges`.

---

## 5. Multi-Way Branching (3+ Destinations)

Conditional edges aren't limited to two outcomes. The mapping dict can have as many entries as you need:

```python
def router(state: State) -> Literal["path_a", "path_b", "path_c", END]:
    if state["done"]:
        return END
    elif state["score"] > 0.8:
        return "path_a"
    elif state["score"] > 0.4:
        return "path_b"
    else:
        return "path_c"

graph.add_conditional_edges(
    "check",
    router,
    {
        "path_a": "high_confidence_node",
        "path_b": "medium_confidence_node",
        "path_c": "low_confidence_node",
        END: END,
    },
)
```

Think of the router as the `if X / elif Y / else` block, and the mapping dict as the lookup table that turns each branch's label into a real destination. There's no hard cap on the number of branches — this is exactly how you'd implement something like a triage/classification node routing to N different specialist nodes.

---

## 6. Common Mistakes

1. **Router returns a label missing from the mapping dict.** LangGraph doesn't validate this when you call `add_conditional_edges` — it fails with a `KeyError` the first time the graph actually takes that branch during execution. Always make sure every possible return value of the router has a matching key in the dict (this is exactly what `Literal` return types help you catch early, per §4).

2. **Returning a node name instead of a label when the mapping expects a label** (or vice versa) — be consistent. If your mapping is `{"review": "review_node"}`, the router must return `"review"`, not `"review_node"`.

3. **Forgetting the source node needs a real edge into it.** `add_conditional_edges("check", ...)` only wires what happens *after* `check` — you still need `graph.add_edge(<something>, "check")` (or make it the entry point) to get into `check` in the first place.

4. **Using a conditional edge where a direct edge would do.** If the router always returns the same label no matter what's in state, it's not conditional — simplify to `add_edge`.

5. **Not routing to `END` anywhere reachable.** If no branch of any router in the graph can ever reach `END`, you risk an infinite loop (especially with retry/loop-back edges — see §2).

---

## 7. Full Worked Example

Combines direct edges, a multi-way conditional edge, `Literal` typing, and a loop-back to `END`:

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

class State(TypedDict):
    needs_review: bool
    approved: bool
    attempts: int

def check(state: State) -> dict:
    return {}  # imagine this inspects incoming data and sets needs_review

def review_node(state: State) -> dict:
    return {"approved": state["attempts"] >= 2}  # e.g., auto-approve after retries

def publish_node(state: State) -> dict:
    print("Published!")
    return {}

def router(state: State) -> Literal["review", "publish"]:
    return "review" if state["needs_review"] else "publish"

def review_router(state: State) -> Literal["retry", "done"]:
    return "done" if state["approved"] else "retry"

graph = StateGraph(State)
graph.add_node("check", check)
graph.add_node("review_node", review_node)
graph.add_node("publish_node", publish_node)

graph.set_entry_point("check")

graph.add_conditional_edges(
    "check",
    router,
    {"review": "review_node", "publish": "publish_node"},
)

graph.add_conditional_edges(
    "review_node",
    review_router,
    {"retry": "review_node", "done": "publish_node"},  # loop-back
)

graph.add_edge("publish_node", END)

app = graph.compile()
app.invoke({"needs_review": True, "approved": False, "attempts": 0})
```

Walk-through: `check` runs → conditional edge routes to either `review_node` or `publish_node` → if it lands on `review_node`, a *second* conditional edge either loops back to `review_node` again (`"retry"`) or moves on to `publish_node` (`"done"`) → `publish_node` runs and a direct edge sends it to `END`.

---

## 8. Interview Questions

**Q: What's the difference between `add_edge` and `add_conditional_edges`?**
A: `add_edge` is a fixed, unconditional connection — the next node is always the same. `add_conditional_edges` runs a routing function against the current state after the source node finishes, and uses a label → node-name mapping to decide the next node dynamically.

**Q: Why does the routing function return a label instead of the node name directly?**
A: Indirection decouples decision logic from graph wiring — you can rewire which node a label points to (rename nodes, restructure the graph) without touching the routing function itself.

**Q: What happens if a routing function returns a value that isn't in the mapping dict?**
A: A runtime `KeyError` when the graph executes that edge. It is not caught at graph-build time, only when that specific branch is actually taken during execution.

**Q: What does annotating a router with `Literal[...]` actually change at runtime?**
A: Nothing — it's purely a static-typing/IDE aid. It documents every valid return value and lets a type checker catch a router/mapping mismatch before you run the graph, but the runtime behavior is identical to an unannotated `-> str` function.

**Q: How do you implement a self-correcting loop in LangGraph?**
A: A conditional edge whose mapping points a label back to a node that already ran (e.g., `{"retry": "generate", "good": END}`). This is only possible because conditional edges are decided at runtime — a direct edge can't express "go back if failed."

---

## 9. Quick Revision

- **Direct edge** = fixed, always the same next node. `add_edge("A", "B")`.
- **Conditional edge** = runtime decision. `add_conditional_edges(source, router_fn, mapping_dict)`.
- Router function: `(state) -> str` — reads state, returns a **label**, not a node name.
- Mapping dict: `{label: node_name}` — translates the label into where execution actually goes.
- `Literal["a", "b", END]` on the router's return type = compile-time/IDE safety net, zero runtime effect.
- Conditional edges are what enable **branching**, **loops**, and **conditional termination** — the three things a plain LCEL chain structurally cannot do.
- Missing a label in the mapping dict = silent until that branch runs, then `KeyError`. Keep the `Literal` return type and the mapping dict's keys in sync.
