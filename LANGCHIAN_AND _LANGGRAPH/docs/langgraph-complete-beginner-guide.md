# LangGraph — Complete Beginner's Guide
*Detailed notes covering: The Problem with Simple Chains, the LangGraph Solution, When to Use It, Real-World Use Cases, LangGraph 1.0 Highlights, The Three Pillars (State, Nodes, Edges), StateGraph Workflow, State Definition, Nodes, and Edges.*

---

## Table of Contents
1. [What is LangGraph? (Quick Intro)](#1-what-is-langgraph-quick-intro)
2. [The Problem with Simple Chains](#2-the-problem-with-simple-chains)
3. [The LangGraph Solution](#3-the-langgraph-solution)
4. [When to Use LangChain vs LangGraph](#4-when-to-use-langchain-vs-langgraph)
5. [Real-World Use Cases](#5-real-world-use-cases)
6. [LangGraph 1.0 Highlights](#6-langgraph-10-highlights)
7. [The Three Pillars: State, Nodes, Edges](#7-the-three-pillars-state-nodes-edges)
8. [StateGraph Explained — The 5-Step Recipe](#8-stategraph-explained--the-5-step-recipe)
9. [State Definition (Deep Dive)](#9-state-definition-deep-dive)
10. [Nodes (Deep Dive)](#10-nodes-deep-dive)
11. [Edges (Deep Dive)](#11-edges-deep-dive)
12. [Putting It All Together — Full Example](#12-putting-it-all-together--full-example)
13. [Glossary of Every Important Term](#13-glossary-of-every-important-term)

---

## 1. What is LangGraph? (Quick Intro)

**Definition:** LangGraph is a Python framework (built by the LangChain team) for building **stateful, multi-step AI applications** — especially **AI agents** — by representing your application as a **graph** of steps instead of a straight line of steps.

**Simple analogy:**
- A **chain** is like a factory conveyor belt: items move in one direction, step by step, and can never go backward.
- A **graph** is like a city road map: you can go forward, take different routes based on conditions (traffic lights = logic), loop back around a block, and remember where you've been.

LangGraph exists because real AI agents need to **loop, retry, branch, remember things, and recover from failures** — and simple chains can't do any of that well.

---

## 2. The Problem with Simple Chains

### What is a "Simple Chain"?

**Definition:** A simple chain is a linear pipeline where the output of one step becomes the input of the next step, in a fixed order:

```
Input → Step 1 → Step 2 → Step 3 → Output
```

Every run follows the exact same path. Step 2 always comes after Step 1. There is no way to skip, repeat, or change direction.

**Example of a simple chain in plain language:**
1. Take the user's question (Input)
2. Rewrite the question to be clearer (Step 1)
3. Search documents for an answer (Step 2)
4. Generate a final answer with an LLM (Step 3)
5. Return it (Output)

This works fine — **until something goes wrong or you need more flexibility.**

### The Four Problems with Simple Chains

#### ❌ Problem 1: Can't loop back
**Meaning:** Once you pass a step, you can never return to it.

**Why it matters:** Imagine Step 3 generates an answer, but the answer is bad. Ideally you'd want to go **back** to Step 2 and search again with better keywords. In a chain, that's impossible — the pipeline only flows forward. Real agents constantly need loops: *"try → check → if bad, try again."*

#### ❌ Problem 2: No state between steps
**Meaning:** There is no shared "memory object" that all steps can read and write. Each step only sees what the previous step handed it directly.

**Why it matters:** Say Step 1 discovers the user's name and Step 3 needs it. In a chain, Step 2 must manually pass the name along even though it doesn't care about it. There's no shared whiteboard everyone can look at. This makes complex data flow messy and error-prone.

#### ❌ Problem 3: No conditional routing
**Meaning:** The chain cannot make decisions like *"IF the question is about billing, go to the billing step; ELSE go to the general step."*

**Why it matters:** Real applications need branching logic. A support bot must route different tickets to different handlers. A chain has exactly one path, so every input gets the exact same treatment.

#### ❌ Problem 4: Crashes lose all progress
**Meaning:** If the program crashes at Step 3 (server dies, API times out, power cut), **everything** done in Steps 1 and 2 is thrown away, because nothing was being saved along the way.

**Why it matters:** Imagine a 30-minute research task that crashes at minute 29. With a chain, you restart from minute 0. Nothing was checkpointed, so all progress is lost.

> **Summary:** Simple chains = one-way street, no memory board, no decisions, no save points.

---

## 3. The LangGraph Solution

LangGraph fixes all four problems by changing the model from a **line** to a **graph with shared state**.

### The picture from the slide, explained

```
State (persists throughout the whole run)
┌─────────────────────────────────────┐
│   A ──→ B ──→ C                     │
│         │ (conditional)             │
│         ↓                           │
│         D  (can loop back to B) ↺   │
└─────────────────────────────────────┘
```

- **A, B, C, D** are **nodes** (steps/functions).
- The arrow from **B down to D** is a **conditional edge** — B decides at runtime whether to continue to C or divert to D.
- **D can loop back to B** — this is a **cycle**, something a chain can never do.
- The whole thing sits inside a **State** box — a shared memory object that every node can read from and write to, and that survives the entire run.

### The Four Fixes (each one answers a chain problem)

| Chain Problem | LangGraph Fix | What it means |
|---|---|---|
| ❌ Can't loop back | ✅ **Cycles and loops** | Nodes can point back to earlier nodes. "Generate → Check → if bad, Generate again." |
| ❌ No state between steps | ✅ **Persistent state** | One shared state object flows through every node. Any node can read or update it. |
| ❌ No conditional routing | ✅ **Conditional routing** | A node can choose the next node at runtime based on logic ("if X then B, else C"). |
| ❌ Crashes lose all progress | ✅ **Crash recovery** | State is checkpointed (saved) after each step. If the app crashes, it resumes from the last checkpoint instead of restarting. |

**Key definitions introduced here:**

- **Cycle / Loop:** A path in the graph that returns to a node that was already visited. Enables retry, self-correction, and iteration.
- **Persistent State:** Data that lives for the entire execution (and can even live in a database between executions), rather than being thrown away after each step.
- **Conditional Routing:** Choosing the next step dynamically using a function that inspects the current state.
- **Crash Recovery:** Because state is saved at checkpoints, execution can resume from "when things were working" rather than from scratch.

---

## 4. When to Use LangChain vs LangGraph

LangChain and LangGraph are siblings, not enemies. You pick based on the shape of your problem.

### Use **LangChain** when:

| Situation | Why LangChain is enough |
|---|---|
| **Simple chains** | Your flow is genuinely linear: A → B → C, done. No need for graph machinery. |
| **One-shot Q&A** | User asks once, model answers once. No memory across steps needed. |
| **RAG pipelines** | Classic Retrieval-Augmented Generation: retrieve documents → stuff into prompt → answer. This is naturally a straight pipeline. |
| **No loops needed** | If you never need to revisit a step, a chain is simpler and easier to debug. |
| **Prototype phase** | Quick experiments and demos — chains are faster to write. |

### Use **LangGraph** when:

| Situation | Why you need LangGraph |
|---|---|
| **Stateful workflows** | Steps need to share and accumulate information in a common state object. |
| **Multi-turn agents** | Conversations spanning many back-and-forth turns, where context must persist. |
| **Self-correcting loops** | The agent evaluates its own output and retries until it's good ("generate → critique → regenerate"). |
| **Human-in-the-loop** | Execution must **pause**, wait for a human to review/approve, then **resume** exactly where it stopped. |
| **Production agents** | Real deployed systems that must survive crashes, be debuggable, and handle complex routing. |

> **Rule of thumb:** If your flow is a straight line and finishes in one pass → LangChain. If it needs memory, decisions, loops, pausing, or reliability → LangGraph.
>
> Note: LangChain is production-ready too — the point is that LangGraph is *specifically designed* for stateful, agentic, long-running workloads.

---

## 5. Real-World Use Cases

These are the four canonical patterns where LangGraph shines:

### 🎧 1. Customer Support Bot
**What it does:** Handles tickets, escalates, follows up.

**Why it needs LangGraph:**
- A ticket arrives → the bot tries to resolve it (node 1).
- **Conditional routing:** If it can resolve it → reply and close. If not → **escalate** to a human or a specialist node.
- **State** remembers the whole ticket history across turns.
- **Follow-up** means the workflow may pause for hours/days and resume — which requires persistent state.

### 🔍 2. Research Agent
**What it does:** Searches, evaluates, iterates **until satisfied**.

**Why it needs LangGraph:**
- Search the web (node A) → evaluate the results (node B).
- **Loop:** If results are insufficient, go **back** to node A with refined queries.
- The phrase "until satisfied" *is* a loop — impossible in a simple chain.
- State accumulates all findings across iterations.

### 💻 3. Code Review Agent
**What it does:** Analyzes code, suggests fixes, **re-checks after changes**.

**Why it needs LangGraph:**
- Analyze → suggest fixes → apply changes → **re-check** (loop back to analysis).
- This is a **self-correcting loop**: keep cycling until the code passes review.

### ✅ 4. Approval Workflows
**What it does:** Multi-day processes with human review.

**Why it needs LangGraph:**
- An AI drafts something → workflow **pauses** (interrupt) → a human reviews it (maybe tomorrow) → workflow **resumes**.
- This requires **durable state** (survives days, restarts, deployments) and **human-in-the-loop** support — both core LangGraph features.

---

## 6. LangGraph 1.0 Highlights

The four flagship capabilities of LangGraph 1.0:

### 1️⃣ Durable State
**Definition:** The application's state **survives crashes** and can **resume from a checkpoint**.

**Explanation:** After every node finishes, LangGraph saves a snapshot (checkpoint) of the state. If your server crashes at step 7 of 10, you restart and continue from step 7 — not step 1. Think of it like autosave in a video game.

### 2️⃣ Built-in Persistence
**Definition:** LangGraph ships with ready-made storage backends — **SQLite** and **Postgres** — so you write **no custom database code**.

**Explanation:**
- **SQLite** = a lightweight file-based database, great for local development.
- **Postgres** = a robust server database, great for production.
- You just plug in a "checkpointer" object and LangGraph handles saving/loading state automatically. You don't write SQL, tables, or serialization code yourself.

### 3️⃣ Human-in-the-Loop
**Definition:** **First-class interrupt/resume support** — the graph can deliberately pause execution, hand control to a human, and continue later.

**Explanation:** "First-class" means this isn't a hack — it's a built-in feature. You can mark points where the graph should stop and wait (e.g., "before sending this email, get approval"). Because state is durable, the pause can last minutes or days.

### 4️⃣ Production-Ready
**Definition:** Battle-tested at scale — **used by Uber, LinkedIn, Klarna** and others.

**Explanation:** These companies run LangGraph in real customer-facing systems, which signals the framework is stable, performant, and reliable enough for serious production workloads — not just demos.

---

## 7. The Three Pillars: State, Nodes, Edges

**Everything in LangGraph is built from exactly three concepts.** Master these three and you understand LangGraph.

### 🟪 Pillar 1: STATE
**Definition:** *What the agent knows/tracks.* The shared data structure (usually a typed dictionary) that holds everything the workflow knows at any moment.

**Analogy:** A **shared whiteboard** in a meeting room. Every person (node) who enters the room can read what's on the whiteboard and add/update notes on it before leaving.

**Examples of things stored in state:** the conversation messages so far, a counter of steps taken, the current status ("searching", "done"), retrieved documents, the draft answer.

### 🟩 Pillar 2: NODES
**Definition:** *Functions that process state.* Each node is just a Python function that receives the current state, does some work (call an LLM, run a tool, do math), and returns updates to the state.

**Analogy:** **Workers/stations** in a workshop. Each worker looks at the whiteboard (state), does their specialized job, and writes their results back on the whiteboard.

### 🟦 Pillar 3: EDGES
**Definition:** *Connections between nodes.* Edges define the order of execution — which node runs after which.

**Analogy:** **Arrows / roads** between the stations. They tell the work "where to go next." Some roads are straight (always go from A to B), and some have a fork with a signpost (conditional: go to B *or* C depending on the situation).

### How they fit together (one sentence)
> **State** is the data, **Nodes** are the functions that transform the data, and **Edges** are the wiring that decides which function runs next.

---

## 8. StateGraph Explained — The 5-Step Recipe

**Definition — StateGraph:** The main LangGraph class. It's the object you use to *build* your graph: you tell it what the state looks like, add your nodes, wire them with edges, and compile it into a runnable app.

Every LangGraph program follows the same 5 steps:

### Step 1️⃣ — Define State
```python
from typing import TypedDict

class AgentState(TypedDict):
    ...
```
**What this means:** You create a class describing the *shape* of your shared whiteboard — what fields exist and their types.

**Definition — `TypedDict`:** A Python typing tool that lets you define a dictionary with a fixed set of keys, each with a declared type. Example: `{"messages": list, "step_count": int}`. It's like a schema/blueprint for your state. It gives you autocomplete and type-checking without the overhead of a full class.

### Step 2️⃣ — Create Graph
```python
from langgraph.graph import StateGraph

graph = StateGraph(AgentState)
```
**What this means:** You instantiate a `StateGraph` and hand it your state schema. Now the graph knows what data will flow through it. At this point the graph is **empty** — no steps yet.

### Step 3️⃣ — Add Nodes
```python
graph.add_node("process", fn)
```
**What this means:** You register your worker functions. Each node gets:
- a **name** (a string like `"process"`) used to refer to it when wiring edges, and
- a **function** (`fn`) that will be executed — it takes the state and returns updates.

### Step 4️⃣ — Add Edges
```python
from langgraph.graph import START, END

graph.add_edge(START, "process")
graph.add_edge("process", END)
```
**What this means:** You wire the nodes together.

**Definition — `START`:** A special built-in marker meaning "the entry point of the graph." The edge `START → "process"` says: *when the graph runs, begin at the process node.*

**Definition — `END`:** A special built-in marker meaning "the graph is finished." An edge into `END` terminates execution.

### Step 5️⃣ — Compile
```python
app = graph.compile()
```
**What this means:** Compiling **freezes** your blueprint into an executable application. LangGraph validates the graph (checks for missing nodes, dangling edges, etc.) and returns a runnable object.

**Bonus:** the compiled graph can be **visualized** — you can literally render a picture of your nodes and edges to verify the wiring is what you intended:
```python
app.get_graph().draw_mermaid()   # produces a diagram
```

**Then you run it:**
```python
result = app.invoke({"messages": [], "step_count": 0})
```

> **Mnemonic for the 5 steps:** **D**efine → **C**reate → **N**odes → **E**dges → **C**ompile ("**D**on't **C**ode **N**ew **E**rrors, **C**ompile!")

---

## 9. State Definition (Deep Dive)

This is the most important — and most beginner-confusing — part of LangGraph. The core question:

> **When two nodes write to the same state field, what happens? Does the new value REPLACE the old one, or get MERGED with it?**

The answer depends on **how you declare the field**. There are three patterns:

### 🔵 Pattern 1: Simple Field → *Replaced each time*
```python
current_step: str
```
**Behavior:** `old → new` (overwrite)

**Explanation:** A plain field with just a type. Whenever any node returns a new value for it, the old value is **thrown away and replaced**.

**Example:**
- State before: `current_step = "searching"`
- Node returns: `{"current_step": "writing"}`
- State after: `current_step = "writing"` ✅ (the word "searching" is gone)

**Use for:** status flags, the current mode, the latest answer — anything where only the newest value matters.

### 🟢 Pattern 2: Annotated with `add_messages` → *Values accumulated*
```python
from typing import Annotated
from langgraph.graph.message import add_messages

messages: Annotated[list, add_messages]
```
**Behavior:** `[a] + [b] → [a, b]` (append/accumulate)

**Definition — `Annotated`:** A Python typing feature that lets you attach *extra metadata* to a type. Syntax: `Annotated[<type>, <extra_info>]`. LangGraph reads that extra info to learn **how to merge updates** into this field. The extra info here is called a **reducer**.

**Definition — Reducer:** A function that takes the *old value* and the *new value* of a field and decides how to combine them. Without a reducer, the default behavior is "replace."

**Definition — `add_messages`:** A built-in LangGraph reducer designed for chat message lists. Instead of replacing the message list, it **appends** new messages to the existing list (and is smart about updating a message if it has the same ID).

**Example:**
- State before: `messages = [HumanMessage("Hi")]`
- Node returns: `{"messages": [AIMessage("Hello!")]}`
- State after: `messages = [HumanMessage("Hi"), AIMessage("Hello!")]` ✅ (history preserved!)

**Use for:** conversation history — you never want a node to accidentally wipe out the whole chat.

### 🟠 Pattern 3: Annotated with `operator.add` → *Numbers sum*
```python
import operator
from typing import Annotated

token_count: Annotated[int, operator.add]
```
**Behavior:** `5 + 3 → 8` (add together)

**Definition — `operator.add`:** Python's built-in addition function (`operator.add(5, 3)` returns `8`). Used as a reducer, it means: *when a node returns a new value, ADD it to the existing value instead of replacing.*

**Example:**
- State before: `token_count = 5`
- Node returns: `{"token_count": 3}`
- State after: `token_count = 8` ✅ (5 + 3, not replaced by 3)

**Use for:** running totals — tokens used, cost accumulated, retry counters.

### Full state example combining all three
```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    current_step: str                              # replaced each time
    messages: Annotated[list, add_messages]        # accumulated (appended)
    token_count: Annotated[int, operator.add]      # summed
```

> **Key takeaway:** The *annotation* controls the *merge behavior*. No annotation = replace. `add_messages` = append messages. `operator.add` = sum numbers.

---

## 10. Nodes (Deep Dive)

### The Golden Rule of Nodes

> **Nodes receive the FULL state, but return only PARTIAL updates.**

Read that twice — it's the single most important sentence about nodes.

### What does that mean?

**INPUT — Full State:** When a node runs, LangGraph hands it the *entire* current state. The node can read anything it wants:
```python
state["messages"]        # the whole conversation
state["step_count"]      # how many steps so far
state["current_step"]    # what phase we're in
```

**PROCESS:** Inside the node, you do the actual work, typically:
1. **Read state** — pull out whatever fields you need.
2. **Do work** — call an LLM, run a search, execute a tool, do a calculation.
3. **Return updates** — build a small dictionary of *only the fields you changed*.

**OUTPUT — Partial Update:** The node returns a dictionary containing **only the fields it modified** — *not* the whole state:
```python
return {
    "messages": [resp],        # add the LLM's response
    "current_step": "done"     # update the phase
}
```
Notice `step_count` is **not** in the return — this node didn't change it, so it doesn't mention it. LangGraph merges the returned dict into the state (using each field's reducer rules from Section 9), and untouched fields stay exactly as they were.

### A complete node example
```python
def chatbot_node(state: AgentState) -> dict:
    # 1. READ: look at the full state
    conversation = state["messages"]

    # 2. WORK: call the LLM with the conversation so far
    resp = llm.invoke(conversation)

    # 3. RETURN: only what changed (partial update)
    return {
        "messages": [resp],       # add_messages reducer will APPEND this
        "current_step": "done"    # simple field will be REPLACED
    }
```

### Why "partial updates" is a great design

1. **Less error-prone:** You can't accidentally wipe out a field you forgot to copy over — untouched fields are automatically preserved.
2. **Cleaner code:** Each node's return value documents exactly what that node is responsible for changing.
3. **Efficiency:** *"Not everything has to be passed around"* — nodes don't have to reconstruct and re-emit the entire state every time.
4. **Safe merging:** Combined with reducers, multiple nodes can contribute to the same field (e.g., messages) without stepping on each other.

---

## 11. Edges (Deep Dive)

Edges are the arrows — the control flow. There are **two kinds**.

### 🟢 Direct Edge (a.k.a. normal/unconditional edge)

**Definition:** A fixed connection: *"A **always** goes to B."* Every single run, without exception, after node A finishes, node B runs next.

```
A ──→ B
```

**Code:**
```python
graph.add_edge("A", "B")
```

**Use when:** the flow at this point never varies. E.g., "after fetching data, always clean the data."

### 🟣 Conditional Edge

**Definition:** A dynamic connection: *"A goes to B **or** C, based on logic."* After node A finishes, a **routing function** inspects the state and decides where to go next.

```
        ┌──→ B
A ──?───┤
        └──→ C
```

**Code:**
```python
graph.add_conditional_edges(
    "A",                                    # 1. the source node
    routing_fn,                             # 2. the decision function
    {"route_b": "B", "route_c": "C"}        # 3. the mapping
)
```

**The three parts explained:**

1. **`"A"` — source node:** the node whose completion triggers the decision.

2. **`routing_fn` — routing function:** a plain Python function that receives the current **state** and returns a **string** representing the decision:
```python
def routing_fn(state: AgentState) -> str:
    if len(state["messages"]) > 5:
        return "route_b"      # conversation is long → go to B
    else:
        return "route_c"      # conversation is short → go to C
```
Note: it returns a *label* (like `"route_b"`), not the node name directly.

3. **`{"route_b": "B", "route_c": "C"}` — the mapping (dictionary):** translates the routing function's returned label into an actual node name. If `routing_fn` returns `"route_b"`, execution goes to node `"B"`; if it returns `"route_c"`, execution goes to node `"C"`.

**Why the extra mapping layer?** It decouples your decision logic (labels) from your graph wiring (node names). You can rewire which node a label points to without touching the routing function.

### Conditional edges are the superpower

Conditional edges are what enable everything a chain can't do:
- **Branching:** "if billing question → billing node, else → general node."
- **Loops:** the mapping can point *backwards*: `{"retry": "generate", "good": END}` — if the check fails, go back to the generate node. That's a self-correcting loop.
- **Termination:** map a label to `END` to finish the graph when a condition is met.

---

## 12. Putting It All Together — Full Example

A complete, minimal, runnable-style example using **every concept** from these notes:

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# ── STEP 1: Define State ─────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]     # accumulated
    step_count: Annotated[int, operator.add]    # summed
    current_step: str                           # replaced

# ── Node functions (receive FULL state, return PARTIAL updates) ──
def generate(state: AgentState) -> dict:
    resp = llm.invoke(state["messages"])        # do work
    return {"messages": [resp],                 # appended by reducer
            "step_count": 1,                    # +1 via operator.add
            "current_step": "generated"}        # replaced

def check(state: AgentState) -> dict:
    return {"current_step": "checked"}

# ── Routing function for the conditional edge ──
def is_good(state: AgentState) -> str:
    if state["step_count"] >= 3:                # give up after 3 tries
        return "finish"
    last = state["messages"][-1].content
    return "finish" if "final" in last else "retry"

# ── STEP 2: Create Graph ─────────────────────────────
graph = StateGraph(AgentState)

# ── STEP 3: Add Nodes ────────────────────────────────
graph.add_node("generate", generate)
graph.add_node("check", check)

# ── STEP 4: Add Edges ────────────────────────────────
graph.add_edge(START, "generate")               # direct edge
graph.add_edge("generate", "check")             # direct edge
graph.add_conditional_edges(                    # conditional edge
    "check",
    is_good,
    {"retry": "generate",                       # LOOP back!
     "finish": END}
)

# ── STEP 5: Compile ──────────────────────────────────
app = graph.compile()

# ── Run it ───────────────────────────────────────────
result = app.invoke({
    "messages": [("user", "Write me a haiku")],
    "step_count": 0,
    "current_step": "start"
})
```

**Trace what happens:**
1. `START → generate`: LLM produces an answer; messages append, step_count becomes 1.
2. `generate → check`: status updated.
3. Conditional edge at `check`: `is_good` inspects state → returns `"retry"` or `"finish"`.
4. `"retry"` → loops back to `generate` (a **cycle** — impossible in a chain!).
5. `"finish"` → `END`, and `result` holds the final state.

Add a checkpointer (`graph.compile(checkpointer=SqliteSaver(...))`) and the state survives crashes and can pause for human review — durable state, built-in persistence, human-in-the-loop.

---

## 13. Glossary of Every Important Term

| Term | Definition |
|---|---|
| **Chain** | A fixed, linear pipeline: Input → Step 1 → Step 2 → Output. No loops, branches, or shared memory. |
| **Graph** | A structure of nodes connected by edges; allows branching, loops, and shared state. |
| **LangChain** | Framework best suited to linear pipelines: simple chains, one-shot Q&A, RAG, prototypes. |
| **LangGraph** | Framework for stateful, graph-shaped AI workflows: agents, loops, human-in-the-loop, production systems. |
| **State** | The shared data object (the "whiteboard") that every node can read and update; persists through the whole run. |
| **Node** | A function that receives the full state, does work (e.g., LLM call), and returns a partial update. |
| **Edge** | A connection between nodes defining execution order. |
| **Direct Edge** | "A always goes to B." Fixed. `graph.add_edge("A", "B")`. |
| **Conditional Edge** | "A goes to B or C based on logic." Uses a routing function + mapping. `graph.add_conditional_edges(...)`. |
| **Routing Function** | A function that inspects the state and returns a string label deciding the next node. |
| **Cycle / Loop** | An edge pointing back to an earlier node, enabling retries and self-correction. |
| **StateGraph** | The builder class: define state → add nodes → add edges → compile. |
| **START / END** | Special markers for the graph's entry point and termination. |
| **Compile** | Validates the graph and turns the blueprint into a runnable app (`app = graph.compile()`). |
| **TypedDict** | A Python typing construct defining a dictionary schema with named, typed keys. |
| **Annotated** | Python typing feature attaching extra metadata (a reducer) to a state field's type. |
| **Reducer** | A function telling LangGraph *how to merge* a node's update into a field (replace vs append vs sum). |
| **add_messages** | Built-in reducer that appends new messages to the message list instead of replacing it. |
| **operator.add** | Python's addition function; as a reducer it sums numeric updates (5 + 3 → 8). |
| **Partial Update** | A node's return value containing only the fields it changed; untouched fields are preserved. |
| **Checkpoint** | A saved snapshot of state after each step; enables crash recovery and resuming. |
| **Durable State** | State that survives crashes/restarts and resumes from the last checkpoint. |
| **Persistence** | Storing state in a database (SQLite for dev, Postgres for production) with no custom DB code. |
| **Human-in-the-Loop (HITL)** | Built-in interrupt/resume: pause the graph for human review, then continue. |
| **Multi-turn Agent** | An agent that holds a conversation over many exchanges, keeping context in state. |
| **Self-correcting Loop** | Generate → evaluate → if bad, loop back and regenerate until satisfied. |
| **RAG** | Retrieval-Augmented Generation: fetch relevant documents, then answer using them — typically a linear pipeline. |

---

*End of notes — you now know the full mental model: **State** (the whiteboard) + **Nodes** (the workers) + **Edges** (the arrows), built with the 5-step recipe (Define → Create → Nodes → Edges → Compile), with reducers controlling how updates merge, and checkpoints making it all crash-proof.*
