# Accumulated State in LangGraph

## What is Accumulated State?

In LangGraph, the **state** is a shared dictionary that is passed from
one node to the next.

Normally, when a node returns a value for a key, it **replaces** the
existing value.

Example:

``` python
{"count": 0}
```

Node returns:

``` python
{"count": 1}
```

Final state:

``` python
{"count": 1}
```

The old value (`0`) is overwritten.

------------------------------------------------------------------------

## Why do we need Accumulated State?

Sometimes we **do not want to overwrite** the existing value.

Instead, we want to:

-   Keep adding messages to a conversation.
-   Count how many nodes have executed.
-   Collect logs.
-   Build a list of completed steps.

This is called **accumulation**.

LangGraph supports this using:

``` python
Annotated[type, operator.add]
```

------------------------------------------------------------------------

## How `Annotated` works

``` python
messages: Annotated[list[str], operator.add]
```

-   `list[str]` → The field stores a list of strings.
-   `operator.add` → Merge lists using `+`.

Similarly,

``` python
count: Annotated[int, operator.add]
```

adds integers together instead of replacing them.

------------------------------------------------------------------------

## Flow of your example

Initial state:

``` python
{
    "messages": ["initial messages"],
    "count": 0
}
```

### Step One

Returns

``` python
{
    "messages": ["step one got executed"],
    "count": 1
}
```

After merge

``` python
messages = ["initial messages"] + ["step one got executed"]
count = 0 + 1
```

State becomes

``` python
{
    "messages": [
        "initial messages",
        "step one got executed"
    ],
    "count": 1
}
```

### Step Two

Returns

``` python
{
    "messages": ["step two got executed"],
    "count": 1
}
```

After merge

``` python
messages = [
    "initial messages",
    "step one got executed"
] + [
    "step two got executed"
]

count = 1 + 1
```

Final state

``` python
{
    "messages": [
        "initial messages",
        "step one got executed",
        "step two got executed"
    ],
    "count": 2
}
```

------------------------------------------------------------------------

# Your Code (Commented)

``` python
from typing_extensions import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END

# Define the shared state of the graph.
class AcumulatingState(TypedDict):

    # Accumulate lists by concatenating them.
    messages: Annotated[list[str], operator.add]

    # Accumulate integers by adding them.
    count: Annotated[int, operator.add]


def demo_accumated_state():

    # First node
    def step_one(state: AcumulatingState):

        # Returns a new message and increments count by 1.
        return {
            "messages": ["step one got executed"],
            "count": 1
        }

    # Second node
    def step_two(state: AcumulatingState):

        # Again returns one message and increments count by 1.
        return {
            "messages": ["step two got executed"],
            "count": 1
        }

    # Create the graph with the shared state.
    graph = StateGraph(AcumulatingState)

    # Register nodes.
    graph.add_node("step_one", step_one)
    graph.add_node("step_two", step_two)

    # Define execution order.
    graph.add_edge(START, "step_one")
    graph.add_edge("step_one", "step_two")
    graph.add_edge("step_two", END)

    # Compile the graph.
    app = graph.compile()

    # Print Mermaid graph.
    print(app.get_graph().draw_mermaid())

    # Save graph image.
    png_bytes = app.get_graph().draw_mermaid_png()

    with open("graph1.png", "wb") as f:
        f.write(png_bytes)

    print("PNG saved.")

    # Initial state.
    result = app.invoke({
        "messages": ["initial messages"],
        "count": 0
    })

    print("Accumulated State")

    print(f"messages: {result['messages']}")
    print(f"count: {result['count']}")
```

------------------------------------------------------------------------

## Output

``` text
messages:
[
 'initial messages',
 'step one got executed',
 'step two got executed'
]

count:
2
```

## Key takeaway

Without `Annotated[..., operator.add]`, each node **overwrites** the
previous value.

With `Annotated[..., operator.add]`, LangGraph **merges** values
automatically, making it ideal for chat history, logs, counters, and
workflow tracking.
